import pytest

from textbook_kb.section_metadata_builder import (
    SectionEndReason,
    build_section_metadata_records,
    derive_section_ranges,
)
from textbook_kb.structure_boundaries import (
    StructureBoundary,
    StructureBoundaryKind,
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
)


def make_heading(
    *,
    kind: HeadingKind,
    number: str,
    page_number: int,
    title: str | None = None,
    font_size: float = 18.0,
    top: float = 50.0,
) -> StructureHeading:
    if title is None:
        text = number
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
        reasons=("test",),
    )

    return StructureHeading(
        kind=kind,
        number=number,
        title=title,
        page_number=page_number,
        source_candidate=candidate,
    )


def make_section_entry(
    *,
    section_number: str,
    section_page: int,
    section_title: str | None = None,
    chapter_number: str | None = None,
    chapter_title: str | None = None,
    chapter_page: int = 1,
) -> SectionHierarchyEntry:
    section_heading = make_heading(
        kind=HeadingKind.SECTION,
        number=section_number,
        page_number=section_page,
        title=section_title,
        font_size=46.0,
        top=6.5,
    )

    chapter_heading = None

    if chapter_number is not None:
        chapter_heading = make_heading(
            kind=HeadingKind.CHAPTER,
            number=chapter_number,
            page_number=chapter_page,
            title=chapter_title,
            font_size=12.0,
            top=100.0,
        )

    return SectionHierarchyEntry(
        unit_heading=None,
        chapter_heading=chapter_heading,
        section_heading=section_heading,
    )


def make_boundary(
    *,
    page_number: int,
    kind: StructureBoundaryKind = (
        StructureBoundaryKind.CHAPTER_REVIEW
    ),
) -> StructureBoundary:
    text_by_kind = {
        StructureBoundaryKind.CHAPTER_REVIEW:
            "Chapter Review",
        StructureBoundaryKind.CHAPTER_SELF_TEST:
            "Chapter Self-Test",
        StructureBoundaryKind.CHAPTER_TASK:
            "Chapter Task",
    }

    text = text_by_kind[kind]

    candidate = StructureCandidate(
        page_number=page_number,
        text=text,
        font_size=22.0,
        fonts=("Helvetica-Bold",),
        bbox=(
            180.0,
            28.9,
            350.0,
            54.4,
        ),
        reasons=("chapter",),
    )

    return StructureBoundary(
        kind=kind,
        page_number=page_number,
        text=text,
        source_candidate=candidate,
    )


def test_internal_section_ends_before_next_section() -> None:
    section_1 = make_section_entry(
        section_number="1.1",
        section_page=14,
    )

    section_2 = make_section_entry(
        section_number="1.2",
        section_page=24,
    )

    ranges = derive_section_ranges(
        hierarchy=(
            section_1,
            section_2,
        ),
        boundaries=(),
        final_page=30,
    )

    assert ranges[0].page_start == 14
    assert ranges[0].page_end == 23

    assert (
        ranges[0].end_reason
        == SectionEndReason.NEXT_SECTION
    )

    assert ranges[0].stop_page == 24


def test_last_section_in_chapter_ends_before_review() -> None:
    section_1_8 = make_section_entry(
        section_number="1.8",
        section_page=71,
    )

    section_2_1 = make_section_entry(
        section_number="2.1",
        section_page=94,
    )

    review = make_boundary(
        page_number=84,
    )

    ranges = derive_section_ranges(
        hierarchy=(
            section_1_8,
            section_2_1,
        ),
        boundaries=(
            review,
        ),
        final_page=100,
    )

    assert ranges[0].page_start == 71
    assert ranges[0].page_end == 83

    assert (
        ranges[0].end_reason
        == SectionEndReason.STRUCTURE_BOUNDARY
    )

    assert ranges[0].stop_page == 84


def test_boundary_after_next_section_does_not_cut_current_section() -> None:
    section_1 = make_section_entry(
        section_number="1.1",
        section_page=14,
    )

    section_2 = make_section_entry(
        section_number="1.2",
        section_page=24,
    )

    review = make_boundary(
        page_number=84,
    )

    ranges = derive_section_ranges(
        hierarchy=(
            section_1,
            section_2,
        ),
        boundaries=(
            review,
        ),
        final_page=90,
    )

    assert ranges[0].page_end == 23

    assert (
        ranges[0].end_reason
        == SectionEndReason.NEXT_SECTION
    )


def test_final_section_uses_structure_boundary() -> None:
    final_section = make_section_entry(
        section_number="8.6",
        section_page=600,
    )

    review = make_boundary(
        page_number=610,
    )

    ranges = derive_section_ranges(
        hierarchy=(
            final_section,
        ),
        boundaries=(
            review,
        ),
    )

    assert ranges[0].page_start == 600
    assert ranges[0].page_end == 609

    assert (
        ranges[0].end_reason
        == SectionEndReason.STRUCTURE_BOUNDARY
    )


def test_final_section_can_use_document_end() -> None:
    final_section = make_section_entry(
        section_number="8.6",
        section_page=600,
    )

    ranges = derive_section_ranges(
        hierarchy=(
            final_section,
        ),
        boundaries=(),
        final_page=620,
    )

    assert ranges[0].page_start == 600
    assert ranges[0].page_end == 620

    assert (
        ranges[0].end_reason
        == SectionEndReason.DOCUMENT_END
    )

    assert ranges[0].stop_page is None


def test_final_section_without_end_signal_raises_error() -> None:
    final_section = make_section_entry(
        section_number="8.6",
        section_page=600,
    )

    with pytest.raises(
        ValueError,
        match="final section page_end",
    ):
        derive_section_ranges(
            hierarchy=(
                final_section,
            ),
            boundaries=(),
        )


def test_build_section_metadata_records() -> None:
    chapter = make_heading(
        kind=HeadingKind.CHAPTER,
        number="3",
        page_number=7,
        title="Quadratic Functions",
        font_size=12.0,
        top=180.0,
    )

    section = make_heading(
        kind=HeadingKind.SECTION,
        number="3.2",
        page_number=158,
        title="Vertex Form",
        font_size=46.0,
        top=6.5,
    )

    entry = SectionHierarchyEntry(
        unit_heading=None,
        chapter_heading=chapter,
        section_heading=section,
    )

    next_section = make_section_entry(
        section_number="3.3",
        section_page=165,
        chapter_number="3",
        chapter_title="Quadratic Functions",
        chapter_page=7,
    )

    ranges = derive_section_ranges(
        hierarchy=(
            entry,
            next_section,
        ),
        boundaries=(),
        final_page=180,
    )

    records = build_section_metadata_records(
        ranges
    )

    record = records[0]

    assert record.unit is None

    assert (
        record.chapter
        == "Chapter 3: Quadratic Functions"
    )

    assert (
        record.section
        == "3.2 Vertex Form"
    )

    assert record.page_start == 158
    assert record.page_end == 164