from pathlib import Path

import fitz
import pytest

from textbook_kb.structure_boundaries import (
    StructureBoundaryKind,
    classify_structure_boundary_candidate,
    detect_structure_boundaries,
    match_boundary_kind,
)
from textbook_kb.structure_candidates import (
    StructureCandidate,
)


def make_candidate(
    *,
    text: str,
    page_number: int = 1,
    font_size: float = 22.0,
    top: float = 50.0,
) -> StructureCandidate:
    return StructureCandidate(
        page_number=page_number,
        text=text,
        font_size=font_size,
        fonts=("Helvetica-Bold",),
        bbox=(
            72.0,
            top,
            350.0,
            top + 25.0,
        ),
        reasons=("chapter",),
    )


def create_boundary_test_pdf(
    pdf_path: Path,
) -> None:
    document = fitz.open()

    toc_page = document.new_page()

    toc_page.insert_text(
        (72, 80),
        "Chapter Review",
        fontsize=10,
    )

    toc_page.insert_text(
        (72, 110),
        "Chapter Self-Test",
        fontsize=10,
    )

    toc_page.insert_text(
        (72, 140),
        "Chapter Task",
        fontsize=10,
    )

    body_page = document.new_page()

    body_page.insert_text(
        (72, 80),
        "Normal section content",
        fontsize=10,
    )

    review_page = document.new_page()

    review_page.insert_text(
        (72, 80),
        "Chapter Review",
        fontsize=22,
    )

    self_test_page = document.new_page()

    self_test_page.insert_text(
        (72, 80),
        "Chapter Self-Test",
        fontsize=22,
    )

    task_page = document.new_page()

    task_page.insert_text(
        (72, 80),
        "Chapter Task",
        fontsize=22,
    )

    document.save(
        pdf_path
    )

    document.close()


def test_match_boundary_kind() -> None:
    assert (
        match_boundary_kind(
            "Chapter Review"
        )
        == StructureBoundaryKind.CHAPTER_REVIEW
    )

    assert (
        match_boundary_kind(
            "Chapter Self-Test"
        )
        == StructureBoundaryKind.CHAPTER_SELF_TEST
    )

    assert (
        match_boundary_kind(
            "Chapter Task"
        )
        == StructureBoundaryKind.CHAPTER_TASK
    )

    assert (
        match_boundary_kind(
            "Chapter 3"
        )
        is None
    )


def test_classify_body_chapter_review_boundary() -> None:
    candidate = make_candidate(
        text="Chapter Review",
        page_number=84,
        font_size=22.0,
        top=28.9,
    )

    boundary = classify_structure_boundary_candidate(
        candidate
    )

    assert boundary is not None

    assert (
        boundary.kind
        == StructureBoundaryKind.CHAPTER_REVIEW
    )

    assert boundary.page_number == 84
    assert boundary.text == "Chapter Review"


def test_small_toc_chapter_review_is_filtered() -> None:
    candidate = make_candidate(
        text="Chapter Review",
        page_number=7,
        font_size=10.5,
        top=350.0,
    )

    boundary = classify_structure_boundary_candidate(
        candidate
    )

    assert boundary is None


def test_large_boundary_too_low_on_page_is_filtered() -> None:
    candidate = make_candidate(
        text="Chapter Review",
        page_number=50,
        font_size=22.0,
        top=400.0,
    )

    boundary = classify_structure_boundary_candidate(
        candidate
    )

    assert boundary is None


def test_detect_structure_boundaries_from_pdf(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "sample.pdf"

    create_boundary_test_pdf(
        pdf_path
    )

    boundaries = detect_structure_boundaries(
        pdf_path
    )

    assert len(boundaries) == 3

    assert [
        boundary.kind
        for boundary in boundaries
    ] == [
        StructureBoundaryKind.CHAPTER_REVIEW,
        StructureBoundaryKind.CHAPTER_SELF_TEST,
        StructureBoundaryKind.CHAPTER_TASK,
    ]

    assert [
        boundary.page_number
        for boundary in boundaries
    ] == [
        3,
        4,
        5,
    ]


def test_invalid_boundary_settings_raise_error() -> None:
    candidate = make_candidate(
        text="Chapter Review",
    )

    with pytest.raises(
        ValueError,
        match="min_boundary_font_size",
    ):
        classify_structure_boundary_candidate(
            candidate=candidate,
            min_boundary_font_size=0,
        )

    with pytest.raises(
        ValueError,
        match="max_boundary_top",
    ):
        classify_structure_boundary_candidate(
            candidate=candidate,
            max_boundary_top=-1,
        )