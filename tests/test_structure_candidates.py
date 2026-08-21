from pathlib import Path

import fitz
import pytest

from textbook_kb.structure_candidates import (
    StructureCandidate,
    extract_page_structure_candidates,
    match_structure_patterns,
    scan_structure_candidates,
)


def create_test_pdf(
    pdf_path: Path,
) -> None:
    document = fitz.open()

    page_1 = document.new_page()

    page_1.insert_text(
        (72, 72),
        "Normal body paragraph",
        fontsize=10,
    )

    page_1.insert_text(
        (72, 110),
        "1.2 Vertex Form",
        fontsize=11,
    )

    page_1.insert_text(
        (72, 150),
        "Exploring Quadratic Functions",
        fontsize=18,
    )

    page_2 = document.new_page()

    page_2.insert_text(
        (72, 72),
        "Chapter 3",
        fontsize=12,
    )

    page_2.insert_text(
        (72, 110),
        "Another normal paragraph",
        fontsize=10,
    )

    document.save(pdf_path)
    document.close()


def test_match_structure_patterns() -> None:
    assert match_structure_patterns(
        "Unit 2"
    ) == ("unit",)

    assert match_structure_patterns(
        "Chapter 3"
    ) == ("chapter",)

    assert match_structure_patterns(
        "Section 4"
    ) == ("section",)

    assert match_structure_patterns(
        "3.2 Vertex Form"
    ) == ("numbered heading",)

    assert match_structure_patterns(
        "Normal body paragraph"
    ) == ()


def test_extract_page_structure_candidates(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"

    create_test_pdf(pdf_path)

    with fitz.open(pdf_path) as document:
        page = document.load_page(0)

        candidates = extract_page_structure_candidates(
            page=page,
            page_number=1,
            min_font_size=14.0,
        )

    assert len(candidates) == 2

    numbered_candidate = candidates[0]
    large_font_candidate = candidates[1]

    assert isinstance(
        numbered_candidate,
        StructureCandidate,
    )

    assert numbered_candidate.page_number == 1
    assert numbered_candidate.text == "1.2 Vertex Form"
    assert numbered_candidate.reasons == (
        "numbered heading",
    )

    assert large_font_candidate.page_number == 1
    assert (
        large_font_candidate.text
        == "Exploring Quadratic Functions"
    )
    assert large_font_candidate.font_size == pytest.approx(
        18.0
    )
    assert large_font_candidate.reasons == (
        "large font",
    )

    assert len(
        large_font_candidate.bbox
    ) == 4


def test_regex_only_excludes_large_font_only_candidates(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"

    create_test_pdf(pdf_path)

    candidates = scan_structure_candidates(
        pdf_path=pdf_path,
        regex_only=True,
    )

    candidate_texts = {
        candidate.text
        for candidate in candidates
    }

    assert "1.2 Vertex Form" in candidate_texts
    assert "Chapter 3" in candidate_texts

    assert (
        "Exploring Quadratic Functions"
        not in candidate_texts
    )


def test_scan_structure_candidates_across_pages(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"

    create_test_pdf(pdf_path)

    candidates = scan_structure_candidates(
        pdf_path=pdf_path,
        min_font_size=14.0,
    )

    candidate_texts = [
        candidate.text
        for candidate in candidates
    ]

    assert candidate_texts == [
        "1.2 Vertex Form",
        "Exploring Quadratic Functions",
        "Chapter 3",
    ]

    assert [
        candidate.page_number
        for candidate in candidates
    ] == [
        1,
        1,
        2,
    ]


def test_scan_structure_candidates_respects_page_range(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"

    create_test_pdf(pdf_path)

    candidates = scan_structure_candidates(
        pdf_path=pdf_path,
        start_page=2,
        end_page=2,
    )

    assert len(candidates) == 1
    assert candidates[0].page_number == 2
    assert candidates[0].text == "Chapter 3"


def test_invalid_candidate_settings_raise_error(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"

    create_test_pdf(pdf_path)

    with pytest.raises(
        ValueError,
        match="min_font_size",
    ):
        scan_structure_candidates(
            pdf_path=pdf_path,
            min_font_size=0,
        )

    with pytest.raises(
        ValueError,
        match="max_heading_length",
    ):
        scan_structure_candidates(
            pdf_path=pdf_path,
            max_heading_length=0,
        )