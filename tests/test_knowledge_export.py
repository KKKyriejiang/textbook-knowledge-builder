import json
from pathlib import Path

import pytest

from textbook_kb.knowledge_export import (
    KnowledgeExportResult,
    build_and_export_knowledge_base,
    export_knowledge_base_local,
    is_private_knowledge_output_path,
    validate_private_knowledge_output_path,
)
from textbook_kb.knowledge_extraction import (
    KnowledgeExtractionRequest,
    KnowledgeExtractionResult,
)
from textbook_kb.knowledge_pipeline import (
    build_knowledge_base,
)
from textbook_kb.knowledge_schema import (
    SectionKnowledge,
    load_knowledge_json,
)
from textbook_kb.metadata import (
    SectionMetadata,
    TextbookMetadata,
)
from textbook_kb.pdf_parser import ParsedPage
from textbook_kb.section_source import (
    SectionSource,
)


def build_synthetic_textbook_metadata() -> TextbookMetadata:
    return TextbookMetadata(
        grade="10",
        course_id="MATH10",
        course_name="Synthetic Mathematics",
        textbook="Synthetic Algebra Textbook",
        source_file="synthetic_textbook.pdf",
    )


def build_first_section_source() -> SectionSource:
    return SectionSource(
        textbook_metadata=(
            build_synthetic_textbook_metadata()
        ),
        section_metadata=SectionMetadata(
            unit="Unit 1",
            chapter="Chapter 2",
            section="2.1 Solving Linear Equations",
            page_start=10,
            page_end=11,
        ),
        pages=(
            ParsedPage(
                page_number=10,
                text=(
                    "Synthetic private source content "
                    "for page ten."
                ),
                source_file="synthetic_textbook.pdf",
            ),
            ParsedPage(
                page_number=11,
                text=(
                    "Synthetic private source content "
                    "for page eleven."
                ),
                source_file="synthetic_textbook.pdf",
            ),
        ),
    )


def build_second_section_source() -> SectionSource:
    return SectionSource(
        textbook_metadata=(
            build_synthetic_textbook_metadata()
        ),
        section_metadata=SectionMetadata(
            unit="Unit 1",
            chapter="Chapter 2",
            section="2.2 Graphing Linear Equations",
            page_start=12,
            page_end=13,
        ),
        pages=(
            ParsedPage(
                page_number=12,
                text=(
                    "Synthetic private source content "
                    "for page twelve."
                ),
                source_file="synthetic_textbook.pdf",
            ),
            ParsedPage(
                page_number=13,
                text=(
                    "Synthetic private source content "
                    "for page thirteen."
                ),
                source_file="synthetic_textbook.pdf",
            ),
        ),
    )


def build_synthetic_section_sources() -> list[
    SectionSource
]:
    return [
        build_first_section_source(),
        build_second_section_source(),
    ]


class SyntheticExportExtractor:
    """
    Deterministic synthetic extractor.

    It performs no API calls and uses only synthetic test data.
    """

    def extract(
        self,
        request: KnowledgeExtractionRequest,
    ) -> KnowledgeExtractionResult:
        warnings: list[str] = []

        if "Graphing" in request.section:
            warnings.append(
                "Synthetic export warning."
            )

        return KnowledgeExtractionResult(
            knowledge=SectionKnowledge(
                summary=(
                    "Synthetic derived summary for "
                    f"{request.section}."
                ),
                key_concepts=[
                    request.section,
                ],
                skills=[
                    "synthetic reasoning",
                ],
                retrieval_keywords=[
                    request.section,
                    request.course_id,
                ],
            ),
            extractor_name=(
                "synthetic-export-extractor"
            ),
            warnings=warnings,
        )


def test_private_knowledge_path_is_accepted(
    tmp_path: Path,
) -> None:
    output_path = (
        tmp_path
        / "data"
        / "processed"
        / "synthetic_knowledge.json"
    )

    assert is_private_knowledge_output_path(
        output_path=output_path,
        project_root=tmp_path,
    )


def test_kb_filename_is_accepted(
    tmp_path: Path,
) -> None:
    output_path = (
        tmp_path
        / "data"
        / "processed"
        / "synthetic_kb.json"
    )

    assert is_private_knowledge_output_path(
        output_path=output_path,
        project_root=tmp_path,
    )


def test_unprotected_processed_filename_is_rejected(
    tmp_path: Path,
) -> None:
    output_path = (
        tmp_path
        / "data"
        / "processed"
        / "output.json"
    )

    assert not is_private_knowledge_output_path(
        output_path=output_path,
        project_root=tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="private knowledge naming convention",
    ):
        validate_private_knowledge_output_path(
            output_path=output_path,
            project_root=tmp_path,
        )


def test_output_outside_processed_directory_is_rejected(
    tmp_path: Path,
) -> None:
    output_path = (
        tmp_path
        / "knowledge.json"
    )

    assert not is_private_knowledge_output_path(
        output_path=output_path,
        project_root=tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="private knowledge naming convention",
    ):
        validate_private_knowledge_output_path(
            output_path=output_path,
            project_root=tmp_path,
        )


def test_output_outside_project_is_rejected(
    tmp_path: Path,
) -> None:
    project_root = (
        tmp_path
        / "project"
    )

    project_root.mkdir()

    outside_path = (
        tmp_path
        / "data"
        / "processed"
        / "outside_knowledge.json"
    )

    with pytest.raises(
        ValueError,
        match="inside the project directory",
    ):
        validate_private_knowledge_output_path(
            output_path=outside_path,
            project_root=project_root,
        )


def test_non_json_output_is_rejected(
    tmp_path: Path,
) -> None:
    output_path = (
        tmp_path
        / "data"
        / "processed"
        / "synthetic_knowledge.txt"
    )

    with pytest.raises(
        ValueError,
        match=".json extension",
    ):
        validate_private_knowledge_output_path(
            output_path=output_path,
            project_root=tmp_path,
        )


def test_relative_private_path_is_resolved_from_project_root(
    tmp_path: Path,
) -> None:
    resolved_path = (
        validate_private_knowledge_output_path(
            output_path=(
                "data/processed/"
                "synthetic_knowledge.json"
            ),
            project_root=tmp_path,
        )
    )

    assert resolved_path == (
        tmp_path
        / "data"
        / "processed"
        / "synthetic_knowledge.json"
    ).resolve()


def test_export_existing_knowledge_base_local(
    tmp_path: Path,
) -> None:
    extractor = SyntheticExportExtractor()

    knowledge_base = build_knowledge_base(
        section_sources=(
            build_synthetic_section_sources()
        ),
        extractor=extractor,
    )

    output_path = (
        "data/processed/"
        "synthetic_knowledge.json"
    )

    saved_path = export_knowledge_base_local(
        knowledge_base=knowledge_base,
        output_path=output_path,
        project_root=tmp_path,
    )

    assert saved_path.exists()

    assert saved_path == (
        tmp_path
        / output_path
    ).resolve()

    loaded = load_knowledge_json(
        saved_path
    )

    assert loaded == knowledge_base


def test_build_and_export_complete_pipeline(
    tmp_path: Path,
) -> None:
    extractor = SyntheticExportExtractor()

    result = build_and_export_knowledge_base(
        section_sources=(
            build_synthetic_section_sources()
        ),
        extractor=extractor,
        output_path=(
            "data/processed/"
            "synthetic_knowledge.json"
        ),
        project_root=tmp_path,
    )

    assert isinstance(
        result,
        KnowledgeExportResult,
    )

    assert result.output_path.exists()

    assert len(
        result.knowledge_base.records
    ) == 2

    assert len(
        result.warnings
    ) == 1

    assert (
        result.warnings[0].message
        == "Synthetic export warning."
    )


def test_exported_json_can_be_loaded(
    tmp_path: Path,
) -> None:
    extractor = SyntheticExportExtractor()

    result = build_and_export_knowledge_base(
        section_sources=(
            build_synthetic_section_sources()
        ),
        extractor=extractor,
        output_path=(
            "data/processed/"
            "synthetic_knowledge.json"
        ),
        project_root=tmp_path,
    )

    loaded = load_knowledge_json(
        result.output_path
    )

    assert (
        loaded
        == result.knowledge_base
    )

    assert len(
        loaded.records
    ) == 2


def test_exported_json_does_not_contain_source_text(
    tmp_path: Path,
) -> None:
    section_sources = (
        build_synthetic_section_sources()
    )

    source_fragments = [
        page.text
        for section_source in section_sources
        for page in section_source.pages
    ]

    result = build_and_export_knowledge_base(
        section_sources=section_sources,
        extractor=SyntheticExportExtractor(),
        output_path=(
            "data/processed/"
            "synthetic_knowledge.json"
        ),
        project_root=tmp_path,
    )

    with result.output_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        serialized = file.read()

    assert "source_text" not in serialized

    for fragment in source_fragments:
        assert fragment not in serialized


def test_exported_json_contains_derived_knowledge(
    tmp_path: Path,
) -> None:
    result = build_and_export_knowledge_base(
        section_sources=(
            build_synthetic_section_sources()
        ),
        extractor=SyntheticExportExtractor(),
        output_path=(
            "data/processed/"
            "synthetic_knowledge.json"
        ),
        project_root=tmp_path,
    )

    with result.output_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    records = data["records"]

    assert len(records) == 2

    assert (
        records[0]["knowledge"]["summary"]
        == (
            "Synthetic derived summary for "
            "2.1 Solving Linear Equations."
        )
    )


def test_pipeline_warnings_are_not_written_to_json(
    tmp_path: Path,
) -> None:
    result = build_and_export_knowledge_base(
        section_sources=(
            build_synthetic_section_sources()
        ),
        extractor=SyntheticExportExtractor(),
        output_path=(
            "data/processed/"
            "synthetic_knowledge.json"
        ),
        project_root=tmp_path,
    )

    serialized = (
        result.output_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        "Synthetic export warning."
        not in serialized
    )


def test_export_does_not_create_file_when_path_is_unsafe(
    tmp_path: Path,
) -> None:
    unsafe_path = (
        tmp_path
        / "public_knowledge.json"
    )

    with pytest.raises(
        ValueError,
    ):
        build_and_export_knowledge_base(
            section_sources=(
                build_synthetic_section_sources()
            ),
            extractor=(
                SyntheticExportExtractor()
            ),
            output_path=unsafe_path,
            project_root=tmp_path,
        )

    assert not unsafe_path.exists()