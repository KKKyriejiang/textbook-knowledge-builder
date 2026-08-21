from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from textbook_kb.structure_candidates import (
    StructureCandidate,
    scan_structure_candidates,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan a textbook PDF for possible Unit, Chapter, "
            "and Section heading candidates."
        )
    )

    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to the textbook PDF.",
    )

    parser.add_argument(
        "--start-page",
        type=int,
        default=1,
        help="First PDF page to scan. Uses 1-based numbering.",
    )

    parser.add_argument(
        "--end-page",
        type=int,
        default=None,
        help=(
            "Last PDF page to scan. Uses 1-based numbering. "
            "Defaults to the final page."
        ),
    )

    parser.add_argument(
        "--min-font-size",
        type=float,
        default=14.0,
        help=(
            "Text at or above this font size is considered "
            "a possible heading."
        ),
    )

    parser.add_argument(
        "--max-heading-length",
        type=int,
        default=120,
        help=(
            "Maximum text length for a large-font line to be "
            "treated as a heading candidate."
        ),
    )

    parser.add_argument(
        "--regex-only",
        action="store_true",
        help=(
            "Only show candidates matching Unit, Chapter, "
            "Section, or numbered-heading patterns."
        ),
    )

    return parser.parse_args()


def print_candidates(
    candidates: tuple[StructureCandidate, ...],
) -> None:
    if not candidates:
        print("No structure candidates found.")
        return

    current_page: int | None = None

    for candidate in candidates:
        if candidate.page_number != current_page:
            current_page = candidate.page_number

            print()
            print(
                f"--- PDF PAGE "
                f"{candidate.page_number} ---"
            )

        reasons = ", ".join(
            candidate.reasons
        )

        fonts = ", ".join(
            candidate.fonts
        )

        print(
            f"[{candidate.font_size:.1f} pt] "
            f"{candidate.text}"
        )

        print(
            f"    reason: {reasons}"
        )

        print(
            f"    font: {fonts}"
        )

        print(
            f"    bbox: {candidate.bbox}"
        )


def print_summary(
    candidates: tuple[StructureCandidate, ...],
) -> None:
    reason_counter: Counter[str] = Counter()

    for candidate in candidates:
        reason_counter.update(
            candidate.reasons
        )

    candidate_pages = {
        candidate.page_number
        for candidate in candidates
    }

    print()
    print("=" * 80)
    print("SCAN SUMMARY")
    print("=" * 80)

    print(
        f"Total candidates: "
        f"{len(candidates)}"
    )

    print(
        f"Pages containing candidates: "
        f"{len(candidate_pages)}"
    )

    if reason_counter:
        print("Candidate reasons:")

        for reason, count in sorted(
            reason_counter.items()
        ):
            print(
                f"  {reason}: {count}"
            )


def main() -> None:
    args = parse_args()

    candidates = scan_structure_candidates(
        pdf_path=args.pdf_path,
        start_page=args.start_page,
        end_page=args.end_page,
        min_font_size=args.min_font_size,
        max_heading_length=args.max_heading_length,
        regex_only=args.regex_only,
    )

    print(f"PDF: {args.pdf_path.name}")
    print(
        f"Scanning from PDF page "
        f"{args.start_page}"
    )

    if args.end_page is None:
        print("End page: final PDF page")
    else:
        print(
            f"Requested end page: "
            f"{args.end_page}"
        )

    print(
        f"Large-font threshold: "
        f"{args.min_font_size:.1f} pt"
    )

    print_candidates(candidates)

    print_summary(candidates)


if __name__ == "__main__":
    main()