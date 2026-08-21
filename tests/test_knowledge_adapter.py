import pytest

from textbook_kb.knowledge_adapter import (
    build_knowledge_extraction_request,
    format_section_source_text,
    validate_section_source_for_extraction,
)
from textbook_kb.knowledge_extraction import (
    KnowledgeExtractionRequest,
)
from textbook_kb.metadata import (
    SectionMetadata,
    TextbookMetadata,
)
from textbook_kb.pdf_parser import ParsedPage
from textbook_kb.section_source import SectionSource


def build_synthetic_section_source() -> SectionSource:
    textbook_metadata = TextbookMetadata(
        grade="10",
        course_id="MATH10",
        course_name="Synthetic Mathematics",
        textbook="Synthetic Algebra Textbook",
        source_file="synthetic_textbook.pdf",
    )

    section_metadata = SectionMetadata(
        unit="Unit 1",
        chapter="Chapter 2",
        section="2.1 Solving Linear Equations",
        page_start=10,
        page_end=12,
    )

    pages = (
        ParsedPage(
            page_number=10,
            text=(
                "Synthetic page ten about equations "
                "and equality."
            ),
            source_file="synthetic_textbook.pdf",
        ),
        ParsedPage(
            page_number=11,
            text=(
                "Synthetic page eleven about "
                "inverse operations."
            ),
            source_file="synthetic_textbook.pdf",
        ),
        ParsedPage(
            page_number=12,
            text=(
                "Synthetic page twelve about "
                "checking solutions."
            ),
            source_file="synthetic_textbook.pdf",
        ),
    )

    return SectionSource(
        textbook_metadata=textbook_metadata,
        section_metadata=section_metadata,
        pages=pages,
    )


def test_validate_valid_section_source() -> None:
    section_source = build_synthetic_section_source()

    validate_section_source_for_extraction(
        section_source
    )


def test_format_section_source_text_preserves_page_boundaries() -> None:
    section_source = build_synthetic_section_source()

    source_text = format_section_source_text(
        section_source
    )

    assert "--- PAGE 10 ---" in source_text
    assert "--- PAGE 11 ---" in source_text
    assert "--- PAGE 12 ---" in source_text

    assert (
        "Synthetic page ten about equations"
        in source_text
    )

    assert (
        "Synthetic page eleven about inverse operations."
        in source_text
    )

    assert (
        "Synthetic page twelve about checking solutions."
        in source_text
    )


def test_build_knowledge_extraction_request() -> None:
    section_source = build_synthetic_section_source()

    request = build_knowledge_extraction_request(
        section_source=section_source,
        knowledge_id="math10-u1-c2-s2.1",
        trace_ids=[
            "trace-math10-u1-c2-s2.1",
        ],
    )

    assert isinstance(
        request,
        KnowledgeExtractionRequest,
    )

    assert request.knowledge_id == (
        "math10-u1-c2-s2.1"
    )

    assert request.grade == "10"
    assert request.course_id == "MATH10"

    assert (
        request.course_name
        == "Synthetic Mathematics"
    )

    assert (
        request.textbook
        == "Synthetic Algebra Textbook"
    )

    assert request.unit == "Unit 1"
    assert request.chapter == "Chapter 2"

    assert (
        request.section
        == "2.1 Solving Linear Equations"
    )

    assert request.page_start == 10
    assert request.page_end == 12

    assert request.page_numbers == [
        10,
        11,
        12,
    ]

    assert (
        request.source_file
        == "synthetic_textbook.pdf"
    )

    assert request.trace_ids == [
        "trace-math10-u1-c2-s2.1",
    ]


def test_adapter_copies_all_page_text_into_transient_request() -> None:
    section_source = build_synthetic_section_source()

    request = build_knowledge_extraction_request(
        section_source=section_source,
        knowledge_id="synthetic-id",
    )

    for page in section_source.pages:
        assert page.text in request.source_text


def test_adapter_does_not_mutate_section_source() -> None:
    section_source = build_synthetic_section_source()

    original_pages = section_source.pages

    build_knowledge_extraction_request(
        section_source=section_source,
        knowledge_id="synthetic-id",
    )

    assert section_source.pages == original_pages


def test_rejects_empty_page_text() -> None:
    original = build_synthetic_section_source()

    bad_pages = (
        ParsedPage(
            page_number=10,
            text="Synthetic page ten.",
            source_file="synthetic_textbook.pdf",
        ),
        ParsedPage(
            page_number=11,
            text="   ",
            source_file="synthetic_textbook.pdf",
        ),
        ParsedPage(
            page_number=12,
            text="Synthetic page twelve.",
            source_file="synthetic_textbook.pdf",
        ),
    )

    bad_source = SectionSource(
        textbook_metadata=original.textbook_metadata,
        section_metadata=original.section_metadata,
        pages=bad_pages,
    )

    with pytest.raises(
        ValueError,
        match="page 11 text",
    ):
        validate_section_source_for_extraction(
            bad_source
        )


def test_rejects_page_range_mismatch() -> None:
    original = build_synthetic_section_source()

    bad_pages = (
        ParsedPage(
            page_number=10,
            text="Synthetic page ten.",
            source_file="synthetic_textbook.pdf",
        ),
        ParsedPage(
            page_number=12,
            text="Synthetic page twelve.",
            source_file="synthetic_textbook.pdf",
        ),
    )

    bad_source = SectionSource(
        textbook_metadata=original.textbook_metadata,
        section_metadata=original.section_metadata,
        pages=bad_pages,
    )

    with pytest.raises(
        ValueError,
        match="do not match",
    ):
        validate_section_source_for_extraction(
            bad_source
        )


def test_rejects_page_source_mismatch() -> None:
    original = build_synthetic_section_source()

    bad_pages = (
        ParsedPage(
            page_number=10,
            text="Synthetic page ten.",
            source_file="synthetic_textbook.pdf",
        ),
        ParsedPage(
            page_number=11,
            text="Synthetic page eleven.",
            source_file="wrong_textbook.pdf",
        ),
        ParsedPage(
            page_number=12,
            text="Synthetic page twelve.",
            source_file="synthetic_textbook.pdf",
        ),
    )

    bad_source = SectionSource(
        textbook_metadata=original.textbook_metadata,
        section_metadata=original.section_metadata,
        pages=bad_pages,
    )

    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        validate_section_source_for_extraction(
            bad_source
        )


def test_rejects_blank_knowledge_id() -> None:
    section_source = build_synthetic_section_source()

    with pytest.raises(
        ValueError,
        match="knowledge_id",
    ):
        build_knowledge_extraction_request(
            section_source=section_source,
            knowledge_id="   ",
        )


def test_knowledge_id_is_generated_by_default() -> None:
    section_source = build_synthetic_section_source()

    request = build_knowledge_extraction_request(
        section_source=section_source,
    )

    assert request.knowledge_id
    assert request.knowledge_id.startswith(
        "kb-math10-"
    )


def test_trace_ids_are_generated_by_default() -> None:
    section_source = build_synthetic_section_source()

    request = build_knowledge_extraction_request(
        section_source=section_source,
        knowledge_id="synthetic-id",
    )

    assert len(request.trace_ids) == 3

    assert request.trace_ids[0].startswith(
        "tr-p10-"
    )

    assert request.trace_ids[1].startswith(
        "tr-p11-"
    )

    assert request.trace_ids[2].startswith(
        "tr-p12-"
    )

    assert len(
        set(request.trace_ids)
    ) == 3


def test_explicit_empty_trace_ids_are_preserved() -> None:
    section_source = build_synthetic_section_source()

    request = build_knowledge_extraction_request(
        section_source=section_source,
        knowledge_id="synthetic-id",
        trace_ids=[],
    )

    assert request.trace_ids == []


def test_generated_ids_are_deterministic() -> None:
    section_source = build_synthetic_section_source()

    first = build_knowledge_extraction_request(
        section_source=section_source,
    )

    second = build_knowledge_extraction_request(
        section_source=section_source,
    )

    assert (
        first.knowledge_id
        == second.knowledge_id
    )

    assert (
        first.trace_ids
        == second.trace_ids
    )