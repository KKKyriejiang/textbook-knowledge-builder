from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from textbook_kb.knowledge_schema import (
    SectionKnowledge,
)
from textbook_kb.knowledge_spec import (
    DEFAULT_KNOWLEDGE_EXTRACTION_SPEC,
    FORMULA_VARIABLE_MAX_ITEMS,
    KnowledgeExtractionSpec,
)


class KnowledgeResponseError(ValueError):
    """
    Base error raised when an extractor response cannot be converted into
    a valid SectionKnowledge object.
    """


class KnowledgeResponseJSONError(
    KnowledgeResponseError
):
    """
    Raised when model output is not valid JSON.
    """


class KnowledgeResponseValidationError(
    KnowledgeResponseError
):
    """
    Raised when valid JSON violates the SectionKnowledge response contract.
    """


def _raise_validation(
    message: str,
) -> None:
    raise KnowledgeResponseValidationError(
        message
    )


def _require_exact_keys(
    payload: Mapping[str, Any],
    expected_keys: set[str],
    location: str,
) -> None:
    actual_keys = set(
        payload.keys()
    )

    missing_keys = (
        expected_keys
        - actual_keys
    )

    extra_keys = (
        actual_keys
        - expected_keys
    )

    if missing_keys:
        _raise_validation(
            f"{location} is missing required fields: "
            f"{sorted(missing_keys)}"
        )

    if extra_keys:
        _raise_validation(
            f"{location} contains unexpected fields: "
            f"{sorted(extra_keys)}"
        )


def _require_non_empty_string(
    value: Any,
    location: str,
) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        _raise_validation(
            f"{location} must be a non-empty string."
        )

    return value


def _validate_string_list(
    value: Any,
    location: str,
    max_items: int | None,
) -> list[str]:
    if not isinstance(
        value,
        list,
    ):
        _raise_validation(
            f"{location} must be an array."
        )

    if (
        max_items is not None
        and len(value) > max_items
    ):
        _raise_validation(
            f"{location} contains too many items. "
            f"Maximum allowed: {max_items}."
        )

    validated: list[str] = []

    for index, item in enumerate(
        value
    ):
        validated.append(
            _require_non_empty_string(
                item,
                f"{location}[{index}]",
            )
        )

    return validated


def _validate_definitions(
    value: Any,
    max_items: int | None,
) -> list[dict[str, Any]]:
    if not isinstance(
        value,
        list,
    ):
        _raise_validation(
            "definitions must be an array."
        )

    if (
        max_items is not None
        and len(value) > max_items
    ):
        _raise_validation(
            "definitions contains too many items. "
            f"Maximum allowed: {max_items}."
        )

    validated: list[
        dict[str, Any]
    ] = []

    expected_keys = {
        "term",
        "definition",
    }

    for index, item in enumerate(
        value
    ):
        if not isinstance(
            item,
            Mapping,
        ):
            _raise_validation(
                f"definitions[{index}] must be an object."
            )

        _require_exact_keys(
            item,
            expected_keys,
            f"definitions[{index}]",
        )

        validated.append(
            {
                "term": (
                    _require_non_empty_string(
                        item["term"],
                        f"definitions[{index}].term",
                    )
                ),
                "definition": (
                    _require_non_empty_string(
                        item["definition"],
                        (
                            f"definitions[{index}]"
                            ".definition"
                        ),
                    )
                ),
            }
        )

    return validated


def _validate_formula_variables(
    value: Any,
    location: str,
) -> dict[str, str]:
    """
    Validate provider-facing formula variable pairs and normalize them to
    the domain model's dict[str, str] representation.
    """

    if not isinstance(
        value,
        list,
    ):
        _raise_validation(
            f"{location} must be an array."
        )

    if len(value) > FORMULA_VARIABLE_MAX_ITEMS:
        _raise_validation(
            f"{location} contains too many items. "
            "Maximum allowed: "
            f"{FORMULA_VARIABLE_MAX_ITEMS}."
        )

    expected_keys = {
        "symbol",
        "meaning",
    }

    validated: dict[
        str,
        str
    ] = {}

    for index, item in enumerate(
        value
    ):
        item_location = (
            f"{location}[{index}]"
        )

        if not isinstance(
            item,
            Mapping,
        ):
            _raise_validation(
                f"{item_location} must be an object."
            )

        _require_exact_keys(
            item,
            expected_keys,
            item_location,
        )

        symbol = (
            _require_non_empty_string(
                item["symbol"],
                f"{item_location}.symbol",
            )
        )

        meaning = (
            _require_non_empty_string(
                item["meaning"],
                f"{item_location}.meaning",
            )
        )

        if symbol in validated:
            _raise_validation(
                f"{location} contains duplicate "
                f"variable symbol: {symbol!r}."
            )

        validated[
            symbol
        ] = meaning

    return validated


def _validate_formulas(
    value: Any,
    max_items: int | None,
) -> list[dict[str, Any]]:
    if not isinstance(
        value,
        list,
    ):
        _raise_validation(
            "formulas must be an array."
        )

    if (
        max_items is not None
        and len(value) > max_items
    ):
        _raise_validation(
            "formulas contains too many items. "
            f"Maximum allowed: {max_items}."
        )

    validated: list[
        dict[str, Any]
    ] = []

    expected_keys = {
        "name",
        "expression",
        "variables",
        "notes",
    }

    for index, item in enumerate(
        value
    ):
        if not isinstance(
            item,
            Mapping,
        ):
            _raise_validation(
                f"formulas[{index}] must be an object."
            )

        _require_exact_keys(
            item,
            expected_keys,
            f"formulas[{index}]",
        )

        notes = item["notes"]

        if notes is not None:
            notes = (
                _require_non_empty_string(
                    notes,
                    f"formulas[{index}].notes",
                )
            )

        validated.append(
            {
                "name": (
                    _require_non_empty_string(
                        item["name"],
                        f"formulas[{index}].name",
                    )
                ),
                "expression": (
                    _require_non_empty_string(
                        item["expression"],
                        (
                            f"formulas[{index}]"
                            ".expression"
                        ),
                    )
                ),
                "variables": (
                    _validate_formula_variables(
                        item["variables"],
                        (
                            f"formulas[{index}]"
                            ".variables"
                        ),
                    )
                ),
                "notes": notes,
            }
        )

    return validated


def _validate_worked_example_patterns(
    value: Any,
    max_items: int | None,
) -> list[dict[str, Any]]:
    if not isinstance(
        value,
        list,
    ):
        _raise_validation(
            "worked_example_patterns must be an array."
        )

    if (
        max_items is not None
        and len(value) > max_items
    ):
        _raise_validation(
            "worked_example_patterns contains too many items. "
            f"Maximum allowed: {max_items}."
        )

    validated: list[
        dict[str, Any]
    ] = []

    expected_keys = {
        "name",
        "problem_type",
        "when_to_use",
        "steps",
    }

    for index, item in enumerate(
        value
    ):
        if not isinstance(
            item,
            Mapping,
        ):
            _raise_validation(
                "worked_example_patterns"
                f"[{index}] must be an object."
            )

        _require_exact_keys(
            item,
            expected_keys,
            (
                "worked_example_patterns"
                f"[{index}]"
            ),
        )

        steps = _validate_string_list(
            item["steps"],
            (
                "worked_example_patterns"
                f"[{index}].steps"
            ),
            max_items=15,
        )

        if not steps:
            _raise_validation(
                "worked_example_patterns"
                f"[{index}].steps must contain "
                "at least one step."
            )

        validated.append(
            {
                "name": (
                    _require_non_empty_string(
                        item["name"],
                        (
                            "worked_example_patterns"
                            f"[{index}].name"
                        ),
                    )
                ),
                "problem_type": (
                    _require_non_empty_string(
                        item["problem_type"],
                        (
                            "worked_example_patterns"
                            f"[{index}].problem_type"
                        ),
                    )
                ),
                "when_to_use": (
                    _require_non_empty_string(
                        item["when_to_use"],
                        (
                            "worked_example_patterns"
                            f"[{index}].when_to_use"
                        ),
                    )
                ),
                "steps": steps,
            }
        )

    return validated


def _field_max_items(
    spec: KnowledgeExtractionSpec,
) -> dict[str, int | None]:
    return {
        rule.field_name: rule.max_items
        for rule in spec.field_rules
    }


def validate_knowledge_response_payload(
    payload: Mapping[str, Any],
    spec: KnowledgeExtractionSpec = (
        DEFAULT_KNOWLEDGE_EXTRACTION_SPEC
    ),
) -> dict[str, Any]:
    """
    Strictly validate a parsed model response.

    No type coercion is performed.

    Provider-facing formula variable arrays are normalized into the
    KnowledgeFormula domain representation during this step.
    """

    if not isinstance(
        spec,
        KnowledgeExtractionSpec,
    ):
        raise TypeError(
            "spec must be a "
            "KnowledgeExtractionSpec object."
        )

    if not isinstance(
        payload,
        Mapping,
    ):
        _raise_validation(
            "Knowledge response root must be an object."
        )

    expected_top_level_fields = {
        rule.field_name
        for rule in spec.field_rules
    }

    _require_exact_keys(
        payload,
        expected_top_level_fields,
        "Knowledge response",
    )

    max_items = (
        _field_max_items(
            spec
        )
    )

    validated = {
        "summary": (
            _require_non_empty_string(
                payload["summary"],
                "summary",
            )
        ),
        "key_concepts": (
            _validate_string_list(
                payload["key_concepts"],
                "key_concepts",
                max_items["key_concepts"],
            )
        ),
        "definitions": (
            _validate_definitions(
                payload["definitions"],
                max_items["definitions"],
            )
        ),
        "formulas": (
            _validate_formulas(
                payload["formulas"],
                max_items["formulas"],
            )
        ),
        "skills": (
            _validate_string_list(
                payload["skills"],
                "skills",
                max_items["skills"],
            )
        ),
        "worked_example_patterns": (
            _validate_worked_example_patterns(
                payload[
                    "worked_example_patterns"
                ],
                max_items[
                    "worked_example_patterns"
                ],
            )
        ),
        "common_mistakes": (
            _validate_string_list(
                payload["common_mistakes"],
                "common_mistakes",
                max_items["common_mistakes"],
            )
        ),
        "prerequisites": (
            _validate_string_list(
                payload["prerequisites"],
                "prerequisites",
                max_items["prerequisites"],
            )
        ),
        "student_friendly_explanations": (
            _validate_string_list(
                payload[
                    "student_friendly_explanations"
                ],
                "student_friendly_explanations",
                max_items[
                    "student_friendly_explanations"
                ],
            )
        ),
        "retrieval_keywords": (
            _validate_string_list(
                payload["retrieval_keywords"],
                "retrieval_keywords",
                max_items["retrieval_keywords"],
            )
        ),
    }

    return validated


def parse_knowledge_response_payload(
    payload: Mapping[str, Any],
    spec: KnowledgeExtractionSpec = (
        DEFAULT_KNOWLEDGE_EXTRACTION_SPEC
    ),
) -> SectionKnowledge:
    """
    Validate an already-parsed structured response and convert it into
    SectionKnowledge.
    """

    validated = (
        validate_knowledge_response_payload(
            payload=payload,
            spec=spec,
        )
    )

    try:
        return SectionKnowledge.from_dict(
            validated
        )
    except (
        TypeError,
        ValueError,
        KeyError,
    ) as exc:
        raise KnowledgeResponseValidationError(
            "Validated response could not be converted "
            "into SectionKnowledge."
        ) from exc


def parse_knowledge_response_json(
    response_text: str,
    spec: KnowledgeExtractionSpec = (
        DEFAULT_KNOWLEDGE_EXTRACTION_SPEC
    ),
) -> SectionKnowledge:
    """
    Parse strict JSON model output into SectionKnowledge.
    """

    if (
        not isinstance(response_text, str)
        or not response_text.strip()
    ):
        raise KnowledgeResponseJSONError(
            "response_text must be a non-empty JSON string."
        )

    try:
        payload = json.loads(
            response_text
        )
    except json.JSONDecodeError as exc:
        raise KnowledgeResponseJSONError(
            "Model response is not valid JSON."
        ) from exc

    if not isinstance(
        payload,
        Mapping,
    ):
        raise KnowledgeResponseValidationError(
            "Knowledge response root must be an object."
        )

    return parse_knowledge_response_payload(
        payload=payload,
        spec=spec,
    )