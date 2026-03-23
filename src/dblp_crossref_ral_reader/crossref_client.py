from __future__ import annotations

import time
from typing import Any, Iterable
from urllib.parse import quote

import requests
from rapidfuzz import fuzz

from .models import DEFAULT_JOURNAL, PaperRecord
from .utils import (
    better_text,
    first_nonempty,
    journal_matches_requested,
    normalize_doi,
    normalize_requested_journals,
    normalize_title,
    normalize_whitespace,
    parse_crossref_message_date,
    reconcile_preferred_fields,
    strip_html_tags,
    unique_preserve_order,
)


class CrossrefClient:
    BASE_URL = "https://api.crossref.org/works"

    def __init__(self, mailto: str | None = None, timeout: int = 25, max_retries: int = 3) -> None:
        self.mailto = mailto
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()

        contact = mailto or "not-provided@example.invalid"
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": f"dblp-crossref-ral-reader/0.3 (mailto:{contact})",
            }
        )

    def _request_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        if params is None:
            params = {}
        if self.mailto:
            params = {**params, "mailto": self.mailto}

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException:
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(2 ** attempt)
                continue

            if response.status_code == 429:
                delay = int(response.headers.get("Retry-After", 2 ** attempt))
                time.sleep(delay)
                continue

            if response.status_code >= 500:
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(2 ** attempt)
                continue

            if response.status_code == 404:
                return None

            try:
                response.raise_for_status()
                return response.json()
            except Exception:
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(2 ** attempt)

        return None

    def fetch_by_doi(self, doi: str) -> dict[str, Any] | None:
        norm = normalize_doi(doi)
        if not norm:
            return None
        payload = self._request_json(f"{self.BASE_URL}/{quote(norm, safe='')}")
        if not payload:
            return None
        return payload.get("message")

    def search_by_title(self, title: str, journals: Iterable[str] | None = None) -> dict[str, Any] | None:
        params = {
            "query.title": title,
            "rows": 5,
        }
        payload = self._request_json(self.BASE_URL, params=params)
        if not payload:
            return None

        items = payload.get("message", {}).get("items", [])
        if not items:
            return None

        requested_journals = normalize_requested_journals(journals or [DEFAULT_JOURNAL])
        title_norm = normalize_title(title)
        best_item = None
        best_score = 0.0

        for item in items:
            candidate_title = normalize_whitespace(" ".join(item.get("title") or []))
            similarity = fuzz.token_sort_ratio(title_norm, normalize_title(candidate_title))

            container_title = normalize_whitespace(" ".join(item.get("container-title") or []))
            if journal_matches_requested(container_title, requested_journals):
                similarity += 5.0

            if similarity > best_score:
                best_score = similarity
                best_item = item

        if not best_item or best_score < 85:
            return None

        best_container = normalize_whitespace(" ".join(best_item.get("container-title") or []))
        if best_container and not journal_matches_requested(best_container, requested_journals):
            return None
        return best_item

    def _authors_from_message(self, message: dict[str, Any]) -> list[str]:
        authors: list[str] = []
        for item in message.get("author") or []:
            given = normalize_whitespace(item.get("given"))
            family = normalize_whitespace(item.get("family"))
            full_name = normalize_whitespace(f"{given} {family}")
            if full_name:
                authors.append(full_name)
        return unique_preserve_order(authors)

    def _message_to_patch(self, message: dict[str, Any]) -> dict[str, Any]:
        title = normalize_whitespace(" ".join(message.get("title") or [])) or None
        abstract = strip_html_tags(message.get("abstract"))
        doi = normalize_doi(message.get("DOI"))
        url = normalize_whitespace(message.get("URL")) or None
        journal = normalize_whitespace(" ".join(message.get("container-title") or [])) or None
        publication_date, publication_year = parse_crossref_message_date(message)
        subjects = unique_preserve_order(
            normalize_whitespace(item) for item in message.get("subject") or [] if item
        )
        crossref_score = message.get("score")
        if crossref_score is not None:
            try:
                crossref_score = float(crossref_score)
            except Exception:
                crossref_score = None

        return {
            "title": title,
            "authors": self._authors_from_message(message),
            "crossref_abstract": abstract,
            "doi": doi,
            "url": url,
            "journal": journal,
            "publication_year": publication_year,
            "publication_date": publication_date,
            "crossref_score": crossref_score,
            "subjects": subjects,
            "publication_type": message.get("type"),
            "publisher": normalize_whitespace(message.get("publisher")) or None,
        }

    def _merge_record(self, record: PaperRecord, patch: dict[str, Any], source_tag: str) -> PaperRecord:
        merged = PaperRecord.from_dict(record.to_dict())

        merged.title = better_text(merged.title, patch.get("title")) or merged.title
        if patch.get("authors") and len(patch.get("authors") or []) > len(merged.authors):
            merged.authors = patch.get("authors") or merged.authors
        merged.crossref_abstract = better_text(merged.crossref_abstract, patch.get("crossref_abstract"))
        merged.doi = normalize_doi(first_nonempty(merged.doi, patch.get("doi")))
        merged.url = first_nonempty(merged.url, patch.get("url"))
        merged.journal = first_nonempty(merged.journal, patch.get("journal"))
        merged.publication_date = better_text(merged.publication_date, patch.get("publication_date")) or merged.publication_date
        merged.publication_year = patch.get("publication_year") or merged.publication_year
        if patch.get("crossref_score") is not None:
            merged.crossref_score = patch.get("crossref_score")
        merged.subjects = unique_preserve_order((merged.subjects or []) + (patch.get("subjects") or []))
        merged.publication_type = first_nonempty(merged.publication_type, patch.get("publication_type"))
        merged.publisher = first_nonempty(merged.publisher, patch.get("publisher"))
        merged.source_tags = unique_preserve_order((merged.source_tags or []) + [source_tag])
        merged = reconcile_preferred_fields(merged)
        return merged

    def enrich_record(self, record: PaperRecord, journals: Iterable[str] | None = None) -> PaperRecord:
        message = None
        source_tag = ""

        if record.doi:
            message = self.fetch_by_doi(record.doi)
            source_tag = "crossref-doi"

        if message is None and record.title:
            message = self.search_by_title(record.title, journals=journals)
            source_tag = "crossref-title"

        if message is None:
            return reconcile_preferred_fields(record)

        patch = self._message_to_patch(message)
        return self._merge_record(record, patch, source_tag)
