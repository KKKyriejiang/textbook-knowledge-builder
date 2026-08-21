from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from textbook_kb.structure_candidates import StructureCandidate


class HeadingKind(str, Enum):
    UNIT = "unit"
    CHAPTER = "chapter"
    SECTION = "section"


KEYWORD_HEADING_PATTERN = re.compile(
    r"^(?P<kind>unit|chapter|section)\s+"
    r"(?P<number>\d+(?:\.\d+)*|[IVXLCDM]+)"
    r"(?:\s*[:\-–—]\s*|\s+)?"
    r"(?P<title>.*)$",
    re.IGNORECASE,
)

NUMBERED_SECTION_PATTERN = re.compile(
    r"^(?P<number>\d+\.\d+(?:\.\d+)?)"
    r"(?:\s*[:\-–—]\s*|\s+)?"
    r"(?P<title>.*)$"
)


@dataclass(frozen=True, slots=True)
class StructureHeading:
    kind: HeadingKind
    number: str
    title: str | None
    page_number: int
    source_candidate: StructureCandidate

    def __post_init__(self) -> None:
        if not self.number.strip():
            raise ValueError(
                "StructureHeading number must be non-empty."
            )

        if self.page_number < 1:
            raise ValueError(
                "StructureHeading page_number must be at least 1."
            )

        if (
            self.page_number
            != self.source_candidate.page_number
        ):
            raise ValueError(
                "StructureHeading page_number must match "
                "source_candidate.page_number."
            )


def normalize_title(
    title: str,
) -> str | None:
    normalized = " ".join(
        title.split()
    )

    if not normalized:
        return None

    return normalized


def parse_keyword_heading(
    candidate: StructureCandidate,
) -> StructureHeading | None:
    match = KEYWORD_HEADING_PATTERN.fullmatch(
        candidate.text
    )

    if match is None:
        return None

    kind_text = match.group("kind").lower()

    kind = HeadingKind(kind_text)

    number = match.group("number").strip()

    title = normalize_title(
        match.group("title")
    )

    return StructureHeading(
        kind=kind,
        number=number,
        title=title,
        page_number=candidate.page_number,
        source_candidate=candidate,
    )


def parse_numbered_section_heading(
    candidate: StructureCandidate,
) -> StructureHeading | None:
    match = NUMBERED_SECTION_PATTERN.fullmatch(
        candidate.text
    )

    if match is None:
        return None

    number = match.group("number").strip()

    title = normalize_title(
        match.group("title")
    )

    return StructureHeading(
        kind=HeadingKind.SECTION,
        number=number,
        title=title,
        page_number=candidate.page_number,
        source_candidate=candidate,
    )


def classify_structure_candidate(
    candidate: StructureCandidate,
) -> StructureHeading | None:
    keyword_heading = parse_keyword_heading(
        candidate
    )

    if keyword_heading is not None:
        return keyword_heading

    numbered_section = (
        parse_numbered_section_heading(
            candidate
        )
    )

    if numbered_section is not None:
        return numbered_section

    return None


def classify_structure_candidates(
    candidates: tuple[StructureCandidate, ...],
) -> tuple[StructureHeading, ...]:
    headings: list[StructureHeading] = []

    for candidate in candidates:
        heading = classify_structure_candidate(
            candidate
        )

        if heading is None:
            continue

        headings.append(heading)

    return tuple(headings)