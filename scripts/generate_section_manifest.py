from __future__ import annotations

import argparse
from pathlib import Path

from textbook_kb.metadata import (
    find_textbook_metadata,
    load_section_manifest,
    load_textbook_metadata,
    save_section_manifest,
    validate_section_manifest,
)
from textbook_kb.structure_manifest import (
    generate_section_manifest_from_pdf,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Automatically extract textbook structure "
            "and generate a validated SectionManifest."
        )
    )

    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to the textbook PDF.",
    )

    parser.add_argument(
        "--textbook-config",
        type=Path,
        default=Path("config/textbooks.json"),
        help=(
            "Path to textbook metadata configuration. "
            "Defaults to config/textbooks.json."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Output path for the generated SectionManifest. "
            "Defaults to "
            "data/intermediate/<pdf_stem>_sections.json."
        ),
    )

    parser.add_argument(
        "--include-large-font-headings",
        action="store_true",
        help=(
            "Allow large-font-only candidates to participate "
            "in structural heading classification."
        ),
    )

    parser.add_argument(
        "--min-body-font-size",
        type=float,
        default=14.0,
        help="Minimum font size for BODY heading detection.",
    )

    parser.add_argument(
        "--max-body-top",
        type=float,
        default=180.0,
        help=(
            "Maximum bbox top coordinate for BODY "
            "heading detection."
        ),
    )

    parser.add_argument(
        "--min-body-font-gap",
        type=float,
        default=2.0,
        help=(
            "Minimum font-size gap when selecting "
            "between BODY-like occurrences."
        ),
    )

    parser.add_argument(
        "--min-boundary-font-size",
        type=float,
        default=18.0,
        help=(
            "Minimum font size for chapter terminal "
            "boundary detection."
        ),
    )

    parser.add_argument(
        "--max-boundary-top",
        type=float,
        default=180.0,
        help=(
            "Maximum bbox top coordinate for chapter "
            "terminal boundary detection."
        ),
    )

    parser.add_argument(
        "--min-title-font-size",
        type=float,
        default=14.0,
        help="Minimum font size for Section title extraction.",
    )

    parser.add_argument(
        "--max-title-vertical-gap",
        type=float,
        default=100.0,
        help=(
            "Maximum vertical distance between a "
            "Section number and title."
        ),
    )

    parser.add_argument(
        "--max-title-top",
        type=float,
        default=200.0,
        help=(
            "Maximum bbox top coordinate for a possible "
            "Section title."
        ),
    )

    return parser.parse_args()


def resolve_output_path(
    pdf_path: Path,
    output_path: Path | None,
) -> Path:
    if output_path is not None:
        return output_path

    return (
        Path("data/intermediate")
        / f"{pdf_path.stem}_sections.json"
    )


def main() -> None:
    args = parse_args()

    output_path = resolve_output_path(
        pdf_path=args.pdf_path,
        output_path=args.output,
    )

    manifest = generate_section_manifest_from_pdf(
        pdf_path=args.pdf_path,
        regex_only=not args.include_large_font_headings,
        min_body_font_size=args.min_body_font_size,
        max_body_top=args.max_body_top,
        min_body_font_gap=args.min_body_font_gap,
        min_boundary_font_size=args.min_boundary_font_size,
        max_boundary_top=args.max_boundary_top,
        min_title_font_size=args.min_title_font_size,
        max_title_vertical_gap=args.max_title_vertical_gap,
        max_title_top=args.max_title_top,
    )

    textbooks = load_textbook_metadata(
        args.textbook_config
    )

    textbook_metadata = find_textbook_metadata(
        textbooks=textbooks,
        source_file=manifest.source_file,
    )

    validate_section_manifest(
        manifest=manifest,
        textbook_metadata=textbook_metadata,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    save_section_manifest(
        manifest=manifest,
        output_path=output_path,
    )

    loaded_manifest = load_section_manifest(
        output_path
    )

    validate_section_manifest(
        manifest=loaded_manifest,
        textbook_metadata=textbook_metadata,
    )

    if loaded_manifest != manifest:
        raise ValueError(
            "Saved SectionManifest does not match "
            "the generated manifest after reload."
        )

    print(
        f"Source PDF: "
        f"{args.pdf_path}"
    )

    print(
        f"Textbook: "
        f"{textbook_metadata.textbook}"
    )

    print(
        f"Course: "
        f"{textbook_metadata.course_id} "
        f"{textbook_metadata.course_name}"
    )

    print(
        f"Generated sections: "
        f"{len(manifest.sections)}"
    )

    print(
        f"Output: "
        f"{output_path}"
    )

    print()
    print("First sections:")

    for section in manifest.sections[:5]:
        print(
            f"  {section.section} "
            f"[pages {section.page_start}-{section.page_end}]"
        )

    print()
    print("Manifest validation: PASS")
    print("Save/load round trip: PASS")


if __name__ == "__main__":
    main()