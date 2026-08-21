from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import fitz


STRUCTURE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "unit",
        re.compile(r"^unit\b", re.IGNORECASE),
    ),
    (
        "chapter",
        re.compile(r"^chapter\b", re.IGNORECASE),
    ),
    (
        "section",
        re.compile(r"^section\b", re.IGNORECASE),
    ),
    (
        "numbered heading",
        re.compile(r"^\d+\.\d+(?:\.\d+)?(?:\s|$)"),
    ),
)


@dataclass(frozen=True, slots=True)
class StructureCandidate:
    page_number: int
    text: str
    font_size: float
    fonts: tuple[str, ...]
    bbox: tuple[float, float, float, float]
    reasons: tuple[str, ...]


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def validate_pdf_path(pdf_path: Path) -> None:
    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF file does not exist: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            f"Expected a PDF file: {pdf_path}"
        )


def validate_page_range(
    start_page: int,
    end_page: int,
    page_count: int,
) -> None:
    if start_page < 1:
        raise ValueError(
            "start_page must be at least 1."
        )

    if end_page < start_page:
        raise ValueError(
            "end_page must be greater than or equal to start_page."
        )

    if start_page > page_count:
        raise ValueError(
            f"start_page {start_page} exceeds "
            f"PDF page count {page_count}."
        )


def validate_candidate_settings(
    min_font_size: float,
    max_heading_length: int,
) -> None:
    if min_font_size <= 0:
        raise ValueError(
            "min_font_size must be greater than 0."
        )

    if max_heading_length < 1:
        raise ValueError(
            "max_heading_length must be at least 1."
        )


def match_structure_patterns(
    text: str,
) -> tuple[str, ...]:
    matches: list[str] = []

    for label, pattern in STRUCTURE_PATTERNS:
        if pattern.search(text):
            matches.append(label)

    return tuple(matches)


def extract_page_structure_candidates(
    page: fitz.Page,
    page_number: int,
    min_font_size: float = 14.0,
    max_heading_length: int = 120,
    regex_only: bool = False,
) -> tuple[StructureCandidate, ...]:
    if page_number < 1:
        raise ValueError(
            "page_number must be at least 1."
        )

    validate_candidate_settings(
        min_font_size=min_font_size,
        max_heading_length=max_heading_length,
    )

    page_dict = page.get_text("dict")

    candidates: list[StructureCandidate] = []

    for block in page_dict.get("blocks", []):
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

            fonts = tuple(
                sorted(
                    {
                        str(span.get("font", "unknown"))
                        for span in spans
                    }
                )
            )

            raw_bbox = line.get(
                "bbox",
                (0.0, 0.0, 0.0, 0.0),
            )

            bbox = tuple(
                round(float(value), 1)
                for value in raw_bbox
            )

            pattern_reasons = list(
                match_structure_patterns(text)
            )

            is_large_font_candidate = (
                font_size >= min_font_size
                and len(text) <= max_heading_length
            )

            if (
                is_large_font_candidate
                and not regex_only
            ):
                pattern_reasons.append(
                    "large font"
                )

            if not pattern_reasons:
                continue

            candidates.append(
                StructureCandidate(
                    page_number=page_number,
                    text=text,
                    font_size=font_size,
                    fonts=fonts,
                    bbox=bbox,
                    reasons=tuple(pattern_reasons),
                )
            )

    return tuple(candidates)


def scan_structure_candidates(
    pdf_path: Path,
    start_page: int = 1,
    end_page: int | None = None,
    min_font_size: float = 14.0,
    max_heading_length: int = 120,
    regex_only: bool = False,
) -> tuple[StructureCandidate, ...]:
    validate_pdf_path(pdf_path)

    validate_candidate_settings(
        min_font_size=min_font_size,
        max_heading_length=max_heading_length,
    )

    all_candidates: list[StructureCandidate] = []

    with fitz.open(pdf_path) as document:
        page_count = document.page_count

        actual_end_page = (
            page_count
            if end_page is None
            else min(end_page, page_count)
        )

        validate_page_range(
            start_page=start_page,
            end_page=actual_end_page,
            page_count=page_count,
        )

        for page_number in range(
            start_page,
            actual_end_page + 1,
        ):
            page = document.load_page(
                page_number - 1
            )

            page_candidates = (
                extract_page_structure_candidates(
                    page=page,
                    page_number=page_number,
                    min_font_size=min_font_size,
                    max_heading_length=max_heading_length,
                    regex_only=regex_only,
                )
            )

            all_candidates.extend(
                page_candidates
            )

    return tuple(all_candidates)