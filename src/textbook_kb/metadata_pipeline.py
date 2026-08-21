from dataclasses import dataclass
from pathlib import Path

from textbook_kb.metadata import (
    SectionManifest,
    TextbookMetadata,
    find_textbook_metadata,
    load_section_manifest,
    load_textbook_metadata,
    validate_section_manifest,
)
from textbook_kb.pdf_parser import ParsedPage
from textbook_kb.section_source import (
    SectionSource,
    build_section_source,
)


@dataclass(frozen=True, slots=True)
class TextbookStructure:
    """Validated textbook metadata and section structure."""

    textbook_metadata: TextbookMetadata
    section_manifest: SectionManifest


def load_textbook_structure(
    source_file: str,
    textbook_config_path: str | Path,
    section_manifest_path: str | Path,
) -> TextbookStructure:
    """Load and validate metadata structure for one textbook."""

    textbooks = load_textbook_metadata(textbook_config_path)

    textbook_metadata = find_textbook_metadata(
        textbooks,
        source_file,
    )

    section_manifest = load_section_manifest(
        section_manifest_path
    )

    validate_section_manifest(
        section_manifest,
        textbook_metadata,
    )

    return TextbookStructure(
        textbook_metadata=textbook_metadata,
        section_manifest=section_manifest,
    )


def build_textbook_section_sources(
    pages: list[ParsedPage],
    structure: TextbookStructure,
) -> tuple[SectionSource, ...]:
    """Build validated source objects for every section in a textbook."""

    return tuple(
        build_section_source(
            pages=pages,
            section_metadata=section_metadata,
            textbook_metadata=structure.textbook_metadata,
        )
        for section_metadata in structure.section_manifest.sections
    )