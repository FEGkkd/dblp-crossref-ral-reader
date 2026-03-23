from __future__ import annotations

import math
import re
from collections import Counter
from datetime import date
from difflib import SequenceMatcher
from itertools import combinations
from typing import Iterable

try:
    from rapidfuzz import fuzz
except Exception:
    fuzz = None

from .models import PaperRecord
from .utils import (
    better_text,
    keyword_matches_text,
    metadata_completeness,
    normalize_doi,
    normalize_title,
    parse_date_to_date,
    reconcile_preferred_fields,
    unique_preserve_order,
)


def title_similarity(left: str, right: str) -> float:
    left_norm = normalize_title(left)
    right_norm = normalize_title(right)
    if not left_norm or not right_norm:
        return 0.0
    if fuzz is not None:
        return float(fuzz.token_sort_ratio(left_norm, right_norm))
    return SequenceMatcher(None, left_norm, right_norm).ratio() * 100.0


def match_keywords(record: PaperRecord, keywords: Iterable[str]) -> list[str]:
    corpus = " ".join(
        filter(
            None,
            [
                record.title or "",
                record.abstract or "",
                " ".join(record.topic_tags or []),
                " ".join(record.semantic_scholar_fields_of_study or []),
                record.raw_venue or "",
            ],
        )
    ).casefold()

    matched = [keyword for keyword in keywords if keyword_matches_text(keyword, corpus)]
    return unique_preserve_order(matched)


def merge_records(primary: PaperRecord, secondary: PaperRecord) -> PaperRecord:
    merged = PaperRecord.from_dict(primary.to_dict())

    merged.title = better_text(merged.title, secondary.title) or merged.title
    merged.crossref_abstract = better_text(merged.crossref_abstract, secondary.crossref_abstract)
    merged.semantic_scholar_abstract = better_text(merged.semantic_scholar_abstract, secondary.semantic_scholar_abstract)
    merged.doi = normalize_doi(merged.doi) or normalize_doi(secondary.doi)
    merged.url = merged.url or secondary.url
    merged.pdf_url = merged.pdf_url or secondary.pdf_url
    merged.pdf_url_source = merged.pdf_url_source or secondary.pdf_url_source
    merged.journal = merged.journal or secondary.journal
    merged.publication_date = better_text(merged.publication_date, secondary.publication_date) or merged.publication_date
    merged.publication_year = merged.publication_year or secondary.publication_year
    merged.dblp_url = merged.dblp_url or secondary.dblp_url
    if secondary.crossref_score is not None:
        merged.crossref_score = secondary.crossref_score
    merged.raw_venue = merged.raw_venue or secondary.raw_venue
    merged.publication_type = merged.publication_type or secondary.publication_type
    merged.publisher = merged.publisher or secondary.publisher
    merged.recommendation_reason = merged.recommendation_reason or secondary.recommendation_reason
    merged.chinese_summary = merged.chinese_summary or secondary.chinese_summary
    merged.abstract_source = merged.abstract_source or secondary.abstract_source

    merged.semantic_scholar_paper_id = merged.semantic_scholar_paper_id or secondary.semantic_scholar_paper_id
    merged.semantic_scholar_url = merged.semantic_scholar_url or secondary.semantic_scholar_url
    merged.semantic_scholar_publication_date = better_text(
        merged.semantic_scholar_publication_date,
        secondary.semantic_scholar_publication_date,
    ) or merged.semantic_scholar_publication_date
    if secondary.semantic_scholar_citation_count is not None:
        if merged.semantic_scholar_citation_count is None or secondary.semantic_scholar_citation_count > merged.semantic_scholar_citation_count:
            merged.semantic_scholar_citation_count = secondary.semantic_scholar_citation_count
    merged.semantic_scholar_fields_of_study = unique_preserve_order(
        (merged.semantic_scholar_fields_of_study or []) + (secondary.semantic_scholar_fields_of_study or [])
    )
    merged.semantic_scholar_open_access_pdf_url = (
        merged.semantic_scholar_open_access_pdf_url or secondary.semantic_scholar_open_access_pdf_url
    )
    merged.semantic_scholar_open_access_pdf_status = (
        merged.semantic_scholar_open_access_pdf_status or secondary.semantic_scholar_open_access_pdf_status
    )
    if secondary.semantic_scholar_match_score is not None:
        merged.semantic_scholar_match_score = secondary.semantic_scholar_match_score

    if len(secondary.authors) > len(merged.authors):
        merged.authors = list(secondary.authors)

    merged.matched_keywords = unique_preserve_order(merged.matched_keywords + secondary.matched_keywords)
    merged.source_tags = unique_preserve_order(merged.source_tags + secondary.source_tags)
    merged.topic_tags = unique_preserve_order(merged.topic_tags + secondary.topic_tags)
    merged.subjects = unique_preserve_order((merged.subjects or []) + (secondary.subjects or []))
    return reconcile_preferred_fields(merged)


def deduplicate_records(records: list[PaperRecord], title_threshold: float = 93.0) -> list[PaperRecord]:
    deduped: list[PaperRecord] = []
    doi_index: dict[str, int] = {}

    for record in records:
        record = reconcile_preferred_fields(record)
        doi_key = normalize_doi(record.doi)

        if doi_key and doi_key in doi_index:
            index = doi_index[doi_key]
            deduped[index] = merge_records(deduped[index], record)
            continue

        matched_index = None
        for idx, existing in enumerate(deduped):
            same_doi = doi_key and normalize_doi(existing.doi) == doi_key
            same_title = title_similarity(existing.title, record.title) >= title_threshold
            if same_doi or same_title:
                matched_index = idx
                break

        if matched_index is None:
            deduped.append(record)
            if doi_key:
                doi_index[doi_key] = len(deduped) - 1
        else:
            deduped[matched_index] = merge_records(deduped[matched_index], record)
            merged_doi = normalize_doi(deduped[matched_index].doi)
            if merged_doi:
                doi_index[merged_doi] = matched_index

    return deduped


def compute_rank_score(record: PaperRecord) -> float:
    score = 0.0
    today = date.today()

    candidate_date = parse_date_to_date(record.publication_date)
    if candidate_date is None and record.publication_year:
        candidate_date = date(record.publication_year, 12, 31)

    if candidate_date is not None:
        age_days = max(0, (today - candidate_date).days)
        recency_score = max(0.0, 8.0 - age_days / 365.0)
        score += recency_score
    elif record.publication_year:
        score += max(0.0, 6.0 - (today.year - record.publication_year))

    if record.abstract:
        score += 2.5
        if record.abstract_source == "semantic_scholar":
            score += 0.8
        elif record.abstract_source == "crossref":
            score += 0.4

    if record.pdf_url:
        score += 0.6

    if len(record.matched_keywords) >= 2:
        score += 2.5
    elif len(record.matched_keywords) == 1:
        score += 1.0

    completeness = metadata_completeness(record)
    score += min(4.0, completeness * 0.28)

    if any(tag.startswith("crossref") for tag in record.source_tags):
        score += 1.0
    if any(tag.startswith("semantic-scholar") for tag in record.source_tags):
        score += 0.8

    if record.semantic_scholar_citation_count:
        score += min(1.2, math.log10(record.semantic_scholar_citation_count + 1) * 0.7)

    record.metadata_completeness = completeness
    record.rank_score = round(score, 3)
    return record.rank_score


def build_recommendation_reason(record: PaperRecord) -> str:
    reasons: list[str] = []

    candidate_date = parse_date_to_date(record.publication_date)
    current_year = date.today().year
    if candidate_date is not None:
        years_old = (date.today() - candidate_date).days / 365.0
        if years_old <= 1.0:
            reasons.append("发表时间较新，适合快速了解近期方向")
        elif years_old <= 2.0:
            reasons.append("近两年发表，具备近期参考价值")
    elif record.publication_year and current_year - record.publication_year <= 2:
        reasons.append("年份较新，适合做近期文献初筛")

    if len(record.matched_keywords) >= 2:
        reasons.append("同时命中多个关键词，适合交叉主题阅读")
    elif len(record.matched_keywords) == 1:
        reasons.append("与检索关键词直接相关")

    if record.abstract:
        if record.abstract_source == "semantic_scholar":
            reasons.append("Semantic Scholar 提供了公开摘要，便于快速初筛")
        else:
            reasons.append("摘要较完整，便于快速判断方法路线")

    if record.pdf_url:
        reasons.append("存在开放获取 PDF 链接，可进一步核对原文")

    if record.semantic_scholar_citation_count and record.semantic_scholar_citation_count >= 20:
        reasons.append("引用量具备一定参考价值，可作为弱辅助信号")

    if record.metadata_completeness >= 10:
        reasons.append("DOI、日期、摘要和链接等元数据较完整，便于继续追踪")

    if not reasons:
        reasons.append("信息结构较完整，适合作为补充阅读材料")
    return "；".join(reasons) + "。"


def rank_records(records: list[PaperRecord]) -> list[PaperRecord]:
    for record in records:
        compute_rank_score(record)
        if not record.recommendation_reason:
            record.recommendation_reason = build_recommendation_reason(record)

    return sorted(
        records,
        key=lambda item: (
            item.rank_score,
            item.publication_date or "",
            item.publication_year or 0,
            len(item.matched_keywords),
        ),
        reverse=True,
    )


def group_records_by_keyword(
    records: list[PaperRecord],
    keywords: list[str],
) -> dict[str, list[dict[str, object]]]:
    groups: dict[str, list[dict[str, object]]] = {keyword: [] for keyword in keywords}
    for record in records:
        for keyword in record.matched_keywords:
            if keyword not in groups:
                groups[keyword] = []
            groups[keyword].append(
                {
                    "title": record.title,
                    "publication_year": record.publication_year,
                    "doi": record.doi,
                    "rank_score": record.rank_score,
                }
            )
    return groups


def keyword_overlap_counts(records: list[PaperRecord]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for record in records:
        unique_keywords = unique_preserve_order(record.matched_keywords)
        for left, right in combinations(sorted(unique_keywords), 2):
            counter[f"{left} <-> {right}"] += 1
    return dict(counter)


def build_recommendations(records: list[PaperRecord], limit: int = 10) -> list[dict[str, object]]:
    ranked = rank_records(list(records))[:limit]
    return [
        {
            "title": item.title,
            "doi": item.doi,
            "publication_year": item.publication_year,
            "rank_score": item.rank_score,
            "reason": item.recommendation_reason,
        }
        for item in ranked
    ]
