from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


KNOWLEDGE_SCHEMA_VERSION = "1.0"

# Real textbook-derived knowledge should normally be written here.
# The repository .gitignore already protects:
# data/processed/*knowledge*.json
DEFAULT_KNOWLEDGE_OUTPUT_PATH = Path(
    "data/processed/textbook_knowledge.json"
)


def _require_non_empty_string(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{field_name} must be a non-empty string."
        )


def _validate_optional_string(
    value: str | None,
    field_name: str,
) -> None:
    if value is None:
        return

    _require_non_empty_string(value, field_name)


def _validate_string_list(
    values: list[str],
    field_name: str,
) -> None:
    if not isinstance(values, list):
        raise ValueError(
            f"{field_name} must be a list of strings."
        )

    for index, value in enumerate(values):
        _require_non_empty_string(
            value,
            f"{field_name}[{index}]",
        )


@dataclass(frozen=True)
class KnowledgeTextbookMetadata:
    """
    Stable textbook-level metadata stored in the final knowledge JSON.

    This intentionally contains only metadata required by the downstream
    RAG system and does not contain raw textbook content.
    """

    grade: str
    course_id: str
    course_name: str
    textbook: str

    def __post_init__(self) -> None:
        _require_non_empty_string(self.grade, "grade")
        _require_non_empty_string(self.course_id, "course_id")
        _require_non_empty_string(self.course_name, "course_name")
        _require_non_empty_string(self.textbook, "textbook")

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> KnowledgeTextbookMetadata:
        return cls(
            grade=data["grade"],
            course_id=data["course_id"],
            course_name=data["course_name"],
            textbook=data["textbook"],
        )


@dataclass(frozen=True)
class KnowledgeSectionMetadata:
    """
    Stable section-level metadata used by the downstream RAG system.
    """

    unit: str | None
    chapter: str | None
    section: str
    page_start: int
    page_end: int

    def __post_init__(self) -> None:
        _validate_optional_string(self.unit, "unit")
        _validate_optional_string(self.chapter, "chapter")
        _require_non_empty_string(self.section, "section")

        if self.page_start < 1:
            raise ValueError(
                "page_start must be greater than or equal to 1."
            )

        if self.page_end < self.page_start:
            raise ValueError(
                "page_end must be greater than or equal to page_start."
            )

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> KnowledgeSectionMetadata:
        return cls(
            unit=data.get("unit"),
            chapter=data.get("chapter"),
            section=data["section"],
            page_start=data["page_start"],
            page_end=data["page_end"],
        )


@dataclass(frozen=True)
class KnowledgeProvenance:
    """
    Lightweight provenance information.

    It stores where the derived knowledge came from without embedding
    raw textbook page text into the knowledge record.
    """

    source_file: str
    page_numbers: list[int]
    trace_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_non_empty_string(
            self.source_file,
            "source_file",
        )

        if not self.page_numbers:
            raise ValueError(
                "page_numbers must contain at least one page number."
            )

        if any(
            not isinstance(page_number, int)
            or isinstance(page_number, bool)
            or page_number < 1
            for page_number in self.page_numbers
        ):
            raise ValueError(
                "page_numbers must contain positive integers."
            )

        if self.page_numbers != sorted(set(self.page_numbers)):
            raise ValueError(
                "page_numbers must be unique and sorted "
                "in ascending order."
            )

        _validate_string_list(
            self.trace_ids,
            "trace_ids",
        )

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> KnowledgeProvenance:
        return cls(
            source_file=data["source_file"],
            page_numbers=list(data["page_numbers"]),
            trace_ids=list(data.get("trace_ids", [])),
        )


@dataclass(frozen=True)
class KnowledgeDefinition:
    """
    A structured definition extracted from a section.

    definition should contain derived explanatory content rather than
    a large verbatim textbook passage.
    """

    term: str
    definition: str

    def __post_init__(self) -> None:
        _require_non_empty_string(self.term, "term")
        _require_non_empty_string(
            self.definition,
            "definition",
        )

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> KnowledgeDefinition:
        return cls(
            term=data["term"],
            definition=data["definition"],
        )


@dataclass(frozen=True)
class KnowledgeFormula:
    """
    A mathematical/scientific formula and its structured explanation.
    """

    name: str
    expression: str
    variables: dict[str, str] = field(default_factory=dict)
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.name, "formula.name")
        _require_non_empty_string(
            self.expression,
            "formula.expression",
        )
        _validate_optional_string(
            self.notes,
            "formula.notes",
        )

        if not isinstance(self.variables, dict):
            raise ValueError(
                "formula.variables must be a dictionary."
            )

        for variable, explanation in self.variables.items():
            _require_non_empty_string(
                variable,
                "formula.variables key",
            )
            _require_non_empty_string(
                explanation,
                f"formula.variables[{variable!r}]",
            )

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> KnowledgeFormula:
        return cls(
            name=data["name"],
            expression=data["expression"],
            variables=dict(data.get("variables", {})),
            notes=data.get("notes"),
        )


@dataclass(frozen=True)
class WorkedExamplePattern:
    """
    Generalized problem-solving pattern derived from worked examples.

    This stores the reusable reasoning pattern instead of copying an
    entire textbook example.
    """

    name: str
    problem_type: str
    when_to_use: str
    steps: list[str]

    def __post_init__(self) -> None:
        _require_non_empty_string(
            self.name,
            "worked_example_pattern.name",
        )
        _require_non_empty_string(
            self.problem_type,
            "worked_example_pattern.problem_type",
        )
        _require_non_empty_string(
            self.when_to_use,
            "worked_example_pattern.when_to_use",
        )

        if not self.steps:
            raise ValueError(
                "worked_example_pattern.steps must contain "
                "at least one step."
            )

        _validate_string_list(
            self.steps,
            "worked_example_pattern.steps",
        )

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> WorkedExamplePattern:
        return cls(
            name=data["name"],
            problem_type=data["problem_type"],
            when_to_use=data["when_to_use"],
            steps=list(data["steps"]),
        )


@dataclass(frozen=True)
class SectionKnowledge:
    """
    Derived knowledge extracted from one textbook section.

    Empty lists are valid because some sections may contain no formulas,
    definitions, worked examples, or explicit prerequisites. This avoids
    forcing later extraction stages to invent missing information.
    """

    summary: str
    key_concepts: list[str] = field(default_factory=list)
    definitions: list[KnowledgeDefinition] = field(
        default_factory=list
    )
    formulas: list[KnowledgeFormula] = field(
        default_factory=list
    )
    skills: list[str] = field(default_factory=list)
    worked_example_patterns: list[WorkedExamplePattern] = field(
        default_factory=list
    )
    common_mistakes: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    student_friendly_explanations: list[str] = field(
        default_factory=list
    )
    retrieval_keywords: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_non_empty_string(
            self.summary,
            "knowledge.summary",
        )

        _validate_string_list(
            self.key_concepts,
            "knowledge.key_concepts",
        )
        _validate_string_list(
            self.skills,
            "knowledge.skills",
        )
        _validate_string_list(
            self.common_mistakes,
            "knowledge.common_mistakes",
        )
        _validate_string_list(
            self.prerequisites,
            "knowledge.prerequisites",
        )
        _validate_string_list(
            self.student_friendly_explanations,
            "knowledge.student_friendly_explanations",
        )
        _validate_string_list(
            self.retrieval_keywords,
            "knowledge.retrieval_keywords",
        )

        if not all(
            isinstance(item, KnowledgeDefinition)
            for item in self.definitions
        ):
            raise ValueError(
                "knowledge.definitions must contain "
                "KnowledgeDefinition objects."
            )

        if not all(
            isinstance(item, KnowledgeFormula)
            for item in self.formulas
        ):
            raise ValueError(
                "knowledge.formulas must contain "
                "KnowledgeFormula objects."
            )

        if not all(
            isinstance(item, WorkedExamplePattern)
            for item in self.worked_example_patterns
        ):
            raise ValueError(
                "knowledge.worked_example_patterns must contain "
                "WorkedExamplePattern objects."
            )

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> SectionKnowledge:
        return cls(
            summary=data["summary"],
            key_concepts=list(
                data.get("key_concepts", [])
            ),
            definitions=[
                KnowledgeDefinition.from_dict(item)
                for item in data.get("definitions", [])
            ],
            formulas=[
                KnowledgeFormula.from_dict(item)
                for item in data.get("formulas", [])
            ],
            skills=list(
                data.get("skills", [])
            ),
            worked_example_patterns=[
                WorkedExamplePattern.from_dict(item)
                for item in data.get(
                    "worked_example_patterns",
                    [],
                )
            ],
            common_mistakes=list(
                data.get("common_mistakes", [])
            ),
            prerequisites=list(
                data.get("prerequisites", [])
            ),
            student_friendly_explanations=list(
                data.get(
                    "student_friendly_explanations",
                    [],
                )
            ),
            retrieval_keywords=list(
                data.get("retrieval_keywords", [])
            ),
        )


@dataclass(frozen=True)
class KnowledgeRecord:
    """
    One RAG-ready structured knowledge record for one textbook section.
    """

    knowledge_id: str
    textbook_metadata: KnowledgeTextbookMetadata
    section_metadata: KnowledgeSectionMetadata
    provenance: KnowledgeProvenance
    knowledge: SectionKnowledge

    def __post_init__(self) -> None:
        _require_non_empty_string(
            self.knowledge_id,
            "knowledge_id",
        )

        if not isinstance(
            self.textbook_metadata,
            KnowledgeTextbookMetadata,
        ):
            raise ValueError(
                "textbook_metadata must be a "
                "KnowledgeTextbookMetadata object."
            )

        if not isinstance(
            self.section_metadata,
            KnowledgeSectionMetadata,
        ):
            raise ValueError(
                "section_metadata must be a "
                "KnowledgeSectionMetadata object."
            )

        if not isinstance(
            self.provenance,
            KnowledgeProvenance,
        ):
            raise ValueError(
                "provenance must be a KnowledgeProvenance object."
            )

        if not isinstance(
            self.knowledge,
            SectionKnowledge,
        ):
            raise ValueError(
                "knowledge must be a SectionKnowledge object."
            )

        page_start = self.section_metadata.page_start
        page_end = self.section_metadata.page_end

        outside_section = [
            page_number
            for page_number in self.provenance.page_numbers
            if not page_start <= page_number <= page_end
        ]

        if outside_section:
            raise ValueError(
                "provenance.page_numbers contains pages outside "
                f"the section range {page_start}-{page_end}: "
                f"{outside_section}"
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> KnowledgeRecord:
        return cls(
            knowledge_id=data["knowledge_id"],
            textbook_metadata=KnowledgeTextbookMetadata.from_dict(
                data["textbook_metadata"]
            ),
            section_metadata=KnowledgeSectionMetadata.from_dict(
                data["section_metadata"]
            ),
            provenance=KnowledgeProvenance.from_dict(
                data["provenance"]
            ),
            knowledge=SectionKnowledge.from_dict(
                data["knowledge"]
            ),
        )


@dataclass(frozen=True)
class KnowledgeBase:
    """
    Top-level JSON structure consumed by downstream RAG systems.
    """

    records: list[KnowledgeRecord]
    schema_version: str = KNOWLEDGE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_non_empty_string(
            self.schema_version,
            "schema_version",
        )

        if self.schema_version != KNOWLEDGE_SCHEMA_VERSION:
            raise ValueError(
                "Unsupported knowledge schema version: "
                f"{self.schema_version!r}. "
                f"Expected {KNOWLEDGE_SCHEMA_VERSION!r}."
            )

        if not self.records:
            raise ValueError(
                "KnowledgeBase.records must contain "
                "at least one KnowledgeRecord."
            )

        if not all(
            isinstance(record, KnowledgeRecord)
            for record in self.records
        ):
            raise ValueError(
                "KnowledgeBase.records must contain "
                "KnowledgeRecord objects."
            )

        knowledge_ids = [
            record.knowledge_id
            for record in self.records
        ]

        if len(knowledge_ids) != len(set(knowledge_ids)):
            raise ValueError(
                "KnowledgeBase contains duplicate knowledge_id values."
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> KnowledgeBase:
        return cls(
            schema_version=data["schema_version"],
            records=[
                KnowledgeRecord.from_dict(record)
                for record in data["records"]
            ],
        )


def save_knowledge_json(
    knowledge_base: KnowledgeBase,
    output_path: str | Path = DEFAULT_KNOWLEDGE_OUTPUT_PATH,
) -> Path:
    """
    Save the structured knowledge base as UTF-8 JSON.

    Real textbook-derived outputs should remain local-only. The default
    filename is intentionally placed under data/processed/ and contains
    "knowledge" so that the project's existing .gitignore rules protect it.
    """

    if not isinstance(knowledge_base, KnowledgeBase):
        raise TypeError(
            "knowledge_base must be a KnowledgeBase object."
        )

    path = Path(output_path)

    if path.suffix.lower() != ".json":
        raise ValueError(
            "Knowledge output path must use the .json extension."
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            knowledge_base.to_dict(),
            file,
            ensure_ascii=False,
            indent=2,
        )

    return path


def load_knowledge_json(
    input_path: str | Path = DEFAULT_KNOWLEDGE_OUTPUT_PATH,
) -> KnowledgeBase:
    """
    Load and validate a previously saved knowledge JSON file.
    """

    path = Path(input_path)

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "Knowledge JSON root must be an object."
        )

    return KnowledgeBase.from_dict(data)