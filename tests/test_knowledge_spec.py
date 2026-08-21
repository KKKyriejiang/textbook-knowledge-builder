from dataclasses import fields
from typing import Any

import pytest

from textbook_kb.knowledge_schema import (
    SectionKnowledge,
)
from textbook_kb.knowledge_spec import (
    DEFAULT_KNOWLEDGE_EXTRACTION_SPEC,
    FORBIDDEN_PERSISTENT_FIELDS,
    FORMULA_VARIABLE_MAX_ITEMS,
    KNOWLEDGE_EXTRACTION_SPEC_VERSION,
    KnowledgeExtractionSpec,
    KnowledgeFieldRule,
    build_section_knowledge_json_schema,
    render_knowledge_extraction_instructions,
    validate_persistent_knowledge_contract,
)


def section_knowledge_field_names() -> list[str]:
    return [
        field_info.name
        for field_info in fields(
            SectionKnowledge
        )
    ]


def iter_schema_nodes(
    node: Any,
):
    if isinstance(
        node,
        dict,
    ):
        yield node

        for value in node.values():
            yield from iter_schema_nodes(
                value
            )

    elif isinstance(
        node,
        list,
    ):
        for item in node:
            yield from iter_schema_nodes(
                item
            )


def test_default_spec_version() -> None:
    assert (
        DEFAULT_KNOWLEDGE_EXTRACTION_SPEC.version
        == KNOWLEDGE_EXTRACTION_SPEC_VERSION
    )


def test_default_spec_matches_section_knowledge_schema() -> None:
    expected = (
        section_knowledge_field_names()
    )

    actual = [
        rule.field_name
        for rule in (
            DEFAULT_KNOWLEDGE_EXTRACTION_SPEC
            .field_rules
        )
    ]

    assert actual == expected


def test_every_field_has_extraction_rule() -> None:
    for rule in (
        DEFAULT_KNOWLEDGE_EXTRACTION_SPEC
        .field_rules
    ):
        assert rule.purpose.strip()
        assert rule.extraction_rule.strip()
        assert rule.empty_behavior.strip()


def test_optional_list_fields_define_max_items() -> None:
    for rule in (
        DEFAULT_KNOWLEDGE_EXTRACTION_SPEC
        .field_rules
    ):
        if rule.field_name == "summary":
            assert rule.max_items is None
        else:
            assert rule.max_items is not None
            assert rule.max_items > 0


def test_global_rules_cover_grounding_and_missing_evidence() -> None:
    combined_rules = " ".join(
        DEFAULT_KNOWLEDGE_EXTRACTION_SPEC
        .global_rules
    ).lower()

    assert "source" in combined_rules
    assert "external facts" in combined_rules
    assert "empty list" in combined_rules
    assert "worked examples" in combined_rules
    assert "raw source text" in combined_rules


def test_global_rules_require_mathematical_quality_check() -> None:
    combined_rules = " ".join(
        DEFAULT_KNOWLEDGE_EXTRACTION_SPEC
        .global_rules
    ).lower()

    assert "mathematical claim" in combined_rules
    assert "correct conditions" in combined_rules
    assert "unlike quantities" in combined_rules


def test_global_rules_discourage_unsupported_generalization() -> None:
    combined_rules = " ".join(
        DEFAULT_KNOWLEDGE_EXTRACTION_SPEC
        .global_rules
    ).lower()

    assert "conservative" in combined_rules
    assert "source-grounded" in combined_rules
    assert "domain generalizations" in combined_rules


def field_rule_text(field_name: str) -> str:
    for rule in (
        DEFAULT_KNOWLEDGE_EXTRACTION_SPEC
        .field_rules
    ):
        if rule.field_name == field_name:
            return " ".join(
                (
                    rule.purpose,
                    rule.extraction_rule,
                    rule.empty_behavior,
                )
            ).lower()

    raise AssertionError(
        f"Unknown field rule: {field_name}"
    )


def test_formula_rule_requires_conditions_and_indexing() -> None:
    rule_text = field_rule_text(
        "formulas"
    )

    assert "domain conditions" in rule_text
    assert "indexing conventions" in rule_text
    assert "growth or decrease conditions" in rule_text


def test_student_explanations_preserve_math_conditions() -> None:
    rule_text = field_rule_text(
        "student_friendly_explanations"
    )

    assert "correct mathematical conditions" in rule_text


def test_retrieval_keywords_must_stay_source_grounded() -> None:
    rule_text = field_rule_text(
        "retrieval_keywords"
    )

    assert "source supports" in rule_text
    assert "broad synonyms" in rule_text


def test_json_schema_requires_all_section_knowledge_fields() -> None:
    schema = (
        build_section_knowledge_json_schema()
    )

    assert schema["type"] == "object"

    assert (
        schema["additionalProperties"]
        is False
    )

    assert (
        schema["required"]
        == section_knowledge_field_names()
    )


def test_json_schema_has_exact_top_level_properties() -> None:
    schema = (
        build_section_knowledge_json_schema()
    )

    assert list(
        schema["properties"].keys()
    ) == section_knowledge_field_names()


def test_json_schema_summary_is_string() -> None:
    schema = (
        build_section_knowledge_json_schema()
    )

    summary_schema = (
        schema["properties"]["summary"]
    )

    assert (
        summary_schema["type"]
        == "string"
    )


def test_json_schema_allows_empty_optional_arrays() -> None:
    schema = (
        build_section_knowledge_json_schema()
    )

    array_fields = [
        "key_concepts",
        "definitions",
        "formulas",
        "skills",
        "worked_example_patterns",
        "common_mistakes",
        "prerequisites",
        "student_friendly_explanations",
        "retrieval_keywords",
    ]

    for field_name in array_fields:
        field_schema = (
            schema["properties"][
                field_name
            ]
        )

        assert (
            field_schema["type"]
            == "array"
        )

        assert (
            "minItems"
            not in field_schema
        )


def test_formula_json_contract() -> None:
    schema = (
        build_section_knowledge_json_schema()
    )

    formula_schema = (
        schema["properties"][
            "formulas"
        ]["items"]
    )

    assert (
        formula_schema[
            "additionalProperties"
        ]
        is False
    )

    assert formula_schema["required"] == [
        "name",
        "expression",
        "variables",
        "notes",
    ]

    properties = (
        formula_schema[
            "properties"
        ]
    )

    assert (
        properties["expression"]["type"]
        == "string"
    )

    variables_schema = (
        properties["variables"]
    )

    assert (
        variables_schema["type"]
        == "array"
    )

    assert (
        variables_schema["maxItems"]
        == FORMULA_VARIABLE_MAX_ITEMS
    )

    variable_item = (
        variables_schema["items"]
    )

    assert (
        variable_item["type"]
        == "object"
    )

    assert (
        variable_item[
            "additionalProperties"
        ]
        is False
    )

    assert (
        variable_item["required"]
        == [
            "symbol",
            "meaning",
        ]
    )


def test_every_object_schema_disables_additional_properties() -> None:
    schema = (
        build_section_knowledge_json_schema()
    )

    object_nodes = [
        node
        for node in iter_schema_nodes(
            schema
        )
        if node.get("type") == "object"
    ]

    assert object_nodes

    for object_schema in object_nodes:
        assert (
            object_schema.get(
                "additionalProperties"
            )
            is False
        )


def test_worked_example_contract_uses_generalized_steps() -> None:
    schema = (
        build_section_knowledge_json_schema()
    )

    pattern_schema = (
        schema["properties"][
            "worked_example_patterns"
        ]["items"]
    )

    assert pattern_schema["required"] == [
        "name",
        "problem_type",
        "when_to_use",
        "steps",
    ]

    assert (
        pattern_schema[
            "properties"
        ]["steps"]["type"]
        == "array"
    )


def test_persistent_contract_has_no_raw_source_fields() -> None:
    schema = (
        build_section_knowledge_json_schema()
    )

    properties = set(
        schema[
            "properties"
        ].keys()
    )

    assert (
        properties
        .isdisjoint(
            FORBIDDEN_PERSISTENT_FIELDS
        )
    )

    validate_persistent_knowledge_contract(
        schema
    )


def test_contract_validator_rejects_source_text() -> None:
    unsafe_schema = {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
            },
            "source_text": {
                "type": "string",
            },
        },
    }

    with pytest.raises(
        ValueError,
        match="forbidden transient fields",
    ):
        validate_persistent_knowledge_contract(
            unsafe_schema
        )


def test_rendered_instructions_include_every_field() -> None:
    instructions = (
        render_knowledge_extraction_instructions()
    )

    for field_name in (
        section_knowledge_field_names()
    ):
        assert field_name in instructions


def test_rendered_instructions_contain_no_source_content() -> None:
    instructions = (
        render_knowledge_extraction_instructions()
    )

    synthetic_private_text = (
        "THIS IS PRIVATE SYNTHETIC PAGE CONTENT"
    )

    assert (
        synthetic_private_text
        not in instructions
    )


def test_spec_rejects_duplicate_field_rules() -> None:
    duplicate_rule = KnowledgeFieldRule(
        field_name="summary",
        purpose="Synthetic purpose.",
        extraction_rule=(
            "Synthetic extraction rule."
        ),
        empty_behavior=(
            "Synthetic empty behavior."
        ),
    )

    with pytest.raises(
        ValueError,
    ):
        KnowledgeExtractionSpec(
            version="test",
            global_rules=(
                "Synthetic global rule.",
            ),
            field_rules=(
                duplicate_rule,
                duplicate_rule,
            ),
        )


def test_spec_rejects_missing_schema_fields() -> None:
    only_summary = KnowledgeFieldRule(
        field_name="summary",
        purpose="Synthetic purpose.",
        extraction_rule=(
            "Synthetic extraction rule."
        ),
        empty_behavior=(
            "Synthetic empty behavior."
        ),
    )

    with pytest.raises(
        ValueError,
        match="SectionKnowledge fields",
    ):
        KnowledgeExtractionSpec(
            version="test",
            global_rules=(
                "Synthetic global rule.",
            ),
            field_rules=(
                only_summary,
            ),
        )
