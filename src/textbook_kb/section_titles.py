from __future__ import annotations

from dataclasses import dataclass

from textbook_kb.structure_candidates import (
    StructureCandidate,
)
from textbook_kb.structure_headings import (
    HeadingKind,
    StructureHeading,
    normalize_title,
)


STRUCTURAL_REASONS = {
    "unit",
    "chapter",
    "section",
    "numbered heading",
}


@dataclass(frozen=True, slots=True)
class SectionTitleMatch:
    section_heading: StructureHeading
    title_candidate: StructureCandidate
    vertical_gap: float

    def __post_init__(self) -> None:
        if self.section_heading.kind != HeadingKind.SECTION:
            raise ValueError(
                "section_heading must have kind SECTION."
            )

        if (
            self.section_heading.page_number
            != self.title_candidate.page_number
        ):
            raise ValueError(
                "Section title candidate must be on the "
                "same page as the section heading."
            )

        if self.vertical_gap < 0:
            raise ValueError(
                "vertical_gap must be greater than or equal to 0."
            )


def validate_title_settings(
    min_title_font_size: float,
    max_vertical_gap: float,
    max_title_top: float,
    max_title_length: int,
) -> None:
    if min_title_font_size <= 0:
        raise ValueError(
            "min_title_font_size must be greater than 0."
        )

    if max_vertical_gap < 0:
        raise ValueError(
            "max_vertical_gap must be greater than or equal to 0."
        )

    if max_title_top < 0:
        raise ValueError(
            "max_title_top must be greater than or equal to 0."
        )

    if max_title_length < 1:
        raise ValueError(
            "max_title_length must be at least 1."
        )


def calculate_vertical_gap(
    source_bbox: tuple[float, float, float, float],
    candidate_bbox: tuple[float, float, float, float],
) -> float:
    source_top = source_bbox[1]
    source_bottom = source_bbox[3]

    candidate_top = candidate_bbox[1]
    candidate_bottom = candidate_bbox[3]

    if candidate_bottom < source_top:
        return source_top - candidate_bottom

    if candidate_top > source_bottom:
        return candidate_top - source_bottom

    return 0.0


def is_possible_section_title_candidate(
    candidate: StructureCandidate,
    section_heading: StructureHeading,
    min_title_font_size: float = 14.0,
    max_vertical_gap: float = 100.0,
    max_title_top: float = 200.0,
    max_title_length: int = 120,
) -> bool:
    validate_title_settings(
        min_title_font_size=min_title_font_size,
        max_vertical_gap=max_vertical_gap,
        max_title_top=max_title_top,
        max_title_length=max_title_length,
    )

    if candidate == section_heading.source_candidate:
        return False

    if candidate.page_number != section_heading.page_number:
        return False

    if candidate.font_size < min_title_font_size:
        return False

    if candidate.bbox[1] > max_title_top:
        return False

    if len(candidate.text) > max_title_length:
        return False

    if not candidate.text.strip():
        return False

    if STRUCTURAL_REASONS.intersection(
        candidate.reasons
    ):
        return False

    vertical_gap = calculate_vertical_gap(
        source_bbox=section_heading.source_candidate.bbox,
        candidate_bbox=candidate.bbox,
    )

    if vertical_gap > max_vertical_gap:
        return False

    return True


def find_section_title_match(
    section_heading: StructureHeading,
    candidates: tuple[StructureCandidate, ...],
    min_title_font_size: float = 14.0,
    max_vertical_gap: float = 100.0,
    max_title_top: float = 200.0,
    max_title_length: int = 120,
) -> SectionTitleMatch | None:
    if section_heading.kind != HeadingKind.SECTION:
        raise ValueError(
            "section_heading must have kind SECTION."
        )

    if section_heading.title is not None:
        return None

    possible_matches: list[
        SectionTitleMatch
    ] = []

    for candidate in candidates:
        if not is_possible_section_title_candidate(
            candidate=candidate,
            section_heading=section_heading,
            min_title_font_size=min_title_font_size,
            max_vertical_gap=max_vertical_gap,
            max_title_top=max_title_top,
            max_title_length=max_title_length,
        ):
            continue

        vertical_gap = calculate_vertical_gap(
            source_bbox=section_heading.source_candidate.bbox,
            candidate_bbox=candidate.bbox,
        )

        possible_matches.append(
            SectionTitleMatch(
                section_heading=section_heading,
                title_candidate=candidate,
                vertical_gap=vertical_gap,
            )
        )

    if not possible_matches:
        return None

    return min(
        possible_matches,
        key=lambda match: (
            match.vertical_gap,
            -match.title_candidate.font_size,
            match.title_candidate.bbox[1],
            match.title_candidate.bbox[0],
        ),
    )


def enrich_section_heading_title(
    heading: StructureHeading,
    candidates: tuple[StructureCandidate, ...],
    min_title_font_size: float = 14.0,
    max_vertical_gap: float = 100.0,
    max_title_top: float = 200.0,
    max_title_length: int = 120,
) -> StructureHeading:
    if heading.kind != HeadingKind.SECTION:
        return heading

    if heading.title is not None:
        return heading

    match = find_section_title_match(
        section_heading=heading,
        candidates=candidates,
        min_title_font_size=min_title_font_size,
        max_vertical_gap=max_vertical_gap,
        max_title_top=max_title_top,
        max_title_length=max_title_length,
    )

    if match is None:
        return heading

    title = normalize_title(
        match.title_candidate.text
    )

    if title is None:
        return heading

    return StructureHeading(
        kind=heading.kind,
        number=heading.number,
        title=title,
        page_number=heading.page_number,
        source_candidate=heading.source_candidate,
    )


def enrich_section_heading_titles(
    headings: tuple[StructureHeading, ...],
    candidates: tuple[StructureCandidate, ...],
    min_title_font_size: float = 14.0,
    max_vertical_gap: float = 100.0,
    max_title_top: float = 200.0,
    max_title_length: int = 120,
) -> tuple[StructureHeading, ...]:
    validate_title_settings(
        min_title_font_size=min_title_font_size,
        max_vertical_gap=max_vertical_gap,
        max_title_top=max_title_top,
        max_title_length=max_title_length,
    )

    return tuple(
        enrich_section_heading_title(
            heading=heading,
            candidates=candidates,
            min_title_font_size=min_title_font_size,
            max_vertical_gap=max_vertical_gap,
            max_title_top=max_title_top,
            max_title_length=max_title_length,
        )
        for heading in headings
    )