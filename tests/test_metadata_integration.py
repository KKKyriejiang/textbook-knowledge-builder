import json

import fitz

from textbook_kb.metadata import (
    SectionManifest,
    SectionMetadata,
    save_section_manifest,
)
from textbook_kb.metadata_pipeline import (
    build_textbook_section_sources,
    load_textbook_structure,
)
from textbook_kb.pdf_parser import extract_pages


def test_pdf_to_section_sources_integration(tmp_path):
    pdf_path = tmp_path / "MCR3U_Functions.pdf"

    document = fitz.open()

    page_1 = document.new_page()
    page_1.insert_text(
        (72, 72),
        "Quadratic Functions\nIntroduction to quadratic functions.",
    )

    page_2 = document.new_page()
    page_2.insert_text(
        (72, 72),
        "Vertex Form\nThe vertex form is y = a(x - h)^2 + k.",
    )

    document.save(pdf_path)
    document.close()

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
                chapter=None,
                section="Introduction to Quadratic Functions",
                page_start=1,
                page_end=1,
            ),
            SectionMetadata(
                unit="Quadratic Functions",
                chapter=None,
                section="Vertex Form",
                page_start=2,
                page_end=2,
            ),
        ),
    )

    section_manifest_path = tmp_path / "sections.json"

    save_section_manifest(
        section_manifest,
        section_manifest_path,
    )

    pages = extract_pages(pdf_path)

    structure = load_textbook_structure(
        source_file=pdf_path.name,
        textbook_config_path=textbook_config_path,
        section_manifest_path=section_manifest_path,
    )

    section_sources = build_textbook_section_sources(
        pages,
        structure,
    )

    assert len(pages) == 2
    assert len(section_sources) == 2

    first_section = section_sources[0]
    second_section = section_sources[1]

    assert first_section.textbook_metadata.grade == "11"
    assert first_section.textbook_metadata.course_id == "MCR3U"

    assert (
        first_section.section_metadata.section
        == "Introduction to Quadratic Functions"
    )
    assert [page.page_number for page in first_section.pages] == [1]
    assert "Quadratic Functions" in first_section.pages[0].text

    assert second_section.section_metadata.section == "Vertex Form"
    assert [page.page_number for page in second_section.pages] == [2]
    assert "vertex form" in second_section.pages[0].text.lower()

    assert (
        first_section.pages[0].source_file
        == "MCR3U_Functions.pdf"
    )
    assert (
        second_section.pages[0].source_file
        == "MCR3U_Functions.pdf"
    )
