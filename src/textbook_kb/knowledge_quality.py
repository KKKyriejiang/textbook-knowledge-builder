from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from textbook_kb.knowledge_schema import (
    KnowledgeBase,
    load_knowledge_json,
)
from textbook_kb.knowledge_spec import (
    FORBIDDEN_PERSISTENT_FIELDS,
)


FORBIDDEN_TEXT_MARKERS = frozenset(
    {
        "--- PAGE ",
        "Textbook source begins",
        "Response JSON Schema",
        "<TEXTBOOK_SOURCE_",
    }
)


@dataclass(frozen=True)
class KnowledgeRecordQualitySummary:
    """
    Public-safe review summary for one KnowledgeRecord.

    Counts and identifiers are safe to print. Raw source text and full
    generated content are intentionally excluded.
    """

    knowledge_id: str
    course_id: str
    grade: str
    section: str
    page_start: int
    page_end: int
    page_count: int
    key_concept_count: int
    definition_count: int
    formula_count: int
    skill_count: int
    worked_example_pattern_count: int
    common_mistake_count: int
    prerequisite_count: int
    student_explanation_count: int
    retrieval_keyword_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgeQualityReport:
    """
    Public-safe quality report for a local knowledge JSON file.
    """

    input_path: Path
    schema_version: str
    record_count: int
    forbidden_key_findings: list[str]
    forbidden_text_marker_findings: list[str]
    record_summaries: list[KnowledgeRecordQualitySummary]

    @property
    def passed(self) -> bool:
        return (
            not self.forbidden_key_findings
            and not self.forbidden_text_marker_findings
        )

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "input_path": str(
                self.input_path
            ),
            "schema_version": (
                self.schema_version
            ),
            "record_count": (
                self.record_count
            ),
            "passed": self.passed,
            "forbidden_key_findings": list(
                self.forbidden_key_findings
            ),
            "forbidden_text_marker_findings": list(
                self.forbidden_text_marker_findings
            ),
            "record_summaries": [
                summary.to_dict()
                for summary
                in self.record_summaries
            ],
        }


def _iter_json_key_paths(
    value: Any,
    path: str = "$",
):
    if isinstance(
        value,
        dict,
    ):
        for key, child in value.items():
            child_path = (
                f"{path}.{key}"
            )

            yield (
                child_path,
                key,
            )

            yield from _iter_json_key_paths(
                child,
                child_path,
            )

    elif isinstance(
        value,
        list,
    ):
        for index, child in enumerate(
            value
        ):
            yield from _iter_json_key_paths(
                child,
                f"{path}[{index}]",
            )


def _find_forbidden_keys(
    payload: Any,
) -> list[str]:
    findings: list[str] = []

    for path, key in _iter_json_key_paths(
        payload
    ):
        if key in FORBIDDEN_PERSISTENT_FIELDS:
            findings.append(
                path
            )

    return findings


def _find_forbidden_text_markers(
    payload: Any,
) -> list[str]:
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
    )

    return [
        marker
        for marker
        in sorted(
            FORBIDDEN_TEXT_MARKERS
        )
        if marker in serialized
    ]


def _build_record_summary(
    knowledge_base: KnowledgeBase,
) -> list[KnowledgeRecordQualitySummary]:
    summaries: list[
        KnowledgeRecordQualitySummary
    ] = []

    for record in knowledge_base.records:
        knowledge = record.knowledge

        summaries.append(
            KnowledgeRecordQualitySummary(
                knowledge_id=record.knowledge_id,
                course_id=(
                    record
                    .textbook_metadata
                    .course_id
                ),
                grade=(
                    record
                    .textbook_metadata
                    .grade
                ),
                section=(
                    record
                    .section_metadata
                    .section
                ),
                page_start=(
                    record
                    .section_metadata
                    .page_start
                ),
                page_end=(
                    record
                    .section_metadata
                    .page_end
                ),
                page_count=len(
                    record
                    .provenance
                    .page_numbers
                ),
                key_concept_count=len(
                    knowledge.key_concepts
                ),
                definition_count=len(
                    knowledge.definitions
                ),
                formula_count=len(
                    knowledge.formulas
                ),
                skill_count=len(
                    knowledge.skills
                ),
                worked_example_pattern_count=len(
                    knowledge
                    .worked_example_patterns
                ),
                common_mistake_count=len(
                    knowledge.common_mistakes
                ),
                prerequisite_count=len(
                    knowledge.prerequisites
                ),
                student_explanation_count=len(
                    knowledge
                    .student_friendly_explanations
                ),
                retrieval_keyword_count=len(
                    knowledge.retrieval_keywords
                ),
            )
        )

    return summaries


def review_knowledge_json(
    input_path: str | Path,
) -> KnowledgeQualityReport:
    """
    Validate and summarize a local knowledge JSON file.

    This review is intentionally public-safe: it reports schema status,
    counts, identifiers, and forbidden raw-text carrier fields without
    printing source text or full generated knowledge content.
    """

    path = Path(
        input_path
    )

    knowledge_base = load_knowledge_json(
        path
    )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        payload = json.load(
            file
        )

    return KnowledgeQualityReport(
        input_path=path,
        schema_version=(
            knowledge_base
            .schema_version
        ),
        record_count=len(
            knowledge_base.records
        ),
        forbidden_key_findings=(
            _find_forbidden_keys(
                payload
            )
        ),
        forbidden_text_marker_findings=(
            _find_forbidden_text_markers(
                payload
            )
        ),
        record_summaries=(
            _build_record_summary(
                knowledge_base
            )
        ),
    )
