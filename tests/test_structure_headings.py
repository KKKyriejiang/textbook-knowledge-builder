import pytest

from textbook_kb.structure_candidates import (
    StructureCandidate,
)
from textbook_kb.structure_headings import (
    HeadingKind,
    StructureHeading,
    classify_structure_candidate,
    classify_structure_candidates,
)


def make_candidate(
    text: str,
    page_number: int = 1,
    font_size: float = 16.0,
    reasons: tuple[str, ...] = (
        "large font",
    ),
) -> StructureCandidate:
    return StructureCandidate(
        page_number=page_number,
        text=text,
        font_size=font_size,
        fonts=("Helvetica-Bold",),
        bbox=(72.0, 72.0, 300.0, 100.0),
        reasons=reasons,
    )


def test_classify_unit_heading() -> None:
    candidate = make_candidate(
        text="Unit 2 Quadratic Functions",
        page_number=10,
        reasons=(
            "unit",
            "large font",
        ),
    )

    heading = classify_structure_candidate(
        candidate
    )

    assert heading is not None
    assert heading.kind == HeadingKind.UNIT
    assert heading.number == "2"
    assert heading.title == "Quadratic Functions"
    assert heading.page_number == 10
    assert heading.source_candidate == candidate


def test_classify_chapter_heading() -> None:
    candidate = make_candidate(
        text="Chapter 3: Polynomial Functions",
        page_number=20,
        reasons=(
            "chapter",
            "large font",
        ),
    )

    heading = classify_structure_candidate(
        candidate
    )

    assert heading is not None
    assert heading.kind == HeadingKind.CHAPTER
    assert heading.number == "3"
    assert heading.title == "Polynomial Functions"
    assert heading.page_number == 20


def test_classify_numbered_section_heading() -> None:
    candidate = make_candidate(
        text="3.2 Vertex Form",
        page_number=35,
        reasons=(
            "numbered heading",
            "large font",
        ),
    )

    heading = classify_structure_candidate(
        candidate
    )

    assert heading is not None
    assert heading.kind == HeadingKind.SECTION
    assert heading.number == "3.2"
    assert heading.title == "Vertex Form"
    assert heading.page_number == 35


def test_classify_section_keyword_heading() -> None:
    candidate = make_candidate(
        text="Section 4.1 Transformations",
        page_number=50,
        reasons=(
            "section",
            "large font",
        ),
    )

    heading = classify_structure_candidate(
        candidate
    )

    assert heading is not None
    assert heading.kind == HeadingKind.SECTION
    assert heading.number == "4.1"
    assert heading.title == "Transformations"
    assert heading.page_number == 50


def test_heading_without_title_is_allowed() -> None:
    candidate = make_candidate(
        text="Chapter 5",
        page_number=60,
        reasons=("chapter",),
    )

    heading = classify_structure_candidate(
        candidate
    )

    assert heading is not None
    assert heading.kind == HeadingKind.CHAPTER
    assert heading.number == "5"
    assert heading.title is None


def test_large_font_only_candidate_is_not_classified() -> None:
    candidate = make_candidate(
        text="Exploring Quadratic Functions",
        page_number=70,
        reasons=("large font",),
    )

    heading = classify_structure_candidate(
        candidate
    )

    assert heading is None


def test_classify_structure_candidates_filters_non_headings() -> None:
    candidates = (
        make_candidate(
            text="Unit 1 Functions",
            page_number=5,
            reasons=("unit",),
        ),
        make_candidate(
            text="Interesting Example",
            page_number=6,
            reasons=("large font",),
        ),
        make_candidate(
            text="1.2 Function Notation",
            page_number=10,
            reasons=("numbered heading",),
        ),
    )

    headings = classify_structure_candidates(
        candidates
    )

    assert len(headings) == 2

    assert headings[0].kind == HeadingKind.UNIT
    assert headings[0].number == "1"

    assert headings[1].kind == HeadingKind.SECTION
    assert headings[1].number == "1.2"


def test_heading_page_must_match_candidate_page() -> None:
    candidate = make_candidate(
        text="Chapter 3",
        page_number=20,
    )

    with pytest.raises(
        ValueError,
        match="source_candidate.page_number",
    ):
        StructureHeading(
            kind=HeadingKind.CHAPTER,
            number="3",
            title=None,
            page_number=21,
            source_candidate=candidate,
        )