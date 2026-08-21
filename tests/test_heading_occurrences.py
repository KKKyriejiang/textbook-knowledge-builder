import pytest

from textbook_kb.heading_occurrences import (
    HeadingOccurrenceRole,
    classify_heading_group_occurrences,
    classify_heading_occurrences,
    select_body_heading,
)
from textbook_kb.structure_candidates import (
    StructureCandidate,
)
from textbook_kb.structure_headings import (
    HeadingKind,
    StructureHeading,
)
from textbook_kb.structure_pipeline import (
    StructureHeadingGroup,
)


def make_heading(
    *,
    number: str,
    page_number: int,
    font_size: float,
    top: float,
    title: str = "Example Heading",
    kind: HeadingKind = HeadingKind.SECTION,
) -> StructureHeading:
    text = f"{number} {title}"

    candidate = StructureCandidate(
        page_number=page_number,
        text=text,
        font_size=font_size,
        fonts=("Helvetica-Bold",),
        bbox=(
            72.0,
            top,
            350.0,
            top + 25.0,
        ),
        reasons=(
            "numbered heading",
            "large font",
        ),
    )

    return StructureHeading(
        kind=kind,
        number=number,
        title=title,
        page_number=page_number,
        source_candidate=candidate,
    )


def test_unique_body_like_heading_is_selected() -> None:
    heading = make_heading(
        number="3.2",
        page_number=100,
        font_size=18.0,
        top=70.0,
    )

    group = StructureHeadingGroup(
        kind=HeadingKind.SECTION,
        number="3.2",
        headings=(heading,),
    )

    selected = select_body_heading(
        group
    )

    assert selected == heading


def test_repeated_toc_and_body_are_classified() -> None:
    toc_heading = make_heading(
        number="3.2",
        page_number=8,
        font_size=10.0,
        top=300.0,
    )

    body_heading = make_heading(
        number="3.2",
        page_number=100,
        font_size=18.0,
        top=70.0,
    )

    group = StructureHeadingGroup(
        kind=HeadingKind.SECTION,
        number="3.2",
        headings=(
            toc_heading,
            body_heading,
        ),
    )

    occurrences = (
        classify_heading_group_occurrences(
            group
        )
    )

    assert len(occurrences) == 2

    assert (
        occurrences[0].role
        == HeadingOccurrenceRole.TOC
    )

    assert (
        occurrences[1].role
        == HeadingOccurrenceRole.BODY
    )


def test_two_equally_strong_body_candidates_remain_unknown() -> None:
    first_heading = make_heading(
        number="4.1",
        page_number=20,
        font_size=18.0,
        top=70.0,
    )

    second_heading = make_heading(
        number="4.1",
        page_number=80,
        font_size=18.0,
        top=75.0,
    )

    group = StructureHeadingGroup(
        kind=HeadingKind.SECTION,
        number="4.1",
        headings=(
            first_heading,
            second_heading,
        ),
    )

    occurrences = (
        classify_heading_group_occurrences(
            group
        )
    )

    assert all(
        occurrence.role
        == HeadingOccurrenceRole.UNKNOWN
        for occurrence in occurrences
    )


def test_largest_font_can_break_body_candidate_tie() -> None:
    weaker_heading = make_heading(
        number="5.1",
        page_number=10,
        font_size=15.0,
        top=80.0,
    )

    stronger_heading = make_heading(
        number="5.1",
        page_number=90,
        font_size=20.0,
        top=75.0,
    )

    group = StructureHeadingGroup(
        kind=HeadingKind.SECTION,
        number="5.1",
        headings=(
            weaker_heading,
            stronger_heading,
        ),
    )

    selected = select_body_heading(
        group=group,
        min_body_font_gap=2.0,
    )

    assert selected == stronger_heading


def test_later_smaller_heading_is_not_marked_as_toc() -> None:
    body_heading = make_heading(
        number="6.1",
        page_number=50,
        font_size=20.0,
        top=70.0,
    )

    later_heading = make_heading(
        number="6.1",
        page_number=80,
        font_size=10.0,
        top=300.0,
    )

    group = StructureHeadingGroup(
        kind=HeadingKind.SECTION,
        number="6.1",
        headings=(
            body_heading,
            later_heading,
        ),
    )

    occurrences = (
        classify_heading_group_occurrences(
            group
        )
    )

    assert (
        occurrences[0].role
        == HeadingOccurrenceRole.BODY
    )

    assert (
        occurrences[1].role
        == HeadingOccurrenceRole.UNKNOWN
    )


def test_classify_heading_occurrences_returns_document_order() -> None:
    section_2_body = make_heading(
        number="2.1",
        page_number=40,
        font_size=18.0,
        top=70.0,
    )

    section_1_toc = make_heading(
        number="1.1",
        page_number=5,
        font_size=10.0,
        top=250.0,
    )

    section_1_body = make_heading(
        number="1.1",
        page_number=20,
        font_size=18.0,
        top=70.0,
    )

    headings = (
        section_2_body,
        section_1_toc,
        section_1_body,
    )

    occurrences = classify_heading_occurrences(
        headings
    )

    assert [
        occurrence.page_number
        for occurrence in occurrences
    ] == [
        5,
        20,
        40,
    ]

    assert [
        occurrence.role
        for occurrence in occurrences
    ] == [
        HeadingOccurrenceRole.TOC,
        HeadingOccurrenceRole.BODY,
        HeadingOccurrenceRole.BODY,
    ]


def test_invalid_occurrence_settings_raise_error() -> None:
    heading = make_heading(
        number="1.1",
        page_number=10,
        font_size=18.0,
        top=70.0,
    )

    group = StructureHeadingGroup(
        kind=HeadingKind.SECTION,
        number="1.1",
        headings=(heading,),
    )

    with pytest.raises(
        ValueError,
        match="min_body_font_size",
    ):
        classify_heading_group_occurrences(
            group=group,
            min_body_font_size=0,
        )

    with pytest.raises(
        ValueError,
        match="max_body_top",
    ):
        classify_heading_group_occurrences(
            group=group,
            max_body_top=-1,
        )

    with pytest.raises(
        ValueError,
        match="min_body_font_gap",
    ):
        classify_heading_group_occurrences(
            group=group,
            min_body_font_gap=0,
        )