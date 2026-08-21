import re

from textbook_kb.knowledge_ids import (
    build_knowledge_identity_payload,
    generate_knowledge_id,
    generate_page_trace_id,
    generate_page_trace_ids,
)
from textbook_kb.metadata import (
    SectionMetadata,
    TextbookMetadata,
)


def build_textbook_metadata(
    source_file: str = "synthetic_textbook.pdf",
) -> TextbookMetadata:
    return TextbookMetadata(
        grade="10",
        course_id="MATH10",
        course_name="Synthetic Mathematics",
        textbook="Synthetic Algebra Textbook",
        source_file=source_file,
    )


def build_section_metadata(
    section: str = "2.1 Solving Linear Equations",
    page_start: int = 10,
    page_end: int = 12,
) -> SectionMetadata:
    return SectionMetadata(
        unit="Unit 1",
        chapter="Chapter 2",
        section=section,
        page_start=page_start,
        page_end=page_end,
    )


def test_generate_knowledge_id_is_deterministic() -> None:
    textbook_metadata = build_textbook_metadata()
    section_metadata = build_section_metadata()

    first = generate_knowledge_id(
        textbook_metadata,
        section_metadata,
    )

    second = generate_knowledge_id(
        textbook_metadata,
        section_metadata,
    )

    assert first == second


def test_knowledge_id_has_readable_prefix_and_hash() -> None:
    knowledge_id = generate_knowledge_id(
        build_textbook_metadata(),
        build_section_metadata(),
    )

    assert knowledge_id.startswith(
        "kb-math10-"
    )

    assert re.fullmatch(
        r"[a-z0-9-]+",
        knowledge_id,
    )


def test_different_section_produces_different_id() -> None:
    textbook_metadata = build_textbook_metadata()

    first = generate_knowledge_id(
        textbook_metadata,
        build_section_metadata(
            section="2.1 Solving Linear Equations",
        ),
    )

    second = generate_knowledge_id(
        textbook_metadata,
        build_section_metadata(
            section="2.2 Graphing Linear Equations",
        ),
    )

    assert first != second


def test_page_boundary_change_does_not_change_knowledge_id() -> None:
    textbook_metadata = build_textbook_metadata()

    original = generate_knowledge_id(
        textbook_metadata,
        build_section_metadata(
            page_start=10,
            page_end=12,
        ),
    )

    corrected = generate_knowledge_id(
        textbook_metadata,
        build_section_metadata(
            page_start=10,
            page_end=13,
        ),
    )

    assert original == corrected


def test_machine_specific_directory_does_not_change_id() -> None:
    windows_metadata = build_textbook_metadata(
        source_file=(
            r"D:\private\data\synthetic_textbook.pdf"
        ),
    )

    linux_metadata = build_textbook_metadata(
        source_file=(
            "/home/user/private/synthetic_textbook.pdf"
        ),
    )

    section_metadata = build_section_metadata()

    windows_id = generate_knowledge_id(
        windows_metadata,
        section_metadata,
    )

    linux_id = generate_knowledge_id(
        linux_metadata,
        section_metadata,
    )

    assert windows_id == linux_id


def test_identity_payload_does_not_include_page_range() -> None:
    payload = build_knowledge_identity_payload(
        build_textbook_metadata(),
        build_section_metadata(),
    )

    assert "page_start" not in payload
    assert "page_end" not in payload


def test_identity_payload_does_not_include_raw_text() -> None:
    payload = build_knowledge_identity_payload(
        build_textbook_metadata(),
        build_section_metadata(),
    )

    forbidden_fields = {
        "text",
        "source_text",
        "raw_text",
        "page_text",
        "pages",
    }

    assert forbidden_fields.isdisjoint(
        payload.keys()
    )


def test_identity_payload_stores_filename_only() -> None:
    payload = build_knowledge_identity_payload(
        build_textbook_metadata(
            source_file=(
                r"D:\private\books\synthetic_textbook.pdf"
            ),
        ),
        build_section_metadata(),
    )

    assert (
        payload["source_file"]
        == "synthetic_textbook.pdf"
    )


def test_generate_page_trace_id_is_deterministic() -> None:
    first = generate_page_trace_id(
        knowledge_id="kb-test-section-123456789abc",
        source_file="synthetic_textbook.pdf",
        page_number=10,
    )

    second = generate_page_trace_id(
        knowledge_id="kb-test-section-123456789abc",
        source_file="synthetic_textbook.pdf",
        page_number=10,
    )

    assert first == second


def test_different_pages_produce_different_trace_ids() -> None:
    first = generate_page_trace_id(
        knowledge_id="kb-test-section-123456789abc",
        source_file="synthetic_textbook.pdf",
        page_number=10,
    )

    second = generate_page_trace_id(
        knowledge_id="kb-test-section-123456789abc",
        source_file="synthetic_textbook.pdf",
        page_number=11,
    )

    assert first != second


def test_generate_page_trace_ids_preserves_page_order() -> None:
    trace_ids = generate_page_trace_ids(
        knowledge_id="kb-test-section-123456789abc",
        source_file="synthetic_textbook.pdf",
        page_numbers=[
            10,
            11,
            12,
        ],
    )

    assert len(trace_ids) == 3

    assert trace_ids[0].startswith(
        "tr-p10-"
    )

    assert trace_ids[1].startswith(
        "tr-p11-"
    )

    assert trace_ids[2].startswith(
        "tr-p12-"
    )


def test_trace_ids_are_unique_for_pages() -> None:
    trace_ids = generate_page_trace_ids(
        knowledge_id="kb-test-section-123456789abc",
        source_file="synthetic_textbook.pdf",
        page_numbers=[
            10,
            11,
            12,
        ],
    )

    assert len(trace_ids) == len(
        set(trace_ids)
    )


def test_trace_ids_do_not_expose_local_directory() -> None:
    trace_id = generate_page_trace_id(
        knowledge_id="kb-test-section-123456789abc",
        source_file=(
            r"D:\private\books\synthetic_textbook.pdf"
        ),
        page_number=10,
    )

    assert "private" not in trace_id
    assert "books" not in trace_id
    assert "synthetic_textbook" not in trace_id