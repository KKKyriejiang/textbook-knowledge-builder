from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from textbook_kb.structure_boundaries import (
    StructureBoundary,
    StructureBoundaryKind,
    detect_structure_boundaries,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect detected chapter terminal boundaries "
            "such as Chapter Review, Chapter Self-Test, "
            "and Chapter Task."
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
        help="First PDF page to inspect.",
    )

    parser.add_argument(
        "--end-page",
        type=int,
        default=None,
        help=(
            "Last PDF page to inspect. "
            "Defaults to the final PDF page."
        ),
    )

    parser.add_argument(
        "--min-boundary-font-size",
        type=float,
        default=18.0,
        help=(
            "Minimum font size for a chapter terminal "
            "boundary."
        ),
    )

    parser.add_argument(
        "--max-boundary-top",
        type=float,
        default=180.0,
        help=(
            "Maximum bbox top coordinate for a chapter "
            "terminal boundary."
        ),
    )

    return parser.parse_args()


def print_boundary(
    boundary: StructureBoundary,
) -> None:
    candidate = boundary.source_candidate

    print()
    print("=" * 80)

    print(
        f"BOUNDARY: "
        f"{boundary.kind.value}"
    )

    print(
        f"PDF page: "
        f"{boundary.page_number}"
    )

    print(
        f"Text: "
        f"{boundary.text}"
    )

    print(
        f"Font size: "
        f"{candidate.font_size:.1f} pt"
    )

    print(
        f"Fonts: "
        f"{', '.join(candidate.fonts)}"
    )

    print(
        f"bbox: "
        f"{candidate.bbox}"
    )


def print_summary(
    boundaries: tuple[StructureBoundary, ...],
) -> None:
    counter = Counter(
        boundary.kind
        for boundary in boundaries
    )

    print()
    print("=" * 80)
    print("BOUNDARY SUMMARY")
    print("=" * 80)

    print(
        f"Total boundaries: "
        f"{len(boundaries)}"
    )

    for kind in StructureBoundaryKind:
        print(
            f"{kind.value}: "
            f"{counter[kind]}"
        )


def main() -> None:
    args = parse_args()

    boundaries = detect_structure_boundaries(
        pdf_path=args.pdf_path,
        start_page=args.start_page,
        end_page=args.end_page,
        min_boundary_font_size=args.min_boundary_font_size,
        max_boundary_top=args.max_boundary_top,
    )

    print(
        f"PDF: "
        f"{args.pdf_path.name}"
    )

    print(
        f"Detected boundaries: "
        f"{len(boundaries)}"
    )

    for boundary in boundaries:
        print_boundary(
            boundary
        )

    print_summary(
        boundaries
    )


if __name__ == "__main__":
    main()