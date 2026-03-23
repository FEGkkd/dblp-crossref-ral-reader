from __future__ import annotations

import argparse
import json

from .models import DEFAULT_JOURNAL, SearchConfig
from .pipeline import run_search_pipeline
from .utils import normalize_requested_journals


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Search robotics venues such as RAL, T-RO, T-ASE, IJRR, RSS, CoRL, ICRA, and IROS "
            "with DBLP + Crossref retrieval and optional Semantic Scholar enrichment."
        )
    )
    parser.add_argument("--keywords", nargs="+", required=True, help="One or more keywords.")
    parser.add_argument(
        "--journal",
        default=DEFAULT_JOURNAL,
        help="Single target venue. Default: IEEE Robotics and Automation Letters",
    )
    parser.add_argument(
        "--journals",
        nargs="+",
        default=None,
        help="One or more target venues or aliases, such as RAL TRO TASE IJRR RSS CoRL ICRA IROS.",
    )
    parser.add_argument("--years-back", type=int, default=None, help="Limit results to the last N years.")
    parser.add_argument("--days-back", type=int, default=None, help="Limit results to the last N days.")
    parser.add_argument("--max-results", type=int, default=30, help="Maximum number of final papers.")
    parser.add_argument("--output-dir", default="./outputs", help="Output directory.")
    parser.add_argument("--language", default="zh", help="Report language, default zh.")
    parser.add_argument("--require-abstract", action="store_true", help="Prefer papers with abstract.")
    parser.add_argument(
        "--group-by-keyword",
        dest="group_by_keyword",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether to group report output by keyword.",
    )
    parser.add_argument(
        "--save-json",
        dest="save_json",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether to save results.json.",
    )
    parser.add_argument(
        "--save-markdown",
        dest="save_markdown",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether to save summary.md.",
    )
    parser.add_argument(
        "--save-docx",
        dest="save_docx",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether to save summary.docx.",
    )
    parser.add_argument(
        "--crossref-mailto",
        default=None,
        help="Email used for Crossref polite requests.",
    )
    parser.add_argument(
        "--enable-semantic-scholar",
        dest="enable_semantic_scholar",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable Semantic Scholar enrich for filtered papers.",
    )
    parser.add_argument(
        "--semantic-scholar-api-key-env",
        default="SEMANTIC_SCHOLAR_API_KEY",
        help="Environment variable name used to read the Semantic Scholar API key.",
    )
    parser.add_argument(
        "--semantic-scholar-top-k",
        type=int,
        default=5,
        help="Top-k Semantic Scholar title search candidates kept for local validation.",
    )
    parser.add_argument(
        "--semantic-scholar-enrich-limit",
        type=int,
        default=300,
        help="Maximum number of filtered papers to enrich with Semantic Scholar.",
    )
    parser.add_argument(
        "--semantic-scholar-timeout",
        type=int,
        default=30,
        help="Semantic Scholar request timeout in seconds.",
    )
    parser.add_argument(
        "--semantic-scholar-max-retries",
        type=int,
        default=3,
        help="Maximum retries for Semantic Scholar requests.",
    )
    return parser


def build_config_from_args(args: argparse.Namespace) -> SearchConfig:
    journals = args.journals or [args.journal]
    return SearchConfig(
        keywords=args.keywords,
        journal=journals[0],
        journals=journals,
        years_back=args.years_back,
        days_back=args.days_back,
        max_results=args.max_results,
        output_dir=args.output_dir,
        language=args.language,
        require_abstract=args.require_abstract,
        group_by_keyword=args.group_by_keyword,
        save_json=args.save_json,
        save_markdown=args.save_markdown,
        save_docx=args.save_docx,
        crossref_mailto=args.crossref_mailto,
        enable_semantic_scholar=args.enable_semantic_scholar,
        semantic_scholar_api_key_env=args.semantic_scholar_api_key_env,
        semantic_scholar_top_k=args.semantic_scholar_top_k,
        semantic_scholar_enrich_limit=args.semantic_scholar_enrich_limit,
        semantic_scholar_timeout=args.semantic_scholar_timeout,
        semantic_scholar_max_retries=args.semantic_scholar_max_retries,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = build_config_from_args(args)
    package = run_search_pipeline(config)

    summary = {
        "run_dir": package.run_dir,
        "paper_count": len(package.papers),
        "generated_files": package.stats.generated_files,
        "journals": normalize_requested_journals(config.normalized_journals()),
        "semantic_scholar_enabled": config.enable_semantic_scholar,
        "semantic_scholar_enriched": package.stats.semantic_scholar_enriched,
        "papers_with_pdf": package.stats.papers_with_pdf,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
