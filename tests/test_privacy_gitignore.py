from __future__ import annotations

import subprocess
from pathlib import Path


PRIVATE_ARTIFACT_PATHS = (
    "data/raw/MCR3U_Functions.pdf",
    "data/intermediate/MCR3U_Functions_section_sources.json",
    "data/intermediate/MCR3U_Functions_source_pages.json",
    "data/intermediate/structure_headings_debug.txt",
    "data/intermediate/pdf_text_extracted.txt",
    "data/processed/MCR3U_Functions_knowledge.json",
    "data/processed/MCR3U_Functions_knowledge_base.json",
)


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def assert_git_ignores(path: str) -> None:
    repo_root = get_repo_root()

    result = subprocess.run(
        [
            "git",
            "check-ignore",
            "-q",
            path,
        ],
        cwd=repo_root,
        check=False,
    )

    assert result.returncode == 0, (
        "Expected Git to ignore private or copyrighted artifact path: "
        f"{path}"
    )


def test_private_textbook_artifacts_are_gitignored() -> None:
    for path in PRIVATE_ARTIFACT_PATHS:
        assert_git_ignores(path)