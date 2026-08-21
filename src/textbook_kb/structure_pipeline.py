from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from textbook_kb.section_titles import (
    enrich_section_heading_titles,
)
from textbook_kb.structure_candidates import (
    StructureCandidate,
    scan_structure_candidates,
)
from textbook_kb.structure_headings import (
    HeadingKind,
    StructureHeading,
    classify_structure_candidates,
)


@dataclass(frozen=True, slots=True)
class StructureHeadingGroup:
    kind: HeadingKind
    number: str
    headings: tuple[StructureHeading, ...]

    def __post_init__(self) -> None:
        if not self.number.strip():
            raise ValueError(
                "StructureHeadingGroup number must be non-empty."
            )

        if not self.headings:
            raise ValueError(
                "StructureHeadingGroup must contain at least one heading."
            )

        for heading in self.headings:
            if heading.kind != self.kind:
                raise ValueError(
                    "All headings in a StructureHeadingGroup "
                    "must have the same kind."
                )

            if (
                heading.number.casefold()
                != self.number.casefold()
            ):
                raise ValueError(
                    "All headings in a StructureHeadingGroup "
                    "must have the same number."
                )

    @property
    def pages(self) -> tuple[int, ...]:
        return tuple(
            heading.page_number
            for heading in self.headings
        )

    @property
    def is_repeated(self) -> bool:
        return len(self.headings) > 1


def select_heading_candidates(
    candidates: tuple[StructureCandidate, ...],
    regex_only: bool,
) -> tuple[StructureCandidate, ...]:
    if not regex_only:
        return candidates

    return tuple(
        candidate
        for candidate in candidates
        if any(
            reason != "large font"
            for reason in candidate.reasons
        )
    )


def extract_structure_headings(
    pdf_path: Path,
    start_page: int = 1,
    end_page: int | None = None,
    min_font_size: float = 14.0,
    max_heading_length: int = 120,
    regex_only: bool = False,
    enrich_titles: bool = False,
    min_title_font_size: float = 14.0,
    max_title_vertical_gap: float = 100.0,
    max_title_top: float = 200.0,
    max_title_length: int = 120,
) -> tuple[StructureHeading, ...]:
    if enrich_titles:
        all_candidates = scan_structure_candidates(
            pdf_path=pdf_path,
            start_page=start_page,
            end_page=end_page,
            min_font_size=min_font_size,
            max_heading_length=max_heading_length,
            regex_only=False,
        )

        heading_candidates = (
            select_heading_candidates(
                candidates=all_candidates,
                regex_only=regex_only,
            )
        )

        headings = classify_structure_candidates(
            heading_candidates
        )

        return enrich_section_heading_titles(
            headings=headings,
            candidates=all_candidates,
            min_title_font_size=min_title_font_size,
            max_vertical_gap=max_title_vertical_gap,
            max_title_top=max_title_top,
            max_title_length=max_title_length,
        )

    candidates = scan_structure_candidates(
        pdf_path=pdf_path,
        start_page=start_page,
        end_page=end_page,
        min_font_size=min_font_size,
        max_heading_length=max_heading_length,
        regex_only=regex_only,
    )

    return classify_structure_candidates(
        candidates
    )


def group_structure_headings(
    headings: tuple[StructureHeading, ...],
) -> tuple[StructureHeadingGroup, ...]:
    grouped: dict[
        tuple[HeadingKind, str],
        list[StructureHeading],
    ] = {}

    for heading in headings:
        key = (
            heading.kind,
            heading.number.casefold(),
        )

        grouped.setdefault(
            key,
            [],
        ).append(heading)

    groups: list[StructureHeadingGroup] = []

    for heading_list in grouped.values():
        first_heading = heading_list[0]

        groups.append(
            StructureHeadingGroup(
                kind=first_heading.kind,
                number=first_heading.number,
                headings=tuple(heading_list),
            )
        )

    return tuple(groups)


def find_repeated_structure_headings(
    headings: tuple[StructureHeading, ...],
) -> tuple[StructureHeadingGroup, ...]:
    groups = group_structure_headings(
        headings
    )

    return tuple(
        group
        for group in groups
        if group.is_repeated
    )