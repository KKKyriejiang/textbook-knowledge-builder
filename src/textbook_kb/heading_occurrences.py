from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from textbook_kb.structure_headings import (
    StructureHeading,
)
from textbook_kb.structure_pipeline import (
    StructureHeadingGroup,
    group_structure_headings,
)


class HeadingOccurrenceRole(str, Enum):
    TOC = "toc"
    BODY = "body"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class HeadingOccurrence:
    heading: StructureHeading
    role: HeadingOccurrenceRole
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.reasons:
            raise ValueError(
                "HeadingOccurrence must contain at least one reason."
            )

    @property
    def page_number(self) -> int:
        return self.heading.page_number


def validate_occurrence_settings(
    min_body_font_size: float,
    max_body_top: float,
    min_body_font_gap: float,
) -> None:
    if min_body_font_size <= 0:
        raise ValueError(
            "min_body_font_size must be greater than 0."
        )

    if max_body_top < 0:
        raise ValueError(
            "max_body_top must be greater than or equal to 0."
        )

    if min_body_font_gap <= 0:
        raise ValueError(
            "min_body_font_gap must be greater than 0."
        )


def is_body_like_heading(
    heading: StructureHeading,
    min_body_font_size: float = 14.0,
    max_body_top: float = 180.0,
) -> bool:
    candidate = heading.source_candidate

    return (
        candidate.font_size >= min_body_font_size
        and candidate.bbox[1] <= max_body_top
    )


def select_body_heading(
    group: StructureHeadingGroup,
    min_body_font_size: float = 14.0,
    max_body_top: float = 180.0,
    min_body_font_gap: float = 2.0,
) -> StructureHeading | None:
    validate_occurrence_settings(
        min_body_font_size=min_body_font_size,
        max_body_top=max_body_top,
        min_body_font_gap=min_body_font_gap,
    )

    body_like = [
        heading
        for heading in group.headings
        if is_body_like_heading(
            heading=heading,
            min_body_font_size=min_body_font_size,
            max_body_top=max_body_top,
        )
    ]

    if len(body_like) == 1:
        return body_like[0]

    if len(body_like) < 2:
        return None

    ranked = sorted(
        body_like,
        key=lambda heading: (
            heading.source_candidate.font_size,
            -heading.source_candidate.bbox[1],
        ),
        reverse=True,
    )

    strongest = ranked[0]
    second_strongest = ranked[1]

    font_gap = (
        strongest.source_candidate.font_size
        - second_strongest.source_candidate.font_size
    )

    if font_gap >= min_body_font_gap:
        return strongest

    return None


def classify_heading_group_occurrences(
    group: StructureHeadingGroup,
    min_body_font_size: float = 14.0,
    max_body_top: float = 180.0,
    min_body_font_gap: float = 2.0,
) -> tuple[HeadingOccurrence, ...]:
    validate_occurrence_settings(
        min_body_font_size=min_body_font_size,
        max_body_top=max_body_top,
        min_body_font_gap=min_body_font_gap,
    )

    body_heading = select_body_heading(
        group=group,
        min_body_font_size=min_body_font_size,
        max_body_top=max_body_top,
        min_body_font_gap=min_body_font_gap,
    )

    occurrences: list[HeadingOccurrence] = []

    for heading in group.headings:
        candidate = heading.source_candidate

        if heading == body_heading:
            occurrences.append(
                HeadingOccurrence(
                    heading=heading,
                    role=HeadingOccurrenceRole.BODY,
                    reasons=(
                        "large enough font for body heading",
                        "positioned near top of page",
                        "selected as strongest body occurrence",
                    ),
                )
            )
            continue

        if body_heading is not None:
            body_candidate = (
                body_heading.source_candidate
            )

            appears_before_body = (
                heading.page_number
                < body_heading.page_number
            )

            uses_smaller_font = (
                candidate.font_size
                < body_candidate.font_size
            )

            if (
                appears_before_body
                and uses_smaller_font
            ):
                occurrences.append(
                    HeadingOccurrence(
                        heading=heading,
                        role=HeadingOccurrenceRole.TOC,
                        reasons=(
                            "appears before identified body occurrence",
                            "uses smaller font than body occurrence",
                        ),
                    )
                )
                continue

        occurrences.append(
            HeadingOccurrence(
                heading=heading,
                role=HeadingOccurrenceRole.UNKNOWN,
                reasons=(
                    "insufficient evidence to classify occurrence",
                ),
            )
        )

    return tuple(occurrences)


def classify_heading_occurrences(
    headings: tuple[StructureHeading, ...],
    min_body_font_size: float = 14.0,
    max_body_top: float = 180.0,
    min_body_font_gap: float = 2.0,
) -> tuple[HeadingOccurrence, ...]:
    validate_occurrence_settings(
        min_body_font_size=min_body_font_size,
        max_body_top=max_body_top,
        min_body_font_gap=min_body_font_gap,
    )

    groups = group_structure_headings(
        headings
    )

    occurrences: list[HeadingOccurrence] = []

    for group in groups:
        group_occurrences = (
            classify_heading_group_occurrences(
                group=group,
                min_body_font_size=min_body_font_size,
                max_body_top=max_body_top,
                min_body_font_gap=min_body_font_gap,
            )
        )

        occurrences.extend(
            group_occurrences
        )

    occurrences.sort(
        key=lambda occurrence: (
            occurrence.heading.page_number,
            occurrence.heading.source_candidate.bbox[1],
            occurrence.heading.source_candidate.bbox[0],
        )
    )

    return tuple(occurrences)