from pathlib import Path

import fitz
import pytest

from textbook_kb.metadata import (
    SectionMetadata,
    TextbookMetadata,
    load_section_manifest,
    save_section_manifest,
    validate_section_manifest,
)
from textbook_kb.structure_manifest import (
    build_generated_section_manifest,
    generate_section_manifest_from_pdf,
    validate_generated_section_metadata,
)


def create_test_pdf(
    pdf_path: Path,
) -> None:
    document = fitz.open()

    toc_page = document.new_page()

    toc_page.insert_text(
        (72, 70),
        "Chapter 1: Functions",
        fontsize=12,
    )

    toc_page.insert_text(
        (72, 100),
        "1.1",
        fontsize=10.5,
    )

    toc_page.insert_text(
        (72, 125),
        "1.2",
        fontsize=10.5,
    )

    toc_page.insert_text(
        (300, 70),
        "Chapter 2: Quadratic Functions",
        fontsize=12,
    )

    toc_page.insert_text(
        (300, 100),
        "2.1",
        fontsize=10.5,
    )

    section_1_page = document.new_page()

    section_1_page.insert_text(
        (72, 55),
        "1.1",
        fontsize=46,
    )

    section_1_page.insert_text(
        (72, 130),
        "Function Notation",
        fontsize=22,
    )

    section_1_page.insert_text(
        (72, 200),
        "Normal body text.",
        fontsize=10,
    )

    section_2_page = document.new_page()

    section_2_page.insert_text(
        (72, 55),
        "1.2",
        fontsize=46,
    )

    section_2_page.insert_text(
        (72, 130),
        "Domain and Range",
        fontsize=22,
    )

    section_2_page.insert_text(
        (72, 200),
        "Normal body text.",
        fontsize=10,
    )

    chapter_1_review = document.new_page()

    chapter_1_review.insert_text(
        (72, 70),
        "Chapter Review",
        fontsize=22,
    )

    section_3_page = document.new_page()

    section_3_page.insert_text(
        (72, 55),
        "2.1",
        fontsize=46,
    )

    section_3_page.insert_text(
        (72, 130),
        "Equivalent Algebraic Expressions",
        fontsize=22,
    )

    section_3_page.insert_text(
        (72, 200),
        "Normal body text.",
        fontsize=10,
    )

    chapter_2_review = document.new_page()

    chapter_2_review.insert_text(
        (72, 70),
        "Chapter Review",
        fontsize=22,
    )

    document.save(
        pdf_path
    )

    document.close()


def test_validate_generated_section_metadata() -> None:
    sections = (
        SectionMetadata(
            unit=None,
            chapter="Chapter 1: Functions",
            section="1.1 Function Notation",
            page_start=2,
            page_end=2,
        ),
        SectionMetadata(
            unit=None,
            chapter="Chapter 1: Functions",
            section="1.2 Domain and Range",
            page_start=3,
            page_end=3,
        ),
    )

    validate_generated_section_metadata(
        sections
    )


def test_generated_section_metadata_rejects_overlap() -> None:
    sections = (
        SectionMetadata(
            unit=None,
            chapter="Chapter 1",
            section="1.1 First Section",
            page_start=10,
            page_end=20,
        ),
        SectionMetadata(
            unit=None,
            chapter="Chapter 1",
            section="1.2 Second Section",
            page_start=20,
            page_end=30,
        ),
    )

    with pytest.raises(
        ValueError,
        match="must not overlap",
    ):
        validate_generated_section_metadata(
            sections
        )


def test_generated_section_metadata_rejects_duplicates() -> None:
    sections = (
        SectionMetadata(
            unit=None,
            chapter="Chapter 1",
            section="1.1 Function Notation",
            page_start=10,
            page_end=15,
        ),
        SectionMetadata(
            unit=None,
            chapter="Chapter 1",
            section="1.1 Function Notation",
            page_start=20,
            page_end=25,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Duplicate generated section metadata",
    ):
        validate_generated_section_metadata(
            sections
        )


def test_build_generated_section_manifest() -> None:
    sections = (
        SectionMetadata(
            unit=None,
            chapter="Chapter 1: Functions",
            section="1.1 Function Notation",
            page_start=2,
            page_end=5,
        ),
    )

    manifest = build_generated_section_manifest(
        source_file="sample.pdf",
        sections=sections,
    )

    assert manifest.source_file == "sample.pdf"
    assert manifest.sections == sections


def test_generate_section_manifest_from_pdf(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"

    create_test_pdf(
        pdf_path
    )

    manifest = generate_section_manifest_from_pdf(
        pdf_path=pdf_path,
        regex_only=True,
    )

    assert manifest.source_file == "sample.pdf"

    assert len(manifest.sections) == 3

    section_1 = manifest.sections[0]
    section_2 = manifest.sections[1]
    section_3 = manifest.sections[2]

    assert (
        section_1.section
        == "1.1 Function Notation"
    )

    assert (
        section_1.chapter
        == "Chapter 1: Functions"
    )

    assert section_1.page_start == 2
    assert section_1.page_end == 2

    assert (
        section_2.section
        == "1.2 Domain and Range"
    )

    assert (
        section_2.chapter
        == "Chapter 1: Functions"
    )

    assert section_2.page_start == 3
    assert section_2.page_end == 3

    assert (
        section_3.section
        == "2.1 Equivalent Algebraic Expressions"
    )

    assert (
        section_3.chapter
        == "Chapter 2: Quadratic Functions"
    )

    assert section_3.page_start == 5
    assert section_3.page_end == 5


def test_generated_manifest_save_load_and_validation(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"

    create_test_pdf(
        pdf_path
    )

    manifest = generate_section_manifest_from_pdf(
        pdf_path=pdf_path,
        regex_only=True,
    )

    textbook_metadata = TextbookMetadata(
        grade=11,
        course_id="MCR3U",
        course_name="Functions",
        textbook="Synthetic Functions Textbook",
        source_file="sample.pdf",
    )

    validate_section_manifest(
        manifest=manifest,
        textbook_metadata=textbook_metadata,
    )

    output_path = (
        tmp_path
        / "sample_sections.json"
    )

    save_section_manifest(
        manifest=manifest,
        output_path=output_path,
    )

    loaded_manifest = load_section_manifest(
        output_path
    )

    validate_section_manifest(
        manifest=loaded_manifest,
        textbook_metadata=textbook_metadata,
    )

    assert loaded_manifest == manifest