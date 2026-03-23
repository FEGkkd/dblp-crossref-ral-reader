from __future__ import annotations

from typing import Any

import requests

from .models import PaperRecord, SearchConfig
from .utils import (
    guess_doi_from_url,
    expanded_execution_keywords,
    infer_journal_from_values,
    normalize_doi,
    normalize_requested_journals,
    normalize_whitespace,
    record_matches_requested_journals,
    safe_int,
    unique_preserve_order,
)


class DBLPClient:
    BASE_URL = "https://dblp.org/search/publ/api"

    def __init__(self, timeout: int = 20) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "dblp-crossref-ral-reader/0.4 (+public metadata workflow)",
            }
        )

    def _build_queries(self, execution_keyword: str) -> list[str]:
        normalized = normalize_whitespace(execution_keyword)
        if not normalized:
            return []
        queries = [normalized]
        if " " in normalized:
            queries.append(f'"{normalized}"')
        return unique_preserve_order(queries)

    def _first_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            for item in value:
                text = self._first_text(item)
                if text:
                    return text
            return ""
        if isinstance(value, dict):
            return normalize_whitespace(value.get("text") or value.get("name") or value.get("@name"))
        return normalize_whitespace(str(value))

    def _parse_authors(self, info: dict[str, Any]) -> list[str]:
        authors_block = info.get("authors") or {}
        author_items = authors_block.get("author") if isinstance(authors_block, dict) else authors_block
        if not author_items:
            return []

        if isinstance(author_items, dict):
            author_items = [author_items]
        if isinstance(author_items, str):
            author_items = [author_items]

        authors: list[str] = []
        for item in author_items:
            name = self._first_text(item)
            if name:
                authors.append(name)
        return unique_preserve_order(authors)

    def _hit_to_record(self, hit: dict[str, Any], keyword: str, requested_journal: str) -> PaperRecord | None:
        info = hit.get("info") or {}
        title = self._first_text(info.get("title"))
        if not title:
            return None

        year = safe_int(info.get("year"))
        venue = self._first_text(info.get("venue") or info.get("journal"))
        dblp_url = self._first_text(info.get("url"))
        ee_url = self._first_text(info.get("ee"))

        doi = normalize_doi(info.get("doi")) or guess_doi_from_url(ee_url)
        inferred_journal = infer_journal_from_values([venue, dblp_url, ee_url])

        record = PaperRecord(
            title=title,
            authors=self._parse_authors(info),
            doi=doi,
            url=ee_url or (f"https://doi.org/{doi}" if doi else None),
            journal=inferred_journal,
            publication_year=year,
            publication_date=str(year) if year else None,
            dblp_url=dblp_url or None,
            matched_keywords=[keyword],
            source_tags=["dblp"],
            raw_venue=venue or None,
        )
        return record if record_matches_requested_journals(record, [requested_journal]) else None

    def search_publications(self, query: str, offset: int, limit: int) -> list[dict[str, Any]]:
        params = {
            "q": query,
            "h": limit,
            "f": offset,
            "format": "json",
        }
        response = self.session.get(self.BASE_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        hits = data.get("result", {}).get("hits", {}).get("hit", [])
        if isinstance(hits, dict):
            return [hits]
        return list(hits or [])

    def fetch_candidates(self, config: SearchConfig) -> list[PaperRecord]:
        results: list[PaperRecord] = []
        journals = normalize_requested_journals(config.normalized_journals())
        per_query_target = max(min(config.max_results * 20, config.dblp_batch_size * 3), 300)
        execution_keywords = expanded_execution_keywords(config.normalized_keywords())

        for original_keyword, execution_keyword in execution_keywords:
            for journal in journals:
                for query in self._build_queries(execution_keyword):
                    collected_for_query = 0
                    for batch_index in range(config.dblp_max_batches_per_keyword):
                        offset = batch_index * config.dblp_batch_size
                        try:
                            hits = self.search_publications(query, offset=offset, limit=config.dblp_batch_size)
                        except requests.RequestException:
                            break

                        if not hits:
                            break

                        for hit in hits:
                            record = self._hit_to_record(hit, keyword=original_keyword, requested_journal=journal)
                            if record is None:
                                continue
                            record.source_tags = unique_preserve_order(record.source_tags + [f"dblp-exec:{execution_keyword}"])
                            results.append(record)
                            collected_for_query += 1
                            if collected_for_query >= per_query_target:
                                break

                        if collected_for_query >= per_query_target:
                            break

                        if len(hits) < config.dblp_batch_size:
                            break

        return results
