import json
from pathlib import Path

import pytest

from textbook_kb.controlled_extraction import (
    ControlledExtractionResult,
    extract_single_section_local,
    list_controlled_sections,
    load_local_section_sources_json,
    select_controlled_section,
)
from textbook_kb.knowledge_model import (
    FakeStructuredKnowledgeModelClient,
)
from textbook_kb.llm_config import (
    OpenAIKnowledgeConfig,
)


def build_section_sources_payload() -> list[dict]:
    return [
        {
            "textbook_metadata": {
                "grade": "10",
                "course_id": "MATH10",
                "course_name": (
                    "Synthetic Mathematics"
                ),
                "textbook": (
                    "Synthetic Algebra Textbook"
                ),
                "source_file": (
                    "synthetic_textbook.pdf"
                ),
            },
            "section_metadata": {
                "unit": "Unit 1",
                "chapter": "Chapter 1",
                "section": (
                    "1.1 Synthetic Variables"
                ),
                "page_start": 1,
                "page_end": 2,
            },
            "pages": [
                {
                    "page_number": 1,
                    "text": (
                        "Synthetic private "
                        "page one."
                    ),
                    "source_file": (
                        "synthetic_textbook.pdf"
                    ),
                },
                {
                    "page_number": 2,
                    "text": (
                        "Synthetic private "
                        "page two."
                    ),
                    "source_file": (
                        "synthetic_textbook.pdf"
                    ),
                },
            ],
        },
        {
            "textbook_metadata": {
                "grade": "10",
                "course_id": "MATH10",
                "course_name": (
                    "Synthetic Mathematics"
                ),
                "textbook": (
                    "Synthetic Algebra Textbook"
                ),
                "source_file": (
                    "synthetic_textbook.pdf"
                ),
            },
            "section_metadata": {
                "unit": "Unit 1",
                "chapter": "Chapter 1",
                "section": (
                    "1.2 Synthetic Equations"
                ),
                "page_start": 3,
                "page_end": 3,
            },
            "pages": [
                {
                    "page_number": 3,
                    "text": (
                        "Synthetic private "
                        "page three."
                    ),
                    "source_file": (
                        "synthetic_textbook.pdf"
                    ),
                },
            ],
        },
    ]


def build_fake_response() -> dict:
    return {
        "summary": (
            "Synthetic derived section summary."
        ),
        "key_concepts": [
            "synthetic concept",
        ],
        "definitions": [],
        "formulas": [],
        "skills": [
            "synthetic skill",
        ],
        "worked_example_patterns": [],
        "common_mistakes": [],
        "prerequisites": [],
        "student_friendly_explanations": [
            (
                "Synthetic student explanation."
            ),
        ],
        "retrieval_keywords": [
            "synthetic keyword",
        ],
    }


def build_config() -> OpenAIKnowledgeConfig:
    return OpenAIKnowledgeConfig(
        model="synthetic-test-model",
        max_output_tokens=1000,
        timeout_seconds=10.0,
        max_retries=0,
    )


def write_section_sources(
    tmp_path: Path,
) -> Path:
    path = (
        tmp_path
        / "section_sources.json"
    )

    path.write_text(
        json.dumps(
            build_section_sources_payload(),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return path


def test_load_local_section_sources_json(
    tmp_path: Path,
) -> None:
    path = write_section_sources(
        tmp_path
    )

    section_sources = (
        load_local_section_sources_json(
            path
        )
    )

    assert len(
        section_sources
    ) == 2

    assert (
        section_sources[0]
        .section_metadata
        .section
        == "1.1 Synthetic Variables"
    )

    assert [
        page.page_number
        for page in (
            section_sources[0].pages
        )
    ] == [
        1,
        2,
    ]


def test_loader_accepts_wrapped_root(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "wrapped_section_sources.json"
    )

    path.write_text(
        json.dumps(
            {
                "section_sources": (
                    build_section_sources_payload()
                )
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    loaded = (
        load_local_section_sources_json(
            path
        )
    )

    assert len(
        loaded
    ) == 2


def test_list_sections_contains_no_source_text(
    tmp_path: Path,
) -> None:
    section_sources = (
        load_local_section_sources_json(
            write_section_sources(
                tmp_path
            )
        )
    )

    infos = list_controlled_sections(
        section_sources
    )

    serialized = str(
        infos
    )

    assert (
        "Synthetic private page one."
        not in serialized
    )

    assert (
        infos[0].page_count
        == 2
    )


def test_select_controlled_section(
    tmp_path: Path,
) -> None:
    section_sources = (
        load_local_section_sources_json(
            write_section_sources(
                tmp_path
            )
        )
    )

    selected = (
        select_controlled_section(
            section_sources,
            section_index=1,
        )
    )

    assert (
        selected
        .section_metadata
        .section
        == "1.2 Synthetic Equations"
    )


def test_rejects_section_index_outside_range(
    tmp_path: Path,
) -> None:
    section_sources = (
        load_local_section_sources_json(
            write_section_sources(
                tmp_path
            )
        )
    )

    with pytest.raises(
        IndexError,
    ):
        select_controlled_section(
            section_sources,
            section_index=99,
        )


def test_extract_single_section_local(
    tmp_path: Path,
) -> None:
    section_sources = (
        load_local_section_sources_json(
            write_section_sources(
                tmp_path
            )
        )
    )

    fake_client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_fake_response()
            )
        )
    )

    result = (
        extract_single_section_local(
            section_source=(
                section_sources[0]
            ),
            model_client=fake_client,
            config=build_config(),
            output_path=(
                "data/processed/"
                "controlled_knowledge.json"
            ),
            project_root=tmp_path,
        )
    )

    assert isinstance(
        result,
        ControlledExtractionResult,
    )

    assert (
        result.output_path.exists()
    )

    assert (
        result.section
        == "1.1 Synthetic Variables"
    )

    assert (
        result.page_numbers
        == [1, 2]
    )

    assert len(
        fake_client.received_bundles
    ) == 1


def test_controlled_output_has_exactly_one_record(
    tmp_path: Path,
) -> None:
    section_sources = (
        load_local_section_sources_json(
            write_section_sources(
                tmp_path
            )
        )
    )

    result = (
        extract_single_section_local(
            section_source=(
                section_sources[0]
            ),
            model_client=(
                FakeStructuredKnowledgeModelClient(
                    default_response=(
                        build_fake_response()
                    )
                )
            ),
            config=build_config(),
            output_path=(
                "data/processed/"
                "controlled_knowledge.json"
            ),
            project_root=tmp_path,
        )
    )

    data = json.loads(
        result.output_path.read_text(
            encoding="utf-8"
        )
    )

    assert len(
        data["records"]
    ) == 1


def test_controlled_output_contains_no_source_page_text(
    tmp_path: Path,
) -> None:
    section_sources = (
        load_local_section_sources_json(
            write_section_sources(
                tmp_path
            )
        )
    )

    selected = (
        section_sources[0]
    )

    source_fragments = [
        page.text
        for page in selected.pages
    ]

    result = (
        extract_single_section_local(
            section_source=selected,
            model_client=(
                FakeStructuredKnowledgeModelClient(
                    default_response=(
                        build_fake_response()
                    )
                )
            ),
            config=build_config(),
            output_path=(
                "data/processed/"
                "controlled_knowledge.json"
            ),
            project_root=tmp_path,
        )
    )

    serialized = (
        result.output_path.read_text(
            encoding="utf-8"
        )
    )

    for fragment in source_fragments:
        assert fragment not in serialized


def test_controlled_public_result_contains_no_source_text(
    tmp_path: Path,
) -> None:
    section_sources = (
        load_local_section_sources_json(
            write_section_sources(
                tmp_path
            )
        )
    )

    selected = (
        section_sources[0]
    )

    result = (
        extract_single_section_local(
            section_source=selected,
            model_client=(
                FakeStructuredKnowledgeModelClient(
                    default_response=(
                        build_fake_response()
                    )
                )
            ),
            config=build_config(),
            output_path=(
                "data/processed/"
                "controlled_knowledge.json"
            ),
            project_root=tmp_path,
        )
    )

    serialized = str(
        result.to_public_dict()
    )

    for page in selected.pages:
        assert (
            page.text
            not in serialized
        )