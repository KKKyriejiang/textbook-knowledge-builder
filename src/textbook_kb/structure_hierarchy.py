from __future__ import annotations

from dataclasses import dataclass

from textbook_kb.heading_occurrences import (
    HeadingOccurrence,
    HeadingOccurrenceRole,
)
from textbook_kb.structure_headings import (
    HeadingKind,
    StructureHeading,
)


@dataclass(frozen=True, slots=True)
class SectionHierarchyEntry:
    unit_heading: StructureHeading | None
    chapter_heading: StructureHeading | None
    section_heading: StructureHeading

    def __post_init__(self) -> None:
        if (
            self.unit_heading is not None
            and self.unit_heading.kind != HeadingKind.UNIT
        ):
            raise ValueError(
                "unit_heading must have kind UNIT."
            )

        if (
            self.chapter_heading is not None
            and self.chapter_heading.kind != HeadingKind.CHAPTER
        ):
            raise ValueError(
                "chapter_heading must have kind CHAPTER."
            )

        if self.section_heading.kind != HeadingKind.SECTION:
            raise ValueError(
                "section_heading must have kind SECTION."
            )

        if (
            self.unit_heading is not None
            and self.unit_heading.page_number
            > self.section_heading.page_number
        ):
            raise ValueError(
                "unit_heading cannot appear after section_heading."
            )

        if (
            self.chapter_heading is not None
            and self.chapter_heading.page_number
            > self.section_heading.page_number
        ):
            raise ValueError(
                "chapter_heading cannot appear after section_heading."
            )


def select_body_headings(
    occurrences: tuple[HeadingOccurrence, ...],
) -> tuple[StructureHeading, ...]:
    body_headings = [
        occurrence.heading
        for occurrence in occurrences
        if occurrence.role == HeadingOccurrenceRole.BODY
    ]

    body_headings.sort(
        key=lambda heading: (
            heading.page_number,
            heading.source_candidate.bbox[1],
            heading.source_candidate.bbox[0],
        )
    )

    return tuple(body_headings)


def get_section_chapter_number(
    section_heading: StructureHeading,
) -> str | None:
    if section_heading.kind != HeadingKind.SECTION:
        raise ValueError(
            "section_heading must have kind SECTION."
        )

    parts = section_heading.number.split(".")

    if len(parts) < 2:
        return None

    chapter_number = parts[0].strip()

    if not chapter_number:
        return None

    return chapter_number


def build_chapter_heading_lookup(
    occurrences: tuple[HeadingOccurrence, ...],
) -> dict[str, StructureHeading]:
    chapter_candidates: dict[
        str,
        list[StructureHeading],
    ] = {}

    for occurrence in occurrences:
        heading = occurrence.heading

        if heading.kind != HeadingKind.CHAPTER:
            continue

        chapter_candidates.setdefault(
            heading.number.casefold(),
            [],
        ).append(heading)

    lookup: dict[str, StructureHeading] = {}

    for number, headings in chapter_candidates.items():
        ranked = sorted(
            headings,
            key=lambda heading: (
                heading.title is None,
                heading.page_number,
                -heading.source_candidate.font_size,
            ),
        )

        lookup[number] = ranked[0]

    return lookup


def build_section_hierarchy(
    occurrences: tuple[HeadingOccurrence, ...],
) -> tuple[SectionHierarchyEntry, ...]:
    body_headings = select_body_headings(
        occurrences
    )

    chapter_lookup = build_chapter_heading_lookup(
        occurrences
    )

    current_unit: StructureHeading | None = None
    current_chapter: StructureHeading | None = None

    sections: list[SectionHierarchyEntry] = []

    for heading in body_headings:
        if heading.kind == HeadingKind.UNIT:
            current_unit = heading
            current_chapter = None

            continue

        if heading.kind == HeadingKind.CHAPTER:
            current_chapter = heading

            continue

        if heading.kind != HeadingKind.SECTION:
            continue

        section_chapter_number = (
            get_section_chapter_number(
                heading
            )
        )

        inferred_chapter: StructureHeading | None = None

        if section_chapter_number is not None:
            inferred_chapter = chapter_lookup.get(
                section_chapter_number.casefold()
            )

        chapter_context = (
            inferred_chapter
            if inferred_chapter is not None
            else current_chapter
        )

        sections.append(
            SectionHierarchyEntry(
                unit_heading=current_unit,
                chapter_heading=chapter_context,
                section_heading=heading,
            )
        )

    return tuple(sections)