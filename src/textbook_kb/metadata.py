import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TextbookMetadata:
    """Metadata that describes a textbook as a whole."""

    grade: int
    course_id: str
    course_name: str
    textbook: str
    source_file: str


@dataclass(frozen=True, slots=True)
class SectionMetadata:
    """Metadata that describes a section within a textbook."""

    unit: str | None
    chapter: str | None
    section: str
    page_start: int
    page_end: int

    def __post_init__(self) -> None:
        if not self.section.strip():
            raise ValueError("Section name cannot be empty")

        if self.page_start < 1:
            raise ValueError("page_start must be at least 1")

        if self.page_end < self.page_start:
            raise ValueError(
                "page_end must be greater than or equal to page_start"
            )

def load_textbook_metadata(config_path: str | Path) -> list[TextbookMetadata]:
    """Load textbook metadata records from a JSON configuration file."""

    config_path = Path(config_path)

    with config_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return [
        TextbookMetadata(**item)
        for item in data["textbooks"]
    ]

def find_textbook_metadata(
    textbooks: list[TextbookMetadata],
    source_file: str,
) -> TextbookMetadata:
    """Find the textbook metadata associated with a source PDF filename."""

    matches = [
        textbook
        for textbook in textbooks
        if textbook.source_file == source_file
    ]

    if len(matches) == 0:
        raise ValueError(
            f"No textbook metadata found for source file: {source_file}"
        )

    if len(matches) > 1:
        raise ValueError(
            f"Multiple textbook metadata records found for source file: {source_file}"
        )

    return matches[0]