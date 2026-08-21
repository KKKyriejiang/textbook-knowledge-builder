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


def load_textbook_metadata(config_path: str | Path) -> list[TextbookMetadata]:
    """Load textbook metadata records from a JSON configuration file."""

    config_path = Path(config_path)

    with config_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return [
        TextbookMetadata(**item)
        for item in data["textbooks"]
    ]