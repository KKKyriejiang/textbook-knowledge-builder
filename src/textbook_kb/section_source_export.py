from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from textbook_kb.metadata import (
    SectionManifest,
    TextbookMetadata,
)
from textbook_kb.metadata_pipeline import (
    TextbookStructure,
    build_textbook_section_sources,
)
from textbook_kb.pdf_parser import extract_pages
from textbook_kb.section_source import SectionSource


def section_source_to_dict(
    section_source: SectionSource,
) -> dict[str, Any]:
    if is_dataclass(section_source):
        return asdict(section_source)

    raise TypeError(
        "Expected SectionSource to be a dataclass instance. "
        f"Got: {type(section_source)!r}"
    )


def build_section_sources_from_pdf(
    *,
    pdf_path: Path,
    textbook_metadata: TextbookMetadata,
    section_manifest: SectionManifest,
) -> tuple[SectionSource, ...]:
    parsed_pages = extract_pages(pdf_path)

    textbook_structure = TextbookStructure(
        textbook_metadata=textbook_metadata,
        section_manifest=section_manifest,
    )

    section_sources = build_textbook_section_sources(
        pages=parsed_pages,
        structure=textbook_structure,
    )

    validate_section_sources_have_text(section_sources)

    return section_sources


def validate_section_sources_have_text(
    section_sources: tuple[SectionSource, ...],
) -> None:
    if not section_sources:
        raise ValueError("Expected at least one SectionSource.")

    for section_source in section_sources:
        if not section_source.pages:
            raise ValueError(
                "SectionSource has no pages: "
                f"{section_source.section_metadata!r}"
            )

        for page in section_source.pages:
            if not page.text.strip():
                raise ValueError(
                    "SectionSource contains an empty page text. "
                    f"page_number={page.page_number}, "
                    f"section={section_source.section_metadata.section!r}"
                )


def save_section_sources_json(
    *,
    section_sources: tuple[SectionSource, ...],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = [
        section_source_to_dict(section_source)
        for section_source in section_sources
    ]

    output_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )