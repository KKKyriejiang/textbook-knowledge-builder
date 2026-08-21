from dataclasses import dataclass
from pathlib import Path

import pymupdf


@dataclass(slots=True)
class ParsedPage:
    """Text extracted from one physical page of a PDF."""

    page_number: int
    text: str
    source_file: str


def extract_pages(pdf_path: str | Path) -> list[ParsedPage]:
    """Extract text from every page of a PDF.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A list of ParsedPage objects in PDF page order.

    Raises:
        FileNotFoundError: If the PDF does not exist.
        ValueError: If the supplied file is not a PDF.
    """

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file does not exist: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, received: {path}")

    pages: list[ParsedPage] = []

    with pymupdf.open(path) as document:
        for page_index, page in enumerate(document):
            text = page.get_text("text").strip()

            pages.append(
                ParsedPage(
                    page_number=page_index + 1,
                    text=text,
                    source_file=path.name,
                )
            )

    return pages