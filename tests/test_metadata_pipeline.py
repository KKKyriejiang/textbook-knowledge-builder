import json

import pytest

from textbook_kb.metadata import (
    SectionManifest,
    SectionMetadata,
    TextbookMetadata,
    save_section_manifest,
)
from textbook_kb.metadata_pipeline import (
    TextbookStructure,
    build_textbook_section_sources,
    load_textbook_structure,
)
from textbook_kb.pdf_parser import ParsedPage


def test_load_textbook_structure_returns_validated_structure(tmp_path):
    textbook_config = {
        "textbooks": [
            {
                "grade": "11",
                "course_id": "MCR3U",
                "course_name": "Functions",
                "textbook": "MCR3U Functions",
                "source_file": "MCR3U_Functions.pdf",
            }
        ]
    }

    textbook_config_path = tmp_path / "textbooks.json"
    textbook_config_path.write_text(
        json.dumps(textbook_config),
        encoding="utf-8",
    )

    section_manifest = SectionManifest(
        source_file="MCR3U_Functions.pdf",
        sections=(
            SectionMetadata(
                unit="Quadratic Functions",
                chapter="Chapter 3",
                section="3.2 Vertex Form",
                page_start=142,
                page_end=149,
            ),
        ),
    )

    section_manifest_path = tmp_path / "sections.json"

    save_section_manifest(
        section_manifest,
        section_manifest_path,
    )

    structure = load_textbook_structure(
        source_file="MCR3U_Functions.pdf",
        textbook_config_path=textbook_config_path,
        section_manifest_path=section_manifest_path,
    )

    assert isinstance(structure, TextbookStructure)

    assert structure.textbook_metadata.grade == "11"
    assert structure.textbook_metadata.course_id == "MCR3U"

    assert (
        structure.section_manifest.source_file
        == "MCR3U_Functions.pdf"
    )

    assert len(structure.section_manifest.sections) == 1

    assert (
        structure.section_manifest.sections[0].section
        == "3.2 Vertex Form"
    )


def test_load_textbook_structure_rejects_mismatched_manifest(tmp_path):
    textbook_config = {
        "textbooks": [
            {
                "grade": "11",
                "course_id": "MCR3U",
                "course_name": "Functions",
                "textbook": "MCR3U Functions",
                "source_file": "MCR3U_Functions.pdf",
            }
        ]
    }

    textbook_config_path = tmp_path / "textbooks.json"
    textbook_config_path.write_text(
        json.dumps(textbook_config),
        encoding="utf-8",
    )

    section_manifest = SectionManifest(
        source_file="MHF4U_Advanced_Functions.pdf",
        sections=(
            SectionMetadata(
                unit="Polynomial Functions",
                chapter="Chapter 1",
                section="1.1 Polynomial Functions",
                page_start=1,
                page_end=10,
            ),
        ),
    )

    section_manifest_path = tmp_path / "sections.json"

    save_section_manifest(
        section_manifest,
        section_manifest_path,
    )

    with pytest.raises(
        ValueError,
        match="does not match textbook source file",
    ):
        load_textbook_structure(
            source_file="MCR3U_Functions.pdf",
            textbook_config_path=textbook_config_path,
            section_manifest_path=section_manifest_path,
        )


def test_build_textbook_section_sources_builds_all_sections():
    pages = [
        ParsedPage(
            page_number=1,
            text="Introduction to quadratic functions.",
            source_file="MCR3U_Functions.pdf",
        ),
        ParsedPage(
            page_number=2,
            text="Quadratic function examples.",
            source_file="MCR3U_Functions.pdf",
        ),
        ParsedPage(
            page_number=3,
            text="Vertex form is y = a(x - h)^2 + k.",
            source_file="MCR3U_Functions.pdf",
        ),
        ParsedPage(
            page_number=4,
            text="The vertex is located at (h, k).",
            source_file="MCR3U_Functions.pdf",
        ),
    ]

    textbook_metadata = TextbookMetadata(
        grade="11",
        course_id="MCR3U",
        course_name="Functions",
        textbook="MCR3U Functions",
        source_file="MCR3U_Functions.pdf",
    )

    section_manifest = SectionManifest(
        source_file="MCR3U_Functions.pdf",
        sections=(
            SectionMetadata(
                unit="Quadratic Functions",
                chapter="Chapter 3",
                section="3.1 Introduction",
                page_start=1,
                page_end=2,
            ),
            SectionMetadata(
                unit="Quadratic Functions",
                chapter="Chapter 3",
                section="3.2 Vertex Form",
                page_start=3,
                page_end=4,
            ),
        ),
    )

    structure = TextbookStructure(
        textbook_metadata=textbook_metadata,
        section_manifest=section_manifest,
    )

    section_sources = build_textbook_section_sources(
        pages,
        structure,
    )

    assert len(section_sources) == 2

    first_section = section_sources[0]
    second_section = section_sources[1]

    assert first_section.section_metadata.section == "3.1 Introduction"
    assert [page.page_number for page in first_section.pages] == [1, 2]

    assert second_section.section_metadata.section == "3.2 Vertex Form"
    assert [page.page_number for page in second_section.pages] == [3, 4]

    assert first_section.textbook_metadata == textbook_metadata
    assert second_section.textbook_metadata == textbook_metadata


def test_build_textbook_section_sources_propagates_source_validation():
    pages = [
        ParsedPage(
            page_number=1,
            text="Introduction",
            source_file="MCR3U_Functions.pdf",
        ),
        ParsedPage(
            page_number=3,
            text="Vertex form",
            source_file="MCR3U_Functions.pdf",
        ),
    ]

    textbook_metadata = TextbookMetadata(
        grade="11",
        course_id="MCR3U",
        course_name="Functions",
        textbook="MCR3U Functions",
        source_file="MCR3U_Functions.pdf",
    )

    section_manifest = SectionManifest(
        source_file="MCR3U_Functions.pdf",
        sections=(
            SectionMetadata(
                unit="Quadratic Functions",
                chapter="Chapter 3",
                section="3.1 Introduction",
                page_start=1,
                page_end=3,
            ),
        ),
    )

    structure = TextbookStructure(
        textbook_metadata=textbook_metadata,
        section_manifest=section_manifest,
    )

    with pytest.raises(
        ValueError,
        match="Missing parsed pages",
    ):
        build_textbook_section_sources(
            pages,
            structure,
        )
