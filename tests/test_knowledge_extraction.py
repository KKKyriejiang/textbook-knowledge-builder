import json

import pytest

from textbook_kb.knowledge_extraction import (
    KnowledgeExtractionRequest,
    KnowledgeExtractionResult,
    KnowledgeExtractor,
    build_knowledge_record_from_extraction,
    run_knowledge_extraction,
)
from textbook_kb.knowledge_schema import (
    KnowledgeDefinition,
    SectionKnowledge,
)


def build_synthetic_request() -> KnowledgeExtractionRequest:
    return KnowledgeExtractionRequest(
        knowledge_id="math10-u1-c2-s2.1",
        grade="10",
        course_id="MATH10",
        course_name="Synthetic Mathematics",
        textbook="Synthetic Algebra Textbook",
        unit="Unit 1",
        chapter="Chapter 2",
        section="2.1 Solving Linear Equations",
        page_start=10,
        page_end=12,
        source_file="synthetic_textbook.pdf",
        page_numbers=[
            10,
            11,
            12,
        ],
        source_text=(
            "Synthetic educational source text about solving "
            "linear equations. This text is created only for tests."
        ),
        trace_ids=[
            "math10-u1-c2-s2.1",
        ],
    )


def build_synthetic_knowledge() -> SectionKnowledge:
    return SectionKnowledge(
        summary=(
            "Linear equations can be solved by applying "
            "inverse operations while preserving equality."
        ),
        key_concepts=[
            "linear equation",
            "inverse operations",
        ],
        definitions=[
            KnowledgeDefinition(
                term="linear equation",
                definition=(
                    "An equation whose variable has degree one."
                ),
            ),
        ],
        skills=[
            "isolate a variable",
            "check a solution",
        ],
        common_mistakes=[
            "Applying an operation to only one side.",
        ],
        prerequisites=[
            "integer arithmetic",
        ],
        student_friendly_explanations=[
            (
                "An equation behaves like a balanced scale, "
                "so the same operation is applied to both sides."
            ),
        ],
        retrieval_keywords=[
            "linear equation",
            "solve for x",
            "inverse operations",
        ],
    )


class SyntheticExtractor:
    """
    Deterministic test extractor.

    It contains no API calls and uses no real textbook content.
    """

    def extract(
        self,
        request: KnowledgeExtractionRequest,
    ) -> KnowledgeExtractionResult:
        assert request.source_text

        return KnowledgeExtractionResult(
            knowledge=build_synthetic_knowledge(),
            extractor_name="synthetic-test-extractor",
        )


class BadReturnTypeExtractor:
    def extract(
        self,
        request: KnowledgeExtractionRequest,
    ) -> dict:
        return {
            "summary": "invalid raw dictionary result",
        }


def test_valid_extraction_request() -> None:
    request = build_synthetic_request()

    assert request.knowledge_id == "math10-u1-c2-s2.1"
    assert request.page_numbers == [
        10,
        11,
        12,
    ]
    assert request.source_text


def test_synthetic_extractor_implements_protocol() -> None:
    extractor = SyntheticExtractor()

    assert isinstance(
        extractor,
        KnowledgeExtractor,
    )


def test_run_knowledge_extraction() -> None:
    request = build_synthetic_request()
    extractor = SyntheticExtractor()

    result = run_knowledge_extraction(
        extractor,
        request,
    )

    assert isinstance(
        result,
        KnowledgeExtractionResult,
    )

    assert (
        result.extractor_name
        == "synthetic-test-extractor"
    )

    assert (
        result.knowledge.summary
        == (
            "Linear equations can be solved by applying "
            "inverse operations while preserving equality."
        )
    )


def test_build_knowledge_record_from_extraction() -> None:
    request = build_synthetic_request()

    result = KnowledgeExtractionResult(
        knowledge=build_synthetic_knowledge(),
        extractor_name="synthetic-test-extractor",
    )

    record = build_knowledge_record_from_extraction(
        request,
        result,
    )

    assert record.knowledge_id == request.knowledge_id

    assert (
        record.textbook_metadata.grade
        == request.grade
    )

    assert (
        record.textbook_metadata.course_id
        == request.course_id
    )

    assert (
        record.section_metadata.section
        == request.section
    )

    assert (
        record.section_metadata.page_start
        == 10
    )

    assert (
        record.section_metadata.page_end
        == 12
    )

    assert record.provenance.page_numbers == [
        10,
        11,
        12,
    ]

    assert (
        record.knowledge.summary
        == result.knowledge.summary
    )


def test_final_record_does_not_contain_source_text() -> None:
    request = build_synthetic_request()

    result = KnowledgeExtractionResult(
        knowledge=build_synthetic_knowledge(),
        extractor_name="synthetic-test-extractor",
    )

    record = build_knowledge_record_from_extraction(
        request,
        result,
    )

    serialized = json.dumps(
        record.to_dict(),
        ensure_ascii=False,
    )

    assert "source_text" not in serialized

    assert (
        request.source_text
        not in serialized
    )


def test_extraction_result_does_not_store_raw_response() -> None:
    result = KnowledgeExtractionResult(
        knowledge=build_synthetic_knowledge(),
        extractor_name="synthetic-test-extractor",
    )

    assert not hasattr(
        result,
        "raw_response",
    )

    assert not hasattr(
        result,
        "source_text",
    )


def test_rejects_blank_source_text() -> None:
    with pytest.raises(
        ValueError,
        match="source_text",
    ):
        KnowledgeExtractionRequest(
            knowledge_id="synthetic-id",
            grade="10",
            course_id="MATH10",
            course_name="Synthetic Mathematics",
            textbook="Synthetic Textbook",
            unit="Unit 1",
            chapter="Chapter 1",
            section="1.1 Synthetic Section",
            page_start=1,
            page_end=2,
            source_file="synthetic.pdf",
            page_numbers=[
                1,
                2,
            ],
            source_text="   ",
        )


def test_rejects_page_outside_section_range() -> None:
    with pytest.raises(
        ValueError,
        match="outside the section range",
    ):
        KnowledgeExtractionRequest(
            knowledge_id="synthetic-id",
            grade="10",
            course_id="MATH10",
            course_name="Synthetic Mathematics",
            textbook="Synthetic Textbook",
            unit="Unit 1",
            chapter="Chapter 1",
            section="1.1 Synthetic Section",
            page_start=5,
            page_end=7,
            source_file="synthetic.pdf",
            page_numbers=[
                5,
                6,
                8,
            ],
            source_text="Synthetic test source.",
        )


def test_rejects_unsorted_page_numbers() -> None:
    with pytest.raises(
        ValueError,
        match="unique and sorted",
    ):
        KnowledgeExtractionRequest(
            knowledge_id="synthetic-id",
            grade="10",
            course_id="MATH10",
            course_name="Synthetic Mathematics",
            textbook="Synthetic Textbook",
            unit="Unit 1",
            chapter="Chapter 1",
            section="1.1 Synthetic Section",
            page_start=5,
            page_end=7,
            source_file="synthetic.pdf",
            page_numbers=[
                5,
                7,
                6,
            ],
            source_text="Synthetic test source.",
        )


def test_rejects_duplicate_page_numbers() -> None:
    with pytest.raises(
        ValueError,
        match="unique and sorted",
    ):
        KnowledgeExtractionRequest(
            knowledge_id="synthetic-id",
            grade="10",
            course_id="MATH10",
            course_name="Synthetic Mathematics",
            textbook="Synthetic Textbook",
            unit="Unit 1",
            chapter="Chapter 1",
            section="1.1 Synthetic Section",
            page_start=5,
            page_end=7,
            source_file="synthetic.pdf",
            page_numbers=[
                5,
                5,
                6,
            ],
            source_text="Synthetic test source.",
        )


def test_rejects_invalid_extractor_return_type() -> None:
    request = build_synthetic_request()
    extractor = BadReturnTypeExtractor()

    with pytest.raises(
        TypeError,
        match="KnowledgeExtractionResult",
    ):
        run_knowledge_extraction(
            extractor,
            request,
        )


def test_extraction_warnings_are_allowed() -> None:
    result = KnowledgeExtractionResult(
        knowledge=build_synthetic_knowledge(),
        extractor_name="synthetic-test-extractor",
        warnings=[
            "No formula was identified in the synthetic section.",
        ],
    )

    assert len(result.warnings) == 1


def test_empty_warnings_are_allowed() -> None:
    result = KnowledgeExtractionResult(
        knowledge=build_synthetic_knowledge(),
        extractor_name="synthetic-test-extractor",
    )

    assert result.warnings == []