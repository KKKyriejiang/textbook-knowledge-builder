import json
from pathlib import Path

from textbook_kb.knowledge_quality import (
    review_knowledge_json,
)
from textbook_kb.knowledge_schema import (
    KnowledgeBase,
    KnowledgeRecord,
    KnowledgeSectionMetadata,
    KnowledgeTextbookMetadata,
    KnowledgeProvenance,
    SectionKnowledge,
    save_knowledge_json,
)


def build_synthetic_knowledge_base() -> KnowledgeBase:
    return KnowledgeBase(
        records=[
            KnowledgeRecord(
                knowledge_id=(
                    "kb-math10-linear-equations-123456789abc"
                ),
                textbook_metadata=KnowledgeTextbookMetadata(
                    grade="10",
                    course_id="MATH10",
                    course_name=(
                        "Synthetic Mathematics"
                    ),
                    textbook=(
                        "Synthetic Algebra Textbook"
                    ),
                ),
                section_metadata=KnowledgeSectionMetadata(
                    unit="Unit 1",
                    chapter="Chapter 2",
                    section=(
                        "2.1 Solving Linear Equations"
                    ),
                    page_start=10,
                    page_end=11,
                ),
                provenance=KnowledgeProvenance(
                    source_file=(
                        "synthetic_textbook.pdf"
                    ),
                    page_numbers=[
                        10,
                        11,
                    ],
                    trace_ids=[
                        "tr-p10-1234567890",
                        "tr-p11-0987654321",
                    ],
                ),
                knowledge=SectionKnowledge(
                    summary=(
                        "Synthetic derived summary."
                    ),
                    key_concepts=[
                        "linear equation",
                    ],
                    definitions=[],
                    formulas=[],
                    skills=[
                        "solve simple equations",
                    ],
                    worked_example_patterns=[],
                    common_mistakes=[
                        "synthetic mistake",
                    ],
                    prerequisites=[
                        "inverse operations",
                    ],
                    student_friendly_explanations=[
                        "Synthetic explanation.",
                    ],
                    retrieval_keywords=[
                        "linear equations",
                    ],
                ),
            )
        ]
    )


def test_review_knowledge_json_reports_safe_counts(
    tmp_path: Path,
) -> None:
    output_path = (
        tmp_path
        / "synthetic_knowledge.json"
    )

    save_knowledge_json(
        build_synthetic_knowledge_base(),
        output_path,
    )

    report = review_knowledge_json(
        output_path
    )

    assert report.passed
    assert report.record_count == 1
    assert report.schema_version == "1.0"
    assert report.forbidden_key_findings == []
    assert report.forbidden_text_marker_findings == []

    summary = report.record_summaries[0]

    assert (
        summary.knowledge_id
        == "kb-math10-linear-equations-123456789abc"
    )

    assert summary.grade == "10"
    assert summary.course_id == "MATH10"
    assert summary.section == "2.1 Solving Linear Equations"
    assert summary.page_count == 2
    assert summary.key_concept_count == 1
    assert summary.skill_count == 1
    assert summary.common_mistake_count == 1
    assert summary.prerequisite_count == 1


def test_review_knowledge_json_finds_forbidden_keys(
    tmp_path: Path,
) -> None:
    output_path = (
        tmp_path
        / "synthetic_knowledge.json"
    )

    save_knowledge_json(
        build_synthetic_knowledge_base(),
        output_path,
    )

    payload = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    payload["records"][0]["source_text"] = (
        "Synthetic private source text."
    )

    output_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = review_knowledge_json(
        output_path
    )

    assert not report.passed
    assert (
        "$.records[0].source_text"
        in report.forbidden_key_findings
    )


def test_review_knowledge_json_finds_source_markers(
    tmp_path: Path,
) -> None:
    output_path = (
        tmp_path
        / "synthetic_knowledge.json"
    )

    save_knowledge_json(
        build_synthetic_knowledge_base(),
        output_path,
    )

    payload = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    payload["records"][0]["knowledge"]["retrieval_keywords"].append(
        "--- PAGE 10 ---"
    )

    output_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = review_knowledge_json(
        output_path
    )

    assert not report.passed
    assert (
        "--- PAGE "
        in report.forbidden_text_marker_findings
    )
