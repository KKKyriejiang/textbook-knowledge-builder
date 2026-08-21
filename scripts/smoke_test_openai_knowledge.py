from __future__ import annotations

import argparse
import json
import sys

from textbook_kb.llm_config import (
    OPENAI_API_KEY_ENV,
    OpenAIKnowledgeConfig,
    openai_runtime_is_configured,
)
from textbook_kb.openai_smoke import (
    run_openai_synthetic_smoke,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a controlled synthetic smoke test "
            "for the OpenAI knowledge extractor."
        )
    )

    parser.add_argument(
        "--confirm-api-call",
        action="store_true",
        help=(
            "Explicitly authorize exactly one "
            "real OpenAI API request."
        ),
    )

    return parser.parse_args()


def print_runtime_configuration(
    config: OpenAIKnowledgeConfig,
) -> None:
    public_config = (
        config.to_public_dict()
    )

    print(
        "OpenAI knowledge smoke-test configuration:"
    )

    print(
        json.dumps(
            public_config,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )

    print(
        "api_key_configured="
        f"{openai_runtime_is_configured()}"
    )


def main() -> int:
    args = parse_args()

    config = (
        OpenAIKnowledgeConfig
        .from_environment()
    )

    print_runtime_configuration(
        config
    )

    if not args.confirm_api_call:
        print(
            "mode=dry-run"
        )

        print(
            "api_call_count=0"
        )

        print(
            "To authorize one synthetic API call, run:"
        )

        print(
            "python "
            "scripts/smoke_test_openai_knowledge.py "
            "--confirm-api-call"
        )

        return 0

    if not openai_runtime_is_configured():
        print(
            f"error={OPENAI_API_KEY_ENV}_required",
            file=sys.stderr,
        )

        return 2

    print(
        "mode=real-synthetic-smoke-test"
    )

    print(
        "authorized_api_call_count=1"
    )

    try:
        result = (
            run_openai_synthetic_smoke(
                config=config
            )
        )
    except Exception as exc:
        print(
            "smoke_test_status=failed "
            f"error_type={type(exc).__name__}",
            file=sys.stderr,
        )

        return 1

    print(
        "smoke_test_status=passed"
    )

    print(
        json.dumps(
            result.to_public_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )