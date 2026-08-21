from pathlib import Path

import fitz

from textbook_kb.metadata import (
    SectionManifest,
    TextbookMetadata,
    save_section_manifest,
)
from textbook_kb.section_source_export import (
    build_section_sources_from_pdf,
    save_section_sources_json,
)
from textbook_kb.structure_manifest import generate_section_manifest_from_pdf


def create_synthetic_textbook_pdf(pdf_path: Path) -> None:
    document = fitz.open()

    page = document.new_page()
    page.insert_text((72, 72), "Contents", fontsize=24)
    page.insert_text((72, 120), "Chapter 1: Functions", fontsize=12)
    page.insert_text((72, 150), "1.1 Function Notation", fontsize=10)
    page.insert_text((72, 175), "1.2 Domain and Range", fontsize=10)

    page = document.new_page()
    page.insert_text((72, 70), "Chapter 1", fontsize=16)
    page.insert_text((72, 105), "Introduction to Functions", fontsize=22)
    page.insert_text((72, 170), "Synthetic chapter opener text.", fontsize=10)

    page = document.new_page()
    page.insert_text((72, 55), "1.1", fontsize=46)
    page.insert_text((72, 130), "Function Notation", fontsize=22)
    page.insert_text(
        (72, 200),
        "Synthetic lesson text for function notation.",
        fontsize=10,
    )

    page = document.new_page()
    page.insert_text(
        (72, 90),
        "More synthetic lesson text for section 1.1.",
        fontsize=10,
    )

    page = document.new_page()
    page.insert_text((72, 55), "1.2", fontsize=46)
    page.insert_text((72, 130), "Domain and Range", fontsize=22)
    page.insert_text(
        (72, 200),
        "Synthetic lesson text for domain and range.",
        fontsize=10,
    )

    page = document.new_page()
    page.insert_text((72, 70), "Chapter Review", fontsize=22)
    page.insert_text((72, 130), "Synthetic review text.", fontsize=10)

    document.save(pdf_path)
    document.close()


def make_textbook_metadata(source_file: str) -> TextbookMetadata:
    return TextbookMetadata(
        grade="11",
        course_id="MCR3U",
        course_name="Functions",
        textbook="Synthetic Functions",
        source_file=source_file,
    )


def test_pdf_to_section_manifest_to_section_sources(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "synthetic_functions.pdf"
    manifest_path = tmp_path / "synthetic_functions_sections.json"
    section_sources_path = (
        tmp_path / "synthetic_functions_section_sources.json"
    )

    create_synthetic_textbook_pdf(pdf_path)

    manifest = generate_section_manifest_from_pdf(pdf_path)

    assert isinstance(manifest, SectionManifest)
    assert manifest.source_file == pdf_path.name
    assert len(manifest.sections) == 2

    assert manifest.sections[0].section == "1.1 Function Notation"
    assert manifest.sections[0].page_start == 3
    assert manifest.sections[0].page_end == 4

    assert manifest.sections[1].section == "1.2 Domain and Range"
    assert manifest.sections[1].page_start == 5
    assert manifest.sections[1].page_end == 5

    save_section_manifest(
        manifest=manifest,
        output_path=manifest_path,
    )

    textbook_metadata = make_textbook_metadata(pdf_path.name)

    section_sources = build_section_sources_from_pdf(
        pdf_path=pdf_path,
        textbook_metadata=textbook_metadata,
        section_manifest=manifest,
    )

    assert len(section_sources) == 2

    first_source = section_sources[0]
    second_source = section_sources[1]

    assert first_source.section_metadata.section == "1.1 Function Notation"
    assert [page.page_number for page in first_source.pages] == [3, 4]
    assert any(
        "Synthetic lesson text for function notation." in page.text
        for page in first_source.pages
    )
    assert any(
        "More synthetic lesson text for section 1.1." in page.text
        for page in first_source.pages
    )

    assert second_source.section_metadata.section == "1.2 Domain and Range"
    assert [page.page_number for page in second_source.pages] == [5]
    assert any(
        "Synthetic lesson text for domain and range." in page.text
        for page in second_source.pages
    )

    save_section_sources_json(
        section_sources=section_sources,
        output_path=section_sources_path,
    )

    saved_text = section_sources_path.read_text(encoding="utf-8")

    assert "Synthetic lesson text for function notation." in saved_text
    assert "Synthetic lesson text for domain and range." in saved_text
