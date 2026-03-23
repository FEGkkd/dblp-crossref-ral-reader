#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate environment for the DBLP + Crossref + Semantic Scholar robotics venue skill."
    )
    parser.add_argument("--output-dir", default="./outputs")
    parser.add_argument("--crossref-mailto", default=None)
    parser.add_argument("--semantic-scholar-api-key-env", default="SEMANTIC_SCHOLAR_API_KEY")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    if sys.version_info < (3, 10):
        errors.append(
            f"Python 3.10+ is required, current version is "
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}."
        )

    required_modules = {
        "requests": "requests",
        "docx": "python-docx",
        "dateutil": "python-dateutil",
        "rapidfuzz": "rapidfuzz",
    }

    for module_name, package_name in required_modules.items():
        try:
            importlib.import_module(module_name)
        except Exception:
            errors.append(f"Missing dependency: {package_name}")

    output_dir = Path(args.output_dir).resolve()
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        errors.append(f"Cannot create output directory {output_dir}: {exc}")

    if not args.crossref_mailto:
        warnings.append(
            "crossref_mailto was not provided. The pipeline can still run, "
            "but polite requests with contact info are strongly recommended."
        )

    if not os.getenv(args.semantic_scholar_api_key_env):
        warnings.append(
            f"Semantic Scholar API key env '{args.semantic_scholar_api_key_env}' was not found. "
            "The pipeline can still run without it, but enrich requests may be more rate-limited."
        )

    print("Environment validation")
    print(f"- Python: {sys.version.split()[0]}")
    print(f"- Output directory: {output_dir}")
    print("- Supported venues: RAL, T-RO, T-ASE, ICRA, IROS")
    print(f"- Semantic Scholar API key env: {args.semantic_scholar_api_key_env}")

    if warnings:
        print("- Warnings:")
        for item in warnings:
            print(f"  * {item}")

    if errors:
        print("- Errors:")
        for item in errors:
            print(f"  * {item}")
        return 1

    print("- Status: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
