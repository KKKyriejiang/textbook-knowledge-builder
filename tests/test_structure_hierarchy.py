import pytest

from textbook_kb.heading_occurrences import (
    HeadingOccurrence,
    HeadingOccurrenceRole,
)
from textbook_kb.structure_candidates import (
    StructureCandidate,
)
from textbook_kb.structure_headings import (
    HeadingKind,
    StructureHeading,
)
from textbook_kb.structure_hierarchy import (
    SectionHierarchyEntry,
    build_chapter_heading_lookup,
    build_section_hierarchy,
    get_section_chapter_number,
    select_body_headings,
)


def make_heading(
    *,
    kind: HeadingKind,
    number: str,
    page_number: int,
    top: float,
    title: str | None = None,
    font_size: float = 18.0,
) -> StructureHeading:
    if title is None:
        text = f"{kind.value} {number}"
    else:
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
        reasons=("large font",),
    )

    return StructureHeading(
        kind=kind,
        number=number,
        title=title,
        page_number=page_number,
        source_candidate=candidate,
    )


def make_occurrence(
    heading: StructureHeading,
    role: HeadingOccurrenceRole,
) -> HeadingOccurrence:
    return HeadingOccurrence(
        heading=heading,
        role=role,
        reasons=("test classification",),
    )


def test_select_body_headings_ignores_toc_and_unknown() -> None:
    toc_heading = make_heading(
        kind=HeadingKind.SECTION,
        number="1.1",
        page_number=2,
        top=200.0,
        title="Function Notation",
    )

    body_heading = make_heading(
        kind=HeadingKind.SECTION,
        number="1.1",
        page_number=20,
        top=70.0,
        title="Function Notation",
    )

    unknown_heading = make_heading(
        kind=HeadingKind.SECTION,
        number="2.1",
        page_number=30,
        top=70.0,
        title="Quadratic Functions",
    )

    occurrences = (
        make_occurrence(
            toc_heading,
            HeadingOccurrenceRole.TOC,
        ),
        make_occurrence(
            body_heading,
            HeadingOccurrenceRole.BODY,
        ),
        make_occurrence(
            unknown_heading,
            HeadingOccurrenceRole.UNKNOWN,
        ),
    )

    body_headings = select_body_headings(
        occurrences
    )

    assert body_headings == (
        body_heading,
    )


def test_select_body_headings_returns_document_order() -> None:
    later_heading = make_heading(
        kind=HeadingKind.SECTION,
        number="1.2",
        page_number=30,
        top=70.0,
        title="Domain and Range",
    )

    earlier_heading = make_heading(
        kind=HeadingKind.SECTION,
        number="1.1",
        page_number=20,
        top=70.0,
        title="Function Notation",
    )

    occurrences = (
        make_occurrence(
            later_heading,
            HeadingOccurrenceRole.BODY,
        ),
        make_occurrence(
            earlier_heading,
            HeadingOccurrenceRole.BODY,
        ),
    )

    body_headings = select_body_headings(
        occurrences
    )

    assert body_headings == (
        earlier_heading,
        later_heading,
    )


def test_get_section_chapter_number() -> None:
    section = make_heading(
        kind=HeadingKind.SECTION,
        number="3.2",
        page_number=100,
        top=70.0,
        title="Vertex Form",
    )

    assert (
        get_section_chapter_number(section)
        == "3"
    )


def test_get_section_chapter_number_rejects_non_section() -> None:
    chapter = make_heading(
        kind=HeadingKind.CHAPTER,
        number="3",
        page_number=90,
        top=70.0,
        title="Quadratic Functions",
    )

    with pytest.raises(
        ValueError,
        match="section_heading",
    ):
        get_section_chapter_number(
            chapter
        )


def test_build_chapter_heading_lookup_prefers_titled_heading() -> None:
    toc_chapter = make_heading(
        kind=HeadingKind.CHAPTER,
        number="3",
        page_number=7,
        top=180.0,
        title="Quadratic Functions",
        font_size=12.0,
    )

    footer_chapter = make_heading(
        kind=HeadingKind.CHAPTER,
        number="3",
        page_number=150,
        top=680.0,
        title=None,
        font_size=9.0,
    )

    occurrences = (
        make_occurrence(
            toc_chapter,
            HeadingOccurrenceRole.UNKNOWN,
        ),
        make_occurrence(
            footer_chapter,
            HeadingOccurrenceRole.UNKNOWN,
        ),
    )

    lookup = build_chapter_heading_lookup(
        occurrences
    )

    assert lookup["3"] == toc_chapter


def test_build_section_hierarchy_tracks_unit_and_chapter() -> None:
    unit = make_heading(
        kind=HeadingKind.UNIT,
        number="1",
        page_number=10,
        top=50.0,
        title="Functions",
    )

    chapter = make_heading(
        kind=HeadingKind.CHAPTER,
        number="1",
        page_number=12,
        top=60.0,
        title="Introduction to Functions",
    )

    section_1 = make_heading(
        kind=HeadingKind.SECTION,
        number="1.1",
        page_number=15,
        top=70.0,
        title="Function Notation",
    )

    section_2 = make_heading(
        kind=HeadingKind.SECTION,
        number="1.2",
        page_number=25,
        top=70.0,
        title="Domain and Range",
    )

    occurrences = tuple(
        make_occurrence(
            heading,
            HeadingOccurrenceRole.BODY,
        )
        for heading in (
            unit,
            chapter,
            section_1,
            section_2,
        )
    )

    hierarchy = build_section_hierarchy(
        occurrences
    )

    assert len(hierarchy) == 2

    assert hierarchy[0].unit_heading == unit
    assert hierarchy[0].chapter_heading == chapter
    assert hierarchy[0].section_heading == section_1

    assert hierarchy[1].unit_heading == unit
    assert hierarchy[1].chapter_heading == chapter
    assert hierarchy[1].section_heading == section_2


def test_chapter_context_can_be_inferred_from_toc_heading() -> None:
    toc_chapter = make_heading(
        kind=HeadingKind.CHAPTER,
        number="3",
        page_number=7,
        top=180.0,
        title="Quadratic Functions",
        font_size=12.0,
    )

    section_1 = make_heading(
        kind=HeadingKind.SECTION,
        number="3.1",
        page_number=150,
        top=6.5,
        title=None,
        font_size=46.0,
    )

    section_2 = make_heading(
        kind=HeadingKind.SECTION,
        number="3.2",
        page_number=158,
        top=6.5,
        title=None,
        font_size=46.0,
    )

    occurrences = (
        make_occurrence(
            toc_chapter,
            HeadingOccurrenceRole.UNKNOWN,
        ),
        make_occurrence(
            section_1,
            HeadingOccurrenceRole.BODY,
        ),
        make_occurrence(
            section_2,
            HeadingOccurrenceRole.BODY,
        ),
    )

    hierarchy = build_section_hierarchy(
        occurrences
    )

    assert len(hierarchy) == 2

    assert hierarchy[0].chapter_heading == toc_chapter
    assert hierarchy[1].chapter_heading == toc_chapter

    assert hierarchy[0].unit_heading is None
    assert hierarchy[1].unit_heading is None


def test_section_number_selects_matching_chapter() -> None:
    chapter_1 = make_heading(
        kind=HeadingKind.CHAPTER,
        number="1",
        page_number=5,
        top=100.0,
        title="Introduction to Functions",
    )

    chapter_2 = make_heading(
        kind=HeadingKind.CHAPTER,
        number="2",
        page_number=6,
        top=100.0,
        title="Equivalent Algebraic Expressions",
    )

    section_1 = make_heading(
        kind=HeadingKind.SECTION,
        number="1.1",
        page_number=20,
        top=6.5,
        font_size=46.0,
    )

    section_2 = make_heading(
        kind=HeadingKind.SECTION,
        number="2.1",
        page_number=90,
        top=6.5,
        font_size=46.0,
    )

    occurrences = (
        make_occurrence(
            chapter_1,
            HeadingOccurrenceRole.UNKNOWN,
        ),
        make_occurrence(
            chapter_2,
            HeadingOccurrenceRole.UNKNOWN,
        ),
        make_occurrence(
            section_1,
            HeadingOccurrenceRole.BODY,
        ),
        make_occurrence(
            section_2,
            HeadingOccurrenceRole.BODY,
        ),
    )

    hierarchy = build_section_hierarchy(
        occurrences
    )

    assert hierarchy[0].chapter_heading == chapter_1
    assert hierarchy[1].chapter_heading == chapter_2


def test_new_chapter_updates_section_context() -> None:
    unit = make_heading(
        kind=HeadingKind.UNIT,
        number="1",
        page_number=5,
        top=50.0,
        title="Functions",
    )

    chapter_1 = make_heading(
        kind=HeadingKind.CHAPTER,
        number="1",
        page_number=10,
        top=60.0,
        title="Introduction",
    )

    section_1 = make_heading(
        kind=HeadingKind.SECTION,
        number="1.1",
        page_number=15,
        top=70.0,
        title="Function Notation",
    )

    chapter_2 = make_heading(
        kind=HeadingKind.CHAPTER,
        number="2",
        page_number=30,
        top=60.0,
        title="Transformations",
    )

    section_2 = make_heading(
        kind=HeadingKind.SECTION,
        number="2.1",
        page_number=35,
        top=70.0,
        title="Transformations of Functions",
    )

    occurrences = tuple(
        make_occurrence(
            heading,
            HeadingOccurrenceRole.BODY,
        )
        for heading in (
            unit,
            chapter_1,
            section_1,
            chapter_2,
            section_2,
        )
    )

    hierarchy = build_section_hierarchy(
        occurrences
    )

    assert hierarchy[0].chapter_heading == chapter_1
    assert hierarchy[1].chapter_heading == chapter_2

    assert hierarchy[0].unit_heading == unit
    assert hierarchy[1].unit_heading == unit


def test_new_unit_resets_previous_chapter() -> None:
    unit_1 = make_heading(
        kind=HeadingKind.UNIT,
        number="1",
        page_number=5,
        top=50.0,
        title="Functions",
    )

    chapter_1 = make_heading(
        kind=HeadingKind.CHAPTER,
        number="1",
        page_number=10,
        top=60.0,
        title="Introduction",
    )

    section_1 = make_heading(
        kind=HeadingKind.SECTION,
        number="1.1",
        page_number=15,
        top=70.0,
        title="Function Notation",
    )

    unit_2 = make_heading(
        kind=HeadingKind.UNIT,
        number="2",
        page_number=50,
        top=50.0,
        title="Quadratic Functions",
    )

    section_2 = make_heading(
        kind=HeadingKind.SECTION,
        number="2.1",
        page_number=55,
        top=70.0,
        title="Quadratic Relations",
    )

    occurrences = tuple(
        make_occurrence(
            heading,
            HeadingOccurrenceRole.BODY,
        )
        for heading in (
            unit_1,
            chapter_1,
            section_1,
            unit_2,
            section_2,
        )
    )

    hierarchy = build_section_hierarchy(
        occurrences
    )

    assert len(hierarchy) == 2

    assert hierarchy[0].unit_heading == unit_1
    assert hierarchy[0].chapter_heading == chapter_1

    assert hierarchy[1].unit_heading == unit_2
    assert hierarchy[1].chapter_heading is None


def test_section_without_matching_chapter_is_allowed() -> None:
    section = make_heading(
        kind=HeadingKind.SECTION,
        number="9.1",
        page_number=10,
        top=70.0,
        title="Function Notation",
    )

    occurrences = (
        make_occurrence(
            section,
            HeadingOccurrenceRole.BODY,
        ),
    )

    hierarchy = build_section_hierarchy(
        occurrences
    )

    assert len(hierarchy) == 1

    assert hierarchy[0].unit_heading is None
    assert hierarchy[0].chapter_heading is None
    assert hierarchy[0].section_heading == section


def test_section_hierarchy_entry_rejects_wrong_heading_kind() -> None:
    chapter = make_heading(
        kind=HeadingKind.CHAPTER,
        number="1",
        page_number=10,
        top=60.0,
        title="Functions",
    )

    with pytest.raises(
        ValueError,
        match="section_heading",
    ):
        SectionHierarchyEntry(
            unit_heading=None,
            chapter_heading=None,
            section_heading=chapter,
        )