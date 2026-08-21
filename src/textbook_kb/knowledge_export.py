from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Sequence

from textbook_kb.knowledge_extraction import (
    KnowledgeExtractor,
)
from textbook_kb.knowledge_pipeline import (
    KnowledgePipelineWarning,
    run_knowledge_pipeline,
)
from textbook_kb.knowledge_schema import (
    DEFAULT_KNOWLEDGE_OUTPUT_PATH,
    KnowledgeBase,
    save_knowledge_json,
)
from textbook_kb.section_source import SectionSource


PRIVATE_KNOWLEDGE_GITIGNORE_PATTERNS = (
    "data/processed/*knowledge*.json",
    "data/processed/*knowledge_base*.json",
    "data/processed/*kb*.json",
)


@dataclass(frozen=True)
class KnowledgeExportResult:
    """
    Result of building and exporting one local knowledge base.

    warnings remain transient pipeline diagnostics. They are returned to
    the caller and are not written into the final knowledge JSON.
    """

    output_path: Path
    knowledge_base: KnowledgeBase
    warnings: list[KnowledgePipelineWarning]

    def __post_init__(self) -> None:
        if not isinstance(
            self.output_path,
            Path,
        ):
            raise TypeError(
                "output_path must be a pathlib.Path object."
            )

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


def _resolve_project_root(
    project_root: str | Path,
) -> Path:
    root = Path(
        project_root
    ).resolve()

    if not root.exists():
        raise ValueError(
            f"project_root does not exist: {root}"
        )

    if not root.is_dir():
        raise ValueError(
            f"project_root must be a directory: {root}"
        )

    return root


def _resolve_output_path(
    output_path: str | Path,
    project_root: Path,
) -> Path:
    path = Path(
        output_path
    )

    if path.is_absolute():
        return path.resolve()

    return (
        project_root
        / path
    ).resolve()


def _relative_to_project(
    output_path: Path,
    project_root: Path,
) -> Path:
    try:
        return output_path.relative_to(
            project_root
        )
    except ValueError as exc:
        raise ValueError(
            "Knowledge output must remain inside "
            "the project directory."
        ) from exc


def is_private_knowledge_output_path(
    output_path: str | Path,
    project_root: str | Path = ".",
) -> bool:
    """
    Return True when the path matches the project's private knowledge
    output convention.

    Accepted paths must:
      1. remain inside the project directory,
      2. live under data/processed/,
      3. use a filename covered by the project's knowledge JSON
         .gitignore naming convention.

    This function checks the path convention itself and does not write
    any files.
    """

    try:
        root = _resolve_project_root(
            project_root
        )

        resolved_output = _resolve_output_path(
            output_path,
            root,
        )

        relative_path = _relative_to_project(
            resolved_output,
            root,
        )
    except ValueError:
        return False

    relative_posix = (
        relative_path
        .as_posix()
        .lower()
    )

    return any(
        fnmatchcase(
            relative_posix,
            pattern.lower(),
        )
        for pattern
        in PRIVATE_KNOWLEDGE_GITIGNORE_PATTERNS
    )


def validate_private_knowledge_output_path(
    output_path: str | Path,
    project_root: str | Path = ".",
) -> Path:
    """
    Validate and resolve a local-only final knowledge JSON path.

    The final path must match one of the knowledge JSON patterns already
    protected by the repository's .gitignore policy.
    """

    root = _resolve_project_root(
        project_root
    )

    resolved_output = _resolve_output_path(
        output_path,
        root,
    )

    relative_path = _relative_to_project(
        resolved_output,
        root,
    )

    if resolved_output.suffix.lower() != ".json":
        raise ValueError(
            "Knowledge output must use the .json extension."
        )

    relative_posix = (
        relative_path
        .as_posix()
        .lower()
    )

    if not any(
        fnmatchcase(
            relative_posix,
            pattern.lower(),
        )
        for pattern
        in PRIVATE_KNOWLEDGE_GITIGNORE_PATTERNS
    ):
        raise ValueError(
            "Knowledge output path is not covered by the "
            "private knowledge naming convention. "
            "Use data/processed/ with a filename containing "
            "'knowledge' or 'kb'."
        )

    return resolved_output


def export_knowledge_base_local(
    knowledge_base: KnowledgeBase,
    output_path: str | Path = DEFAULT_KNOWLEDGE_OUTPUT_PATH,
    project_root: str | Path = ".",
) -> Path:
    """
    Safely save an already-built KnowledgeBase to a private local path.

    This is the preferred persistence function for real textbook-derived
    knowledge.
    """

    if not isinstance(
        knowledge_base,
        KnowledgeBase,
    ):
        raise TypeError(
            "knowledge_base must be a KnowledgeBase object."
        )

    safe_output_path = (
        validate_private_knowledge_output_path(
            output_path=output_path,
            project_root=project_root,
        )
    )

    return save_knowledge_json(
        knowledge_base=knowledge_base,
        output_path=safe_output_path,
    )


def build_and_export_knowledge_base(
    section_sources: Sequence[SectionSource],
    extractor: KnowledgeExtractor,
    output_path: str | Path = DEFAULT_KNOWLEDGE_OUTPUT_PATH,
    project_root: str | Path = ".",
) -> KnowledgeExportResult:
    """
    Run the complete Milestone 4 knowledge pipeline and save the final
    KnowledgeBase to a protected local-only JSON path.

    Flow:

        SectionSource[]
            ->
        KnowledgeExtractionRequest[]
            ->
        KnowledgeExtractor
            ->
        KnowledgeRecord[]
            ->
        KnowledgeBase
            ->
        private local JSON

    Raw SectionSource page text remains transient and is not written into
    the final KnowledgeBase JSON.
    """

    safe_output_path = (
        validate_private_knowledge_output_path(
            output_path=output_path,
            project_root=project_root,
        )
    )

    pipeline_result = (
        run_knowledge_pipeline(
            section_sources=section_sources,
            extractor=extractor,
        )
    )

    saved_path = save_knowledge_json(
        knowledge_base=(
            pipeline_result.knowledge_base
        ),
        output_path=safe_output_path,
    )

    return KnowledgeExportResult(
        output_path=saved_path,
        knowledge_base=(
            pipeline_result.knowledge_base
        ),
        warnings=(
            pipeline_result.warnings
        ),
    )