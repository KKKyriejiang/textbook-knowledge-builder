import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TextbookMetadata:
    """Metadata that describes a textbook as a whole."""

    grade: str
    course_id: str
    course_name: str
    textbook: str
    source_file: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("grade", self.grade),
            ("course_id", self.course_id),
            ("course_name", self.course_name),
            ("textbook", self.textbook),
            ("source_file", self.source_file),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{field_name} must be a non-empty string"
                )


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


@dataclass(frozen=True, slots=True)
class SectionManifest:
    """Section metadata records associated with one source textbook."""

    source_file: str
    sections: tuple[SectionMetadata, ...]

    def __post_init__(self) -> None:
        if not self.source_file.strip():
            raise ValueError("source_file cannot be empty")


def load_textbook_metadata(
    config_path: str | Path,
) -> list[TextbookMetadata]:
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
            f"Multiple textbook metadata records found for source file: "
            f"{source_file}"
        )

    return matches[0]


def validate_section_manifest(
    manifest: SectionManifest,
    textbook_metadata: TextbookMetadata,
) -> None:
    """Validate that a section manifest belongs to the textbook."""

    if manifest.source_file != textbook_metadata.source_file:
        raise ValueError(
            f"Section manifest source file {manifest.source_file} "
            f"does not match textbook source file "
            f"{textbook_metadata.source_file}"
        )


def save_section_manifest(
    manifest: SectionManifest,
    output_path: str | Path,
) -> None:
    """Save a section manifest to a JSON file."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "source_file": manifest.source_file,
        "sections": [
            asdict(section)
            for section in manifest.sections
        ],
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def load_section_manifest(
    input_path: str | Path,
) -> SectionManifest:
    """Load a section manifest from a JSON file."""

    input_path = Path(input_path)

    with input_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    sections = tuple(
        SectionMetadata(**item)
        for item in data["sections"]
    )

    return SectionManifest(
        source_file=data["source_file"],
        sections=sections,
    )
