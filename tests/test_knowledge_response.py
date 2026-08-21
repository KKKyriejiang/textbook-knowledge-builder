import copy
import json

import pytest

from textbook_kb.knowledge_response import (
    KnowledgeResponseJSONError,
    KnowledgeResponseValidationError,
    parse_knowledge_response_json,
    parse_knowledge_response_payload,
    validate_knowledge_response_payload,
)
from textbook_kb.knowledge_schema import (
    SectionKnowledge,
)
from textbook_kb.knowledge_spec import (
    FORMULA_VARIABLE_MAX_ITEMS,
)


def build_valid_payload() -> dict:
    return {
        "summary": (
            "Linear equations can be solved using "
            "inverse operations while preserving equality."
        ),
        "key_concepts": [
            "linear equation",
            "inverse operations",
        ],
        "definitions": [
            {
                "term": "linear equation",
                "definition": (
                    "An equation with a variable "
                    "raised to the first power."
                ),
            },
        ],
        "formulas": [
            {
                "name": (
                    "one-step linear equation"
                ),
                "expression": "x + a = b",
                "variables": [
                    {
                        "symbol": "x",
                        "meaning": (
                            "the unknown value"
                        ),
                    },
                    {
                        "symbol": "a",
                        "meaning": (
                            "a known constant"
                        ),
                    },
                    {
                        "symbol": "b",
                        "meaning": (
                            "a known constant"
                        ),
                    },
                ],
                "notes": (
                    "Subtract a from both sides "
                    "to isolate x."
                ),
            },
        ],
        "skills": [
            "isolate a variable",
            "check a solution",
        ],
        "worked_example_patterns": [
            {
                "name": (
                    "solve a linear equation"
                ),
                "problem_type": (
                    "one-variable linear equation"
                ),
                "when_to_use": (
                    "Use when one unknown must "
                    "be isolated."
                ),
                "steps": [
                    "Simplify each side.",
                    "Apply inverse operations.",
                    "Check the solution.",
                ],
            },
        ],
        "common_mistakes": [
            (
                "Applying an operation to only "
                "one side of the equation."
            ),
        ],
        "prerequisites": [
            "integer arithmetic",
        ],
        "student_friendly_explanations": [
            (
                "Think of an equation as a balanced "
                "scale."
            ),
        ],
        "retrieval_keywords": [
            "linear equation",
            "solve for x",
            "inverse operations",
        ],
    }


def test_parse_valid_payload() -> None:
    knowledge = (
        parse_knowledge_response_payload(
            build_valid_payload()
        )
    )

    assert isinstance(
        knowledge,
        SectionKnowledge,
    )

    assert (
        knowledge.summary
        == build_valid_payload()["summary"]
    )


def test_formula_variables_are_normalized_to_domain_dict() -> None:
    knowledge = (
        parse_knowledge_response_payload(
            build_valid_payload()
        )
    )

    assert (
        knowledge.formulas[0].variables
        == {
            "x": "the unknown value",
            "a": "a known constant",
            "b": "a known constant",
        }
    )


def test_parse_valid_json() -> None:
    response_text = json.dumps(
        build_valid_payload(),
        ensure_ascii=False,
    )

    knowledge = (
        parse_knowledge_response_json(
            response_text
        )
    )

    assert isinstance(
        knowledge,
        SectionKnowledge,
    )

    assert knowledge.key_concepts == [
        "linear equation",
        "inverse operations",
    ]


def test_valid_response_round_trip_structure() -> None:
    payload = build_valid_payload()

    knowledge = (
        parse_knowledge_response_payload(
            payload
        )
    )

    restored = SectionKnowledge.from_dict(
        {
            "summary": knowledge.summary,
            "key_concepts": (
                knowledge.key_concepts
            ),
            "definitions": [
                {
                    "term": item.term,
                    "definition": (
                        item.definition
                    ),
                }
                for item
                in knowledge.definitions
            ],
            "formulas": [
                {
                    "name": item.name,
                    "expression": (
                        item.expression
                    ),
                    "variables": (
                        item.variables
                    ),
                    "notes": item.notes,
                }
                for item
                in knowledge.formulas
            ],
            "skills": knowledge.skills,
            "worked_example_patterns": [
                {
                    "name": item.name,
                    "problem_type": (
                        item.problem_type
                    ),
                    "when_to_use": (
                        item.when_to_use
                    ),
                    "steps": item.steps,
                }
                for item
                in (
                    knowledge
                    .worked_example_patterns
                )
            ],
            "common_mistakes": (
                knowledge.common_mistakes
            ),
            "prerequisites": (
                knowledge.prerequisites
            ),
            "student_friendly_explanations": (
                knowledge
                .student_friendly_explanations
            ),
            "retrieval_keywords": (
                knowledge.retrieval_keywords
            ),
        }
    )

    assert restored == knowledge


def test_empty_optional_arrays_are_valid() -> None:
    payload = build_valid_payload()

    payload[
        "key_concepts"
    ] = []

    payload[
        "definitions"
    ] = []

    payload[
        "formulas"
    ] = []

    payload[
        "skills"
    ] = []

    payload[
        "worked_example_patterns"
    ] = []

    payload[
        "common_mistakes"
    ] = []

    payload[
        "prerequisites"
    ] = []

    payload[
        "student_friendly_explanations"
    ] = []

    payload[
        "retrieval_keywords"
    ] = []

    knowledge = (
        parse_knowledge_response_payload(
            payload
        )
    )

    assert knowledge.key_concepts == []
    assert knowledge.definitions == []
    assert knowledge.formulas == []
    assert knowledge.skills == []


def test_formula_notes_may_be_null() -> None:
    payload = build_valid_payload()

    payload["formulas"][0][
        "notes"
    ] = None

    knowledge = (
        parse_knowledge_response_payload(
            payload
        )
    )

    assert (
        knowledge.formulas[0].notes
        is None
    )


def test_rejects_invalid_json() -> None:
    response_text = (
        '{"summary": "Synthetic",'
    )

    with pytest.raises(
        KnowledgeResponseJSONError,
        match="not valid JSON",
    ):
        parse_knowledge_response_json(
            response_text
        )


def test_rejects_markdown_code_fence() -> None:
    response_text = (
        "```json\n"
        + json.dumps(
            build_valid_payload()
        )
        + "\n```"
    )

    with pytest.raises(
        KnowledgeResponseJSONError,
    ):
        parse_knowledge_response_json(
            response_text
        )


def test_rejects_explanatory_text_around_json() -> None:
    response_text = (
        "Here is the result:\n"
        + json.dumps(
            build_valid_payload()
        )
    )

    with pytest.raises(
        KnowledgeResponseJSONError,
    ):
        parse_knowledge_response_json(
            response_text
        )


def test_rejects_json_array_root() -> None:
    response_text = json.dumps(
        [
            build_valid_payload(),
        ]
    )

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="root must be an object",
    ):
        parse_knowledge_response_json(
            response_text
        )


def test_rejects_missing_top_level_field() -> None:
    payload = build_valid_payload()

    del payload[
        "retrieval_keywords"
    ]

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="missing required fields",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_extra_top_level_field() -> None:
    payload = build_valid_payload()

    payload[
        "raw_response"
    ] = "Synthetic unsafe field."

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="unexpected fields",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_source_text_field() -> None:
    payload = build_valid_payload()

    payload[
        "source_text"
    ] = "Synthetic source."

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="unexpected fields",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_blank_summary() -> None:
    payload = build_valid_payload()

    payload["summary"] = "   "

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="summary",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_non_string_summary() -> None:
    payload = build_valid_payload()

    payload["summary"] = [
        "Synthetic summary",
    ]

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="summary",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_string_instead_of_array() -> None:
    payload = build_valid_payload()

    payload[
        "key_concepts"
    ] = "linear equation"

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="key_concepts must be an array",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_blank_string_inside_array() -> None:
    payload = build_valid_payload()

    payload[
        "skills"
    ] = [
        "solve equations",
        "   ",
    ]

    with pytest.raises(
        KnowledgeResponseValidationError,
        match=r"skills\[1\]",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_definition_missing_field() -> None:
    payload = build_valid_payload()

    payload[
        "definitions"
    ][0] = {
        "term": "linear equation",
    }

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="missing required fields",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_definition_extra_field() -> None:
    payload = build_valid_payload()

    payload[
        "definitions"
    ][0][
        "quote"
    ] = "Synthetic quote."

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="unexpected fields",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_formula_missing_notes() -> None:
    payload = build_valid_payload()

    del payload[
        "formulas"
    ][0][
        "notes"
    ]

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="missing required fields",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_formula_extra_field() -> None:
    payload = build_valid_payload()

    payload[
        "formulas"
    ][0][
        "source_page"
    ] = 10

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="unexpected fields",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_formula_variables_dictionary() -> None:
    payload = build_valid_payload()

    payload[
        "formulas"
    ][0][
        "variables"
    ] = {
        "x": "unknown",
    }

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="variables must be an array",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_formula_variable_missing_field() -> None:
    payload = build_valid_payload()

    payload[
        "formulas"
    ][0][
        "variables"
    ][0] = {
        "symbol": "x",
    }

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="missing required fields",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_formula_variable_extra_field() -> None:
    payload = build_valid_payload()

    payload[
        "formulas"
    ][0][
        "variables"
    ][0][
        "source"
    ] = "synthetic"

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="unexpected fields",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_blank_formula_variable_explanation() -> None:
    payload = build_valid_payload()

    payload[
        "formulas"
    ][0][
        "variables"
    ][0][
        "meaning"
    ] = "   "

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="variables",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_duplicate_formula_variable_symbols() -> None:
    payload = build_valid_payload()

    payload[
        "formulas"
    ][0][
        "variables"
    ].append(
        {
            "symbol": "x",
            "meaning": (
                "duplicate synthetic meaning"
            ),
        }
    )

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="duplicate variable symbol",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_too_many_formula_variables() -> None:
    payload = build_valid_payload()

    payload[
        "formulas"
    ][0][
        "variables"
    ] = [
        {
            "symbol": f"x{index}",
            "meaning": (
                f"synthetic variable {index}"
            ),
        }
        for index in range(
            FORMULA_VARIABLE_MAX_ITEMS
            + 1
        )
    ]

    with pytest.raises(
        KnowledgeResponseValidationError,
        match=(
            "Maximum allowed: "
            f"{FORMULA_VARIABLE_MAX_ITEMS}"
        ),
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_invalid_formula_notes_type() -> None:
    payload = build_valid_payload()

    payload[
        "formulas"
    ][0][
        "notes"
    ] = 123

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="notes",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_worked_example_without_steps() -> None:
    payload = build_valid_payload()

    payload[
        "worked_example_patterns"
    ][0][
        "steps"
    ] = []

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="at least one step",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_worked_example_extra_field() -> None:
    payload = build_valid_payload()

    payload[
        "worked_example_patterns"
    ][0][
        "full_example"
    ] = "Synthetic copied example."

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="unexpected fields",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_too_many_key_concepts() -> None:
    payload = build_valid_payload()

    payload[
        "key_concepts"
    ] = [
        f"concept-{index}"
        for index in range(
            16
        )
    ]

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="Maximum allowed: 15",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_rejects_too_many_retrieval_keywords() -> None:
    payload = build_valid_payload()

    payload[
        "retrieval_keywords"
    ] = [
        f"keyword-{index}"
        for index in range(
            31
        )
    ]

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="Maximum allowed: 30",
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_validation_does_not_mutate_payload() -> None:
    payload = build_valid_payload()

    original = copy.deepcopy(
        payload
    )

    validate_knowledge_response_payload(
        payload
    )

    assert payload == original


def test_parser_does_not_coerce_wrong_types() -> None:
    payload = build_valid_payload()

    payload[
        "skills"
    ] = [
        123,
    ]

    with pytest.raises(
        KnowledgeResponseValidationError,
    ):
        parse_knowledge_response_payload(
            payload
        )


def test_parser_does_not_allow_raw_page_objects() -> None:
    payload = build_valid_payload()

    payload[
        "pages"
    ] = [
        {
            "page_number": 10,
            "text": "Synthetic source.",
        },
    ]

    with pytest.raises(
        KnowledgeResponseValidationError,
        match="unexpected fields",
    ):
        parse_knowledge_response_payload(
            payload
        )