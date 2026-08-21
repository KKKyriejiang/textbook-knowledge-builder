from __future__ import annotations

import argparse
from pathlib import Path

from textbook_kb.local_web_app import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    run_local_web_app,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the local Textbook Knowledge Builder web UI."
        )
    )

    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="Host interface for the local web UI.",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Port for the local web UI.",
    )

    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the UI in the default browser.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    run_local_web_app(
        project_root=Path.cwd(),
        host=args.host,
        port=args.port,
        open_browser=args.open_browser,
    )


if __name__ == "__main__":
    main()
