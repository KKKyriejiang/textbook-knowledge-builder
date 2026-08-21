from __future__ import annotations

from pathlib import Path

import fitz

from textbook_kb.heading_occurrences import classify_heading_occurrences
from textbook_kb.metadata import SectionManifest, SectionMetadata
from textbook_kb.section_metadata_builder import (
    build_section_metadata_records,
    derive_section_ranges,
)
from textbook_kb.structure_boundaries import detect_structure_boundaries
from textbook_kb.structure_hierarchy import build_section_hierarchy
from textbook_kb.structure_pipeline import extract_structure_headings


def validate_generated_section_metadata(
    sections: tuple[SectionMetadata, ...],
) -> None:
    if not sections:
        raise ValueError(
            "Generated section metadata must contain at least one section."
        )

    seen_sections: set[str] = set()
    previous_section: SectionMetadata | None = None

    for section in sections:
        normalized_section = section.section.strip().casefold()

        if normalized_section in seen_sections:
            raise ValueError(
                f"Duplicate generated section metadata: {section.section}"
            )

        seen_sections.add(normalized_section)

        if section.page_start < 1:
            raise ValueError("page_start must be at least 1.")

        if section.page_end < section.page_start:
            raise ValueError(
                "page_end must be greater than or equal to page_start."
            )

        if previous_section is not None:
            if section.page_start <= previous_section.page_start:
                raise ValueError(
                    "Generated sections must have strictly increasing "
                    "page_start values."
                )

            if section.page_start <= previous_section.page_end:
                raise ValueError(
                    "Generated section page ranges must not overlap."
                )

        previous_section = section


def build_generated_section_manifest(
    source_file: str,
    sections: tuple[SectionMetadata, ...],
) -> SectionManifest:
    if not source_file.strip():
        raise ValueError("source_file must be non-empty.")

    validate_generated_section_metadata(sections)

    return SectionManifest(
        source_file=source_file,
        sections=sections,
    )


def generate_section_manifest_from_pdf(
    pdf_path: Path,
    *,
    regex_only: bool = True,
    min_font_size: float = 14.0,
    max_heading_length: int = 120,
    min_body_font_size: float = 14.0,
    max_body_top: float = 260.0,
    min_body_font_gap: float = 2.0,
    min_boundary_font_size: float = 18.0,
    max_boundary_top: float = 260.0,
    min_title_font_size: float = 14.0,
    max_title_vertical_gap: float = 100.0,
    max_title_top: float = 260.0,
    max_title_length: int = 120,
) -> SectionManifest:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file does not exist: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file: {pdf_path}")

    with fitz.open(pdf_path) as document:
        final_page = document.page_count

    headings = extract_structure_headings(
        pdf_path=pdf_path,
        min_font_size=min_font_size,
        max_heading_length=max_heading_length,
        regex_only=regex_only,
        enrich_titles=True,
        min_title_font_size=min_title_font_size,
        max_title_vertical_gap=max_title_vertical_gap,
        max_title_top=max_title_top,
        max_title_length=max_title_length,
    )

    occurrences = classify_heading_occurrences(
        headings=headings,
        min_body_font_size=min_body_font_size,
        max_body_top=max_body_top,
        min_body_font_gap=min_body_font_gap,
    )

    hierarchy = build_section_hierarchy(occurrences)

    boundaries = detect_structure_boundaries(
        pdf_path=pdf_path,
        min_boundary_font_size=min_boundary_font_size,
        max_boundary_top=max_boundary_top,
    )

    ranges = derive_section_ranges(
        hierarchy=hierarchy,
        boundaries=boundaries,
        final_page=final_page,
    )

    sections = build_section_metadata_records(ranges)

    return build_generated_section_manifest(
        source_file=pdf_path.name,
        sections=sections,
    )