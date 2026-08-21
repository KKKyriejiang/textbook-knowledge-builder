from pathlib import Path

import fitz

from textbook_kb.section_titles import (
    enrich_section_heading_title,
    enrich_section_heading_titles,
    find_section_title_match,
)
from textbook_kb.structure_candidates import (
    StructureCandidate,
)
from textbook_kb.structure_headings import (
    HeadingKind,
    StructureHeading,
)
from textbook_kb.structure_pipeline import (
    extract_structure_headings,
)


def make_candidate(
    *,
    text: str,
    page_number: int = 1,
    font_size: float = 20.0,
    top: float = 70.0,
    reasons: tuple[str, ...] = ("large font",),
) -> StructureCandidate:
    return StructureCandidate(
        page_number=page_number,
        text=text,
        font_size=font_size,
        fonts=("Helvetica-Bold",),
        bbox=(
            72.0,
            top,
            400.0,
            top + 25.0,
        ),
        reasons=reasons,
    )


def make_section_heading(
    *,
    number: str = "3.2",
    page_number: int = 100,
    title: str | None = None,
) -> StructureHeading:
    candidate = make_candidate(
        text=number,
        page_number=page_number,
        font_size=46.0,
        top=6.5,
        reasons=(
            "numbered heading",
            "large font",
        ),
    )

    return StructureHeading(
        kind=HeadingKind.SECTION,
        number=number,
        title=title,
        page_number=page_number,
        source_candidate=candidate,
    )


def test_find_section_title_match_selects_nearest_large_text() -> None:
    section = make_section_heading()

    title = make_candidate(
        text="Vertex Form of a Quadratic Function",
        page_number=100,
        font_size=22.0,
        top=70.0,
    )

    later_heading = make_candidate(
        text="Learning Goals",
        page_number=100,
        font_size=18.0,
        top=150.0,
    )

    match = find_section_title_match(
        section_heading=section,
        candidates=(
            section.source_candidate,
            later_heading,
            title,
        ),
    )

    assert match is not None

    assert (
        match.title_candidate
        == title
    )


def test_enrich_section_heading_title() -> None:
    section = make_section_heading()

    title = make_candidate(
        text="Vertex Form",
        page_number=100,
        font_size=22.0,
        top=70.0,
    )

    enriched = enrich_section_heading_title(
        heading=section,
        candidates=(
            section.source_candidate,
            title,
        ),
    )

    assert enriched.number == "3.2"
    assert enriched.title == "Vertex Form"
    assert enriched.page_number == 100

    assert (
        enriched.source_candidate
        == section.source_candidate
    )


def test_existing_section_title_is_preserved() -> None:
    section = make_section_heading(
        title="Existing Title",
    )

    candidate = make_candidate(
        text="Different Title",
        page_number=100,
        font_size=24.0,
        top=70.0,
    )

    enriched = enrich_section_heading_title(
        heading=section,
        candidates=(
            section.source_candidate,
            candidate,
        ),
    )

    assert enriched == section


def test_small_toc_text_is_not_used_as_title() -> None:
    section = make_section_heading(
        page_number=7,
    )

    toc_title = make_candidate(
        text="Vertex Form",
        page_number=7,
        font_size=10.5,
        top=100.0,
    )

    enriched = enrich_section_heading_title(
        heading=section,
        candidates=(
            section.source_candidate,
            toc_title,
        ),
    )

    assert enriched.title is None


def test_structural_candidate_is_not_used_as_title() -> None:
    section = make_section_heading()

    chapter_candidate = make_candidate(
        text="Chapter 3",
        page_number=100,
        font_size=22.0,
        top=70.0,
        reasons=(
            "chapter",
            "large font",
        ),
    )

    enriched = enrich_section_heading_titles(
        headings=(section,),
        candidates=(
            section.source_candidate,
            chapter_candidate,
        ),
    )

    assert enriched[0].title is None


def test_extract_structure_headings_can_enrich_titles(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"

    document = fitz.open()

    page = document.new_page()

    page.insert_text(
        (72, 70),
        "3.2",
        fontsize=46,
    )

    page.insert_text(
        (72, 145),
        "Vertex Form",
        fontsize=22,
    )

    page.insert_text(
        (72, 220),
        "Normal body text",
        fontsize=10,
    )

    document.save(
        pdf_path
    )

    document.close()

    headings = extract_structure_headings(
        pdf_path=pdf_path,
        regex_only=True,
        enrich_titles=True,
    )

    section_headings = tuple(
        heading
        for heading in headings
        if heading.kind == HeadingKind.SECTION
    )

    assert len(section_headings) == 1

    assert (
        section_headings[0].number
        == "3.2"
    )

    assert (
        section_headings[0].title
        == "Vertex Form"
    )