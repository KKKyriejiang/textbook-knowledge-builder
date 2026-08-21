from pathlib import Path

import pymupdf

from textbook_kb.pdf_parser import extract_pages


def create_test_pdf(path: Path) -> None:
    """Create a small synthetic PDF for testing."""

    document = pymupdf.open()

    first_page = document.new_page()
    first_page.insert_text(
        (72, 72),
        "Quadratic Functions",
    )

    second_page = document.new_page()
    second_page.insert_text(
        (72, 72),
        "The vertex form is y = a(x - h)^2 + k.",
    )

    document.save(path)
    document.close()


def test_extract_pages(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"

    create_test_pdf(pdf_path)

    pages = extract_pages(pdf_path)

    assert len(pages) == 2

    assert pages[0].page_number == 1
    assert pages[0].source_file == "sample.pdf"
    assert "Quadratic Functions" in pages[0].text

    assert pages[1].page_number == 2
    assert "vertex form" in pages[1].text