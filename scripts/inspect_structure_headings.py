from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from textbook_kb.heading_occurrences import (
    HeadingOccurrence,
    HeadingOccurrenceRole,
    classify_heading_occurrences,
)
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
            "Inspect classified textbook structure headings, "
            "repeated occurrences, and inferred TOC/body roles."
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

    parser.add_argument(
        "--min-body-font-size",
        type=float,
        default=14.0,
        help=(
            "Minimum font size for a heading occurrence "
            "to look like a body heading."
        ),
    )

    parser.add_argument(
        "--max-body-top",
        type=float,
        default=180.0,
        help=(
            "Maximum bbox top coordinate for a heading "
            "to be considered near the top of the page."
        ),
    )

    parser.add_argument(
        "--min-body-font-gap",
        type=float,
        default=2.0,
        help=(
            "Minimum font-size gap required to choose one "
            "body heading when multiple body-like "
            "occurrences exist."
        ),
    )

    return parser.parse_args()


def format_heading_text(
    heading: StructureHeading,
) -> str:
    if heading.title is None:
        return (
            f"{heading.kind.value} "
            f"{heading.number}"
        )

    return (
        f"{heading.kind.value} "
        f"{heading.number} "
        f"{heading.title}"
    )


def build_occurrence_lookup(
    occurrences: tuple[HeadingOccurrence, ...],
) -> dict[StructureHeading, HeadingOccurrence]:
    return {
        occurrence.heading: occurrence
        for occurrence in occurrences
    }


def print_heading_occurrence(
    heading: StructureHeading,
    occurrence_number: int,
    occurrence_lookup: dict[
        StructureHeading,
        HeadingOccurrence,
    ],
) -> None:
    candidate = heading.source_candidate

    classified_occurrence = (
        occurrence_lookup[heading]
    )

    print(
        f"  Occurrence {occurrence_number}: "
        f"PDF page {heading.page_number}"
    )

    print(
        f"    role: "
        f"{classified_occurrence.role.value.upper()}"
    )

    print(
        f"    role reasons: "
        f"{', '.join(classified_occurrence.reasons)}"
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
    occurrence_lookup: dict[
        StructureHeading,
        HeadingOccurrence,
    ],
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
            occurrence_lookup=occurrence_lookup,
        )


def print_summary(
    headings: tuple[StructureHeading, ...],
    groups: tuple[StructureHeadingGroup, ...],
    occurrences: tuple[HeadingOccurrence, ...],
) -> None:
    repeated_groups = tuple(
        group
        for group in groups
        if group.is_repeated
    )

    role_counter = Counter(
        occurrence.role
        for occurrence in occurrences
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

    print()
    print("Occurrence roles:")

    for role in HeadingOccurrenceRole:
        print(
            f"  {role.value}: "
            f"{role_counter[role]}"
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

    occurrence_lookup = (
        build_occurrence_lookup(
            occurrences
        )
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

    print(
        f"Body font threshold: "
        f"{args.min_body_font_size:.1f} pt"
    )

    print(
        f"Body top threshold: "
        f"{args.max_body_top:.1f}"
    )

    print(
        f"Body font-gap threshold: "
        f"{args.min_body_font_gap:.1f} pt"
    )

    for group in groups:
        print_heading_group(
            group=group,
            occurrence_lookup=occurrence_lookup,
        )

    all_groups = group_structure_headings(
        headings
    )

    print_summary(
        headings=headings,
        groups=all_groups,
        occurrences=occurrences,
    )


if __name__ == "__main__":
    main()