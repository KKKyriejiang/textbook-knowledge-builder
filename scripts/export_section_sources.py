from __future__ import annotations

import argparse
from pathlib import Path

from textbook_kb.metadata import (
    find_textbook_metadata,
    load_section_manifest,
    load_textbook_metadata,
    validate_section_manifest,
)
from textbook_kb.section_source_export import (
    build_section_sources_from_pdf,
    save_section_sources_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build local-only SectionSource JSON from a textbook PDF "
            "and a generated SectionManifest."
        )
    )

    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to the local textbook PDF.",
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to the SectionManifest JSON.",
    )

    parser.add_argument(
        "--textbook-config",
        type=Path,
        default=Path("config/textbooks.json"),
        help="Path to textbook metadata config.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Output path for local-only section sources JSON. "
            "Defaults to data/intermediate/<pdf_stem>_section_sources.json."
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
        / f"{pdf_path.stem}_section_sources.json"
    )


def main() -> None:
    args = parse_args()

    textbooks = load_textbook_metadata(args.textbook_config)
    manifest = load_section_manifest(args.manifest)

    textbook_metadata = find_textbook_metadata(
        textbooks=textbooks,
        source_file=manifest.source_file,
    )

    validate_section_manifest(
        manifest=manifest,
        textbook_metadata=textbook_metadata,
    )

    section_sources = build_section_sources_from_pdf(
        pdf_path=args.pdf_path,
        textbook_metadata=textbook_metadata,
        section_manifest=manifest,
    )

    output_path = resolve_output_path(
        pdf_path=args.pdf_path,
        output_path=args.output,
    )

    save_section_sources_json(
        section_sources=section_sources,
        output_path=output_path,
    )

    print(f"PDF: {args.pdf_path}")
    print(f"Manifest: {args.manifest}")
    print(f"Generated SectionSource records: {len(section_sources)}")
    print(f"Output: {output_path}")
    print()
    print("Privacy warning:")
    print(
        "This output contains extracted textbook text. "
        "Keep it local and do not commit it to a public GitHub repository."
    )


if __name__ == "__main__":
    main()