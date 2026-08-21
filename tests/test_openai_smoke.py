from textbook_kb.knowledge_model import (
    FakeStructuredKnowledgeModelClient,
)
from textbook_kb.llm_config import (
    OpenAIKnowledgeConfig,
)
from textbook_kb.openai_smoke import (
    SYNTHETIC_SMOKE_KNOWLEDGE_ID,
    OpenAISmokeResult,
    build_synthetic_openai_smoke_request,
    run_openai_synthetic_smoke,
)


def build_fake_response() -> dict:
    return {
        "summary": (
            "Variables represent values, and "
            "simple equations can be solved "
            "using inverse operations."
        ),
        "key_concepts": [
            "variable",
            "equation",
            "inverse operation",
        ],
        "definitions": [
            {
                "term": "variable",
                "definition": (
                    "A symbol representing "
                    "a value."
                ),
            },
        ],
        "formulas": [],
        "skills": [
            "solve a simple equation",
            "check a solution",
        ],
        "worked_example_patterns": [
            {
                "name": (
                    "solve a one-step equation"
                ),
                "problem_type": (
                    "simple linear equation"
                ),
                "when_to_use": (
                    "Use when one operation "
                    "must be undone to isolate "
                    "the variable."
                ),
                "steps": [
                    (
                        "Identify the operation "
                        "applied to the variable."
                    ),
                    (
                        "Apply the corresponding "
                        "inverse operation to "
                        "both sides."
                    ),
                    (
                        "Check the result by "
                        "substitution."
                    ),
                ],
            },
        ],
        "common_mistakes": [],
        "prerequisites": [],
        "student_friendly_explanations": [
            (
                "Think of both sides of an "
                "equation as staying balanced."
            ),
        ],
        "retrieval_keywords": [
            "variable",
            "simple equation",
            "inverse operation",
            "solve for x",
        ],
    }


def build_config() -> OpenAIKnowledgeConfig:
    return OpenAIKnowledgeConfig(
        model="synthetic-test-model",
        max_output_tokens=1000,
        timeout_seconds=10.0,
        max_retries=0,
    )


def test_synthetic_smoke_request_contains_only_synthetic_source() -> None:
    request = (
        build_synthetic_openai_smoke_request()
    )

    assert (
        request.knowledge_id
        == SYNTHETIC_SMOKE_KNOWLEDGE_ID
    )

    assert (
        request.source_file
        == "synthetic_smoke_test.pdf"
    )

    assert (
        request.page_numbers
        == [1]
    )

    assert (
        "A variable is a symbol"
        in request.source_text
    )


def test_smoke_runner_works_with_fake_client() -> None:
    fake_client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_fake_response()
            )
        )
    )

    result = (
        run_openai_synthetic_smoke(
            config=build_config(),
            model_client=fake_client,
        )
    )

    assert isinstance(
        result,
        OpenAISmokeResult,
    )

    assert (
        result.model
        == "synthetic-test-model"
    )

    assert (
        result.knowledge_id
        == SYNTHETIC_SMOKE_KNOWLEDGE_ID
    )


def test_smoke_runner_extracts_expected_counts() -> None:
    fake_client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_fake_response()
            )
        )
    )

    result = (
        run_openai_synthetic_smoke(
            config=build_config(),
            model_client=fake_client,
        )
    )

    assert (
        result.key_concept_count
        == 3
    )

    assert (
        result.definition_count
        == 1
    )

    assert (
        result.formula_count
        == 0
    )

    assert (
        result.skill_count
        == 2
    )

    assert (
        result.worked_example_pattern_count
        == 1
    )


def test_fake_smoke_has_no_provider_usage_metadata() -> None:
    fake_client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_fake_response()
            )
        )
    )

    result = (
        run_openai_synthetic_smoke(
            config=build_config(),
            model_client=fake_client,
        )
    )

    assert (
        result.input_tokens
        is None
    )

    assert (
        result.output_tokens
        is None
    )

    assert (
        result.total_tokens
        is None
    )

    assert (
        result.response_id
        is None
    )


def test_public_smoke_result_contains_no_source_text() -> None:
    fake_client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_fake_response()
            )
        )
    )

    request = (
        build_synthetic_openai_smoke_request()
    )

    result = (
        run_openai_synthetic_smoke(
            config=build_config(),
            model_client=fake_client,
        )
    )

    public_result = (
        result.to_public_dict()
    )

    serialized = str(
        public_result
    )

    assert (
        request.source_text
        not in serialized
    )

    assert (
        "source_text"
        not in public_result
    )

    assert (
        "raw_response"
        not in public_result
    )

    assert (
        "api_key"
        not in public_result
    )


def test_smoke_runner_builds_one_model_request() -> None:
    fake_client = (
        FakeStructuredKnowledgeModelClient(
            default_response=(
                build_fake_response()
            )
        )
    )

    run_openai_synthetic_smoke(
        config=build_config(),
        model_client=fake_client,
    )

    assert len(
        fake_client.received_bundles
    ) == 1