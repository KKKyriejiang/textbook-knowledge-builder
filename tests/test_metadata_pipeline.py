import json

import pytest

from textbook_kb.metadata import (
    SectionManifest,
    SectionMetadata,
    save_section_manifest,
)
from textbook_kb.metadata_pipeline import (
    TextbookStructure,
    load_textbook_structure,
)


def test_load_textbook_structure_returns_validated_structure(tmp_path):
    textbook_config = {
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

    assert structure.textbook_metadata.grade == 11
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
                "grade": 11,
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