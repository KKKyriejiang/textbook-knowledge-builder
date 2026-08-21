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