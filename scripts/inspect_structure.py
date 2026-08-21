from __future__ import annotations

import argparse
import re
from pathlib import Path

import fitz


STRUCTURE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "unit keyword",
        re.compile(r"^unit\b", re.IGNORECASE),
    ),
    (
        "chapter keyword",
        re.compile(r"^chapter\b", re.IGNORECASE),
    ),
    (
        "section keyword",
        re.compile(r"^section\b", re.IGNORECASE),
    ),
    (
        "numbered heading",
        re.compile(r"^\d+(?:\.\d+){1,2}\b"),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect structural signals in a textbook PDF, including "
            "text lines, font sizes, fonts, and possible headings."
        )
    )

    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to the textbook PDF.",
    )

    parser.add_argument(
        "--start-page",
        type=int,
        default=1,
        help="First PDF page to inspect. Uses 1-based numbering.",
    )

    parser.add_argument(
        "--end-page",
        type=int,
        default=30,
        help="Last PDF page to inspect. Uses 1-based numbering.",
    )

    parser.add_argument(
        "--min-font-size",
        type=float,
        default=14.0,
        help=(
            "Lines with a font size at least this large are treated "
            "as possible structural headings."
        ),
    )

    parser.add_argument(
        "--preview-lines",
        type=int,
        default=12,
        help="Number of non-empty plain-text lines to preview per page.",
    )

    parser.add_argument(
        "--all-lines",
        action="store_true",
        help="Print layout information for every extracted text line.",
    )

    return parser.parse_args()


def validate_page_range(
    start_page: int,
    end_page: int,
    page_count: int,
) -> None:
    if start_page < 1:
        raise ValueError("start_page must be at least 1.")

    if end_page < start_page:
        raise ValueError("end_page must be greater than or equal to start_page.")

    if start_page > page_count:
        raise ValueError(
            f"start_page {start_page} exceeds PDF page count {page_count}."
        )


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def get_structure_reasons(
    text: str,
    font_size: float,
    min_font_size: float,
) -> list[str]:
    reasons: list[str] = []

    if font_size >= min_font_size:
        reasons.append(f"large font ({font_size:.1f} pt)")

    for label, pattern in STRUCTURE_PATTERNS:
        if pattern.search(text):
            reasons.append(label)

    return reasons


def extract_text_lines(page: fitz.Page) -> list[dict[str, object]]:
    page_dict = page.get_text("dict")
    extracted_lines: list[dict[str, object]] = []

    for block in page_dict["blocks"]:
        if block.get("type") != 0:
            continue

        for line in block.get("lines", []):
            spans = line.get("spans", [])

            if not spans:
                continue

            text = normalize_text(
                " ".join(
                    str(span.get("text", ""))
                    for span in spans
                )
            )

            if not text:
                continue

            font_size = max(
                float(span.get("size", 0.0))
                for span in spans
            )

            fonts = sorted(
                {
                    str(span.get("font", "unknown"))
                    for span in spans
                }
            )

            bbox = tuple(
                round(float(value), 1)
                for value in line.get(
                    "bbox",
                    (0.0, 0.0, 0.0, 0.0),
                )
            )

            extracted_lines.append(
                {
                    "text": text,
                    "font_size": font_size,
                    "fonts": fonts,
                    "bbox": bbox,
                }
            )

    return extracted_lines


def print_text_preview(
    page: fitz.Page,
    preview_lines: int,
) -> None:
    text = page.get_text("text")

    lines = [
        normalize_text(line)
        for line in text.splitlines()
        if normalize_text(line)
    ]

    print("TEXT PREVIEW")

    if not lines:
        print("  <no extracted text>")
        return

    for line in lines[:preview_lines]:
        print(f"  {line}")

    if len(lines) > preview_lines:
        print(f"  ... ({len(lines) - preview_lines} more lines)")


def print_candidate_lines(
    text_lines: list[dict[str, object]],
    min_font_size: float,
) -> None:
    candidates_found = False

    print("STRUCTURE CANDIDATES")

    for line in text_lines:
        text = str(line["text"])
        font_size = float(line["font_size"])

        reasons = get_structure_reasons(
            text=text,
            font_size=font_size,
            min_font_size=min_font_size,
        )

        if not reasons:
            continue

        candidates_found = True

        fonts = ", ".join(
            str(font)
            for font in line["fonts"]
        )

        print(f"  Text: {text}")
        print(f"    size: {font_size:.1f} pt")
        print(f"    font: {fonts}")
        print(f"    bbox: {line['bbox']}")
        print(f"    reason: {', '.join(reasons)}")

    if not candidates_found:
        print("  <no candidates>")


def print_all_lines(
    text_lines: list[dict[str, object]],
) -> None:
    print("ALL TEXT LINES")

    if not text_lines:
        print("  <no extracted text lines>")
        return

    for line in text_lines:
        fonts = ", ".join(
            str(font)
            for font in line["fonts"]
        )

        print(
            f"  [{float(line['font_size']):.1f} pt] "
            f"{line['text']}"
        )
        print(
            f"    font: {fonts} | "
            f"bbox: {line['bbox']}"
        )


def inspect_pdf(
    pdf_path: Path,
    start_page: int,
    end_page: int,
    min_font_size: float,
    preview_lines: int,
    show_all_lines: bool,
) -> None:
    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF file does not exist: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            f"Expected a PDF file: {pdf_path}"
        )

    with fitz.open(pdf_path) as document:
        page_count = document.page_count

        validate_page_range(
            start_page=start_page,
            end_page=end_page,
            page_count=page_count,
        )

        actual_end_page = min(
            end_page,
            page_count,
        )

        print(f"PDF: {pdf_path.name}")
        print(f"Total PDF pages: {page_count}")
        print(
            f"Inspecting PDF pages: "
            f"{start_page}-{actual_end_page}"
        )
        print(
            f"Large-font threshold: "
            f"{min_font_size:.1f} pt"
        )

        for page_number in range(
            start_page,
            actual_end_page + 1,
        ):
            page = document.load_page(page_number - 1)

            print()
            print("=" * 80)
            print(f"PDF PAGE {page_number}")
            print("=" * 80)

            print_text_preview(
                page=page,
                preview_lines=preview_lines,
            )

            print()

            text_lines = extract_text_lines(page)

            print_candidate_lines(
                text_lines=text_lines,
                min_font_size=min_font_size,
            )

            if show_all_lines:
                print()
                print_all_lines(text_lines)


def main() -> None:
    args = parse_args()

    inspect_pdf(
        pdf_path=args.pdf_path,
        start_page=args.start_page,
        end_page=args.end_page,
        min_font_size=args.min_font_size,
        preview_lines=args.preview_lines,
        show_all_lines=args.all_lines,
    )


if __name__ == "__main__":
    main()