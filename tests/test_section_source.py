import pytest

from textbook_kb.metadata import SectionMetadata
from textbook_kb.pdf_parser import ParsedPage
from textbook_kb.section_source import select_section_pages


def test_select_section_pages_returns_expected_page_range():
    pages = [
        ParsedPage(
            page_number=1,
            text="Introduction",
            source_file="MCR3U_Functions.pdf",
        ),
        ParsedPage(
            page_number=2,
            text="Quadratic Functions",
            source_file="MCR3U_Functions.pdf",
        ),
        ParsedPage(
            page_number=3,
            text="Vertex form is y = a(x - h)^2 + k.",
            source_file="MCR3U_Functions.pdf",
        ),
        ParsedPage(
            page_number=4,
            text="Example questions",
            source_file="MCR3U_Functions.pdf",
        ),
        ParsedPage(
            page_number=5,
            text="Next section",
            source_file="MCR3U_Functions.pdf",
        ),
    ]

    metadata = SectionMetadata(
        unit="Quadratic Functions",
        chapter=None,
        section="Vertex Form",
        page_start=2,
        page_end=4,
    )

    section_pages = select_section_pages(pages, metadata)

    assert [page.page_number for page in section_pages] == [2, 3, 4]


def test_select_section_pages_raises_when_page_is_missing():
    pages = [
        ParsedPage(
            page_number=1,
            text="Introduction",
            source_file="MCR3U_Functions.pdf",
        ),
        ParsedPage(
            page_number=2,
            text="Quadratic Functions",
            source_file="MCR3U_Functions.pdf",
        ),
        ParsedPage(
            page_number=4,
            text="Example questions",
            source_file="MCR3U_Functions.pdf",
        ),
    ]

    metadata = SectionMetadata(
        unit="Quadratic Functions",
        chapter=None,
        section="Vertex Form",
        page_start=2,
        page_end=4,
    )

    with pytest.raises(
        ValueError,
        match="Missing parsed pages",
    ):
        select_section_pages(pages, metadata)