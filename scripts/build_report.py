#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dblp_crossref_ral_reader.exporter import write_outputs
from dblp_crossref_ral_reader.pipeline import (
    build_result_package,
    finalize_records,
    load_records_from_json_file,
)
from dblp_crossref_ral_reader.utils import ensure_dir, run_dir_prefix, timestamp_for_run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Markdown/DOCX report from normalized JSON.")
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--output-dir", default="./outputs/final_report")
    parser.add_argument(
        "--save-json",
        dest="save_json",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--save-markdown",
        dest="save_markdown",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--save-docx",
        dest="save_docx",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config, records, raw_data = load_records_from_json_file(args.input_json)

    config.output_dir = args.output_dir
    config.save_json = args.save_json
    config.save_markdown = args.save_markdown
    config.save_docx = args.save_docx

    finalized = finalize_records(records, config)
    prefix = run_dir_prefix(config.normalized_journals())
    run_dir = ensure_dir(Path(args.output_dir) / f"{prefix}_{timestamp_for_run()}")

    package = build_result_package(
        records=finalized,
        config=config,
        run_dir=str(run_dir),
        dblp_candidate_count=raw_data.get("stats", {}).get("dblp_candidates", len(records)),
        crossref_enriched_count=raw_data.get("stats", {}).get("crossref_enriched", 0),
    )
    write_outputs(
        package,
        run_dir,
        save_json_flag=config.save_json,
        save_markdown_flag=config.save_markdown,
        save_docx_flag=config.save_docx,
    )
    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
