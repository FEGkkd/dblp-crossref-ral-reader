#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dblp_crossref_ral_reader.pipeline import (
    enrich_records_with_crossref,
    finalize_records,
    load_records_from_json_file,
)
from dblp_crossref_ral_reader.utils import dump_json, ensure_dir, timestamp_for_run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Enrich DBLP candidates with Crossref.")
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--output-dir", default="./outputs/crossref_stage")
    parser.add_argument("--crossref-mailto", default=None)
    parser.add_argument("--require-abstract", action="store_true")
    parser.add_argument("--max-results", type=int, default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config, records, raw_data = load_records_from_json_file(args.input_json)

    if args.crossref_mailto:
        config.crossref_mailto = args.crossref_mailto
    if args.require_abstract:
        config.require_abstract = True
    if args.max_results is not None:
        config.max_results = args.max_results
    config.output_dir = args.output_dir

    enriched = enrich_records_with_crossref(records, config)
    finalized = finalize_records(enriched, config)

    crossref_count = sum(
        1 for item in finalized if any(tag.startswith("crossref") for tag in item.source_tags)
    )

    out_dir = ensure_dir(args.output_dir)
    out_path = out_dir / "enriched_results.json"

    payload = {
        "generated_at": timestamp_for_run(),
        "config": config.to_dict(),
        "stats": {
            "dblp_candidates": raw_data.get("stats", {}).get("dblp_candidates", len(records)),
            "crossref_enriched": crossref_count,
            "final_papers": len(finalized),
        },
        "papers": [item.to_dict() for item in finalized],
    }
    dump_json(out_path, payload)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
