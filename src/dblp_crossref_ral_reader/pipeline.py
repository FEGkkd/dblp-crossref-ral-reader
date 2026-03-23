from __future__ import annotations

import os
import sys
from pathlib import Path

from .crossref_client import CrossrefClient
from .dblp_client import DBLPClient
from .exporter import write_outputs
from .matcher import (
    build_recommendations,
    deduplicate_records,
    group_records_by_keyword,
    keyword_overlap_counts,
    match_keywords,
    rank_records,
)
from .models import PaperRecord, SearchConfig, SearchResultPackage, SearchStats
from .semantic_scholar_client import SemanticScholarClient
from .summarizer import (
    generate_chinese_summary,
    generate_keyword_observations,
    generate_overview,
    generate_topic_tags,
)
from .utils import (
    ensure_dir,
    load_json,
    metadata_completeness,
    normalize_requested_journals,
    reconcile_preferred_fields,
    record_matches_requested_journals,
    run_dir_prefix,
    timestamp_for_run,
    within_time_window,
)


def requested_journals(config: SearchConfig) -> list[str]:
    return normalize_requested_journals(config.normalized_journals())


def fetch_candidates_from_dblp(config: SearchConfig) -> list[PaperRecord]:
    client = DBLPClient()
    records = client.fetch_candidates(config)
    journals = requested_journals(config)

    filtered: list[PaperRecord] = []
    for record in records:
        record = reconcile_preferred_fields(record)
        record.matched_keywords = match_keywords(record, config.normalized_keywords())
        if not record_matches_requested_journals(record, journals):
            continue
        if not within_time_window(
            record.publication_date,
            record.publication_year,
            config.years_back,
            config.days_back,
        ):
            continue
        filtered.append(record)

    return deduplicate_records(filtered)


def enrich_records_with_crossref(records: list[PaperRecord], config: SearchConfig) -> list[PaperRecord]:
    client = CrossrefClient(mailto=config.crossref_mailto)
    journals = requested_journals(config)
    enriched: list[PaperRecord] = []
    for record in records:
        try:
            enriched_record = client.enrich_record(record, journals=journals)
        except Exception:
            enriched_record = reconcile_preferred_fields(record)
        enriched.append(enriched_record)
    return deduplicate_records(enriched)


def filter_records_for_semantic_enrich(records: list[PaperRecord], config: SearchConfig) -> list[PaperRecord]:
    filtered: list[PaperRecord] = []
    journals = requested_journals(config)

    for record in records:
        record = reconcile_preferred_fields(record)
        if not record.title:
            continue

        record.matched_keywords = match_keywords(record, config.normalized_keywords())
        if not record.matched_keywords:
            continue
        if not record_matches_requested_journals(record, journals):
            continue
        if not within_time_window(
            record.publication_date,
            record.publication_year,
            config.years_back,
            config.days_back,
        ):
            continue

        record.metadata_completeness = metadata_completeness(record)
        filtered.append(record)

    return deduplicate_records(filtered)


def _semantic_enrich_priority(record: PaperRecord) -> tuple[str, int, int, int]:
    return (
        record.publication_date or "",
        record.publication_year or 0,
        len(record.matched_keywords),
        record.metadata_completeness,
    )


def enrich_records_with_semantic_scholar(records: list[PaperRecord], config: SearchConfig) -> list[PaperRecord]:
    if not config.enable_semantic_scholar or not records:
        return records

    api_key = os.getenv(config.semantic_scholar_api_key_env) if config.semantic_scholar_api_key_env else None
    if not api_key:
        print(
            f"Warning: Semantic Scholar API key env '{config.semantic_scholar_api_key_env}' is not set; continuing without key.",
            file=sys.stderr,
        )

    client = SemanticScholarClient(
        api_key=api_key,
        timeout=config.semantic_scholar_timeout,
        max_retries=config.semantic_scholar_max_retries,
        top_k=config.semantic_scholar_top_k,
    )

    indexed_records = list(enumerate(records))
    indexed_records.sort(key=lambda item: _semantic_enrich_priority(item[1]), reverse=True)
    selected = indexed_records[: max(0, config.semantic_scholar_enrich_limit)]
    if not selected:
        return records

    selected_indices = [index for index, _ in selected]
    selected_records = [record for _, record in selected]

    try:
        enriched_subset = client.enrich_records(selected_records)
    except Exception:
        return records

    merged = list(records)
    for index, enriched_record in zip(selected_indices, enriched_subset):
        merged[index] = reconcile_preferred_fields(enriched_record)
    return deduplicate_records(merged)


def finalize_records(records: list[PaperRecord], config: SearchConfig) -> list[PaperRecord]:
    filtered: list[PaperRecord] = []
    journals = requested_journals(config)

    for record in records:
        record = reconcile_preferred_fields(record)
        if not record.title:
            continue

        record.matched_keywords = match_keywords(record, config.normalized_keywords())
        if not record.matched_keywords:
            continue
        if not record_matches_requested_journals(record, journals):
            continue
        if not within_time_window(
            record.publication_date,
            record.publication_year,
            config.years_back,
            config.days_back,
        ):
            continue
        if config.require_abstract and not record.abstract:
            continue

        record.metadata_completeness = metadata_completeness(record)
        filtered.append(record)

    deduped = deduplicate_records(filtered)

    for record in deduped:
        record.topic_tags = generate_topic_tags(record, config.normalized_keywords())
        record.chinese_summary = generate_chinese_summary(record)
        record.metadata_completeness = metadata_completeness(record)

    ranked = rank_records(deduped)
    return ranked[: config.max_results]


def build_result_package(
    records: list[PaperRecord],
    config: SearchConfig,
    run_dir: str,
    dblp_candidate_count: int,
    crossref_enriched_count: int,
    semantic_scholar_enriched_count: int,
) -> SearchResultPackage:
    keyword_groups = (
        group_records_by_keyword(records, config.normalized_keywords())
        if config.group_by_keyword
        else {}
    )
    recommendations = build_recommendations(records, limit=min(10, len(records)))
    stats = SearchStats(
        dblp_candidates=dblp_candidate_count,
        crossref_enriched=crossref_enriched_count,
        semantic_scholar_enriched=semantic_scholar_enriched_count,
        final_papers=len(records),
        papers_with_abstract=sum(1 for item in records if item.abstract),
        papers_with_doi=sum(1 for item in records if item.doi),
        papers_with_pdf=sum(1 for item in records if item.pdf_url),
        keyword_hit_counts={
            keyword: sum(1 for item in records if keyword in item.matched_keywords)
            for keyword in config.normalized_keywords()
        },
        overlap_keyword_pairs=keyword_overlap_counts(records),
    )

    package = SearchResultPackage(
        generated_at=timestamp_for_run(),
        run_dir=str(run_dir),
        config=config,
        stats=stats,
        overview=generate_overview(records, config),
        keyword_observations=generate_keyword_observations(
            records, config.normalized_keywords()
        ),
        recommendations=recommendations,
        keyword_groups=keyword_groups,
        papers=records,
    )
    return package


def load_records_from_json_file(path: str | Path) -> tuple[SearchConfig, list[PaperRecord], dict]:
    raw = load_json(path)
    config = SearchConfig.from_dict(raw.get("config"))
    papers = [PaperRecord.from_dict(item) for item in raw.get("papers") or []]
    return config, papers, raw


def run_search_pipeline(config: SearchConfig) -> SearchResultPackage:
    journals = requested_journals(config)
    prefix = run_dir_prefix(journals)
    run_dir = ensure_dir(Path(config.output_dir) / f"{prefix}_{timestamp_for_run()}")

    dblp_records = fetch_candidates_from_dblp(config)
    crossref_records = enrich_records_with_crossref(dblp_records, config)
    filtered_records = filter_records_for_semantic_enrich(crossref_records, config)
    semantic_records = enrich_records_with_semantic_scholar(filtered_records, config)
    final_records = finalize_records(semantic_records, config)

    crossref_enriched_count = sum(
        1
        for item in crossref_records
        if any(tag.startswith("crossref") for tag in item.source_tags)
    )
    semantic_scholar_enriched_count = sum(
        1
        for item in semantic_records
        if any(tag.startswith("semantic-scholar") for tag in item.source_tags)
    )

    package = build_result_package(
        records=final_records,
        config=config,
        run_dir=str(run_dir),
        dblp_candidate_count=len(dblp_records),
        crossref_enriched_count=crossref_enriched_count,
        semantic_scholar_enriched_count=semantic_scholar_enriched_count,
    )

    write_outputs(
        package=package,
        run_dir=run_dir,
        save_json_flag=config.save_json,
        save_markdown_flag=config.save_markdown,
        save_docx_flag=config.save_docx,
    )
    return package
