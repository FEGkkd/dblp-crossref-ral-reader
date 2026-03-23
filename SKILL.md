---
name: dblp-crossref-ral-reader
description: Use this skill when the user wants to search robotics venues such as IEEE Robotics and Automation Letters, IEEE Transactions on Robotics, IEEE Transactions on Automation Science and Engineering, The International Journal of Robotics Research, Robotics: Science and Systems, Conference on Robot Learning, ICRA, and IROS with DBLP + Crossref retrieval and Semantic Scholar enrichment, then generate a structured Chinese summary report.
---

# dblp-crossref-ral-reader

Use this skill when the user needs a reusable workflow for retrieving robotics venue papers with DBLP + Crossref retrieval, then enriching filtered papers with Semantic Scholar abstract and open-access PDF metadata before generating a Chinese JSON / Markdown / DOCX summary report.

## What This Skill Does

This skill:

1. Accepts one or more research keywords.
2. Accepts one or more target venues, defaulting to `IEEE Robotics and Automation Letters`.
3. Uses DBLP public search APIs to collect candidate papers and constrain the venue to the requested venue set as much as possible.
4. Uses Crossref REST API to enrich publication metadata, prioritizing DOI lookup and falling back to title lookup.
5. Performs local keyword matching, deduplication, merge, completeness scoring, recency-first ranking, and recommendation selection.
6. Enriches filtered papers with Semantic Scholar when enabled, adding abstract, Semantic Scholar page URL, publication date, citation count, fields of study, and open-access PDF metadata when available.
7. Generates:
   - `results.json`
   - `summary.md`
   - `summary.docx`
8. Produces Chinese summaries and recommendation reasons without requiring paid APIs or IEEE credentials.

## Supported Venues

Built-in aliases currently include:

1. `RAL` -> `IEEE Robotics and Automation Letters`
2. `TRO` / `T-RO` -> `IEEE Transactions on Robotics`
3. `TASE` / `T-ASE` -> `IEEE Transactions on Automation Science and Engineering`
4. `IJRR` -> `The International Journal of Robotics Research`
5. `RSS` -> `Robotics: Science and Systems`
6. `CoRL` -> `Conference on Robot Learning`
7. `ICRA` -> `IEEE International Conference on Robotics and Automation`
8. `IROS` -> `IEEE/RSJ International Conference on Intelligent Robots and Systems`

## What This Skill Will Not Do

This skill will not:

1. Call the IEEE Xplore official API.
2. Scrape IEEE Xplore webpages.
3. Use Selenium, Playwright, or browser automation against IEEE pages.
4. Depend on any login-protected IEEE workflow.
5. Download PDF files themselves.
6. Parse PDF full text.
7. Guarantee Semantic Scholar enrich for every paper.
8. Guarantee that an `openAccessPdf.url` is always actually reachable; it is treated as public metadata only.
9. Replace a full literature review. It is a retrieval-and-organization workflow, not a citation-quality judgment engine.

## When To Trigger

Trigger this skill when the user wants to:

1. Search one or more supported robotics venues for one or more topics.
2. Prefer recent papers.
3. Build a structured reading list from public metadata sources.
4. Generate a Chinese summary package suitable for internal review, note taking, or briefing.
5. Preserve DBLP + Crossref retrieval as the main workflow, while adding Semantic Scholar abstract and OA PDF enrichment on filtered papers.

## When Not To Trigger

Do not use this skill when the user needs:

1. Full-text access, PDF downloading, or section-level parsing.
2. Exact IEEE Xplore indexing behavior or official IEEE API coverage.
3. Venues outside the supported venue list unless the code is explicitly extended.
4. Exhaustive bibliometrics, citation network analysis, or institution-level analytics.
5. A workflow that must rely on crawling closed or access-restricted sources.

## Default Scope

- Default venue set: `IEEE Robotics and Automation Letters (RAL)`
- Retrieval sources: `DBLP`, `Crossref`
- Enrichment source: `Semantic Scholar` (optional, filtered-papers only)
- Output language: `zh`
- Output formats: `JSON`, `Markdown`, `DOCX`

## Standard Workflow

1. Read input parameters.
2. Search DBLP with keyword batches and paginate when needed.
3. Filter candidates to the requested venue set using venue, container, and DBLP path heuristics.
4. Normalize candidate metadata.
5. Enrich with Crossref using DOI first, then title.
6. Run local keyword matching, deduplication, merge, and filtering.
7. Enrich filtered papers with Semantic Scholar.
8. Generate ranking, grouping, recommendation logic, and Chinese report sections.
9. Write output files into a timestamped directory.

## Inputs

The skill accepts the following parameters:

- `keywords: list[str]`
- `journal: str = "IEEE Robotics and Automation Letters"`
- `journals: list[str] | None = None`
- `years_back: int | None = None`
- `days_back: int | None = None`
- `max_results: int = 30`
- `output_dir: str = "./outputs"`
- `language: str = "zh"`
- `require_abstract: bool = false`
- `group_by_keyword: bool = true`
- `save_json: bool = true`
- `save_markdown: bool = true`
- `save_docx: bool = true`
- `crossref_mailto: str | None = None`
- `enable_semantic_scholar: bool = true`
- `semantic_scholar_api_key_env: str = "SEMANTIC_SCHOLAR_API_KEY"`
- `semantic_scholar_top_k: int = 5`
- `semantic_scholar_enrich_limit: int = 300`
- `semantic_scholar_timeout: int = 30`
- `semantic_scholar_max_retries: int = 3`

## Outputs

For each run, the skill creates one of the following:

- single venue: `ral_search_YYYYMMDD_HHMMSS/`, `tro_search_...`, `tase_search_...`, `icra_search_...`, `iros_search_...`
- multiple venues: `robot_journal_search_YYYYMMDD_HHMMSS/`

Containing:

- `results.json`: normalized structured output, parameters, statistics, and Semantic Scholar enrich fields
- `summary.md`: editable Chinese report
- `summary.docx`: shareable Chinese report document

## Failure Handling

If any stage partially fails:

1. DBLP search failure:
   - retry by keyword batch
   - surface a clear error if no candidates can be fetched
2. Crossref enrichment failure:
   - keep DBLP-only records
   - record source tags and completeness gaps
3. Semantic Scholar enrichment failure:
   - keep DBLP + Crossref results unchanged
   - do not abort the main pipeline
4. Abstract missing:
   - continue with title/authors/date-based summary
5. DOCX generation failure:
   - keep JSON/Markdown outputs
6. No result after filtering:
   - write an empty-but-valid result package with the query context and zero-hit explanation

## Execution Boundary

This skill is intentionally constrained:

1. Main retrieval is limited to DBLP + Crossref.
2. Semantic Scholar is enrichment-only, not the primary recall source.
3. Venue locking is heuristic but transparent.
4. Summary text is generated from metadata and abstract content only.
5. Recommendation logic is explainable and deterministic.
6. OA PDF metadata is treated as a link signal, not as a guarantee of downloadability or accessibility.

## Files To Read First

1. `README.md`
2. `references/data_sources.md`
3. `references/ranking_and_dedup.md`
4. `scripts/run_pipeline.py`
5. `src/dblp_crossref_ral_reader/pipeline.py`
6. `src/dblp_crossref_ral_reader/semantic_scholar_client.py`

## Recommended Execution

Validate the environment first:

```bash
python scripts/validate_env.py \
  --output-dir ./outputs \
  --crossref-mailto your_email@example.com \
  --semantic-scholar-api-key-env SEMANTIC_SCHOLAR_API_KEY
```

Run the full pipeline with Semantic Scholar enrich enabled:

```bash
python scripts/run_pipeline.py \
  --keywords "formation control" "multi-UAV" "reinforcement learning" \
  --journals RAL TRO \
  --days-back 365 \
  --max-results 30 \
  --output-dir ./outputs \
  --crossref-mailto your_email@example.com \
  --enable-semantic-scholar \
  --semantic-scholar-api-key-env SEMANTIC_SCHOLAR_API_KEY
```

Or call the package CLI directly:

```bash
python -m dblp_crossref_ral_reader.cli \
  --keywords "formation control" "multi-UAV" "reinforcement learning" \
  --journals RAL TRO \
  --days-back 365 \
  --max-results 30 \
  --output-dir ./outputs \
  --crossref-mailto your_email@example.com \
  --enable-semantic-scholar
```
