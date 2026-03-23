#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dblp_crossref_ral_reader.models import SearchConfig
from dblp_crossref_ral_reader.pipeline import fetch_candidates_from_dblp
from dblp_crossref_ral_reader.utils import dump_json, ensure_dir, timestamp_for_run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch candidates from DBLP for one or more robotics venues.")
    parser.add_argument("--keywords", nargs="+", required=True)
    parser.add_argument(
        "--journal",
        default="IEEE Robotics and Automation Letters",
    )
    parser.add_argument(
        "--journals",
        nargs="+",
        default=None,
        help="One or more target venues or aliases, such as RAL TRO TASE ICRA IROS.",
    )
    parser.add_argument("--years-back", type=int, default=None)
    parser.add_argument("--days-back", type=int, default=None)
    parser.add_argument("--max-results", type=int, default=30)
    parser.add_argument("--output-dir", default="./outputs/dblp_stage")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    journals = args.journals or [args.journal]
    config = SearchConfig(
        keywords=args.keywords,
        journal=journals[0],
        journals=journals,
        years_back=args.years_back,
        days_back=args.days_back,
        max_results=args.max_results,
        output_dir=args.output_dir,
        save_json=True,
        save_markdown=False,
        save_docx=False,
    )

    records = fetch_candidates_from_dblp(config)
    out_dir = ensure_dir(args.output_dir)
    out_path = out_dir / "dblp_candidates.json"

    payload = {
        "generated_at": timestamp_for_run(),
        "config": config.to_dict(),
        "stats": {
            "dblp_candidates": len(records),
        },
        "papers": [item.to_dict() for item in records],
    }
    dump_json(out_path, payload)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
