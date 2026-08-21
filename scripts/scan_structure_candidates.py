from __future__ import annotations

import argparse
import re
from collections import Counter
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
    reasons: tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan a textbook PDF for possible Unit, Chapter, "
            "and Section heading candidates."
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
        help="First PDF page to scan. Uses 1-based numbering.",
    )

    parser.add_argument(
        "--end-page",
        type=int,
        default=None,
        help=(
            "Last PDF page to scan. Uses 1-based numbering. "
            "Defaults to the final page."
        ),
    )

    parser.add_argument(
        "--min-font-size",
        type=float,
        default=14.0,
        help=(
            "Text at or above this font size is considered "
            "a possible heading."
        ),
    )

    parser.add_argument(
        "--max-heading-length",
        type=int,
        default=120,
        help=(
            "Maximum text length for a large-font line to be "
            "treated as a heading candidate."
        ),
    )

    parser.add_argument(
        "--regex-only",
        action="store_true",
        help=(
            "Only show candidates matching Unit, Chapter, "
            "Section, or numbered-heading patterns."
        ),
    )

    return parser.parse_args()


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


def match_structure_patterns(
    text: str,
) -> list[str]:
    matches: list[str] = []

    for label, pattern in STRUCTURE_PATTERNS:
        if pattern.search(text):
            matches.append(label)

    return matches


def extract_page_candidates(
    page: fitz.Page,
    page_number: int,
    min_font_size: float,
    max_heading_length: int,
    regex_only: bool,
) -> list[StructureCandidate]:
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

            reasons = match_structure_patterns(text)

            is_large_font_candidate = (
                font_size >= min_font_size
                and len(text) <= max_heading_length
            )

            if is_large_font_candidate and not regex_only:
                reasons.append("large font")

            if not reasons:
                continue

            candidates.append(
                StructureCandidate(
                    page_number=page_number,
                    text=text,
                    font_size=font_size,
                    fonts=fonts,
                    reasons=tuple(reasons),
                )
            )

    return candidates


def scan_pdf(
    pdf_path: Path,
    start_page: int,
    end_page: int | None,
    min_font_size: float,
    max_heading_length: int,
    regex_only: bool,
) -> list[StructureCandidate]:
    validate_pdf_path(pdf_path)

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

        print(f"PDF: {pdf_path.name}")
        print(f"Total PDF pages: {page_count}")
        print(
            f"Scanning PDF pages: "
            f"{start_page}-{actual_end_page}"
        )
        print(
            f"Large-font threshold: "
            f"{min_font_size:.1f} pt"
        )
        print()

        for page_number in range(
            start_page,
            actual_end_page + 1,
        ):
            page = document.load_page(
                page_number - 1
            )

            page_candidates = extract_page_candidates(
                page=page,
                page_number=page_number,
                min_font_size=min_font_size,
                max_heading_length=max_heading_length,
                regex_only=regex_only,
            )

            all_candidates.extend(page_candidates)

    return all_candidates


def print_candidates(
    candidates: list[StructureCandidate],
) -> None:
    if not candidates:
        print("No structure candidates found.")
        return

    current_page: int | None = None

    for candidate in candidates:
        if candidate.page_number != current_page:
            current_page = candidate.page_number

            print()
            print(
                f"--- PDF PAGE "
                f"{candidate.page_number} ---"
            )

        reasons = ", ".join(
            candidate.reasons
        )

        fonts = ", ".join(
            candidate.fonts
        )

        print(
            f"[{candidate.font_size:.1f} pt] "
            f"{candidate.text}"
        )
        print(
            f"    reason: {reasons}"
        )
        print(
            f"    font: {fonts}"
        )


def print_summary(
    candidates: list[StructureCandidate],
) -> None:
    reason_counter: Counter[str] = Counter()

    for candidate in candidates:
        reason_counter.update(
            candidate.reasons
        )

    candidate_pages = {
        candidate.page_number
        for candidate in candidates
    }

    print()
    print("=" * 80)
    print("SCAN SUMMARY")
    print("=" * 80)

    print(
        f"Total candidates: "
        f"{len(candidates)}"
    )

    print(
        f"Pages containing candidates: "
        f"{len(candidate_pages)}"
    )

    if reason_counter:
        print("Candidate reasons:")

        for reason, count in sorted(
            reason_counter.items()
        ):
            print(
                f"  {reason}: {count}"
            )


def main() -> None:
    args = parse_args()

    candidates = scan_pdf(
        pdf_path=args.pdf_path,
        start_page=args.start_page,
        end_page=args.end_page,
        min_font_size=args.min_font_size,
        max_heading_length=args.max_heading_length,
        regex_only=args.regex_only,
    )

    print_candidates(candidates)

    print_summary(candidates)


if __name__ == "__main__":
    main()