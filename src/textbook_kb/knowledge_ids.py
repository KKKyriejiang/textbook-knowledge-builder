from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Sequence

from textbook_kb.metadata import (
    SectionMetadata,
    TextbookMetadata,
)


KNOWLEDGE_ID_HASH_LENGTH = 12
TRACE_ID_HASH_LENGTH = 10
MAX_SLUG_LENGTH = 32


def _require_non_empty_string(
    value: str,
    field_name: str,
) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{field_name} must be a non-empty string."
        )


def _normalize_identity_text(value: str) -> str:
    """
    Normalize metadata text before hashing.

    The normalization makes IDs stable against insignificant differences
    such as surrounding whitespace, repeated whitespace, and letter case.
    """

    _require_non_empty_string(
        value,
        "identity value",
    )

    normalized = unicodedata.normalize(
        "NFKC",
        value,
    )

    normalized = " ".join(
        normalized.strip().casefold().split()
    )

    return normalized


def _normalize_optional_identity_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return _normalize_identity_text(value)


def _source_filename(
    source_file: str,
) -> str:
    """
    Return only the final source filename.

    This intentionally removes local directory paths so deterministic IDs
    do not expose machine-specific paths such as D:\\... or /home/....
    """

    _require_non_empty_string(
        source_file,
        "source_file",
    )

    normalized_path = source_file.replace(
        "\\",
        "/",
    )

    filename = normalized_path.rsplit(
        "/",
        1,
    )[-1]

    _require_non_empty_string(
        filename,
        "source filename",
    )

    return filename


def _slugify(
    value: str,
    fallback: str,
    max_length: int = MAX_SLUG_LENGTH,
) -> str:
    """
    Create a short ASCII-safe human-readable ID component.

    The cryptographic hash provides uniqueness, so the slug is only a
    readable hint and may be truncated.
    """

    normalized = unicodedata.normalize(
        "NFKD",
        value,
    )

    ascii_text = normalized.encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    slug = re.sub(
        r"[^a-zA-Z0-9]+",
        "-",
        ascii_text,
    )

    slug = slug.strip("-").lower()

    if not slug:
        slug = fallback

    return slug[:max_length].rstrip("-")


def _stable_hash(
    payload: dict[str, object],
    length: int,
) -> str:
    canonical_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    digest = hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()

    return digest[:length]


def build_knowledge_identity_payload(
    textbook_metadata: TextbookMetadata,
    section_metadata: SectionMetadata,
) -> dict[str, object]:
    """
    Build the canonical metadata payload used for knowledge identity.

    Raw textbook text and page text are intentionally excluded.

    Page ranges are also excluded from the identity. Small corrections to
    section boundaries therefore do not automatically create a new
    knowledge_id for the same logical textbook section.
    """

    if not isinstance(
        textbook_metadata,
        TextbookMetadata,
    ):
        raise TypeError(
            "textbook_metadata must be a TextbookMetadata object."
        )

    if not isinstance(
        section_metadata,
        SectionMetadata,
    ):
        raise TypeError(
            "section_metadata must be a SectionMetadata object."
        )

    return {
        "grade": _normalize_identity_text(
            textbook_metadata.grade
        ),
        "course_id": _normalize_identity_text(
            textbook_metadata.course_id
        ),
        "course_name": _normalize_identity_text(
            textbook_metadata.course_name
        ),
        "textbook": _normalize_identity_text(
            textbook_metadata.textbook
        ),
        "source_file": _normalize_identity_text(
            _source_filename(
                textbook_metadata.source_file
            )
        ),
        "unit": _normalize_optional_identity_text(
            section_metadata.unit
        ),
        "chapter": _normalize_optional_identity_text(
            section_metadata.chapter
        ),
        "section": _normalize_identity_text(
            section_metadata.section
        ),
    }


def generate_knowledge_id(
    textbook_metadata: TextbookMetadata,
    section_metadata: SectionMetadata,
) -> str:
    """
    Generate a deterministic ID for one logical textbook section.

    Example:
        kb-math10-2-1-solving-linear-equations-a1b2c3d4e5f6
    """

    payload = build_knowledge_identity_payload(
        textbook_metadata,
        section_metadata,
    )

    digest = _stable_hash(
        payload,
        KNOWLEDGE_ID_HASH_LENGTH,
    )

    course_slug = _slugify(
        textbook_metadata.course_id,
        fallback="course",
        max_length=20,
    )

    section_slug = _slugify(
        section_metadata.section,
        fallback="section",
    )

    return (
        f"kb-{course_slug}-"
        f"{section_slug}-"
        f"{digest}"
    )


def generate_page_trace_id(
    knowledge_id: str,
    source_file: str,
    page_number: int,
) -> str:
    """
    Generate one deterministic short trace ID for one source page.
    """

    _require_non_empty_string(
        knowledge_id,
        "knowledge_id",
    )

    _require_non_empty_string(
        source_file,
        "source_file",
    )

    if (
        not isinstance(page_number, int)
        or isinstance(page_number, bool)
        or page_number < 1
    ):
        raise ValueError(
            "page_number must be a positive integer."
        )

    payload = {
        "knowledge_id": knowledge_id,
        "source_file": _normalize_identity_text(
            _source_filename(source_file)
        ),
        "page_number": page_number,
    }

    digest = _stable_hash(
        payload,
        TRACE_ID_HASH_LENGTH,
    )

    return (
        f"tr-p{page_number}-{digest}"
    )


def generate_page_trace_ids(
    knowledge_id: str,
    source_file: str,
    page_numbers: Sequence[int],
) -> list[str]:
    """
    Generate page-level trace IDs in the same order as page_numbers.

    The resulting trace_ids list aligns positionally with provenance
    page_numbers.
    """

    if not isinstance(
        page_numbers,
        Sequence,
    ):
        raise TypeError(
            "page_numbers must be a sequence of integers."
        )

    if not page_numbers:
        raise ValueError(
            "page_numbers must contain at least one page number."
        )

    normalized_page_numbers = list(
        page_numbers
    )

    if any(
        not isinstance(page_number, int)
        or isinstance(page_number, bool)
        or page_number < 1
        for page_number in normalized_page_numbers
    ):
        raise ValueError(
            "page_numbers must contain positive integers."
        )

    if normalized_page_numbers != sorted(
        set(normalized_page_numbers)
    ):
        raise ValueError(
            "page_numbers must be unique and sorted "
            "in ascending order."
        )

    return [
        generate_page_trace_id(
            knowledge_id=knowledge_id,
            source_file=source_file,
            page_number=page_number,
        )
        for page_number in normalized_page_numbers
    ]