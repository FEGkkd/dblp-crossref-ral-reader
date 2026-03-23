from __future__ import annotations

import time
from typing import Any
from urllib.parse import quote

import requests

from .matcher import title_similarity
from .models import PaperRecord
from .utils import (
    author_overlap_ratio,
    chunks,
    journal_matches_requested,
    normalize_doi,
    normalize_requested_journals,
    normalize_whitespace,
    reconcile_preferred_fields,
    safe_int,
    strip_html_tags,
    unique_preserve_order,
)


class SemanticScholarClient:
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    PAPER_FIELDS = (
        "paperId",
        "title",
        "url",
        "abstract",
        "publicationDate",
        "citationCount",
        "fieldsOfStudy",
        "openAccessPdf",
        "externalIds",
        "year",
        "authors",
        "venue",
    )

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
        top_k: int = 5,
        pause_seconds: float = 0.15,
    ) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.top_k = max(1, top_k)
        self.pause_seconds = max(0.0, pause_seconds)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "dblp-crossref-ral-reader/0.6 (+semantic-scholar-enrich)",
            }
        )
        if api_key:
            self.session.headers["x-api-key"] = api_key

    @property
    def fields_param(self) -> str:
        return ",".join(self.PAPER_FIELDS)

    def _request_json(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        params = params or {}
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    params=params,
                    json=json_payload,
                    timeout=self.timeout,
                )
            except requests.RequestException:
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(2 ** attempt)
                continue

            if response.status_code == 404:
                return None
            if response.status_code == 429:
                delay = int(response.headers.get("Retry-After", max(1, 2 ** attempt)))
                time.sleep(delay)
                continue
            if response.status_code >= 500:
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(2 ** attempt)
                continue

            try:
                response.raise_for_status()
                payload = response.json()
                if self.pause_seconds:
                    time.sleep(self.pause_seconds)
                return payload
            except Exception:
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(2 ** attempt)
        return None

    def _normalize_fields_of_study(self, values: Any) -> list[str]:
        fields: list[str] = []
        for item in values or []:
            if isinstance(item, dict):
                label = normalize_whitespace(item.get("category") or item.get("name"))
            else:
                label = normalize_whitespace(str(item))
            if label:
                fields.append(label)
        return unique_preserve_order(fields)

    def _authors_from_candidate(self, candidate: dict[str, Any]) -> list[str]:
        authors: list[str] = []
        for item in candidate.get("authors") or []:
            if isinstance(item, dict):
                name = normalize_whitespace(item.get("name"))
            else:
                name = normalize_whitespace(str(item))
            if name:
                authors.append(name)
        return unique_preserve_order(authors)

    def _candidate_doi(self, candidate: dict[str, Any]) -> str | None:
        external_ids = candidate.get("externalIds") or {}
        return normalize_doi(external_ids.get("DOI"))

    def _candidate_publication_year(self, candidate: dict[str, Any]) -> int | None:
        year = safe_int(candidate.get("year"))
        if year is not None:
            return year
        publication_date = normalize_whitespace(candidate.get("publicationDate"))
        if publication_date[:4].isdigit():
            return int(publication_date[:4])
        return None

    def _compute_match_score(self, record: PaperRecord, candidate: dict[str, Any]) -> tuple[float, float, bool]:
        candidate_title = normalize_whitespace(candidate.get("title"))
        candidate_doi = self._candidate_doi(candidate)
        candidate_year = self._candidate_publication_year(candidate)
        candidate_venue = normalize_whitespace(candidate.get("venue"))
        candidate_authors = self._authors_from_candidate(candidate)

        doi_exact = bool(record.doi and candidate_doi and normalize_doi(record.doi) == candidate_doi)
        title_score = title_similarity(record.title, candidate_title)
        year_score = 0.0
        if record.publication_year and candidate_year:
            delta = abs(record.publication_year - candidate_year)
            if delta == 0:
                year_score = 5.0
            elif delta == 1:
                year_score = 2.5
        venue_score = 3.0 if journal_matches_requested(candidate_venue, [record.journal or record.raw_venue or ""]) else 0.0
        author_score = min(5.0, author_overlap_ratio(record.authors, candidate_authors) * 5.0)

        score = 0.0
        if doi_exact:
            score += 60.0
        score += min(30.0, title_score * 0.3)
        score += year_score + venue_score + author_score
        return round(score, 3), title_score, doi_exact

    def _confident_match(self, score: float, title_score: float, doi_exact: bool) -> bool:
        if doi_exact:
            return score >= 60.0
        return title_score >= 88.0 and score >= 70.0

    def _candidate_to_patch(self, candidate: dict[str, Any], match_score: float) -> dict[str, Any]:
        open_access_pdf = candidate.get("openAccessPdf") or {}
        return {
            "semantic_scholar_paper_id": normalize_whitespace(candidate.get("paperId")) or None,
            "semantic_scholar_url": normalize_whitespace(candidate.get("url")) or None,
            "semantic_scholar_abstract": strip_html_tags(candidate.get("abstract")),
            "semantic_scholar_publication_date": normalize_whitespace(candidate.get("publicationDate")) or None,
            "semantic_scholar_citation_count": safe_int(candidate.get("citationCount")),
            "semantic_scholar_fields_of_study": self._normalize_fields_of_study(candidate.get("fieldsOfStudy")),
            "semantic_scholar_open_access_pdf_url": normalize_whitespace(open_access_pdf.get("url")) or None,
            "semantic_scholar_open_access_pdf_status": normalize_whitespace(open_access_pdf.get("status")) or None,
            "semantic_scholar_match_score": match_score,
        }

    def _merge_record(self, record: PaperRecord, patch: dict[str, Any], source_tag: str) -> PaperRecord:
        merged = PaperRecord.from_dict(record.to_dict())
        merged.semantic_scholar_paper_id = merged.semantic_scholar_paper_id or patch.get("semantic_scholar_paper_id")
        merged.semantic_scholar_url = merged.semantic_scholar_url or patch.get("semantic_scholar_url")
        merged.semantic_scholar_abstract = patch.get("semantic_scholar_abstract") or merged.semantic_scholar_abstract
        merged.semantic_scholar_publication_date = (
            patch.get("semantic_scholar_publication_date") or merged.semantic_scholar_publication_date
        )
        citation_count = patch.get("semantic_scholar_citation_count")
        if citation_count is not None:
            if merged.semantic_scholar_citation_count is None or citation_count > merged.semantic_scholar_citation_count:
                merged.semantic_scholar_citation_count = citation_count
        merged.semantic_scholar_fields_of_study = unique_preserve_order(
            (merged.semantic_scholar_fields_of_study or []) + (patch.get("semantic_scholar_fields_of_study") or [])
        )
        merged.semantic_scholar_open_access_pdf_url = (
            patch.get("semantic_scholar_open_access_pdf_url") or merged.semantic_scholar_open_access_pdf_url
        )
        merged.semantic_scholar_open_access_pdf_status = (
            patch.get("semantic_scholar_open_access_pdf_status") or merged.semantic_scholar_open_access_pdf_status
        )
        merged.semantic_scholar_match_score = patch.get("semantic_scholar_match_score") or merged.semantic_scholar_match_score
        merged.source_tags = unique_preserve_order((merged.source_tags or []) + [source_tag])
        return reconcile_preferred_fields(merged)

    def fetch_by_doi(self, doi: str) -> dict[str, Any] | None:
        norm = normalize_doi(doi)
        if not norm:
            return None
        identifier = quote(f"DOI:{norm}", safe="")
        payload = self._request_json(
            "GET",
            f"{self.BASE_URL}/paper/{identifier}",
            params={"fields": self.fields_param},
        )
        return payload if isinstance(payload, dict) else None

    def fetch_by_doi_batch(self, dois: list[str]) -> dict[str, dict[str, Any]]:
        normalized_dois = [normalize_doi(item) for item in dois]
        normalized_dois = [item for item in normalized_dois if item]
        if not normalized_dois:
            return {}

        results: dict[str, dict[str, Any]] = {}
        for batch in chunks(normalized_dois, 100):
            payload = self._request_json(
                "POST",
                f"{self.BASE_URL}/paper/batch",
                params={"fields": self.fields_param},
                json_payload={"ids": batch},
            )
            if not isinstance(payload, list):
                continue
            for item in payload:
                if not isinstance(item, dict):
                    continue
                candidate_doi = self._candidate_doi(item)
                if candidate_doi:
                    results[candidate_doi] = item
        return results

    def search_by_title(self, title: str) -> list[dict[str, Any]]:
        payload = self._request_json(
            "GET",
            f"{self.BASE_URL}/paper/search",
            params={
                "query": title,
                "limit": self.top_k,
                "fields": self.fields_param,
            },
        )
        if not isinstance(payload, dict):
            return []
        items = payload.get("data") or []
        return [item for item in items if isinstance(item, dict)]

    def enrich_record(self, record: PaperRecord, doi_candidates: dict[str, dict[str, Any]] | None = None) -> PaperRecord:
        doi_candidates = doi_candidates or {}
        if record.doi:
            candidate = doi_candidates.get(normalize_doi(record.doi)) or self.fetch_by_doi(record.doi)
            if candidate:
                score, title_score, doi_exact = self._compute_match_score(record, candidate)
                if self._confident_match(score, title_score, doi_exact):
                    return self._merge_record(
                        record,
                        self._candidate_to_patch(candidate, score),
                        "semantic-scholar-doi",
                    )

        best_record = record
        best_score = 0.0
        for candidate in self.search_by_title(record.title):
            score, title_score, doi_exact = self._compute_match_score(record, candidate)
            if not self._confident_match(score, title_score, doi_exact):
                continue
            if score > best_score:
                best_score = score
                best_record = self._merge_record(
                    record,
                    self._candidate_to_patch(candidate, score),
                    "semantic-scholar-title",
                )
        return best_record

    def enrich_records(self, records: list[PaperRecord]) -> list[PaperRecord]:
        doi_map = self.fetch_by_doi_batch([item.doi for item in records if item.doi])
        return [self.enrich_record(record, doi_candidates=doi_map) for record in records]
