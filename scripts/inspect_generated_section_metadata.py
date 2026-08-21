from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import fitz

from textbook_kb.heading_occurrences import (
    classify_heading_occurrences,
)
from textbook_kb.section_metadata_builder import (
    SectionEndReason,
    build_section_metadata_records,
    derive_section_ranges,
)
from textbook_kb.structure_boundaries import (
    detect_structure_boundaries,
)
from textbook_kb.structure_hierarchy import (
    build_section_hierarchy,
)
from textbook_kb.structure_pipeline import (
    extract_structure_headings,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate and inspect SectionMetadata records "
            "derived from textbook structure detection."
        )
    )

    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to the textbook PDF.",
    )

    parser.add_argument(
        "--regex-only",
        action="store_true",
        help=(
            "Only use explicit structural text patterns "
            "during heading candidate detection."
        ),
    )

    parser.add_argument(
        "--min-body-font-size",
        type=float,
        default=14.0,
        help=(
            "Minimum font size for BODY heading detection."
        ),
    )

    parser.add_argument(
        "--max-body-top",
        type=float,
        default=180.0,
        help=(
            "Maximum bbox top position for BODY "
            "heading detection."
        ),
    )

    parser.add_argument(
        "--min-body-font-gap",
        type=float,
        default=2.0,
        help=(
            "Minimum font-size gap used when choosing "
            "between multiple BODY-like headings."
        ),
    )

    parser.add_argument(
        "--min-boundary-font-size",
        type=float,
        default=18.0,
        help=(
            "Minimum font size for chapter terminal "
            "boundary detection."
        ),
    )

    parser.add_argument(
        "--max-boundary-top",
        type=float,
        default=180.0,
        help=(
            "Maximum bbox top position for chapter "
            "terminal boundary detection."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with fitz.open(args.pdf_path) as document:
        final_page = document.page_count

    headings = extract_structure_headings(
        pdf_path=args.pdf_path,
        regex_only=args.regex_only,
    )

    occurrences = classify_heading_occurrences(
        headings=headings,
        min_body_font_size=args.min_body_font_size,
        max_body_top=args.max_body_top,
        min_body_font_gap=args.min_body_font_gap,
    )

    hierarchy = build_section_hierarchy(
        occurrences
    )

    boundaries = detect_structure_boundaries(
        pdf_path=args.pdf_path,
        min_boundary_font_size=args.min_boundary_font_size,
        max_boundary_top=args.max_boundary_top,
    )

    ranges = derive_section_ranges(
        hierarchy=hierarchy,
        boundaries=boundaries,
        final_page=final_page,
    )

    records = build_section_metadata_records(
        ranges
    )

    print(
        f"PDF: {args.pdf_path.name}"
    )

    print(
        f"PDF pages: {final_page}"
    )

    print(
        f"Section metadata records: {len(records)}"
    )

    for record, section_range in zip(
        records,
        ranges,
        strict=True,
    ):
        print()
        print("=" * 80)

        print(
            f"Section: {record.section}"
        )

        print(
            f"Chapter: "
            f"{record.chapter or '<none>'}"
        )

        print(
            f"Unit: "
            f"{record.unit or '<none>'}"
        )

        print(
            f"Page range: "
            f"{record.page_start}-{record.page_end}"
        )

        print(
            f"End reason: "
            f"{section_range.end_reason.value}"
        )

        if section_range.stop_page is not None:
            print(
                f"Stop page: "
                f"{section_range.stop_page}"
            )

    reason_counter = Counter(
        section_range.end_reason
        for section_range in ranges
    )

    sections_with_chapter = sum(
        1
        for record in records
        if record.chapter is not None
    )

    sections_with_unit = sum(
        1
        for record in records
        if record.unit is not None
    )

    print()
    print("=" * 80)
    print("SECTION METADATA SUMMARY")
    print("=" * 80)

    print(
        f"Total records: "
        f"{len(records)}"
    )

    print(
        f"With Chapter context: "
        f"{sections_with_chapter}"
    )

    print(
        f"With Unit context: "
        f"{sections_with_unit}"
    )

    print("Page-end reasons:")

    for reason in SectionEndReason:
        print(
            f"  {reason.value}: "
            f"{reason_counter[reason]}"
        )


if __name__ == "__main__":
    main()