import json
from pathlib import Path

import pytest

from textbook_kb.knowledge_adapter import (
    build_knowledge_extraction_request,
)
from textbook_kb.knowledge_export import (
    build_and_export_knowledge_base,
)
from textbook_kb.knowledge_extraction import (
    KnowledgeExtractionRequest,
    KnowledgeExtractionResult,
    KnowledgeExtractor,
    run_knowledge_extraction,
)
from textbook_kb.knowledge_model import (
    FakeStructuredKnowledgeModelClient,
    ModelKnowledgeExtractor,
    StructuredKnowledgeModelClient,
)
from textbook_kb.knowledge_prompt import (
    KnowledgePromptBundle,
)
from textbook_kb.knowledge_response import (
    KnowledgeResponseValidationError,
)
from textbook_kb.knowledge_schema import (
    SectionKnowledge,
    load_knowledge_json,
)
from textbook_kb.metadata import (
    SectionMetadata,
    TextbookMetadata,
)
from textbook_kb.pdf_parser import ParsedPage
from textbook_kb.section_source import (
    SectionSource,
)


def build_valid_fake_response(
    summary: str = (
        "Synthetic derived knowledge about "
        "linear equations."
    ),
) -> dict:
    return {
        "summary": summary,
        "key_concepts": [
            "linear equation",
            "inverse operations",
        ],
        "definitions": [
            {
                "term": "linear equation",
                "definition": (
                    "A synthetic definition used "
                    "only for testing."
                ),
            },
        ],
        "formulas": [],
        "skills": [
            "solve a synthetic equation",
        ],
        "worked_example_patterns": [],
        "common_mistakes": [],
        "prerequisites": [
            "synthetic arithmetic",
        ],
        "student_friendly_explanations": [
            (
                "A synthetic student-friendly "
                "explanation."
            ),
        ],
        "retrieval_keywords": [
            "linear equation",
            "solve for x",
        ],
    }


def build_textbook_metadata() -> TextbookMetadata:
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
            build_textbook_metadata()
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
                    "Synthetic private page ten "
                    "source content."
                ),
                source_file=(
                    "synthetic_textbook.pdf"
                ),
            ),
            ParsedPage(
                page_number=11,
                text=(
                    "Synthetic private page eleven "
                    "source content."
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
            build_textbook_metadata()
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
                    "Synthetic private page twelve "
                    "source content."
                ),
                source_file=(
                    "synthetic_textbook.pdf"
                ),
            ),
            ParsedPage(
                page_number=13,
                text=(
                    "Synthetic private page thirteen "
                    "source content."
                ),
                source_file=(
                    "synthetic_textbook.pdf"
                ),
            ),
        ),
    )


def build_section_sources() -> list[
    SectionSource
]:
    return [
        build_first_section_source(),
        build_second_section_source(),
    ]


def test_fake_client_implements_protocol() -> None:
    client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_valid_fake_response()
            )
        )
    )

    assert isinstance(
        client,
        StructuredKnowledgeModelClient,
    )


def test_model_extractor_implements_knowledge_extractor() -> None:
    client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_valid_fake_response()
            )
        )
    )

    extractor = ModelKnowledgeExtractor(
        client=client,
        extractor_name=(
            "fake-structured-model"
        ),
    )

    assert isinstance(
        extractor,
        KnowledgeExtractor,
    )


def test_model_extractor_returns_extraction_result() -> None:
    section_source = (
        build_first_section_source()
    )

    request = (
        build_knowledge_extraction_request(
            section_source
        )
    )

    client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_valid_fake_response()
            )
        )
    )

    extractor = ModelKnowledgeExtractor(
        client=client,
        extractor_name=(
            "fake-structured-model"
        ),
    )

    result = run_knowledge_extraction(
        extractor=extractor,
        request=request,
    )

    assert isinstance(
        result,
        KnowledgeExtractionResult,
    )

    assert isinstance(
        result.knowledge,
        SectionKnowledge,
    )

    assert (
        result.extractor_name
        == "fake-structured-model"
    )


def test_model_extractor_builds_prompt_bundle() -> None:
    request = (
        build_knowledge_extraction_request(
            build_first_section_source()
        )
    )

    client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_valid_fake_response()
            )
        )
    )

    extractor = ModelKnowledgeExtractor(
        client=client,
        extractor_name="fake-model",
    )

    extractor.extract(
        request
    )

    assert len(
        client.received_bundles
    ) == 1

    bundle = (
        client.received_bundles[0]
    )

    assert isinstance(
        bundle,
        KnowledgePromptBundle,
    )

    assert (
        bundle.knowledge_id
        == request.knowledge_id
    )


def test_prompt_sent_to_fake_client_contains_source_text() -> None:
    request = (
        build_knowledge_extraction_request(
            build_first_section_source()
        )
    )

    client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_valid_fake_response()
            )
        )
    )

    extractor = ModelKnowledgeExtractor(
        client=client,
        extractor_name="fake-model",
    )

    extractor.extract(
        request
    )

    bundle = (
        client.received_bundles[0]
    )

    combined_prompt = "\n".join(
        message.content
        for message in bundle.messages
    )

    assert (
        request.source_text
        in combined_prompt
    )


def test_fake_client_returns_defensive_copy() -> None:
    original_response = (
        build_valid_fake_response()
    )

    client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                original_response
            )
        )
    )

    request = (
        build_knowledge_extraction_request(
            build_first_section_source()
        )
    )

    extractor = ModelKnowledgeExtractor(
        client=client,
        extractor_name="fake-model",
    )

    extractor.extract(
        request
    )

    assert (
        original_response
        == build_valid_fake_response()
    )


def test_fake_client_can_return_section_specific_response() -> None:
    first_source = (
        build_first_section_source()
    )

    second_source = (
        build_second_section_source()
    )

    first_request = (
        build_knowledge_extraction_request(
            first_source
        )
    )

    second_request = (
        build_knowledge_extraction_request(
            second_source
        )
    )

    client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_valid_fake_response(
                    summary=(
                        "Default synthetic summary."
                    )
                )
            ),
            responses_by_knowledge_id={
                second_request.knowledge_id: (
                    build_valid_fake_response(
                        summary=(
                            "Section-specific synthetic "
                            "graphing summary."
                        )
                    )
                ),
            },
        )
    )

    extractor = ModelKnowledgeExtractor(
        client=client,
        extractor_name="fake-model",
    )

    first_result = extractor.extract(
        first_request
    )

    second_result = extractor.extract(
        second_request
    )

    assert first_result.knowledge.summary == (
        "Default synthetic summary."
    )

    assert second_result.knowledge.summary == (
        "Section-specific synthetic "
        "graphing summary."
    )


def test_invalid_fake_response_is_rejected() -> None:
    invalid_response = (
        build_valid_fake_response()
    )

    del invalid_response[
        "retrieval_keywords"
    ]

    client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                invalid_response
            )
        )
    )

    extractor = ModelKnowledgeExtractor(
        client=client,
        extractor_name="fake-model",
    )

    request = (
        build_knowledge_extraction_request(
            build_first_section_source()
        )
    )

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="missing required fields",
    ):
        extractor.extract(
            request
        )


def test_extra_fake_response_field_is_rejected() -> None:
    invalid_response = (
        build_valid_fake_response()
    )

    invalid_response[
        "source_text"
    ] = "Synthetic unsafe content."

    client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                invalid_response
            )
        )
    )

    extractor = ModelKnowledgeExtractor(
        client=client,
        extractor_name="fake-model",
    )

    request = (
        build_knowledge_extraction_request(
            build_first_section_source()
        )
    )

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="unexpected fields",
    ):
        extractor.extract(
            request
        )


def test_end_to_end_fake_model_pipeline() -> None:
    client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_valid_fake_response()
            )
        )
    )

    extractor = ModelKnowledgeExtractor(
        client=client,
        extractor_name=(
            "fake-structured-model"
        ),
    )

    section_sources = (
        build_section_sources()
    )

    from textbook_kb.knowledge_pipeline import (
        run_knowledge_pipeline,
    )

    result = run_knowledge_pipeline(
        section_sources=section_sources,
        extractor=extractor,
    )

    assert len(
        result.knowledge_base.records
    ) == 2

    assert len(
        client.received_bundles
    ) == 2

    assert (
        result.knowledge_base.records[0]
        .knowledge.summary
        == (
            "Synthetic derived knowledge about "
            "linear equations."
        )
    )


def test_end_to_end_fake_model_export(
    tmp_path: Path,
) -> None:
    client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_valid_fake_response()
            )
        )
    )

    extractor = ModelKnowledgeExtractor(
        client=client,
        extractor_name=(
            "fake-structured-model"
        ),
    )

    result = (
        build_and_export_knowledge_base(
            section_sources=(
                build_section_sources()
            ),
            extractor=extractor,
            output_path=(
                "data/processed/"
                "synthetic_knowledge.json"
            ),
            project_root=tmp_path,
        )
    )

    assert result.output_path.exists()

    loaded = load_knowledge_json(
        result.output_path
    )

    assert len(
        loaded.records
    ) == 2

    assert (
        loaded
        == result.knowledge_base
    )


def test_end_to_end_export_contains_no_source_text(
    tmp_path: Path,
) -> None:
    section_sources = (
        build_section_sources()
    )

    source_fragments = [
        page.text
        for section_source
        in section_sources
        for page
        in section_source.pages
    ]

    client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_valid_fake_response()
            )
        )
    )

    extractor = ModelKnowledgeExtractor(
        client=client,
        extractor_name="fake-model",
    )

    result = (
        build_and_export_knowledge_base(
            section_sources=(
                section_sources
            ),
            extractor=extractor,
            output_path=(
                "data/processed/"
                "synthetic_knowledge.json"
            ),
            project_root=tmp_path,
        )
    )

    serialized = (
        result.output_path.read_text(
            encoding="utf-8"
        )
    )

    assert "source_text" not in serialized

    for fragment in source_fragments:
        assert fragment not in serialized


def test_end_to_end_export_contains_structured_knowledge(
    tmp_path: Path,
) -> None:
    client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_valid_fake_response()
            )
        )
    )

    extractor = ModelKnowledgeExtractor(
        client=client,
        extractor_name="fake-model",
    )

    result = (
        build_and_export_knowledge_base(
            section_sources=(
                build_section_sources()
            ),
            extractor=extractor,
            output_path=(
                "data/processed/"
                "synthetic_knowledge.json"
            ),
            project_root=tmp_path,
        )
    )

    data = json.loads(
        result.output_path.read_text(
            encoding="utf-8"
        )
    )

    first_record = (
        data["records"][0]
    )

    assert (
        first_record[
            "knowledge"
        ][
            "summary"
        ]
        == (
            "Synthetic derived knowledge about "
            "linear equations."
        )
    )

    assert (
        first_record[
            "knowledge"
        ][
            "key_concepts"
        ]
        == [
            "linear equation",
            "inverse operations",
        ]
    )


def test_no_model_call_occurs_before_prompt_construction() -> None:
    request = (
        build_knowledge_extraction_request(
            build_first_section_source()
        )
    )

    client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_valid_fake_response()
            )
        )
    )

    assert (
        client.received_bundles
        == []
    )

    extractor = ModelKnowledgeExtractor(
        client=client,
        extractor_name="fake-model",
    )

    extractor.extract(
        request
    )

    assert len(
        client.received_bundles
    ) == 1