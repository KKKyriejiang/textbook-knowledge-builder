import json
from pathlib import Path

from textbook_kb.knowledge_export import (
    build_and_export_knowledge_base,
)
from textbook_kb.knowledge_model import (
    FakeStructuredKnowledgeModelClient,
    ModelKnowledgeExtractor,
)
from textbook_kb.knowledge_schema import (
    KnowledgeBase,
    load_knowledge_json,
)
from textbook_kb.metadata import (
    SectionManifest,
    SectionMetadata,
    TextbookMetadata,
)
from textbook_kb.metadata_pipeline import (
    TextbookStructure,
    build_textbook_section_sources,
)
from textbook_kb.pdf_parser import ParsedPage


SOURCE_FILE = "synthetic_textbook.pdf"


def build_synthetic_textbook_metadata() -> TextbookMetadata:
    return TextbookMetadata(
        grade="10",
        course_id="MATH10",
        course_name="Synthetic Mathematics",
        textbook="Synthetic Algebra Textbook",
        source_file=SOURCE_FILE,
    )


def build_synthetic_section_manifest() -> SectionManifest:
    return SectionManifest(
        source_file=SOURCE_FILE,
        sections=(
            SectionMetadata(
                unit="Unit 1",
                chapter="Chapter 1",
                section="1.1 Understanding Variables",
                page_start=1,
                page_end=2,
            ),
            SectionMetadata(
                unit="Unit 1",
                chapter="Chapter 1",
                section="1.2 Solving Equations",
                page_start=3,
                page_end=4,
            ),
        ),
    )


def build_synthetic_textbook_structure() -> TextbookStructure:
    return TextbookStructure(
        textbook_metadata=(
            build_synthetic_textbook_metadata()
        ),
        section_manifest=(
            build_synthetic_section_manifest()
        ),
    )


def build_synthetic_pages() -> list[ParsedPage]:
    return [
        ParsedPage(
            page_number=1,
            text=(
                "Synthetic source page one introduces "
                "variables as symbols representing values."
            ),
            source_file=SOURCE_FILE,
        ),
        ParsedPage(
            page_number=2,
            text=(
                "Synthetic source page two discusses "
                "using variables in simple expressions."
            ),
            source_file=SOURCE_FILE,
        ),
        ParsedPage(
            page_number=3,
            text=(
                "Synthetic source page three introduces "
                "solving simple equations."
            ),
            source_file=SOURCE_FILE,
        ),
        ParsedPage(
            page_number=4,
            text=(
                "Synthetic source page four discusses "
                "inverse operations and checking solutions."
            ),
            source_file=SOURCE_FILE,
        ),
    ]


def build_default_fake_response() -> dict:
    return {
        "summary": (
            "Synthetic derived educational knowledge."
        ),
        "key_concepts": [
            "synthetic concept",
        ],
        "definitions": [],
        "formulas": [],
        "skills": [
            "apply a synthetic mathematical method",
        ],
        "worked_example_patterns": [],
        "common_mistakes": [],
        "prerequisites": [],
        "student_friendly_explanations": [
            (
                "A synthetic explanation written "
                "for integration testing."
            ),
        ],
        "retrieval_keywords": [
            "synthetic mathematics",
        ],
    }


def build_section_specific_fake_responses(
    section_sources,
) -> dict[str, dict]:
    first_request_id = None
    second_request_id = None

    from textbook_kb.knowledge_adapter import (
        build_knowledge_extraction_request,
    )

    first_request = (
        build_knowledge_extraction_request(
            section_sources[0]
        )
    )

    second_request = (
        build_knowledge_extraction_request(
            section_sources[1]
        )
    )

    first_request_id = (
        first_request.knowledge_id
    )

    second_request_id = (
        second_request.knowledge_id
    )

    return {
        first_request_id: {
            "summary": (
                "Variables represent values and can "
                "be used in mathematical expressions."
            ),
            "key_concepts": [
                "variable",
                "expression",
            ],
            "definitions": [
                {
                    "term": "variable",
                    "definition": (
                        "A symbol used to represent "
                        "a value."
                    ),
                },
            ],
            "formulas": [],
            "skills": [
                "identify variables",
                "interpret simple expressions",
            ],
            "worked_example_patterns": [],
            "common_mistakes": [],
            "prerequisites": [],
            "student_friendly_explanations": [
                (
                    "A variable acts as a symbol "
                    "that can stand for a value."
                ),
            ],
            "retrieval_keywords": [
                "variable",
                "expression",
                "symbol",
            ],
        },
        second_request_id: {
            "summary": (
                "Simple equations can be solved using "
                "inverse operations and checked afterward."
            ),
            "key_concepts": [
                "equation",
                "inverse operations",
            ],
            "definitions": [],
            "formulas": [],
            "skills": [
                "solve simple equations",
                "check solutions",
            ],
            "worked_example_patterns": [
                {
                    "name": (
                        "solve a simple equation"
                    ),
                    "problem_type": (
                        "one-variable equation"
                    ),
                    "when_to_use": (
                        "Use when a variable must "
                        "be isolated."
                    ),
                    "steps": [
                        "Identify the operation applied to the variable.",
                        "Apply the corresponding inverse operation.",
                        "Check the resulting value.",
                    ],
                },
            ],
            "common_mistakes": [],
            "prerequisites": [],
            "student_friendly_explanations": [
                (
                    "Inverse operations help undo "
                    "operations around the variable."
                ),
            ],
            "retrieval_keywords": [
                "equation",
                "inverse operations",
                "solve for variable",
            ],
        },
    }


def build_fake_extractor(
    section_sources,
) -> ModelKnowledgeExtractor:
    client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_default_fake_response()
            ),
            responses_by_knowledge_id=(
                build_section_specific_fake_responses(
                    section_sources
                )
            ),
        )
    )

    return ModelKnowledgeExtractor(
        client=client,
        extractor_name=(
            "fake-milestone4-integration-model"
        ),
    )


def test_section_manifest_builds_expected_section_sources() -> None:
    pages = build_synthetic_pages()

    structure = (
        build_synthetic_textbook_structure()
    )

    section_sources = (
        build_textbook_section_sources(
            pages=pages,
            structure=structure,
        )
    )

    assert len(
        section_sources
    ) == 2

    first = section_sources[0]
    second = section_sources[1]

    assert (
        first.section_metadata.section
        == "1.1 Understanding Variables"
    )

    assert (
        second.section_metadata.section
        == "1.2 Solving Equations"
    )

    assert [
        page.page_number
        for page in first.pages
    ] == [
        1,
        2,
    ]

    assert [
        page.page_number
        for page in second.pages
    ] == [
        3,
        4,
    ]


def test_full_synthetic_milestone4_pipeline(
    tmp_path: Path,
) -> None:
    pages = build_synthetic_pages()

    structure = (
        build_synthetic_textbook_structure()
    )

    section_sources = (
        build_textbook_section_sources(
            pages=pages,
            structure=structure,
        )
    )

    extractor = build_fake_extractor(
        section_sources
    )

    result = (
        build_and_export_knowledge_base(
            section_sources=section_sources,
            extractor=extractor,
            output_path=(
                "data/processed/"
                "synthetic_knowledge.json"
            ),
            project_root=tmp_path,
        )
    )

    assert result.output_path.exists()

    assert len(
        result.knowledge_base.records
    ) == 2

    assert result.warnings == []


def test_full_pipeline_output_can_be_loaded(
    tmp_path: Path,
) -> None:
    section_sources = (
        build_textbook_section_sources(
            pages=build_synthetic_pages(),
            structure=(
                build_synthetic_textbook_structure()
            ),
        )
    )

    result = (
        build_and_export_knowledge_base(
            section_sources=section_sources,
            extractor=(
                build_fake_extractor(
                    section_sources
                )
            ),
            output_path=(
                "data/processed/"
                "synthetic_knowledge.json"
            ),
            project_root=tmp_path,
        )
    )

    loaded = load_knowledge_json(
        result.output_path
    )

    assert isinstance(
        loaded,
        KnowledgeBase,
    )

    assert (
        loaded
        == result.knowledge_base
    )

    assert len(
        loaded.records
    ) == 2


def test_full_pipeline_preserves_textbook_metadata(
    tmp_path: Path,
) -> None:
    section_sources = (
        build_textbook_section_sources(
            pages=build_synthetic_pages(),
            structure=(
                build_synthetic_textbook_structure()
            ),
        )
    )

    result = (
        build_and_export_knowledge_base(
            section_sources=section_sources,
            extractor=(
                build_fake_extractor(
                    section_sources
                )
            ),
            output_path=(
                "data/processed/"
                "synthetic_knowledge.json"
            ),
            project_root=tmp_path,
        )
    )

    first_record = (
        result.knowledge_base.records[0]
    )

    assert (
        first_record.textbook_metadata.grade
        == "10"
    )

    assert (
        first_record.textbook_metadata.course_id
        == "MATH10"
    )

    assert (
        first_record.textbook_metadata.course_name
        == "Synthetic Mathematics"
    )

    assert (
        first_record.textbook_metadata.textbook
        == "Synthetic Algebra Textbook"
    )


def test_full_pipeline_preserves_section_metadata(
    tmp_path: Path,
) -> None:
    section_sources = (
        build_textbook_section_sources(
            pages=build_synthetic_pages(),
            structure=(
                build_synthetic_textbook_structure()
            ),
        )
    )

    result = (
        build_and_export_knowledge_base(
            section_sources=section_sources,
            extractor=(
                build_fake_extractor(
                    section_sources
                )
            ),
            output_path=(
                "data/processed/"
                "synthetic_knowledge.json"
            ),
            project_root=tmp_path,
        )
    )

    first_record = (
        result.knowledge_base.records[0]
    )

    second_record = (
        result.knowledge_base.records[1]
    )

    assert (
        first_record.section_metadata.section
        == "1.1 Understanding Variables"
    )

    assert (
        first_record.section_metadata.page_start
        == 1
    )

    assert (
        first_record.section_metadata.page_end
        == 2
    )

    assert (
        second_record.section_metadata.section
        == "1.2 Solving Equations"
    )

    assert (
        second_record.section_metadata.page_start
        == 3
    )

    assert (
        second_record.section_metadata.page_end
        == 4
    )


def test_full_pipeline_generates_provenance(
    tmp_path: Path,
) -> None:
    section_sources = (
        build_textbook_section_sources(
            pages=build_synthetic_pages(),
            structure=(
                build_synthetic_textbook_structure()
            ),
        )
    )

    result = (
        build_and_export_knowledge_base(
            section_sources=section_sources,
            extractor=(
                build_fake_extractor(
                    section_sources
                )
            ),
            output_path=(
                "data/processed/"
                "synthetic_knowledge.json"
            ),
            project_root=tmp_path,
        )
    )

    first_record = (
        result.knowledge_base.records[0]
    )

    assert (
        first_record.provenance.source_file
        == SOURCE_FILE
    )

    assert (
        first_record.provenance.page_numbers
        == [
            1,
            2,
        ]
    )

    assert len(
        first_record.provenance.trace_ids
    ) == 2

    assert (
        first_record.provenance.trace_ids[0]
        .startswith("tr-p1-")
    )

    assert (
        first_record.provenance.trace_ids[1]
        .startswith("tr-p2-")
    )


def test_full_pipeline_generates_section_specific_knowledge(
    tmp_path: Path,
) -> None:
    section_sources = (
        build_textbook_section_sources(
            pages=build_synthetic_pages(),
            structure=(
                build_synthetic_textbook_structure()
            ),
        )
    )

    result = (
        build_and_export_knowledge_base(
            section_sources=section_sources,
            extractor=(
                build_fake_extractor(
                    section_sources
                )
            ),
            output_path=(
                "data/processed/"
                "synthetic_knowledge.json"
            ),
            project_root=tmp_path,
        )
    )

    first = (
        result.knowledge_base.records[0]
    )

    second = (
        result.knowledge_base.records[1]
    )

    assert (
        first.knowledge.summary
        == (
            "Variables represent values and can "
            "be used in mathematical expressions."
        )
    )

    assert (
        first.knowledge.key_concepts
        == [
            "variable",
            "expression",
        ]
    )

    assert (
        second.knowledge.summary
        == (
            "Simple equations can be solved using "
            "inverse operations and checked afterward."
        )
    )

    assert len(
        second.knowledge.worked_example_patterns
    ) == 1


def test_final_json_contains_no_source_page_text(
    tmp_path: Path,
) -> None:
    pages = build_synthetic_pages()

    section_sources = (
        build_textbook_section_sources(
            pages=pages,
            structure=(
                build_synthetic_textbook_structure()
            ),
        )
    )

    result = (
        build_and_export_knowledge_base(
            section_sources=section_sources,
            extractor=(
                build_fake_extractor(
                    section_sources
                )
            ),
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

    for page in pages:
        assert (
            page.text
            not in serialized
        )


def test_final_json_contains_no_raw_page_objects(
    tmp_path: Path,
) -> None:
    section_sources = (
        build_textbook_section_sources(
            pages=build_synthetic_pages(),
            structure=(
                build_synthetic_textbook_structure()
            ),
        )
    )

    result = (
        build_and_export_knowledge_base(
            section_sources=section_sources,
            extractor=(
                build_fake_extractor(
                    section_sources
                )
            ),
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
        "pages"
        not in first_record
    )

    assert (
        "source_text"
        not in first_record
    )

    assert (
        "pages"
        not in first_record["provenance"]
    )


def test_full_pipeline_ids_are_deterministic(
    tmp_path: Path,
) -> None:
    section_sources = (
        build_textbook_section_sources(
            pages=build_synthetic_pages(),
            structure=(
                build_synthetic_textbook_structure()
            ),
        )
    )

    first_result = (
        build_and_export_knowledge_base(
            section_sources=section_sources,
            extractor=(
                build_fake_extractor(
                    section_sources
                )
            ),
            output_path=(
                "data/processed/"
                "first_knowledge.json"
            ),
            project_root=tmp_path,
        )
    )

    second_result = (
        build_and_export_knowledge_base(
            section_sources=section_sources,
            extractor=(
                build_fake_extractor(
                    section_sources
                )
            ),
            output_path=(
                "data/processed/"
                "second_knowledge.json"
            ),
            project_root=tmp_path,
        )
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

    assert (
        first_ids
        == second_ids
    )

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