from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from textbook_kb.knowledge_quality import (
    review_knowledge_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Review a local knowledge JSON file using public-safe "
            "schema, privacy, and content-count checks."
        )
    )

    parser.add_argument(
        "input_path",
        type=Path,
        help=(
            "Path to a local knowledge JSON file. "
            "The report never prints raw source text."
        ),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        report = review_knowledge_json(
            args.input_path
        )
    except Exception as exc:
        print(
            "knowledge_quality_status=failed "
            f"error_type={type(exc).__name__}",
            file=sys.stderr,
        )

        return 1

    print(
        "knowledge_quality_status=passed"
        if report.passed
        else "knowledge_quality_status=warning"
    )

    print(
        json.dumps(
            report.to_public_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )

    return 0 if report.passed else 2


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
