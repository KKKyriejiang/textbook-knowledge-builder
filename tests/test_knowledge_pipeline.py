import json

import pytest

from textbook_kb.knowledge_extraction import (
    KnowledgeExtractionRequest,
    KnowledgeExtractionResult,
)
from textbook_kb.knowledge_pipeline import (
    KnowledgePipelineResult,
    KnowledgePipelineWarning,
    build_knowledge_base,
    run_knowledge_pipeline,
)
from textbook_kb.knowledge_schema import (
    KnowledgeBase,
    SectionKnowledge,
)
from textbook_kb.metadata import (
    SectionMetadata,
    TextbookMetadata,
)
from textbook_kb.pdf_parser import ParsedPage
from textbook_kb.section_source import (
    SectionSource,
)


def build_synthetic_textbook_metadata() -> TextbookMetadata:
    return TextbookMetadata(
        grade="10",
        course_id="MATH10",
        course_name="Synthetic Mathematics",
        textbook="Synthetic Algebra Textbook",
        source_file="synthetic_textbook.pdf",
    )


def build_first_section_source() -> SectionSource:
    return SectionSource(
        textbook_metadata=(
            build_synthetic_textbook_metadata()
        ),
        section_metadata=SectionMetadata(
            unit="Unit 1",
            chapter="Chapter 2",
            section="2.1 Solving Linear Equations",
            page_start=10,
            page_end=11,
        ),
        pages=(
            ParsedPage(
                page_number=10,
                text=(
                    "Synthetic source text about "
                    "linear equations."
                ),
                source_file=(
                    "synthetic_textbook.pdf"
                ),
            ),
            ParsedPage(
                page_number=11,
                text=(
                    "Synthetic source text about "
                    "inverse operations."
                ),
                source_file=(
                    "synthetic_textbook.pdf"
                ),
            ),
        ),
    )


def build_second_section_source() -> SectionSource:
    return SectionSource(
        textbook_metadata=(
            build_synthetic_textbook_metadata()
        ),
        section_metadata=SectionMetadata(
            unit="Unit 1",
            chapter="Chapter 2",
            section="2.2 Graphing Linear Equations",
            page_start=12,
            page_end=13,
        ),
        pages=(
            ParsedPage(
                page_number=12,
                text=(
                    "Synthetic source text about "
                    "coordinate graphs."
                ),
                source_file=(
                    "synthetic_textbook.pdf"
                ),
            ),
            ParsedPage(
                page_number=13,
                text=(
                    "Synthetic source text about "
                    "graphing equations."
                ),
                source_file=(
                    "synthetic_textbook.pdf"
                ),
            ),
        ),
    )


class SyntheticPipelineExtractor:
    """
    Deterministic synthetic extractor used only by tests.

    It makes no API calls and contains no real textbook content.
    """

    def __init__(self) -> None:
        self.requests: list[
            KnowledgeExtractionRequest
        ] = []

    def extract(
        self,
        request: KnowledgeExtractionRequest,
    ) -> KnowledgeExtractionResult:
        self.requests.append(
            request
        )

        warnings: list[str] = []

        if "Graphing" in request.section:
            warnings.append(
                "Synthetic quality-control warning."
            )

        return KnowledgeExtractionResult(
            knowledge=SectionKnowledge(
                summary=(
                    "Derived synthetic knowledge for "
                    f"{request.section}."
                ),
                key_concepts=[
                    request.section,
                ],
                skills=[
                    "synthetic problem solving",
                ],
                retrieval_keywords=[
                    request.section,
                    request.course_id,
                ],
            ),
            extractor_name=(
                "synthetic-pipeline-extractor"
            ),
            warnings=warnings,
        )


class BrokenPipelineExtractor:
    def extract(
        self,
        request: KnowledgeExtractionRequest,
    ) -> dict:
        return {
            "invalid": "result",
        }


def build_synthetic_section_sources() -> list[
    SectionSource
]:
    return [
        build_first_section_source(),
        build_second_section_source(),
    ]


def test_run_knowledge_pipeline_returns_result() -> None:
    extractor = SyntheticPipelineExtractor()

    result = run_knowledge_pipeline(
        section_sources=(
            build_synthetic_section_sources()
        ),
        extractor=extractor,
    )

    assert isinstance(
        result,
        KnowledgePipelineResult,
    )

    assert isinstance(
        result.knowledge_base,
        KnowledgeBase,
    )


def test_pipeline_processes_every_section_once() -> None:
    extractor = SyntheticPipelineExtractor()

    section_sources = (
        build_synthetic_section_sources()
    )

    result = run_knowledge_pipeline(
        section_sources=section_sources,
        extractor=extractor,
    )

    assert len(
        extractor.requests
    ) == 2

    assert len(
        result.knowledge_base.records
    ) == 2


def test_pipeline_preserves_section_order() -> None:
    extractor = SyntheticPipelineExtractor()

    result = run_knowledge_pipeline(
        section_sources=(
            build_synthetic_section_sources()
        ),
        extractor=extractor,
    )

    records = result.knowledge_base.records

    assert (
        records[0].section_metadata.section
        == "2.1 Solving Linear Equations"
    )

    assert (
        records[1].section_metadata.section
        == "2.2 Graphing Linear Equations"
    )


def test_pipeline_generates_unique_knowledge_ids() -> None:
    extractor = SyntheticPipelineExtractor()

    result = run_knowledge_pipeline(
        section_sources=(
            build_synthetic_section_sources()
        ),
        extractor=extractor,
    )

    knowledge_ids = [
        record.knowledge_id
        for record
        in result.knowledge_base.records
    ]

    assert len(
        knowledge_ids
    ) == 2

    assert len(
        set(knowledge_ids)
    ) == 2


def test_pipeline_generates_page_trace_ids() -> None:
    extractor = SyntheticPipelineExtractor()

    result = run_knowledge_pipeline(
        section_sources=(
            build_synthetic_section_sources()
        ),
        extractor=extractor,
    )

    first_record = (
        result.knowledge_base.records[0]
    )

    second_record = (
        result.knowledge_base.records[1]
    )

    assert (
        first_record.provenance.page_numbers
        == [10, 11]
    )

    assert len(
        first_record.provenance.trace_ids
    ) == 2

    assert (
        first_record.provenance.trace_ids[0]
        .startswith("tr-p10-")
    )

    assert (
        first_record.provenance.trace_ids[1]
        .startswith("tr-p11-")
    )

    assert (
        second_record.provenance.page_numbers
        == [12, 13]
    )

    assert len(
        second_record.provenance.trace_ids
    ) == 2


def test_pipeline_transfers_structured_knowledge() -> None:
    extractor = SyntheticPipelineExtractor()

    result = run_knowledge_pipeline(
        section_sources=(
            build_synthetic_section_sources()
        ),
        extractor=extractor,
    )

    first_record = (
        result.knowledge_base.records[0]
    )

    assert first_record.knowledge.summary == (
        "Derived synthetic knowledge for "
        "2.1 Solving Linear Equations."
    )

    assert first_record.knowledge.skills == [
        "synthetic problem solving",
    ]


def test_pipeline_does_not_store_source_text() -> None:
    extractor = SyntheticPipelineExtractor()

    section_sources = (
        build_synthetic_section_sources()
    )

    source_text_fragments = [
        page.text
        for section_source in section_sources
        for page in section_source.pages
    ]

    result = run_knowledge_pipeline(
        section_sources=section_sources,
        extractor=extractor,
    )

    serialized = json.dumps(
        result.knowledge_base.to_dict(),
        ensure_ascii=False,
    )

    assert "source_text" not in serialized

    for source_text in source_text_fragments:
        assert source_text not in serialized


def test_pipeline_collects_extraction_warnings() -> None:
    extractor = SyntheticPipelineExtractor()

    result = run_knowledge_pipeline(
        section_sources=(
            build_synthetic_section_sources()
        ),
        extractor=extractor,
    )

    assert len(
        result.warnings
    ) == 1

    warning = result.warnings[0]

    assert isinstance(
        warning,
        KnowledgePipelineWarning,
    )

    assert warning.extractor_name == (
        "synthetic-pipeline-extractor"
    )

    assert warning.message == (
        "Synthetic quality-control warning."
    )

    assert warning.knowledge_id == (
        result.knowledge_base.records[1]
        .knowledge_id
    )


def test_pipeline_warnings_are_not_part_of_knowledge_base() -> None:
    extractor = SyntheticPipelineExtractor()

    result = run_knowledge_pipeline(
        section_sources=(
            build_synthetic_section_sources()
        ),
        extractor=extractor,
    )

    serialized = json.dumps(
        result.knowledge_base.to_dict(),
        ensure_ascii=False,
    )

    assert (
        "Synthetic quality-control warning."
        not in serialized
    )


def test_build_knowledge_base_convenience_wrapper() -> None:
    extractor = SyntheticPipelineExtractor()

    knowledge_base = build_knowledge_base(
        section_sources=(
            build_synthetic_section_sources()
        ),
        extractor=extractor,
    )

    assert isinstance(
        knowledge_base,
        KnowledgeBase,
    )

    assert len(
        knowledge_base.records
    ) == 2


def test_pipeline_rejects_empty_section_sources() -> None:
    extractor = SyntheticPipelineExtractor()

    with pytest.raises(
        ValueError,
        match="at least one",
    ):
        run_knowledge_pipeline(
            section_sources=[],
            extractor=extractor,
        )


def test_pipeline_rejects_invalid_section_source_item() -> None:
    extractor = SyntheticPipelineExtractor()

    with pytest.raises(
        TypeError,
        match="index 1",
    ):
        run_knowledge_pipeline(
            section_sources=[
                build_first_section_source(),
                "invalid-section-source",
            ],
            extractor=extractor,
        )


def test_pipeline_rejects_invalid_extractor_result() -> None:
    extractor = BrokenPipelineExtractor()

    with pytest.raises(
        TypeError,
        match="KnowledgeExtractionResult",
    ):
        run_knowledge_pipeline(
            section_sources=[
                build_first_section_source(),
            ],
            extractor=extractor,
        )


def test_duplicate_sections_produce_duplicate_id_error() -> None:
    extractor = SyntheticPipelineExtractor()

    duplicated_section = (
        build_first_section_source()
    )

    with pytest.raises(
        ValueError,
        match="duplicate knowledge_id",
    ):
        run_knowledge_pipeline(
            section_sources=[
                duplicated_section,
                duplicated_section,
            ],
            extractor=extractor,
        )


def test_pipeline_ids_are_deterministic_across_runs() -> None:
    first_extractor = (
        SyntheticPipelineExtractor()
    )

    second_extractor = (
        SyntheticPipelineExtractor()
    )

    section_sources = (
        build_synthetic_section_sources()
    )

    first_result = run_knowledge_pipeline(
        section_sources=section_sources,
        extractor=first_extractor,
    )

    second_result = run_knowledge_pipeline(
        section_sources=section_sources,
        extractor=second_extractor,
    )

    first_ids = [
        record.knowledge_id
        for record
        in first_result.knowledge_base.records
    ]

    second_ids = [
        record.knowledge_id
        for record
        in second_result.knowledge_base.records
    ]

    assert first_ids == second_ids

    first_trace_ids = [
        record.provenance.trace_ids
        for record
        in first_result.knowledge_base.records
    ]

    second_trace_ids = [
        record.provenance.trace_ids
        for record
        in second_result.knowledge_base.records
    ]

    assert (
        first_trace_ids
        == second_trace_ids
    )