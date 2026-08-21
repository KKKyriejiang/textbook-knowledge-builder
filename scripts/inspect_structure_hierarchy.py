from __future__ import annotations

import argparse
from pathlib import Path

from textbook_kb.heading_occurrences import (
    classify_heading_occurrences,
)
from textbook_kb.structure_hierarchy import (
    SectionHierarchyEntry,
    build_section_hierarchy,
)
from textbook_kb.structure_pipeline import (
    extract_structure_headings,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect reconstructed Unit, Chapter, and Section "
            "hierarchy from classified BODY headings."
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
        help=(
            "First PDF page to inspect. "
            "Uses 1-based numbering."
        ),
    )

    parser.add_argument(
        "--end-page",
        type=int,
        default=None,
        help=(
            "Last PDF page to inspect. "
            "Defaults to the final PDF page."
        ),
    )

    parser.add_argument(
        "--min-font-size",
        type=float,
        default=14.0,
        help=(
            "Minimum font size used during "
            "structure candidate detection."
        ),
    )

    parser.add_argument(
        "--max-heading-length",
        type=int,
        default=120,
        help=(
            "Maximum text length for large-font "
            "candidate detection."
        ),
    )

    parser.add_argument(
        "--regex-only",
        action="store_true",
        help=(
            "Only generate structure candidates from "
            "explicit structural text patterns."
        ),
    )

    parser.add_argument(
        "--min-body-font-size",
        type=float,
        default=14.0,
        help=(
            "Minimum font size for a heading occurrence "
            "to look like a BODY heading."
        ),
    )

    parser.add_argument(
        "--max-body-top",
        type=float,
        default=180.0,
        help=(
            "Maximum bbox top coordinate for a heading "
            "to be considered near the page top."
        ),
    )

    parser.add_argument(
        "--min-body-font-gap",
        type=float,
        default=2.0,
        help=(
            "Minimum font-size gap required to select "
            "one BODY occurrence from multiple candidates."
        ),
    )

    return parser.parse_args()


def format_heading(
    number: str,
    title: str | None,
) -> str:
    if title is None:
        return number

    return f"{number} {title}"


def print_section_entry(
    entry: SectionHierarchyEntry,
) -> None:
    section = entry.section_heading

    print()
    print("=" * 80)

    print(
        "SECTION: "
        f"{format_heading(section.number, section.title)}"
    )

    print(
        f"PDF page: "
        f"{section.page_number}"
    )

    if entry.unit_heading is None:
        print("Unit: <none>")
    else:
        unit = entry.unit_heading

        print(
            "Unit: "
            f"{format_heading(unit.number, unit.title)} "
            f"(PDF page {unit.page_number})"
        )

    if entry.chapter_heading is None:
        print("Chapter: <none>")
    else:
        chapter = entry.chapter_heading

        print(
            "Chapter: "
            f"{format_heading(chapter.number, chapter.title)} "
            f"(PDF page {chapter.page_number})"
        )

    candidate = section.source_candidate

    print(
        f"Section font size: "
        f"{candidate.font_size:.1f} pt"
    )

    print(
        f"Section bbox: "
        f"{candidate.bbox}"
    )


def print_summary(
    sections: tuple[SectionHierarchyEntry, ...],
) -> None:
    sections_with_unit = sum(
        1
        for section in sections
        if section.unit_heading is not None
    )

    sections_with_chapter = sum(
        1
        for section in sections
        if section.chapter_heading is not None
    )

    print()
    print("=" * 80)
    print("HIERARCHY SUMMARY")
    print("=" * 80)

    print(
        f"Total sections: "
        f"{len(sections)}"
    )

    print(
        f"Sections with Unit context: "
        f"{sections_with_unit}"
    )

    print(
        f"Sections with Chapter context: "
        f"{sections_with_chapter}"
    )

    print(
        f"Sections without Unit context: "
        f"{len(sections) - sections_with_unit}"
    )

    print(
        f"Sections without Chapter context: "
        f"{len(sections) - sections_with_chapter}"
    )


def main() -> None:
    args = parse_args()

    headings = extract_structure_headings(
        pdf_path=args.pdf_path,
        start_page=args.start_page,
        end_page=args.end_page,
        min_font_size=args.min_font_size,
        max_heading_length=args.max_heading_length,
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

    print(
        f"PDF: "
        f"{args.pdf_path.name}"
    )

    print(
        f"Classified headings: "
        f"{len(headings)}"
    )

    print(
        f"Reconstructed sections: "
        f"{len(hierarchy)}"
    )

    for entry in hierarchy:
        print_section_entry(
            entry
        )

    print_summary(
        hierarchy
    )


if __name__ == "__main__":
    main()