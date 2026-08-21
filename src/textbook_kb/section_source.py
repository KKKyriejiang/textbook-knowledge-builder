from dataclasses import dataclass

from textbook_kb.metadata import SectionMetadata, TextbookMetadata
from textbook_kb.pdf_parser import ParsedPage


@dataclass(frozen=True, slots=True)
class SectionSource:
    """Validated source content for one textbook section."""

    textbook_metadata: TextbookMetadata
    section_metadata: SectionMetadata
    pages: tuple[ParsedPage, ...]


def select_section_pages(
    pages: list[ParsedPage],
    section_metadata: SectionMetadata,
    textbook_metadata: TextbookMetadata,
) -> list[ParsedPage]:
    """Select and validate parsed pages that belong to a textbook section."""

    section_pages = [
        page
        for page in pages
        if (
            section_metadata.page_start
            <= page.page_number
            <= section_metadata.page_end
        )
    ]

    expected_page_numbers = set(
        range(
            section_metadata.page_start,
            section_metadata.page_end + 1,
        )
    )

    actual_page_numbers = {
        page.page_number
        for page in section_pages
    }

    missing_page_numbers = expected_page_numbers - actual_page_numbers

    if missing_page_numbers:
        missing = sorted(missing_page_numbers)

        raise ValueError(
            f"Missing parsed pages for section "
            f"{section_metadata.section}: {missing}"
        )

    source_files = {
        page.source_file
        for page in section_pages
    }

    if len(source_files) > 1:
        raise ValueError(
            f"Section pages come from multiple source files: "
            f"{sorted(source_files)}"
        )

    source_file = next(iter(source_files))

    if source_file != textbook_metadata.source_file:
        raise ValueError(
            f"Section source file {source_file} does not match "
            f"textbook source file {textbook_metadata.source_file}"
        )

    return section_pages


def build_section_source(
    pages: list[ParsedPage],
    section_metadata: SectionMetadata,
    textbook_metadata: TextbookMetadata,
) -> SectionSource:
    """Build a validated source representation for one textbook section."""

    section_pages = select_section_pages(
        pages,
        section_metadata,
        textbook_metadata,
    )

    return SectionSource(
        textbook_metadata=textbook_metadata,
        section_metadata=section_metadata,
        pages=tuple(section_pages),
    )