from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from textbook_kb.knowledge_schema import SectionKnowledge


KNOWLEDGE_EXTRACTION_SPEC_VERSION = "1.2"

FORMULA_VARIABLE_MAX_ITEMS = 30


FORBIDDEN_PERSISTENT_FIELDS = frozenset(
    {
        "source_text",
        "raw_text",
        "page_text",
        "full_text",
        "pages",
        "raw_response",
        "prompt",
        "completion",
    }
)


@dataclass(frozen=True)
class KnowledgeFieldRule:
    """
    Extraction rule for one SectionKnowledge field.

    These rules describe semantic extraction behavior. They contain no
    textbook content and are safe to keep in the public repository.
    """

    field_name: str
    purpose: str
    extraction_rule: str
    empty_behavior: str
    max_items: int | None = None

    def __post_init__(self) -> None:
        for field_name, value in (
            ("field_name", self.field_name),
            ("purpose", self.purpose),
            ("extraction_rule", self.extraction_rule),
            ("empty_behavior", self.empty_behavior),
        ):
            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise ValueError(
                    f"{field_name} must be a non-empty string."
                )

        if self.max_items is not None:
            if (
                not isinstance(self.max_items, int)
                or isinstance(self.max_items, bool)
                or self.max_items < 1
            ):
                raise ValueError(
                    "max_items must be a positive integer "
                    "or None."
                )


@dataclass(frozen=True)
class KnowledgeExtractionSpec:
    """
    Provider-independent extraction specification.

    A future OpenAI/local-model/rule-based extractor can use this same
    specification. The specification intentionally remains independent
    from any API provider.
    """

    version: str
    global_rules: tuple[str, ...]
    field_rules: tuple[KnowledgeFieldRule, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.version, str)
            or not self.version.strip()
        ):
            raise ValueError(
                "version must be a non-empty string."
            )

        if not self.global_rules:
            raise ValueError(
                "global_rules must contain at least one rule."
            )

        for index, rule in enumerate(
            self.global_rules
        ):
            if (
                not isinstance(rule, str)
                or not rule.strip()
            ):
                raise ValueError(
                    "global_rules must contain only "
                    f"non-empty strings. Invalid index: {index}."
                )

        if not self.field_rules:
            raise ValueError(
                "field_rules must contain at least one rule."
            )

        if not all(
            isinstance(
                rule,
                KnowledgeFieldRule,
            )
            for rule in self.field_rules
        ):
            raise TypeError(
                "field_rules must contain "
                "KnowledgeFieldRule objects."
            )

        field_names = [
            rule.field_name
            for rule in self.field_rules
        ]

        if len(field_names) != len(
            set(field_names)
        ):
            raise ValueError(
                "field_rules contains duplicate field names."
            )

        expected_fields = [
            field_info.name
            for field_info in fields(
                SectionKnowledge
            )
        ]

        if field_names != expected_fields:
            raise ValueError(
                "field_rules must exactly match "
                "SectionKnowledge fields in schema order. "
                f"Expected {expected_fields}, "
                f"got {field_names}."
            )


def build_default_knowledge_extraction_spec(
) -> KnowledgeExtractionSpec:
    """
    Build the canonical Milestone 4 extraction specification.
    """

    global_rules = (
        (
            "Use only information supported by the supplied "
            "section source text."
        ),
        (
            "Do not introduce external facts, formulas, examples, "
            "prerequisites, or claims that are absent from the source."
        ),
        (
            "When evidence for an optional knowledge category is "
            "missing or uncertain, return an empty list for that field."
        ),
        (
            "Keep the summary concise and limited to claims clearly "
            "supported by the source."
        ),
        (
            "Write derived explanations in original concise wording "
            "instead of reproducing long textbook passages."
        ),
        (
            "Generalize worked examples into reusable problem-solving "
            "patterns instead of copying complete textbook examples."
        ),
        (
            "Preserve mathematical expressions accurately when they "
            "are explicitly supported by the source."
        ),
        (
            "Before returning, check each mathematical claim for correct "
            "conditions and comparable quantities; do not compare unlike "
            "quantities such as a ratio and an initial value."
        ),
        (
            "Represent formula variables as explicit symbol-and-meaning "
            "pairs. Include only variables supported by the source."
        ),
        (
            "Prefer conservative, source-grounded wording over broad "
            "domain generalizations. If a claim is only a reasonable "
            "extension from outside knowledge, omit it."
        ),
        (
            "Do not guess common mistakes or prerequisites from general "
            "domain knowledge; include them only when the source provides "
            "reasonable evidence."
        ),
        (
            "Student-friendly explanations may simplify wording while "
            "preserving the meaning and factual boundaries of the source."
        ),
        (
            "Do not place raw source text, page objects, prompts, raw "
            "model responses, or other processing artifacts in the "
            "persistent knowledge output."
        ),
    )

    field_rules = (
        KnowledgeFieldRule(
            field_name="summary",
            purpose=(
                "A concise overview of the main knowledge taught "
                "in the section."
            ),
            extraction_rule=(
                "Summarize the major ideas and learning focus using "
                "only source-supported information."
            ),
            empty_behavior=(
                "A non-empty summary is required. When the section "
                "contains limited instructional content, provide a "
                "short conservative summary."
            ),
            max_items=None,
        ),
        KnowledgeFieldRule(
            field_name="key_concepts",
            purpose=(
                "Important concepts, principles, or named ideas that "
                "students should recognize."
            ),
            extraction_rule=(
                "Extract distinct concepts that are explicitly introduced "
                "or materially discussed in the section. Avoid adding "
                "topic-adjacent concepts that are not supported by the "
                "section source."
            ),
            empty_behavior=(
                "Return an empty list when no clear key concepts can "
                "be identified."
            ),
            max_items=15,
        ),
        KnowledgeFieldRule(
            field_name="definitions",
            purpose=(
                "Structured definitions of important terms."
            ),
            extraction_rule=(
                "Create concise term-definition pairs only for terms "
                "whose meaning is established by the source."
            ),
            empty_behavior=(
                "Return an empty list when the section does not define "
                "or clearly explain terminology."
            ),
            max_items=20,
        ),
        KnowledgeFieldRule(
            field_name="formulas",
            purpose=(
                "Important mathematical or scientific formulas and "
                "their variables."
            ),
            extraction_rule=(
                "Extract formulas supported by the source, preserve their "
                "mathematical meaning, and explain variables only when "
                "their roles are supported. State domain conditions, "
                "indexing conventions, and growth or decrease conditions "
                "accurately when the source provides them."
            ),
            empty_behavior=(
                "Return an empty list when the section contains no "
                "relevant formula."
            ),
            max_items=15,
        ),
        KnowledgeFieldRule(
            field_name="skills",
            purpose=(
                "Actions or abilities a student is expected to perform."
            ),
            extraction_rule=(
                "Extract concrete skills such as calculating, comparing, "
                "interpreting, explaining, solving, or applying a method "
                "when these skills are taught by the section."
            ),
            empty_behavior=(
                "Return an empty list when no clear student skill can "
                "be derived from the source."
            ),
            max_items=15,
        ),
        KnowledgeFieldRule(
            field_name="worked_example_patterns",
            purpose=(
                "Reusable solution strategies abstracted from worked "
                "examples."
            ),
            extraction_rule=(
                "Generalize the problem type, when the strategy applies, "
                "and the reusable solving steps. Remove example-specific "
                "numbers, names, and story details unless required to "
                "understand the method."
            ),
            empty_behavior=(
                "Return an empty list when no worked example or reusable "
                "solution pattern is supported by the source."
            ),
            max_items=10,
        ),
        KnowledgeFieldRule(
            field_name="common_mistakes",
            purpose=(
                "Errors or misconceptions that students should avoid."
            ),
            extraction_rule=(
                "Include a mistake only when it is stated, warned about, "
                "contrasted, or strongly evidenced by the section. Also "
                "use evidence from exercises or worked examples that show "
                "students must distinguish one idea from a nearby idea."
            ),
            empty_behavior=(
                "Return an empty list when the source does not provide "
                "evidence for common mistakes."
            ),
            max_items=12,
        ),
        KnowledgeFieldRule(
            field_name="prerequisites",
            purpose=(
                "Earlier knowledge required to understand the section."
            ),
            extraction_rule=(
                "Extract prerequisite knowledge only when the source "
                "explicitly refers to it or clearly relies on it within "
                "the presented material. Prefer short prerequisite skill "
                "phrases over broad course topics."
            ),
            empty_behavior=(
                "Return an empty list when prerequisites cannot be "
                "grounded in the source."
            ),
            max_items=12,
        ),
        KnowledgeFieldRule(
            field_name="student_friendly_explanations",
            purpose=(
                "Short explanations suitable for a tutoring system."
            ),
            extraction_rule=(
                "Explain difficult ideas in simpler language while "
                "preserving source-supported meaning and avoiding new "
                "claims. Check that simplified statements keep correct "
                "mathematical conditions."
            ),
            empty_behavior=(
                "Return an empty list when no additional simplified "
                "explanation is useful or well supported."
            ),
            max_items=12,
        ),
        KnowledgeFieldRule(
            field_name="retrieval_keywords",
            purpose=(
                "Terms that improve later RAG retrieval for this section."
            ),
            extraction_rule=(
                "Use important terminology, concept names, formula names, "
                "skill phrases, and conservative query-style terms derived "
                "from the section. Do not add broad synonyms unless the "
                "source supports the same idea."
            ),
            empty_behavior=(
                "Return an empty list when useful grounded retrieval "
                "keywords cannot be identified."
            ),
            max_items=30,
        ),
    )

    return KnowledgeExtractionSpec(
        version=KNOWLEDGE_EXTRACTION_SPEC_VERSION,
        global_rules=global_rules,
        field_rules=field_rules,
    )


DEFAULT_KNOWLEDGE_EXTRACTION_SPEC = (
    build_default_knowledge_extraction_spec()
)


def build_section_knowledge_json_schema(
    spec: KnowledgeExtractionSpec = (
        DEFAULT_KNOWLEDGE_EXTRACTION_SPEC
    ),
) -> dict[str, Any]:
    """
    Build the provider structured-output JSON Schema for SectionKnowledge.

    Provider-facing formula variables use an array of explicit
    symbol/meaning objects because strict Structured Outputs requires
    object keys to be explicitly defined.

    The response parser converts those pairs back into the domain model's
    dict[str, str] representation.
    """

    max_items = {
        rule.field_name: rule.max_items
        for rule in spec.field_rules
    }

    string_schema = {
        "type": "string",
    }

    def string_array(
        field_name: str,
    ) -> dict[str, Any]:
        schema: dict[str, Any] = {
            "type": "array",
            "items": dict(
                string_schema
            ),
        }

        limit = max_items[
            field_name
        ]

        if limit is not None:
            schema["maxItems"] = limit

        return schema

    definitions_schema: dict[str, Any] = {
        "type": "array",
        "items": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "term",
                "definition",
            ],
            "properties": {
                "term": dict(
                    string_schema
                ),
                "definition": dict(
                    string_schema
                ),
            },
        },
    }

    if max_items["definitions"] is not None:
        definitions_schema["maxItems"] = (
            max_items["definitions"]
        )

    formula_variable_schema: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "symbol",
            "meaning",
        ],
        "properties": {
            "symbol": dict(
                string_schema
            ),
            "meaning": dict(
                string_schema
            ),
        },
    }

    formulas_schema: dict[str, Any] = {
        "type": "array",
        "items": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "name",
                "expression",
                "variables",
                "notes",
            ],
            "properties": {
                "name": dict(
                    string_schema
                ),
                "expression": dict(
                    string_schema
                ),
                "variables": {
                    "type": "array",
                    "maxItems": (
                        FORMULA_VARIABLE_MAX_ITEMS
                    ),
                    "items": (
                        formula_variable_schema
                    ),
                },
                "notes": {
                    "anyOf": [
                        {
                            "type": "string",
                        },
                        {
                            "type": "null",
                        },
                    ],
                },
            },
        },
    }

    if max_items["formulas"] is not None:
        formulas_schema["maxItems"] = (
            max_items["formulas"]
        )

    worked_examples_schema: dict[str, Any] = {
        "type": "array",
        "items": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "name",
                "problem_type",
                "when_to_use",
                "steps",
            ],
            "properties": {
                "name": dict(
                    string_schema
                ),
                "problem_type": dict(
                    string_schema
                ),
                "when_to_use": dict(
                    string_schema
                ),
                "steps": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 15,
                    "items": dict(
                        string_schema
                    ),
                },
            },
        },
    }

    if (
        max_items[
            "worked_example_patterns"
        ]
        is not None
    ):
        worked_examples_schema[
            "maxItems"
        ] = max_items[
            "worked_example_patterns"
        ]

    properties: dict[str, Any] = {
        "summary": dict(
            string_schema
        ),
        "key_concepts": string_array(
            "key_concepts"
        ),
        "definitions": (
            definitions_schema
        ),
        "formulas": (
            formulas_schema
        ),
        "skills": string_array(
            "skills"
        ),
        "worked_example_patterns": (
            worked_examples_schema
        ),
        "common_mistakes": string_array(
            "common_mistakes"
        ),
        "prerequisites": string_array(
            "prerequisites"
        ),
        "student_friendly_explanations": (
            string_array(
                "student_friendly_explanations"
            )
        ),
        "retrieval_keywords": string_array(
            "retrieval_keywords"
        ),
    }

    required_fields = [
        rule.field_name
        for rule in spec.field_rules
    ]

    return {
        "type": "object",
        "additionalProperties": False,
        "required": required_fields,
        "properties": properties,
    }


def render_knowledge_extraction_instructions(
    spec: KnowledgeExtractionSpec = (
        DEFAULT_KNOWLEDGE_EXTRACTION_SPEC
    ),
) -> str:
    """
    Render public-safe provider-independent extraction instructions.

    The returned string contains extraction rules only. It contains no
    source text and can later be combined with transient source content
    by a concrete extractor.
    """

    lines = [
        (
            "Extract structured educational knowledge from one "
            "textbook section."
        ),
        "",
        "Global rules:",
    ]

    for index, rule in enumerate(
        spec.global_rules,
        start=1,
    ):
        lines.append(
            f"{index}. {rule}"
        )

    lines.extend(
        [
            "",
            "Field rules:",
        ]
    )

    for rule in spec.field_rules:
        lines.append(
            f"- {rule.field_name}"
        )
        lines.append(
            f"  Purpose: {rule.purpose}"
        )
        lines.append(
            f"  Extraction: {rule.extraction_rule}"
        )
        lines.append(
            f"  Missing evidence: {rule.empty_behavior}"
        )

        if rule.max_items is not None:
            lines.append(
                f"  Maximum items: {rule.max_items}"
            )

    lines.extend(
        [
            "",
            (
                "Return only data matching the defined "
                "SectionKnowledge JSON contract."
            ),
        ]
    )

    return "\n".join(
        lines
    )


def validate_persistent_knowledge_contract(
    schema: dict[str, Any] | None = None,
) -> None:
    """
    Verify that the public/persistent output contract does not contain
    fields reserved for transient or raw processing data.
    """

    if schema is None:
        schema = (
            build_section_knowledge_json_schema()
        )

    if not isinstance(
        schema,
        dict,
    ):
        raise TypeError(
            "schema must be a dictionary."
        )

    properties = schema.get(
        "properties"
    )

    if not isinstance(
        properties,
        dict,
    ):
        raise ValueError(
            "schema must contain a properties dictionary."
        )

    forbidden = (
        FORBIDDEN_PERSISTENT_FIELDS
        & set(
            properties.keys()
        )
    )

    if forbidden:
        raise ValueError(
            "Persistent knowledge schema contains "
            "forbidden transient fields: "
            f"{sorted(forbidden)}"
        )
