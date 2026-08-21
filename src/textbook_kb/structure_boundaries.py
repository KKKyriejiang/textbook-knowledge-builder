from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from textbook_kb.structure_candidates import (
    StructureCandidate,
    scan_structure_candidates,
)


class StructureBoundaryKind(str, Enum):
    CHAPTER_REVIEW = "chapter_review"
    CHAPTER_SELF_TEST = "chapter_self_test"
    CHAPTER_TASK = "chapter_task"


BOUNDARY_PATTERNS: tuple[
    tuple[StructureBoundaryKind, re.Pattern[str]],
    ...,
] = (
    (
        StructureBoundaryKind.CHAPTER_REVIEW,
        re.compile(
            r"^Chapter Review\b",
            re.IGNORECASE,
        ),
    ),
    (
        StructureBoundaryKind.CHAPTER_SELF_TEST,
        re.compile(
            r"^Chapter Self-Test\b",
            re.IGNORECASE,
        ),
    ),
    (
        StructureBoundaryKind.CHAPTER_TASK,
        re.compile(
            r"^Chapter Task\b",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class StructureBoundary:
    kind: StructureBoundaryKind
    page_number: int
    text: str
    source_candidate: StructureCandidate

    def __post_init__(self) -> None:
        if self.page_number < 1:
            raise ValueError(
                "StructureBoundary page_number must be at least 1."
            )

        if not self.text.strip():
            raise ValueError(
                "StructureBoundary text must be non-empty."
            )

        if (
            self.page_number
            != self.source_candidate.page_number
        ):
            raise ValueError(
                "StructureBoundary page_number must match "
                "source_candidate.page_number."
            )


def validate_boundary_settings(
    min_boundary_font_size: float,
    max_boundary_top: float,
) -> None:
    if min_boundary_font_size <= 0:
        raise ValueError(
            "min_boundary_font_size must be greater than 0."
        )

    if max_boundary_top < 0:
        raise ValueError(
            "max_boundary_top must be greater than or equal to 0."
        )


def match_boundary_kind(
    text: str,
) -> StructureBoundaryKind | None:
    for kind, pattern in BOUNDARY_PATTERNS:
        if pattern.search(text):
            return kind

    return None


def classify_structure_boundary_candidate(
    candidate: StructureCandidate,
    min_boundary_font_size: float = 18.0,
    max_boundary_top: float = 180.0,
) -> StructureBoundary | None:
    validate_boundary_settings(
        min_boundary_font_size=min_boundary_font_size,
        max_boundary_top=max_boundary_top,
    )

    kind = match_boundary_kind(
        candidate.text
    )

    if kind is None:
        return None

    is_body_boundary = (
        candidate.font_size >= min_boundary_font_size
        and candidate.bbox[1] <= max_boundary_top
    )

    if not is_body_boundary:
        return None

    return StructureBoundary(
        kind=kind,
        page_number=candidate.page_number,
        text=candidate.text,
        source_candidate=candidate,
    )


def classify_structure_boundary_candidates(
    candidates: tuple[StructureCandidate, ...],
    min_boundary_font_size: float = 18.0,
    max_boundary_top: float = 180.0,
) -> tuple[StructureBoundary, ...]:
    validate_boundary_settings(
        min_boundary_font_size=min_boundary_font_size,
        max_boundary_top=max_boundary_top,
    )

    boundaries: list[StructureBoundary] = []

    for candidate in candidates:
        boundary = classify_structure_boundary_candidate(
            candidate=candidate,
            min_boundary_font_size=min_boundary_font_size,
            max_boundary_top=max_boundary_top,
        )

        if boundary is None:
            continue

        boundaries.append(
            boundary
        )

    boundaries.sort(
        key=lambda boundary: (
            boundary.page_number,
            boundary.source_candidate.bbox[1],
            boundary.source_candidate.bbox[0],
        )
    )

    return tuple(boundaries)


def detect_structure_boundaries(
    pdf_path: Path,
    start_page: int = 1,
    end_page: int | None = None,
    min_boundary_font_size: float = 18.0,
    max_boundary_top: float = 180.0,
) -> tuple[StructureBoundary, ...]:
    candidates = scan_structure_candidates(
        pdf_path=pdf_path,
        start_page=start_page,
        end_page=end_page,
        regex_only=True,
    )

    return classify_structure_boundary_candidates(
        candidates=candidates,
        min_boundary_font_size=min_boundary_font_size,
        max_boundary_top=max_boundary_top,
    )