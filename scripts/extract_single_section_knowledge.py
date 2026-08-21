from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from textbook_kb.controlled_extraction import (
    extract_single_section_local,
    list_controlled_sections,
    load_local_section_sources_json,
    select_controlled_section,
)
from textbook_kb.llm_config import (
    OPENAI_API_KEY_ENV,
    OpenAIKnowledgeConfig,
    openai_runtime_is_configured,
)
from textbook_kb.openai_model_client import (
    OpenAIStructuredKnowledgeModelClient,
)


DEFAULT_OUTPUT_PATH = (
    "data/processed/"
    "controlled_section_knowledge.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect local SectionSource records and perform "
            "a controlled one-section OpenAI knowledge extraction."
        )
    )

    parser.add_argument(
        "--section-sources",
        required=True,
        help=(
            "Path to the local-only Milestone 3 "
            "section_sources JSON."
        ),
    )

    parser.add_argument(
        "--list-sections",
        action="store_true",
        help=(
            "List section metadata only. "
            "No textbook text or API request is emitted."
        ),
    )

    parser.add_argument(
        "--section-index",
        type=int,
        help=(
            "Zero-based section index to inspect or extract."
        ),
    )

    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_PATH,
        help=(
            "Private local knowledge JSON output path."
        ),
    )

    parser.add_argument(
        "--confirm-api-call",
        action="store_true",
        help=(
            "Explicitly authorize exactly one real "
            "OpenAI API request for the selected section."
        ),
    )

    return parser.parse_args()


def print_sections(
    section_sources,
) -> None:
    infos = list_controlled_sections(
        section_sources
    )

    for info in infos:
        print(
            json.dumps(
                {
                    "index": info.index,
                    "unit": info.unit,
                    "chapter": (
                        info.chapter
                    ),
                    "section": (
                        info.section
                    ),
                    "page_start": (
                        info.page_start
                    ),
                    "page_end": (
                        info.page_end
                    ),
                    "page_count": (
                        info.page_count
                    ),
                },
                ensure_ascii=False,
            )
        )


def print_selected_section(
    section_source,
) -> None:
    metadata = (
        section_source
        .section_metadata
    )

    print(
        "selected_section="
        + json.dumps(
            {
                "unit": metadata.unit,
                "chapter": (
                    metadata.chapter
                ),
                "section": (
                    metadata.section
                ),
                "page_start": (
                    metadata.page_start
                ),
                "page_end": (
                    metadata.page_end
                ),
                "page_count": len(
                    section_source.pages
                ),
            },
            ensure_ascii=False,
        )
    )


def main() -> int:
    args = parse_args()

    try:
        section_sources = (
            load_local_section_sources_json(
                args.section_sources
            )
        )
    except Exception as exc:
        print(
            "section_source_load_status=failed "
            f"error_type={type(exc).__name__}",
            file=sys.stderr,
        )

        return 1

    print(
        "section_source_load_status=passed"
    )

    print(
        "section_count="
        f"{len(section_sources)}"
    )

    if args.list_sections:
        print_sections(
            section_sources
        )

        return 0

    if args.section_index is None:
        print(
            "error=section_index_required",
            file=sys.stderr,
        )

        print(
            "Use --list-sections first, then supply "
            "--section-index N.",
            file=sys.stderr,
        )

        return 2

    try:
        selected = (
            select_controlled_section(
                section_sources=(
                    section_sources
                ),
                section_index=(
                    args.section_index
                ),
            )
        )
    except Exception as exc:
        print(
            "section_selection_status=failed "
            f"error_type={type(exc).__name__}",
            file=sys.stderr,
        )

        return 2

    print(
        "section_selection_status=passed"
    )

    print_selected_section(
        selected
    )

    config = (
        OpenAIKnowledgeConfig
        .from_environment()
    )

    print(
        "model="
        f"{config.model}"
    )

    print(
        "output_path="
        f"{args.output}"
    )

    print(
        "api_key_configured="
        f"{openai_runtime_is_configured()}"
    )

    if not args.confirm_api_call:
        print(
            "mode=dry-run"
        )

        print(
            "api_call_count=0"
        )

        print(
            "The selected section source text has "
            "not been sent to any API."
        )

        return 0

    if not openai_runtime_is_configured():
        print(
            f"error={OPENAI_API_KEY_ENV}_required",
            file=sys.stderr,
        )

        return 2

    print(
        "mode=controlled-real-section-extraction"
    )

    print(
        "authorized_section_count=1"
    )

    print(
        "authorized_api_call_count=1"
    )

    try:
        model_client = (
            OpenAIStructuredKnowledgeModelClient(
                config=config
            )
        )

        result = (
            extract_single_section_local(
                section_source=selected,
                model_client=model_client,
                config=config,
                output_path=(
                    args.output
                ),
                project_root=Path.cwd(),
            )
        )

    except Exception as exc:
        print(
            "controlled_extraction_status=failed "
            f"error_type={type(exc).__name__}",
            file=sys.stderr,
        )

        return 1

    print(
        "controlled_extraction_status=passed"
    )

    print(
        json.dumps(
            result.to_public_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )

    print(
        "Review the local knowledge JSON before "
        "authorizing any multi-section extraction."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )