import json

from textbook_kb.metadata import (
    TextbookMetadata,
    find_textbook_metadata,
    load_textbook_metadata,
)




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


def test_find_textbook_metadata_returns_matching_record():
    textbooks = [
        TextbookMetadata(
            grade=11,
            course_id="MCR3U",
            course_name="Functions",
            textbook="MCR3U Functions",
            source_file="MCR3U_Functions.pdf",
        ),
        TextbookMetadata(
            grade=12,
            course_id="MHF4U",
            course_name="Advanced Functions",
            textbook="MHF4U Advanced Functions",
            source_file="MHF4U_Advanced_Functions.pdf",
        ),
    ]

    textbook = find_textbook_metadata(
        textbooks,
        "MCR3U_Functions.pdf",
    )

    assert textbook.grade == 11
    assert textbook.course_id == "MCR3U"


def test_find_textbook_metadata_raises_when_missing():
    textbooks = [
        TextbookMetadata(
            grade=11,
            course_id="MCR3U",
            course_name="Functions",
            textbook="MCR3U Functions",
            source_file="MCR3U_Functions.pdf",
        )
    ]

    try:
        find_textbook_metadata(
            textbooks,
            "Unknown.pdf",
        )
    except ValueError as error:
        assert "No textbook metadata found" in str(error)
    else:
        raise AssertionError("Expected ValueError")


def test_find_textbook_metadata_raises_when_duplicate():
    textbooks = [
        TextbookMetadata(
            grade=11,
            course_id="MCR3U",
            course_name="Functions",
            textbook="MCR3U Functions",
            source_file="MCR3U_Functions.pdf",
        ),
        TextbookMetadata(
            grade=11,
            course_id="MCR3U",
            course_name="Functions",
            textbook="Duplicate Record",
            source_file="MCR3U_Functions.pdf",
        ),
    ]

    try:
        find_textbook_metadata(
            textbooks,
            "MCR3U_Functions.pdf",
        )
    except ValueError as error:
        assert "Multiple textbook metadata records found" in str(error)
    else:
        raise AssertionError("Expected ValueError")
