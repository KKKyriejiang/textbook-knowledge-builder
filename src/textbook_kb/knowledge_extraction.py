from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from textbook_kb.knowledge_schema import (
    KnowledgeProvenance,
    KnowledgeRecord,
    KnowledgeSectionMetadata,
    KnowledgeTextbookMetadata,
    SectionKnowledge,
)


def _require_non_empty_string(
    value: str,
    field_name: str,
) -> None:
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

    _require_non_empty_string(
        value,
        field_name,
    )


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
class KnowledgeExtractionRequest:
    """
    Transient input passed to a knowledge extractor.

    source_text may contain copyrighted textbook text. It exists only as
    extraction input and must not be copied into the final KnowledgeRecord.

    This object intentionally has no JSON save/load helper.
    """

    knowledge_id: str

    grade: str
    course_id: str
    course_name: str
    textbook: str

    unit: str | None
    chapter: str | None
    section: str

    page_start: int
    page_end: int

    source_file: str
    page_numbers: list[int]
    source_text: str

    trace_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_non_empty_string(
            self.knowledge_id,
            "knowledge_id",
        )

        _require_non_empty_string(
            self.grade,
            "grade",
        )
        _require_non_empty_string(
            self.course_id,
            "course_id",
        )
        _require_non_empty_string(
            self.course_name,
            "course_name",
        )
        _require_non_empty_string(
            self.textbook,
            "textbook",
        )

        _validate_optional_string(
            self.unit,
            "unit",
        )
        _validate_optional_string(
            self.chapter,
            "chapter",
        )

        _require_non_empty_string(
            self.section,
            "section",
        )

        if (
            not isinstance(self.page_start, int)
            or isinstance(self.page_start, bool)
            or self.page_start < 1
        ):
            raise ValueError(
                "page_start must be a positive integer."
            )

        if (
            not isinstance(self.page_end, int)
            or isinstance(self.page_end, bool)
            or self.page_end < self.page_start
        ):
            raise ValueError(
                "page_end must be greater than or equal "
                "to page_start."
            )

        _require_non_empty_string(
            self.source_file,
            "source_file",
        )

        if not isinstance(self.page_numbers, list):
            raise ValueError(
                "page_numbers must be a list of integers."
            )

        if not self.page_numbers:
            raise ValueError(
                "page_numbers must contain at least one page."
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

        outside_section = [
            page_number
            for page_number in self.page_numbers
            if not self.page_start
            <= page_number
            <= self.page_end
        ]

        if outside_section:
            raise ValueError(
                "page_numbers contains pages outside "
                f"the section range "
                f"{self.page_start}-{self.page_end}: "
                f"{outside_section}"
            )

        _require_non_empty_string(
            self.source_text,
            "source_text",
        )

        _validate_string_list(
            self.trace_ids,
            "trace_ids",
        )


@dataclass(frozen=True)
class KnowledgeExtractionResult:
    """
    Structured output returned by a knowledge extractor.

    Only derived SectionKnowledge is carried forward. Raw model responses
    and raw source text are intentionally excluded from this result.
    """

    knowledge: SectionKnowledge
    extractor_name: str
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(
            self.knowledge,
            SectionKnowledge,
        ):
            raise ValueError(
                "knowledge must be a SectionKnowledge object."
            )

        _require_non_empty_string(
            self.extractor_name,
            "extractor_name",
        )

        _validate_string_list(
            self.warnings,
            "warnings",
        )


@runtime_checkable
class KnowledgeExtractor(Protocol):
    """
    Contract implemented by every knowledge extraction backend.

    Future implementations may use an LLM, a local model, rules, or any
    other extraction method, provided they obey this interface.
    """

    def extract(
        self,
        request: KnowledgeExtractionRequest,
    ) -> KnowledgeExtractionResult:
        ...


def run_knowledge_extraction(
    extractor: KnowledgeExtractor,
    request: KnowledgeExtractionRequest,
) -> KnowledgeExtractionResult:
    """
    Execute one extraction and validate the extractor's return type.
    """

    if not isinstance(
        request,
        KnowledgeExtractionRequest,
    ):
        raise TypeError(
            "request must be a KnowledgeExtractionRequest object."
        )

    if not isinstance(
        extractor,
        KnowledgeExtractor,
    ):
        raise TypeError(
            "extractor must implement the KnowledgeExtractor protocol."
        )

    result = extractor.extract(request)

    if not isinstance(
        result,
        KnowledgeExtractionResult,
    ):
        raise TypeError(
            "extractor.extract() must return "
            "KnowledgeExtractionResult."
        )

    return result


def build_knowledge_record_from_extraction(
    request: KnowledgeExtractionRequest,
    result: KnowledgeExtractionResult,
) -> KnowledgeRecord:
    """
    Convert one validated extraction request/result pair into the stable
    KnowledgeRecord stored in the final local knowledge JSON.

    source_text is deliberately not transferred into the final record.
    """

    if not isinstance(
        request,
        KnowledgeExtractionRequest,
    ):
        raise TypeError(
            "request must be a KnowledgeExtractionRequest object."
        )

    if not isinstance(
        result,
        KnowledgeExtractionResult,
    ):
        raise TypeError(
            "result must be a KnowledgeExtractionResult object."
        )

    textbook_metadata = KnowledgeTextbookMetadata(
        grade=request.grade,
        course_id=request.course_id,
        course_name=request.course_name,
        textbook=request.textbook,
    )

    section_metadata = KnowledgeSectionMetadata(
        unit=request.unit,
        chapter=request.chapter,
        section=request.section,
        page_start=request.page_start,
        page_end=request.page_end,
    )

    provenance = KnowledgeProvenance(
        source_file=request.source_file,
        page_numbers=list(request.page_numbers),
        trace_ids=list(request.trace_ids),
    )

    return KnowledgeRecord(
        knowledge_id=request.knowledge_id,
        textbook_metadata=textbook_metadata,
        section_metadata=section_metadata,
        provenance=provenance,
        knowledge=result.knowledge,
    )