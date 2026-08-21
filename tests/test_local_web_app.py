import base64
from pathlib import Path

import pytest

from textbook_kb.local_web_app import (
    _decode_pdf_payload,
    _ensure_within_local_data,
    _resolve_project_path,
    review_local_knowledge_file,
    safe_uploaded_pdf_name,
)


def test_safe_uploaded_pdf_name_keeps_pdf_extension() -> None:
    assert (
        safe_uploaded_pdf_name(
            "MCR3U Functions.pdf"
        )
        == "MCR3U_Functions.pdf"
    )


def test_safe_uploaded_pdf_name_removes_directories() -> None:
    assert (
        safe_uploaded_pdf_name(
            r"C:\private\Book Name.pdf"
        )
        == "Book_Name.pdf"
    )


def test_safe_uploaded_pdf_name_rejects_non_pdf() -> None:
    with pytest.raises(
        ValueError,
        match=".pdf",
    ):
        safe_uploaded_pdf_name(
            "notes.txt"
        )


def test_decode_pdf_payload_accepts_pdf_bytes() -> None:
    data = b"%PDF-1.7\nsynthetic pdf bytes"

    encoded = base64.b64encode(
        data
    ).decode("ascii")

    assert (
        _decode_pdf_payload(
            encoded
        )
        == data
    )


def test_decode_pdf_payload_rejects_non_pdf_bytes() -> None:
    encoded = base64.b64encode(
        b"not a pdf"
    ).decode("ascii")

    with pytest.raises(
        ValueError,
        match="look like a PDF",
    ):
        _decode_pdf_payload(
            encoded
        )


def test_resolve_project_path_allows_project_child(
    tmp_path: Path,
) -> None:
    resolved = _resolve_project_path(
        tmp_path,
        "data/processed/synthetic_knowledge.json",
    )

    assert resolved == (
        tmp_path
        / "data"
        / "processed"
        / "synthetic_knowledge.json"
    ).resolve()


def test_resolve_project_path_rejects_parent_escape(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="inside the project",
    ):
        _resolve_project_path(
            tmp_path,
            "../outside.json",
        )


def test_ensure_within_local_data_accepts_processed_child(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "data"
        / "processed"
        / "synthetic_knowledge.json"
    )

    _ensure_within_local_data(
        tmp_path,
        path,
        "processed",
    )


def test_ensure_within_local_data_rejects_wrong_data_child(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "data"
        / "intermediate"
        / "synthetic_section_sources.json"
    )

    with pytest.raises(
        ValueError,
        match="data/processed",
    ):
        _ensure_within_local_data(
            tmp_path,
            path,
            "processed",
        )


def test_review_local_knowledge_file_rejects_unprotected_name(
    tmp_path: Path,
) -> None:
    processed = (
        tmp_path
        / "data"
        / "processed"
    )

    processed.mkdir(
        parents=True
    )

    unsafe_path = (
        processed
        / "output.json"
    )

    unsafe_path.write_text(
        "{}",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="private knowledge naming convention",
    ):
        review_local_knowledge_file(
            tmp_path,
            {
                "input_path": (
                    "data/processed/output.json"
                ),
            },
        )
