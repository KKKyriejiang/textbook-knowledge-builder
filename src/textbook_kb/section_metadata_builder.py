from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from textbook_kb.metadata import SectionMetadata
from textbook_kb.structure_boundaries import (
    StructureBoundary,
)
from textbook_kb.structure_headings import (
    StructureHeading,
)
from textbook_kb.structure_hierarchy import (
    SectionHierarchyEntry,
)


class SectionEndReason(str, Enum):
    NEXT_SECTION = "next_section"
    STRUCTURE_BOUNDARY = "structure_boundary"
    DOCUMENT_END = "document_end"


@dataclass(frozen=True, slots=True)
class SectionRange:
    hierarchy_entry: SectionHierarchyEntry
    page_start: int
    page_end: int
    end_reason: SectionEndReason
    stop_page: int | None

    def __post_init__(self) -> None:
        if self.page_start < 1:
            raise ValueError(
                "SectionRange page_start must be at least 1."
            )

        if self.page_end < self.page_start:
            raise ValueError(
                "SectionRange page_end must be greater than "
                "or equal to page_start."
            )

        if (
            self.page_start
            != self.hierarchy_entry.section_heading.page_number
        ):
            raise ValueError(
                "SectionRange page_start must match the "
                "section heading page."
            )

        if self.end_reason == SectionEndReason.DOCUMENT_END:
            if self.stop_page is not None:
                raise ValueError(
                    "DOCUMENT_END ranges must not have a stop_page."
                )

            return

        if self.stop_page is None:
            raise ValueError(
                "Non-document-end ranges must have a stop_page."
            )

        if self.stop_page <= self.page_start:
            raise ValueError(
                "SectionRange stop_page must be after page_start."
            )

        if self.page_end != self.stop_page - 1:
            raise ValueError(
                "SectionRange page_end must equal stop_page - 1."
            )


def validate_hierarchy_order(
    hierarchy: tuple[SectionHierarchyEntry, ...],
) -> None:
    section_pages = [
        entry.section_heading.page_number
        for entry in hierarchy
    ]

    if len(section_pages) != len(set(section_pages)):
        raise ValueError(
            "Section hierarchy contains duplicate section start pages."
        )


def find_first_boundary_after(
    page_number: int,
    boundaries: tuple[StructureBoundary, ...],
) -> StructureBoundary | None:
    later_boundaries = [
        boundary
        for boundary in boundaries
        if boundary.page_number > page_number
    ]

    if not later_boundaries:
        return None

    return min(
        later_boundaries,
        key=lambda boundary: boundary.page_number,
    )


def derive_section_ranges(
    hierarchy: tuple[SectionHierarchyEntry, ...],
    boundaries: tuple[StructureBoundary, ...],
    final_page: int | None = None,
) -> tuple[SectionRange, ...]:
    if final_page is not None and final_page < 1:
        raise ValueError(
            "final_page must be at least 1."
        )

    if not hierarchy:
        return ()

    validate_hierarchy_order(
        hierarchy
    )

    ordered_hierarchy = tuple(
        sorted(
            hierarchy,
            key=lambda entry: (
                entry.section_heading.page_number,
                entry.section_heading.source_candidate.bbox[1],
                entry.section_heading.source_candidate.bbox[0],
            ),
        )
    )

    ranges: list[SectionRange] = []

    for index, entry in enumerate(
        ordered_hierarchy
    ):
        page_start = (
            entry.section_heading.page_number
        )

        next_section_start: int | None = None

        if index + 1 < len(ordered_hierarchy):
            next_section_start = (
                ordered_hierarchy[
                    index + 1
                ].section_heading.page_number
            )

        boundary = find_first_boundary_after(
            page_number=page_start,
            boundaries=boundaries,
        )

        boundary_page = (
            boundary.page_number
            if boundary is not None
            else None
        )

        stop_candidates: list[
            tuple[int, SectionEndReason]
        ] = []

        if next_section_start is not None:
            stop_candidates.append(
                (
                    next_section_start,
                    SectionEndReason.NEXT_SECTION,
                )
            )

        if boundary_page is not None:
            stop_candidates.append(
                (
                    boundary_page,
                    SectionEndReason.STRUCTURE_BOUNDARY,
                )
            )

        if stop_candidates:
            stop_page, end_reason = min(
                stop_candidates,
                key=lambda item: item[0],
            )

            ranges.append(
                SectionRange(
                    hierarchy_entry=entry,
                    page_start=page_start,
                    page_end=stop_page - 1,
                    end_reason=end_reason,
                    stop_page=stop_page,
                )
            )

            continue

        if final_page is None:
            raise ValueError(
                "Cannot determine the final section page_end. "
                "Provide final_page or a later structure boundary."
            )

        if final_page < page_start:
            raise ValueError(
                "final_page cannot appear before the final "
                "section start page."
            )

        ranges.append(
            SectionRange(
                hierarchy_entry=entry,
                page_start=page_start,
                page_end=final_page,
                end_reason=SectionEndReason.DOCUMENT_END,
                stop_page=None,
            )
        )

    return tuple(ranges)


def format_context_heading(
    heading: StructureHeading | None,
    label: str,
) -> str | None:
    if heading is None:
        return None

    base = (
        f"{label} {heading.number}"
    )

    if heading.title is None:
        return base

    return (
        f"{base}: {heading.title}"
    )


def format_section_heading(
    heading: StructureHeading,
) -> str:
    if heading.title is None:
        return heading.number

    return (
        f"{heading.number} {heading.title}"
    )


def build_section_metadata_records(
    ranges: tuple[SectionRange, ...],
) -> tuple[SectionMetadata, ...]:
    records: list[SectionMetadata] = []

    for section_range in ranges:
        entry = section_range.hierarchy_entry

        records.append(
            SectionMetadata(
                unit=format_context_heading(
                    entry.unit_heading,
                    "Unit",
                ),
                chapter=format_context_heading(
                    entry.chapter_heading,
                    "Chapter",
                ),
                section=format_section_heading(
                    entry.section_heading
                ),
                page_start=section_range.page_start,
                page_end=section_range.page_end,
            )
        )

    return tuple(records)