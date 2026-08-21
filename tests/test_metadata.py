from textbook_kb.metadata import TextbookMetadata
import json

from textbook_kb.metadata import (
    TextbookMetadata,
    load_textbook_metadata,
)

def test_textbook_metadata_stores_expected_fields():
    metadata = TextbookMetadata(
        grade=11,
        course_id="MCR3U",
        course_name="Functions",
        textbook="MCR3U Functions",
        source_file="MCR3U_Functions.pdf",
    )

    assert metadata.grade == 11
    assert metadata.course_id == "MCR3U"
    assert metadata.course_name == "Functions"
    assert metadata.textbook == "MCR3U Functions"
    assert metadata.source_file == "MCR3U_Functions.pdf"




def test_textbook_metadata_stores_expected_fields():
    metadata = TextbookMetadata(
        grade=11,
        course_id="MCR3U",
        course_name="Functions",
        textbook="MCR3U Functions",
        source_file="MCR3U_Functions.pdf",
    )

    assert metadata.grade == 11
    assert metadata.course_id == "MCR3U"
    assert metadata.course_name == "Functions"
    assert metadata.textbook == "MCR3U Functions"
    assert metadata.source_file == "MCR3U_Functions.pdf"


def test_load_textbook_metadata(tmp_path):
    config = {
        "textbooks": [
            {
                "grade": 11,
                "course_id": "MCR3U",
                "course_name": "Functions",
                "textbook": "MCR3U Functions",
                "source_file": "MCR3U_Functions.pdf",
            }
        ]
    }

    config_path = tmp_path / "textbooks.json"
    config_path.write_text(
        json.dumps(config),
        encoding="utf-8",
    )

    textbooks = load_textbook_metadata(config_path)

    assert len(textbooks) == 1

    textbook = textbooks[0]

    assert textbook.grade == 11
    assert textbook.course_id == "MCR3U"
    assert textbook.course_name == "Functions"
    assert textbook.source_file == "MCR3U_Functions.pdf"