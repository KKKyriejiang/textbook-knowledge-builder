from pathlib import Path

import fitz
import pytest

from textbook_kb.structure_headings import (
    HeadingKind,
    StructureHeading,
)
from textbook_kb.structure_pipeline import (
    StructureHeadingGroup,
    extract_structure_headings,
    find_repeated_structure_headings,
    group_structure_headings,
)


def create_repeated_heading_pdf(
    pdf_path: Path,
) -> None:
    document = fitz.open()

    toc_page = document.new_page()

    toc_page.insert_text(
        (72, 72),
        "Contents",
        fontsize=20,
    )

    toc_page.insert_text(
        (72, 110),
        "Chapter 1 Functions",
        fontsize=10,
    )

    toc_page.insert_text(
        (72, 135),
        "1.1 Function Notation",
        fontsize=10,
    )

    toc_page.insert_text(
        (72, 160),
        "1.2 Domain and Range",
        fontsize=10,
    )

    filler_page = document.new_page()

    filler_page.insert_text(
        (72, 72),
        "Introduction",
        fontsize=10,
    )

    chapter_page = document.new_page()

    chapter_page.insert_text(
        (72, 72),
        "Chapter 1 Functions",
        fontsize=24,
    )

    chapter_page.insert_text(
        (72, 125),
        "1.1 Function Notation",
        fontsize=18,
    )

    section_page = document.new_page()

    section_page.insert_text(
        (72, 72),
        "1.2 Domain and Range",
        fontsize=18,
    )

    document.save(pdf_path)
    document.close()


def test_extract_structure_headings_connects_pipeline(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"

    create_repeated_heading_pdf(
        pdf_path
    )

    headings = extract_structure_headings(
        pdf_path=pdf_path,
    )

    assert len(headings) == 6

    assert [
        heading.kind
        for heading in headings
    ] == [
        HeadingKind.CHAPTER,
        HeadingKind.SECTION,
        HeadingKind.SECTION,
        HeadingKind.CHAPTER,
        HeadingKind.SECTION,
        HeadingKind.SECTION,
    ]

    assert [
        heading.page_number
        for heading in headings
    ] == [
        1,
        1,
        1,
        3,
        3,
        4,
    ]


def test_group_structure_headings_by_kind_and_number(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"

    create_repeated_heading_pdf(
        pdf_path
    )

    headings = extract_structure_headings(
        pdf_path=pdf_path,
    )

    groups = group_structure_headings(
        headings
    )

    assert len(groups) == 3

    chapter_group = groups[0]

    assert chapter_group.kind == HeadingKind.CHAPTER
    assert chapter_group.number == "1"
    assert chapter_group.pages == (
        1,
        3,
    )
    assert chapter_group.is_repeated

    section_1_group = groups[1]

    assert section_1_group.kind == HeadingKind.SECTION
    assert section_1_group.number == "1.1"
    assert section_1_group.pages == (
        1,
        3,
    )

    section_2_group = groups[2]

    assert section_2_group.kind == HeadingKind.SECTION
    assert section_2_group.number == "1.2"
    assert section_2_group.pages == (
        1,
        4,
    )


def test_find_repeated_structure_headings(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"

    create_repeated_heading_pdf(
        pdf_path
    )

    headings = extract_structure_headings(
        pdf_path=pdf_path,
    )

    repeated = find_repeated_structure_headings(
        headings
    )

    assert len(repeated) == 3

    assert [
        group.number
        for group in repeated
    ] == [
        "1",
        "1.1",
        "1.2",
    ]

    assert all(
        group.is_repeated
        for group in repeated
    )


def test_grouping_uses_number_even_when_titles_vary(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"

    create_repeated_heading_pdf(
        pdf_path
    )

    headings = list(
        extract_structure_headings(
            pdf_path=pdf_path,
        )
    )

    original = headings[4]

    headings[4] = StructureHeading(
        kind=original.kind,
        number=original.number,
        title="Function Notation and Evaluation",
        page_number=original.page_number,
        source_candidate=original.source_candidate,
    )

    groups = group_structure_headings(
        tuple(headings)
    )

    section_1_group = groups[1]

    assert section_1_group.number == "1.1"
    assert section_1_group.pages == (
        1,
        3,
    )

    assert (
        section_1_group.headings[0].title
        == "Function Notation"
    )

    assert (
        section_1_group.headings[1].title
        == "Function Notation and Evaluation"
    )


def test_structure_heading_group_rejects_mixed_numbers(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"

    create_repeated_heading_pdf(
        pdf_path
    )

    headings = extract_structure_headings(
        pdf_path=pdf_path,
    )

    section_1 = headings[1]
    section_2 = headings[2]

    with pytest.raises(
        ValueError,
        match="same number",
    ):
        StructureHeadingGroup(
            kind=HeadingKind.SECTION,
            number="1.1",
            headings=(
                section_1,
                section_2,
            ),
        )