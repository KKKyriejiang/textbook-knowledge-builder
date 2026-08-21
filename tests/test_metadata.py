import json

import pytest

from textbook_kb.metadata import (
    SectionMetadata,
    TextbookMetadata,
    find_textbook_metadata,
    load_section_metadata,
    load_textbook_metadata,
    save_section_metadata,
)


def test_textbook_metadata_stores_expected_fields():
    metadata = TextbookMetadata(
        grade=11,
        course_id="MCR3U",
        course_name="Functions",
        textbook="MCR3U Functions",
        source_file="MCR3U_Functions.pdf",
    )

    assert metadata.grade == 11
    assert metadata.course_id == "MCR3U"
    assert metadata.course_name == "Functions"
    assert metadata.textbook == "MCR3U Functions"
    assert metadata.source_file == "MCR3U_Functions.pdf"


def test_load_textbook_metadata(tmp_path):
    config = {
        "textbooks": [
            {
                "grade": 11,
                "course_id": "MCR3U",
                "course_name": "Functions",
                "textbook": "MCR3U Functions",
                "source_file": "MCR3U_Functions.pdf",
            }
        ]
    }

    config_path = tmp_path / "textbooks.json"
    config_path.write_text(
        json.dumps(config),
        encoding="utf-8",
    )

    textbooks = load_textbook_metadata(config_path)

    assert len(textbooks) == 1

    textbook = textbooks[0]

    assert textbook.grade == 11
    assert textbook.course_id == "MCR3U"
    assert textbook.course_name == "Functions"
    assert textbook.source_file == "MCR3U_Functions.pdf"


def test_find_textbook_metadata_returns_matching_record():
    textbooks = [
        TextbookMetadata(
            grade=11,
            course_id="MCR3U",
            course_name="Functions",
            textbook="MCR3U Functions",
            source_file="MCR3U_Functions.pdf",
        ),
        TextbookMetadata(
            grade=12,
            course_id="MHF4U",
            course_name="Advanced Functions",
            textbook="MHF4U Advanced Functions",
            source_file="MHF4U_Advanced_Functions.pdf",
        ),
    ]

    textbook = find_textbook_metadata(
        textbooks,
        "MCR3U_Functions.pdf",
    )

    assert textbook.grade == 11
    assert textbook.course_id == "MCR3U"


def test_find_textbook_metadata_raises_when_missing():
    textbooks = [
        TextbookMetadata(
            grade=11,
            course_id="MCR3U",
            course_name="Functions",
            textbook="MCR3U Functions",
            source_file="MCR3U_Functions.pdf",
        )
    ]

    with pytest.raises(
        ValueError,
        match="No textbook metadata found",
    ):
        find_textbook_metadata(
            textbooks,
            "Unknown.pdf",
        )


def test_find_textbook_metadata_raises_when_duplicate():
    textbooks = [
        TextbookMetadata(
            grade=11,
            course_id="MCR3U",
            course_name="Functions",
            textbook="MCR3U Functions",
            source_file="MCR3U_Functions.pdf",
        ),
        TextbookMetadata(
            grade=11,
            course_id="MCR3U",
            course_name="Functions",
            textbook="Duplicate Record",
            source_file="MCR3U_Functions.pdf",
        ),
    ]

    with pytest.raises(
        ValueError,
        match="Multiple textbook metadata records found",
    ):
        find_textbook_metadata(
            textbooks,
            "MCR3U_Functions.pdf",
        )


def test_section_metadata_stores_expected_fields():
    metadata = SectionMetadata(
        unit="Quadratic Functions",
        chapter="Chapter 3",
        section="3.2 Vertex Form",
        page_start=142,
        page_end=149,
    )

    assert metadata.unit == "Quadratic Functions"
    assert metadata.chapter == "Chapter 3"
    assert metadata.section == "3.2 Vertex Form"
    assert metadata.page_start == 142
    assert metadata.page_end == 149


def test_section_metadata_allows_missing_chapter():
    metadata = SectionMetadata(
        unit="Quadratic Functions",
        chapter=None,
        section="Vertex Form",
        page_start=142,
        page_end=149,
    )

    assert metadata.chapter is None


def test_section_metadata_rejects_empty_section():
    with pytest.raises(
        ValueError,
        match="Section name cannot be empty",
    ):
        SectionMetadata(
            unit="Quadratic Functions",
            chapter=None,
            section="   ",
            page_start=142,
            page_end=149,
        )


def test_section_metadata_rejects_invalid_page_start():
    with pytest.raises(
        ValueError,
        match="page_start must be at least 1",
    ):
        SectionMetadata(
            unit="Quadratic Functions",
            chapter=None,
            section="Vertex Form",
            page_start=0,
            page_end=149,
        )


def test_section_metadata_rejects_reversed_page_range():
    with pytest.raises(
        ValueError,
        match="page_end must be greater than or equal to page_start",
    ):
        SectionMetadata(
            unit="Quadratic Functions",
            chapter=None,
            section="Vertex Form",
            page_start=149,
            page_end=142,
        )


def test_save_and_load_section_metadata(tmp_path):
    sections = [
        SectionMetadata(
            unit="Quadratic Functions",
            chapter="Chapter 3",
            section="3.1 Introduction to Quadratics",
            page_start=100,
            page_end=110,
        ),
        SectionMetadata(
            unit="Quadratic Functions",
            chapter="Chapter 3",
            section="3.2 Vertex Form",
            page_start=111,
            page_end=120,
        ),
    ]

    output_path = tmp_path / "sections.json"

    save_section_metadata(
        sections,
        output_path,
    )

    loaded_sections = load_section_metadata(output_path)

    assert loaded_sections == sections