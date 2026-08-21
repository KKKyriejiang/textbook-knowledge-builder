from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from textbook_kb.knowledge_export import (
    build_and_export_knowledge_base,
)
from textbook_kb.knowledge_model import (
    ModelKnowledgeExtractor,
    StructuredKnowledgeModelClient,
)
from textbook_kb.llm_config import (
    OpenAIKnowledgeConfig,
)
from textbook_kb.metadata import (
    SectionMetadata,
    TextbookMetadata,
)
from textbook_kb.pdf_parser import (
    ParsedPage,
)
from textbook_kb.section_source import (
    SectionSource,
)


@dataclass(frozen=True)
class ControlledSectionInfo:
    """
    Public-safe metadata describing one local SectionSource.

    Raw page text is intentionally excluded.
    """

    index: int
    unit: str | None
    chapter: str | None
    section: str
    page_start: int
    page_end: int
    page_count: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.index, int)
            or isinstance(self.index, bool)
            or self.index < 0
        ):
            raise ValueError(
                "index must be a non-negative integer."
            )

        if (
            not isinstance(self.section, str)
            or not self.section.strip()
        ):
            raise ValueError(
                "section must be a non-empty string."
            )

        if (
            not isinstance(self.page_count, int)
            or isinstance(self.page_count, bool)
            or self.page_count < 1
        ):
            raise ValueError(
                "page_count must be a positive integer."
            )


@dataclass(frozen=True)
class ControlledExtractionResult:
    """
    Public-safe result of extracting exactly one section.

    The final structured knowledge itself is written to a protected local
    JSON path. This result contains only metadata and safe usage data.
    """

    output_path: Path
    knowledge_id: str
    section: str
    page_numbers: list[int]
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    response_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.output_path,
            Path,
        ):
            raise TypeError(
                "output_path must be a pathlib.Path object."
            )

        if (
            not isinstance(self.knowledge_id, str)
            or not self.knowledge_id.strip()
        ):
            raise ValueError(
                "knowledge_id must be a non-empty string."
            )

        if (
            not isinstance(self.section, str)
            or not self.section.strip()
        ):
            raise ValueError(
                "section must be a non-empty string."
            )

        if not self.page_numbers:
            raise ValueError(
                "page_numbers must contain at least one page."
            )

    def to_public_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "output_path": str(
                self.output_path
            ),
            "knowledge_id": (
                self.knowledge_id
            ),
            "section": self.section,
            "page_numbers": list(
                self.page_numbers
            ),
            "input_tokens": (
                self.input_tokens
            ),
            "output_tokens": (
                self.output_tokens
            ),
            "total_tokens": (
                self.total_tokens
            ),
            "response_id": (
                self.response_id
            ),
        }


def _require_mapping(
    value: Any,
    location: str,
) -> dict[str, Any]:
    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(
            f"{location} must be a JSON object."
        )

    return value


def _build_textbook_metadata(
    data: dict[str, Any],
) -> TextbookMetadata:
    return TextbookMetadata(
        grade=data["grade"],
        course_id=data["course_id"],
        course_name=data["course_name"],
        textbook=data["textbook"],
        source_file=data["source_file"],
    )


def _build_section_metadata(
    data: dict[str, Any],
) -> SectionMetadata:
    return SectionMetadata(
        unit=data.get("unit"),
        chapter=data.get("chapter"),
        section=data["section"],
        page_start=data["page_start"],
        page_end=data["page_end"],
    )


def _build_parsed_page(
    data: dict[str, Any],
) -> ParsedPage:
    return ParsedPage(
        page_number=data["page_number"],
        text=data["text"],
        source_file=data["source_file"],
    )


def _build_section_source(
    data: dict[str, Any],
    index: int,
) -> SectionSource:
    textbook_data = _require_mapping(
        data.get(
            "textbook_metadata"
        ),
        (
            f"section_sources[{index}]"
            ".textbook_metadata"
        ),
    )

    section_data = _require_mapping(
        data.get(
            "section_metadata"
        ),
        (
            f"section_sources[{index}]"
            ".section_metadata"
        ),
    )

    pages_data = data.get(
        "pages"
    )

    if not isinstance(
        pages_data,
        list,
    ):
        raise ValueError(
            f"section_sources[{index}].pages "
            "must be a JSON array."
        )

    if not pages_data:
        raise ValueError(
            f"section_sources[{index}].pages "
            "must contain at least one page."
        )

    pages = tuple(
        _build_parsed_page(
            _require_mapping(
                page_data,
                (
                    f"section_sources[{index}]"
                    f".pages[{page_index}]"
                ),
            )
        )
        for page_index, page_data
        in enumerate(
            pages_data
        )
    )

    return SectionSource(
        textbook_metadata=(
            _build_textbook_metadata(
                textbook_data
            )
        ),
        section_metadata=(
            _build_section_metadata(
                section_data
            )
        ),
        pages=pages,
    )


def load_local_section_sources_json(
    input_path: str | Path,
) -> list[SectionSource]:
    """
    Load the local-only SectionSource JSON created during Milestone 3.

    Supported roots:
      - a JSON array of SectionSource objects,
      - {"section_sources": [...]}.

    The file may contain copyrighted textbook text and must remain local.
    """

    path = Path(
        input_path
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Section source JSON does not exist: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Section source path must be a file: {path}"
        )

    if path.suffix.lower() != ".json":
        raise ValueError(
            "Section source file must use the .json extension."
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        payload = json.load(
            file
        )

    if isinstance(
        payload,
        list,
    ):
        records = payload

    elif isinstance(
        payload,
        dict,
    ):
        records = payload.get(
            "section_sources"
        )

        if not isinstance(
            records,
            list,
        ):
            raise ValueError(
                "Section source JSON object must contain "
                "a 'section_sources' array."
            )

    else:
        raise ValueError(
            "Section source JSON root must be "
            "an array or object."
        )

    if not records:
        raise ValueError(
            "Section source JSON contains no sections."
        )

    return [
        _build_section_source(
            _require_mapping(
                record,
                f"section_sources[{index}]",
            ),
            index=index,
        )
        for index, record
        in enumerate(
            records
        )
    ]


def list_controlled_sections(
    section_sources: Sequence[SectionSource],
) -> list[ControlledSectionInfo]:
    """
    Return metadata-only section information safe for terminal display.
    """

    if not section_sources:
        raise ValueError(
            "section_sources must contain at least one section."
        )

    result: list[
        ControlledSectionInfo
    ] = []

    for index, section_source in enumerate(
        section_sources
    ):
        if not isinstance(
            section_source,
            SectionSource,
        ):
            raise TypeError(
                "section_sources must contain "
                "SectionSource objects."
            )

        metadata = (
            section_source.section_metadata
        )

        result.append(
            ControlledSectionInfo(
                index=index,
                unit=metadata.unit,
                chapter=metadata.chapter,
                section=metadata.section,
                page_start=(
                    metadata.page_start
                ),
                page_end=(
                    metadata.page_end
                ),
                page_count=len(
                    section_source.pages
                ),
            )
        )

    return result


def select_controlled_section(
    section_sources: Sequence[SectionSource],
    section_index: int,
) -> SectionSource:
    """
    Select exactly one local SectionSource by zero-based index.
    """

    if (
        not isinstance(
            section_index,
            int,
        )
        or isinstance(
            section_index,
            bool,
        )
    ):
        raise TypeError(
            "section_index must be an integer."
        )

    if section_index < 0:
        raise ValueError(
            "section_index must be non-negative."
        )

    if section_index >= len(
        section_sources
    ):
        raise IndexError(
            "section_index is outside the available "
            f"range 0-{len(section_sources) - 1}."
        )

    section_source = (
        section_sources[
            section_index
        ]
    )

    if not isinstance(
        section_source,
        SectionSource,
    ):
        raise TypeError(
            "Selected item must be a SectionSource object."
        )

    return section_source


def extract_single_section_local(
    section_source: SectionSource,
    model_client: StructuredKnowledgeModelClient,
    config: OpenAIKnowledgeConfig,
    output_path: str | Path,
    project_root: str | Path = ".",
) -> ControlledExtractionResult:
    """
    Extract exactly one section and save one-record KnowledgeBase JSON.

    This function intentionally accepts one SectionSource rather than a
    sequence, preventing accidental whole-textbook extraction during the
    controlled validation stage.
    """

    if not isinstance(
        section_source,
        SectionSource,
    ):
        raise TypeError(
            "section_source must be a SectionSource object."
        )

    if not isinstance(
        model_client,
        StructuredKnowledgeModelClient,
    ):
        raise TypeError(
            "model_client must implement "
            "StructuredKnowledgeModelClient."
        )

    if not isinstance(
        config,
        OpenAIKnowledgeConfig,
    ):
        raise TypeError(
            "config must be an OpenAIKnowledgeConfig object."
        )

    extractor = ModelKnowledgeExtractor(
        client=model_client,
        extractor_name=(
            f"openai-controlled:{config.model}"
        ),
    )

    export_result = (
        build_and_export_knowledge_base(
            section_sources=[
                section_source
            ],
            extractor=extractor,
            output_path=output_path,
            project_root=project_root,
        )
    )

    records = (
        export_result
        .knowledge_base
        .records
    )

    if len(records) != 1:
        raise RuntimeError(
            "Controlled extraction must produce "
            "exactly one KnowledgeRecord."
        )

    record = records[0]

    usage = getattr(
        model_client,
        "last_usage",
        None,
    )

    if usage is None:
        input_tokens = None
        output_tokens = None
        total_tokens = None
    else:
        input_tokens = getattr(
            usage,
            "input_tokens",
            None,
        )

        output_tokens = getattr(
            usage,
            "output_tokens",
            None,
        )

        total_tokens = getattr(
            usage,
            "total_tokens",
            None,
        )

    response_id = getattr(
        model_client,
        "last_response_id",
        None,
    )

    if not isinstance(
        response_id,
        str,
    ):
        response_id = None

    return ControlledExtractionResult(
        output_path=(
            export_result.output_path
        ),
        knowledge_id=(
            record.knowledge_id
        ),
        section=(
            record
            .section_metadata
            .section
        ),
        page_numbers=list(
            record
            .provenance
            .page_numbers
        ),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        response_id=response_id,
    )