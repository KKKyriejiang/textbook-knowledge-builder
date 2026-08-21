import json

import pytest

from textbook_kb.knowledge_schema import (
    DEFAULT_KNOWLEDGE_OUTPUT_PATH,
    KNOWLEDGE_SCHEMA_VERSION,
    KnowledgeBase,
    KnowledgeDefinition,
    KnowledgeFormula,
    KnowledgeProvenance,
    KnowledgeRecord,
    KnowledgeSectionMetadata,
    KnowledgeTextbookMetadata,
    SectionKnowledge,
    WorkedExamplePattern,
    load_knowledge_json,
    save_knowledge_json,
)


def build_synthetic_record() -> KnowledgeRecord:
    textbook_metadata = KnowledgeTextbookMetadata(
        grade="10",
        course_id="MATH10",
        course_name="Synthetic Mathematics",
        textbook="Synthetic Algebra Textbook",
    )

    section_metadata = KnowledgeSectionMetadata(
        unit="Unit 1",
        chapter="Chapter 2",
        section="2.1 Solving Linear Equations",
        page_start=10,
        page_end=12,
    )

    provenance = KnowledgeProvenance(
        source_file="synthetic_textbook.pdf",
        page_numbers=[10, 11, 12],
        trace_ids=[
            "math10-u1-c2-s2.1",
        ],
    )

    knowledge = SectionKnowledge(
        summary=(
            "Linear equations can be solved by applying inverse "
            "operations while preserving equality."
        ),
        key_concepts=[
            "linear equation",
            "inverse operations",
            "equivalent equations",
        ],
        definitions=[
            KnowledgeDefinition(
                term="linear equation",
                definition=(
                    "An equation in which the variable has "
                    "degree one."
                ),
            ),
            KnowledgeDefinition(
                term="equivalent equations",
                definition=(
                    "Equations that have the same solution set."
                ),
            ),
        ],
        formulas=[
            KnowledgeFormula(
                name="one-step linear equation",
                expression="x + a = b",
                variables={
                    "x": "the unknown value",
                    "a": "a known constant",
                    "b": "a known constant",
                },
                notes=(
                    "Subtract a from both sides to isolate x."
                ),
            ),
        ],
        skills=[
            "isolate a variable",
            "apply inverse operations",
            "check a solution by substitution",
        ],
        worked_example_patterns=[
            WorkedExamplePattern(
                name="solve a one-variable linear equation",
                problem_type="linear equation solving",
                when_to_use=(
                    "Use this pattern when one variable must "
                    "be isolated."
                ),
                steps=[
                    "Simplify both sides if necessary.",
                    "Move variable terms toward one side.",
                    "Apply inverse operations.",
                    "Check the result by substitution.",
                ],
            ),
        ],
        common_mistakes=[
            "Applying an operation to only one side of the equation.",
            "Making a sign error when moving terms.",
        ],
        prerequisites=[
            "integer arithmetic",
            "order of operations",
        ],
        student_friendly_explanations=[
            (
                "Think of an equation as a balanced scale: "
                "whatever operation you apply to one side must "
                "also be applied to the other."
            ),
        ],
        retrieval_keywords=[
            "linear equation",
            "solve for x",
            "inverse operations",
            "equivalent equations",
        ],
    )

    return KnowledgeRecord(
        knowledge_id="math10-u1-c2-s2.1",
        textbook_metadata=textbook_metadata,
        section_metadata=section_metadata,
        provenance=provenance,
        knowledge=knowledge,
    )


def test_knowledge_record_round_trip() -> None:
    record = build_synthetic_record()

    serialized = record.to_dict()
    restored = KnowledgeRecord.from_dict(serialized)

    assert restored == record


def test_knowledge_base_round_trip() -> None:
    record = build_synthetic_record()

    knowledge_base = KnowledgeBase(
        records=[record],
    )

    serialized = knowledge_base.to_dict()
    restored = KnowledgeBase.from_dict(serialized)

    assert restored == knowledge_base
    assert restored.schema_version == KNOWLEDGE_SCHEMA_VERSION


def test_save_and_load_knowledge_json(tmp_path) -> None:
    knowledge_base = KnowledgeBase(
        records=[
            build_synthetic_record(),
        ]
    )

    output_path = (
        tmp_path
        / "synthetic_knowledge.json"
    )

    returned_path = save_knowledge_json(
        knowledge_base,
        output_path,
    )

    assert returned_path == output_path
    assert output_path.exists()

    loaded = load_knowledge_json(output_path)

    assert loaded == knowledge_base


def test_saved_json_has_expected_structure(tmp_path) -> None:
    knowledge_base = KnowledgeBase(
        records=[
            build_synthetic_record(),
        ]
    )

    output_path = (
        tmp_path
        / "synthetic_knowledge.json"
    )

    save_knowledge_json(
        knowledge_base,
        output_path,
    )

    with output_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    assert data["schema_version"] == "1.0"
    assert len(data["records"]) == 1

    record = data["records"][0]

    assert record["knowledge_id"] == "math10-u1-c2-s2.1"

    assert record["textbook_metadata"] == {
        "grade": "10",
        "course_id": "MATH10",
        "course_name": "Synthetic Mathematics",
        "textbook": "Synthetic Algebra Textbook",
    }

    assert record["section_metadata"]["page_start"] == 10
    assert record["section_metadata"]["page_end"] == 12

    assert record["provenance"]["page_numbers"] == [
        10,
        11,
        12,
    ]

    assert (
        record["knowledge"]["key_concepts"][0]
        == "linear equation"
    )


def test_schema_does_not_store_raw_page_text() -> None:
    knowledge_base = KnowledgeBase(
        records=[
            build_synthetic_record(),
        ]
    )

    serialized = knowledge_base.to_dict()

    serialized_text = json.dumps(
        serialized,
        ensure_ascii=False,
    )

    forbidden_fields = [
        '"raw_text"',
        '"page_text"',
        '"pages"',
        '"source_text"',
        '"full_text"',
    ]

    for field_name in forbidden_fields:
        assert field_name not in serialized_text


def test_rejects_invalid_section_page_range() -> None:
    with pytest.raises(
        ValueError,
        match="page_end",
    ):
        KnowledgeSectionMetadata(
            unit="Unit 1",
            chapter="Chapter 1",
            section="1.1 Synthetic Section",
            page_start=12,
            page_end=10,
        )


def test_rejects_unsorted_provenance_pages() -> None:
    with pytest.raises(
        ValueError,
        match="unique and sorted",
    ):
        KnowledgeProvenance(
            source_file="synthetic.pdf",
            page_numbers=[10, 12, 11],
        )


def test_rejects_duplicate_provenance_pages() -> None:
    with pytest.raises(
        ValueError,
        match="unique and sorted",
    ):
        KnowledgeProvenance(
            source_file="synthetic.pdf",
            page_numbers=[10, 10, 11],
        )


def test_rejects_provenance_page_outside_section_range() -> None:
    original = build_synthetic_record()

    bad_provenance = KnowledgeProvenance(
        source_file="synthetic_textbook.pdf",
        page_numbers=[10, 11, 13],
    )

    with pytest.raises(
        ValueError,
        match="outside the section range",
    ):
        KnowledgeRecord(
            knowledge_id=original.knowledge_id,
            textbook_metadata=original.textbook_metadata,
            section_metadata=original.section_metadata,
            provenance=bad_provenance,
            knowledge=original.knowledge,
        )


def test_rejects_blank_summary() -> None:
    with pytest.raises(
        ValueError,
        match="knowledge.summary",
    ):
        SectionKnowledge(
            summary="   ",
        )


def test_empty_optional_knowledge_categories_are_allowed() -> None:
    knowledge = SectionKnowledge(
        summary="Synthetic section summary.",
    )

    assert knowledge.key_concepts == []
    assert knowledge.definitions == []
    assert knowledge.formulas == []
    assert knowledge.skills == []
    assert knowledge.worked_example_patterns == []
    assert knowledge.common_mistakes == []
    assert knowledge.prerequisites == []
    assert knowledge.student_friendly_explanations == []
    assert knowledge.retrieval_keywords == []


def test_duplicate_knowledge_ids_are_rejected() -> None:
    record = build_synthetic_record()

    with pytest.raises(
        ValueError,
        match="duplicate knowledge_id",
    ):
        KnowledgeBase(
            records=[
                record,
                record,
            ]
        )


def test_default_output_path_is_private_processed_knowledge_path() -> None:
    assert (
        DEFAULT_KNOWLEDGE_OUTPUT_PATH.as_posix()
        == "data/processed/textbook_knowledge.json"
    )