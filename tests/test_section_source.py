import pytest

from textbook_kb.metadata import (
    SectionMetadata,
    TextbookMetadata,
)
from textbook_kb.pdf_parser import ParsedPage
from textbook_kb.section_source import (
    SectionSource,
    build_section_source,
    select_section_pages,
)


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

    section_metadata = SectionMetadata(
        unit="Quadratic Functions",
        chapter=None,
        section="Vertex Form",
        page_start=2,
        page_end=4,
    )

    textbook_metadata = TextbookMetadata(
        grade=11,
        course_id="MCR3U",
        course_name="Functions",
        textbook="MCR3U Functions",
        source_file="MCR3U_Functions.pdf",
    )

    section_pages = select_section_pages(
        pages,
        section_metadata,
        textbook_metadata,
    )

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

    section_metadata = SectionMetadata(
        unit="Quadratic Functions",
        chapter=None,
        section="Vertex Form",
        page_start=2,
        page_end=4,
    )

    textbook_metadata = TextbookMetadata(
        grade=11,
        course_id="MCR3U",
        course_name="Functions",
        textbook="MCR3U Functions",
        source_file="MCR3U_Functions.pdf",
    )

    with pytest.raises(
        ValueError,
        match="Missing parsed pages",
    ):
        select_section_pages(
            pages,
            section_metadata,
            textbook_metadata,
        )


def test_select_section_pages_raises_when_sources_are_mixed():
    pages = [
        ParsedPage(
            page_number=2,
            text="Quadratic Functions",
            source_file="MCR3U_Functions.pdf",
        ),
        ParsedPage(
            page_number=3,
            text="Vertex form",
            source_file="MHF4U_Advanced_Functions.pdf",
        ),
        ParsedPage(
            page_number=4,
            text="Example questions",
            source_file="MCR3U_Functions.pdf",
        ),
    ]

    section_metadata = SectionMetadata(
        unit="Quadratic Functions",
        chapter=None,
        section="Vertex Form",
        page_start=2,
        page_end=4,
    )

    textbook_metadata = TextbookMetadata(
        grade=11,
        course_id="MCR3U",
        course_name="Functions",
        textbook="MCR3U Functions",
        source_file="MCR3U_Functions.pdf",
    )

    with pytest.raises(
        ValueError,
        match="Section pages come from multiple source files",
    ):
        select_section_pages(
            pages,
            section_metadata,
            textbook_metadata,
        )


def test_select_section_pages_raises_when_textbook_source_does_not_match():
    pages = [
        ParsedPage(
            page_number=2,
            text="Quadratic Functions",
            source_file="MHF4U_Advanced_Functions.pdf",
        ),
        ParsedPage(
            page_number=3,
            text="Vertex form",
            source_file="MHF4U_Advanced_Functions.pdf",
        ),
        ParsedPage(
            page_number=4,
            text="Example questions",
            source_file="MHF4U_Advanced_Functions.pdf",
        ),
    ]

    section_metadata = SectionMetadata(
        unit="Quadratic Functions",
        chapter=None,
        section="Vertex Form",
        page_start=2,
        page_end=4,
    )

    textbook_metadata = TextbookMetadata(
        grade=11,
        course_id="MCR3U",
        course_name="Functions",
        textbook="MCR3U Functions",
        source_file="MCR3U_Functions.pdf",
    )

    with pytest.raises(
        ValueError,
        match="does not match textbook source file",
    ):
        select_section_pages(
            pages,
            section_metadata,
            textbook_metadata,
        )


def test_build_section_source_returns_validated_section_source():
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
    ]

    section_metadata = SectionMetadata(
        unit="Quadratic Functions",
        chapter=None,
        section="Vertex Form",
        page_start=2,
        page_end=4,
    )

    textbook_metadata = TextbookMetadata(
        grade=11,
        course_id="MCR3U",
        course_name="Functions",
        textbook="MCR3U Functions",
        source_file="MCR3U_Functions.pdf",
    )

    section_source = build_section_source(
        pages,
        section_metadata,
        textbook_metadata,
    )

    assert isinstance(section_source, SectionSource)
    assert section_source.textbook_metadata == textbook_metadata
    assert section_source.section_metadata == section_metadata
    assert [page.page_number for page in section_source.pages] == [2, 3, 4]