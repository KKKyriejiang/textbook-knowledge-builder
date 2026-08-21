from __future__ import annotations

import argparse
from pathlib import Path

from textbook_kb.structure_headings import (
    StructureHeading,
)
from textbook_kb.structure_pipeline import (
    StructureHeadingGroup,
    extract_structure_headings,
    find_repeated_structure_headings,
    group_structure_headings,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect classified textbook structure headings "
            "and identify repeated Unit, Chapter, or Section "
            "occurrences across PDF pages."
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
        help="First PDF page to inspect. Uses 1-based numbering.",
    )

    parser.add_argument(
        "--end-page",
        type=int,
        default=None,
        help=(
            "Last PDF page to inspect. Uses 1-based numbering. "
            "Defaults to the final page."
        ),
    )

    parser.add_argument(
        "--min-font-size",
        type=float,
        default=14.0,
        help=(
            "Minimum font size used by the structure "
            "candidate detector."
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
            "Only create candidates from explicit structural "
            "text patterns before classification."
        ),
    )

    parser.add_argument(
        "--repeated-only",
        action="store_true",
        help=(
            "Only print Unit, Chapter, or Section groups "
            "that occur more than once."
        ),
    )

    return parser.parse_args()


def format_heading_text(
    heading: StructureHeading,
) -> str:
    if heading.title is None:
        return f"{heading.kind.value} {heading.number}"

    return (
        f"{heading.kind.value} "
        f"{heading.number} "
        f"{heading.title}"
    )


def print_heading_occurrence(
    heading: StructureHeading,
    occurrence_number: int,
) -> None:
    candidate = heading.source_candidate

    print(
        f"  Occurrence {occurrence_number}: "
        f"PDF page {heading.page_number}"
    )

    print(
        f"    parsed: "
        f"{format_heading_text(heading)}"
    )

    print(
        f"    raw text: "
        f"{candidate.text}"
    )

    print(
        f"    font size: "
        f"{candidate.font_size:.1f} pt"
    )

    print(
        f"    fonts: "
        f"{', '.join(candidate.fonts)}"
    )

    print(
        f"    bbox: "
        f"{candidate.bbox}"
    )

    print(
        f"    candidate reasons: "
        f"{', '.join(candidate.reasons)}"
    )


def print_heading_group(
    group: StructureHeadingGroup,
) -> None:
    repeated_label = (
        "REPEATED"
        if group.is_repeated
        else "SINGLE"
    )

    print()
    print("=" * 80)

    print(
        f"{group.kind.value.upper()} "
        f"{group.number} "
        f"[{repeated_label}]"
    )

    print(
        f"Occurrences: "
        f"{len(group.headings)}"
    )

    print(
        f"PDF pages: "
        f"{', '.join(str(page) for page in group.pages)}"
    )

    for index, heading in enumerate(
        group.headings,
        start=1,
    ):
        print()

        print_heading_occurrence(
            heading=heading,
            occurrence_number=index,
        )


def print_summary(
    headings: tuple[StructureHeading, ...],
    groups: tuple[StructureHeadingGroup, ...],
) -> None:
    repeated_groups = tuple(
        group
        for group in groups
        if group.is_repeated
    )

    print()
    print("=" * 80)
    print("HEADING SUMMARY")
    print("=" * 80)

    print(
        f"Total classified headings: "
        f"{len(headings)}"
    )

    print(
        f"Unique heading identities: "
        f"{len(groups)}"
    )

    print(
        f"Repeated heading identities: "
        f"{len(repeated_groups)}"
    )

    repeated_units = sum(
        1
        for group in repeated_groups
        if group.kind.value == "unit"
    )

    repeated_chapters = sum(
        1
        for group in repeated_groups
        if group.kind.value == "chapter"
    )

    repeated_sections = sum(
        1
        for group in repeated_groups
        if group.kind.value == "section"
    )

    print(
        f"Repeated units: "
        f"{repeated_units}"
    )

    print(
        f"Repeated chapters: "
        f"{repeated_chapters}"
    )

    print(
        f"Repeated sections: "
        f"{repeated_sections}"
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

    if args.repeated_only:
        groups = find_repeated_structure_headings(
            headings
        )
    else:
        groups = group_structure_headings(
            headings
        )

    print(
        f"PDF: "
        f"{args.pdf_path.name}"
    )

    print(
        f"Classified headings: "
        f"{len(headings)}"
    )

    for group in groups:
        print_heading_group(
            group
        )

    all_groups = group_structure_headings(
        headings
    )

    print_summary(
        headings=headings,
        groups=all_groups,
    )


if __name__ == "__main__":
    main()