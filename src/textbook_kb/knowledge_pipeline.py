from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from textbook_kb.knowledge_adapter import (
    build_knowledge_extraction_request,
)
from textbook_kb.knowledge_extraction import (
    KnowledgeExtractor,
    build_knowledge_record_from_extraction,
    run_knowledge_extraction,
)
from textbook_kb.knowledge_schema import (
    KnowledgeBase,
)
from textbook_kb.section_source import (
    SectionSource,
)


@dataclass(frozen=True)
class KnowledgePipelineWarning:
    """
    One transient warning produced while processing a section.

    Warnings are useful for quality control and debugging. They remain
    outside the final KnowledgeBase JSON so local extraction diagnostics
    do not become part of the persistent RAG knowledge schema.
    """

    knowledge_id: str
    extractor_name: str
    message: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.knowledge_id, str)
            or not self.knowledge_id.strip()
        ):
            raise ValueError(
                "knowledge_id must be a non-empty string."
            )

        if (
            not isinstance(self.extractor_name, str)
            or not self.extractor_name.strip()
        ):
            raise ValueError(
                "extractor_name must be a non-empty string."
            )

        if (
            not isinstance(self.message, str)
            or not self.message.strip()
        ):
            raise ValueError(
                "message must be a non-empty string."
            )


@dataclass(frozen=True)
class KnowledgePipelineResult:
    """
    Result of processing a complete collection of SectionSource objects.

    knowledge_base contains the persistent structured knowledge.

    warnings contains transient extraction diagnostics and should normally
    remain local to the pipeline execution.
    """

    knowledge_base: KnowledgeBase
    warnings: list[KnowledgePipelineWarning]

    def __post_init__(self) -> None:
        if not isinstance(
            self.knowledge_base,
            KnowledgeBase,
        ):
            raise TypeError(
                "knowledge_base must be a KnowledgeBase object."
            )

        if not isinstance(
            self.warnings,
            list,
        ):
            raise TypeError(
                "warnings must be a list."
            )

        if not all(
            isinstance(
                warning,
                KnowledgePipelineWarning,
            )
            for warning in self.warnings
        ):
            raise TypeError(
                "warnings must contain "
                "KnowledgePipelineWarning objects."
            )


def _validate_section_sources(
    section_sources: Sequence[SectionSource],
) -> None:
    if not isinstance(
        section_sources,
        Sequence,
    ):
        raise TypeError(
            "section_sources must be a sequence "
            "of SectionSource objects."
        )

    if not section_sources:
        raise ValueError(
            "section_sources must contain at least "
            "one SectionSource."
        )

    for index, section_source in enumerate(
        section_sources
    ):
        if not isinstance(
            section_source,
            SectionSource,
        ):
            raise TypeError(
                "section_sources must contain only "
                "SectionSource objects. "
                f"Invalid item at index {index}."
            )


def run_knowledge_pipeline(
    section_sources: Sequence[SectionSource],
    extractor: KnowledgeExtractor,
) -> KnowledgePipelineResult:
    """
    Convert SectionSource objects into a validated KnowledgeBase.

    Processing flow for each section:

        SectionSource
            ->
        KnowledgeExtractionRequest
            ->
        KnowledgeExtractor
            ->
        KnowledgeExtractionResult
            ->
        KnowledgeRecord

    All KnowledgeRecord objects are finally assembled into one
    KnowledgeBase.

    The pipeline is intentionally fail-fast. Invalid source data,
    extractor failures, invalid extraction results, and duplicate
    knowledge IDs stop the run immediately.
    """

    _validate_section_sources(
        section_sources
    )

    if not isinstance(
        extractor,
        KnowledgeExtractor,
    ):
        raise TypeError(
            "extractor must implement "
            "the KnowledgeExtractor protocol."
        )

    records = []
    pipeline_warnings: list[
        KnowledgePipelineWarning
    ] = []

    for section_source in section_sources:
        request = (
            build_knowledge_extraction_request(
                section_source
            )
        )

        extraction_result = (
            run_knowledge_extraction(
                extractor=extractor,
                request=request,
            )
        )

        record = (
            build_knowledge_record_from_extraction(
                request=request,
                result=extraction_result,
            )
        )

        records.append(
            record
        )

        for warning_message in (
            extraction_result.warnings
        ):
            pipeline_warnings.append(
                KnowledgePipelineWarning(
                    knowledge_id=(
                        request.knowledge_id
                    ),
                    extractor_name=(
                        extraction_result.extractor_name
                    ),
                    message=warning_message,
                )
            )

    knowledge_base = KnowledgeBase(
        records=records,
    )

    return KnowledgePipelineResult(
        knowledge_base=knowledge_base,
        warnings=pipeline_warnings,
    )


def build_knowledge_base(
    section_sources: Sequence[SectionSource],
    extractor: KnowledgeExtractor,
) -> KnowledgeBase:
    """
    Convenience wrapper for callers that only need the final
    KnowledgeBase.

    Use run_knowledge_pipeline() when transient extraction warnings are
    also needed.
    """

    result = run_knowledge_pipeline(
        section_sources=section_sources,
        extractor=extractor,
    )

    return result.knowledge_base