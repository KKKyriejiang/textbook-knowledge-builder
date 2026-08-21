from __future__ import annotations

from collections.abc import Sequence

from textbook_kb.knowledge_extraction import (
    KnowledgeExtractionRequest,
)
from textbook_kb.knowledge_ids import (
    generate_knowledge_id,
    generate_page_trace_ids,
)
from textbook_kb.section_source import SectionSource


def _require_non_empty_string(
    value: str,
    field_name: str,
) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{field_name} must be a non-empty string."
        )


def validate_section_source_for_extraction(
    section_source: SectionSource,
) -> None:
    """
    Validate the SectionSource at the Milestone 3 -> Milestone 4 boundary.

    SectionSource is already validated when created through the normal
    Milestone 2/3 pipeline. These checks protect the extraction boundary
    against manually constructed or corrupted SectionSource objects.
    """

    if not isinstance(
        section_source,
        SectionSource,
    ):
        raise TypeError(
            "section_source must be a SectionSource object."
        )

    if not section_source.pages:
        raise ValueError(
            "section_source.pages must contain at least one page."
        )

    textbook_metadata = (
        section_source.textbook_metadata
    )

    section_metadata = (
        section_source.section_metadata
    )

    _require_non_empty_string(
        textbook_metadata.source_file,
        "textbook_metadata.source_file",
    )

    expected_page_numbers = list(
        range(
            section_metadata.page_start,
            section_metadata.page_end + 1,
        )
    )

    actual_page_numbers = [
        page.page_number
        for page in section_source.pages
    ]

    if actual_page_numbers != expected_page_numbers:
        raise ValueError(
            "section_source page numbers do not match the "
            "section metadata range. "
            f"Expected {expected_page_numbers}, "
            f"got {actual_page_numbers}."
        )

    for page in section_source.pages:
        _require_non_empty_string(
            page.text,
            f"page {page.page_number} text",
        )

        _require_non_empty_string(
            page.source_file,
            f"page {page.page_number} source_file",
        )

        if (
            page.source_file
            != textbook_metadata.source_file
        ):
            raise ValueError(
                "section_source contains a page whose "
                "source_file does not match "
                "textbook_metadata.source_file: "
                f"page {page.page_number} has "
                f"{page.source_file!r}, expected "
                f"{textbook_metadata.source_file!r}."
            )


def format_section_source_text(
    section_source: SectionSource,
) -> str:
    """
    Convert SectionSource pages into transient extraction text.

    Page markers preserve page boundaries so a future extractor can
    distinguish which source page a piece of information came from.

    The returned text contains textbook source content and should remain
    transient/local. It must not be committed as a public artifact.
    """

    validate_section_source_for_extraction(
        section_source
    )

    page_blocks: list[str] = []

    for page in section_source.pages:
        page_blocks.append(
            f"--- PAGE {page.page_number} ---\n"
            f"{page.text.strip()}"
        )

    return "\n\n".join(
        page_blocks
    )


def build_knowledge_extraction_request(
    section_source: SectionSource,
    knowledge_id: str | None = None,
    trace_ids: Sequence[str] | None = None,
) -> KnowledgeExtractionRequest:
    """
    Adapt one validated SectionSource into KnowledgeExtractionRequest.

    knowledge_id is generated deterministically when omitted.

    Page-level trace IDs are generated deterministically when trace_ids
    is omitted. Explicit values may still be supplied for specialized
    workflows or tests.
    """

    validate_section_source_for_extraction(
        section_source
    )

    textbook_metadata = (
        section_source.textbook_metadata
    )

    section_metadata = (
        section_source.section_metadata
    )

    page_numbers = [
        page.page_number
        for page in section_source.pages
    ]

    if knowledge_id is None:
        resolved_knowledge_id = (
            generate_knowledge_id(
                textbook_metadata,
                section_metadata,
            )
        )
    else:
        _require_non_empty_string(
            knowledge_id,
            "knowledge_id",
        )

        resolved_knowledge_id = (
            knowledge_id
        )

    if trace_ids is None:
        resolved_trace_ids = (
            generate_page_trace_ids(
                knowledge_id=resolved_knowledge_id,
                source_file=(
                    textbook_metadata.source_file
                ),
                page_numbers=page_numbers,
            )
        )
    else:
        resolved_trace_ids = list(
            trace_ids
        )

    source_text = format_section_source_text(
        section_source
    )

    return KnowledgeExtractionRequest(
        knowledge_id=resolved_knowledge_id,
        grade=textbook_metadata.grade,
        course_id=textbook_metadata.course_id,
        course_name=textbook_metadata.course_name,
        textbook=textbook_metadata.textbook,
        unit=section_metadata.unit,
        chapter=section_metadata.chapter,
        section=section_metadata.section,
        page_start=section_metadata.page_start,
        page_end=section_metadata.page_end,
        source_file=textbook_metadata.source_file,
        page_numbers=page_numbers,
        source_text=source_text,
        trace_ids=resolved_trace_ids,
    )