import json
from dataclasses import dataclass
from typing import Any

import pytest

from textbook_kb.knowledge_extraction import (
    KnowledgeExtractionRequest,
)
from textbook_kb.knowledge_model import (
    ModelKnowledgeExtractor,
    StructuredKnowledgeModelClient,
)
from textbook_kb.knowledge_prompt import (
    build_knowledge_prompt_bundle,
)
from textbook_kb.llm_config import (
    OpenAIKnowledgeConfig,
)
from textbook_kb.openai_model_client import (
    OPENAI_KNOWLEDGE_SCHEMA_NAME,
    OpenAIKnowledgeClientError,
    OpenAIKnowledgeResponseError,
    OpenAIKnowledgeUsage,
    OpenAIStructuredKnowledgeModelClient,
)


def build_valid_response_payload() -> dict:
    return {
        "summary": (
            "Synthetic derived knowledge about "
            "linear equations."
        ),
        "key_concepts": [
            "linear equation",
            "inverse operations",
        ],
        "definitions": [
            {
                "term": "linear equation",
                "definition": (
                    "A synthetic definition used "
                    "only for testing."
                ),
            },
        ],
        "formulas": [],
        "skills": [
            "solve a synthetic equation",
        ],
        "worked_example_patterns": [],
        "common_mistakes": [],
        "prerequisites": [],
        "student_friendly_explanations": [
            (
                "A synthetic explanation for "
                "integration testing."
            ),
        ],
        "retrieval_keywords": [
            "linear equation",
            "solve for x",
        ],
    }


def build_request() -> KnowledgeExtractionRequest:
    return KnowledgeExtractionRequest(
        knowledge_id=(
            "kb-math10-linear-equations-"
            "123456789abc"
        ),
        grade="10",
        course_id="MATH10",
        course_name=(
            "Synthetic Mathematics"
        ),
        textbook=(
            "Synthetic Algebra Textbook"
        ),
        unit="Unit 1",
        chapter="Chapter 2",
        section=(
            "2.1 Solving Linear Equations"
        ),
        page_start=10,
        page_end=11,
        source_file=(
            "synthetic_textbook.pdf"
        ),
        page_numbers=[
            10,
            11,
        ],
        source_text=(
            "--- PAGE 10 ---\n"
            "Synthetic private source page ten.\n\n"
            "--- PAGE 11 ---\n"
            "Synthetic private source page eleven."
        ),
        trace_ids=[
            "tr-p10-1234567890",
            "tr-p11-0987654321",
        ],
    )


@dataclass
class FakeUsage:
    input_tokens: int = 120
    output_tokens: int = 80
    total_tokens: int = 200


@dataclass
class FakeOpenAIResponse:
    output_text: str
    status: str = "completed"
    id: str = "resp_synthetic_123"
    usage: Any = None


class FakeResponsesResource:
    def __init__(
        self,
        response: (
            FakeOpenAIResponse
            | None
        ) = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[
            dict[str, Any]
        ] = []

    def create(
        self,
        **kwargs,
    ) -> FakeOpenAIResponse:
        self.calls.append(
            kwargs
        )

        if self.error is not None:
            raise self.error

        if self.response is None:
            raise RuntimeError(
                "Fake response is missing."
            )

        return self.response


class FakeOpenAISDKClient:
    def __init__(
        self,
        response: (
            FakeOpenAIResponse
            | None
        ) = None,
        error: Exception | None = None,
    ) -> None:
        self.responses = (
            FakeResponsesResource(
                response=response,
                error=error,
            )
        )


def build_fake_sdk_client(
) -> FakeOpenAISDKClient:
    response = FakeOpenAIResponse(
        output_text=json.dumps(
            build_valid_response_payload(),
            ensure_ascii=False,
        ),
        usage=FakeUsage(),
    )

    return FakeOpenAISDKClient(
        response=response
    )


def build_config() -> OpenAIKnowledgeConfig:
    return OpenAIKnowledgeConfig(
        model="synthetic-model",
        max_output_tokens=2500,
        timeout_seconds=30.0,
        max_retries=1,
    )


def test_openai_client_implements_protocol() -> None:
    client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=(
                build_fake_sdk_client()
            ),
        )
    )

    assert isinstance(
        client,
        StructuredKnowledgeModelClient,
    )


def test_generate_returns_mapping() -> None:
    request = build_request()

    bundle = (
        build_knowledge_prompt_bundle(
            request
        )
    )

    client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=(
                build_fake_sdk_client()
            ),
        )
    )

    payload = client.generate(
        bundle
    )

    assert isinstance(
        payload,
        dict,
    )

    assert (
        payload["summary"]
        == (
            "Synthetic derived knowledge "
            "about linear equations."
        )
    )


def test_openai_request_uses_expected_model() -> None:
    request = build_request()

    bundle = (
        build_knowledge_prompt_bundle(
            request
        )
    )

    fake_sdk = (
        build_fake_sdk_client()
    )

    client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=fake_sdk,
        )
    )

    client.generate(
        bundle
    )

    call = (
        fake_sdk
        .responses
        .calls[0]
    )

    assert (
        call["model"]
        == "synthetic-model"
    )


def test_openai_request_maps_prompts_correctly() -> None:
    request = build_request()

    bundle = (
        build_knowledge_prompt_bundle(
            request
        )
    )

    fake_sdk = (
        build_fake_sdk_client()
    )

    client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=fake_sdk,
        )
    )

    client.generate(
        bundle
    )

    call = (
        fake_sdk
        .responses
        .calls[0]
    )

    assert (
        call["instructions"]
        == bundle.messages[0].content
    )

    assert (
        call["input"]
        == bundle.messages[1].content
    )


def test_openai_request_uses_structured_output_schema() -> None:
    request = build_request()

    bundle = (
        build_knowledge_prompt_bundle(
            request
        )
    )

    fake_sdk = (
        build_fake_sdk_client()
    )

    client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=fake_sdk,
        )
    )

    client.generate(
        bundle
    )

    call = (
        fake_sdk
        .responses
        .calls[0]
    )

    response_format = (
        call["text"]["format"]
    )

    assert (
        response_format["type"]
        == "json_schema"
    )

    assert (
        response_format["name"]
        == OPENAI_KNOWLEDGE_SCHEMA_NAME
    )

    assert (
        response_format["strict"]
        is True
    )

    assert (
        response_format["schema"]
        == bundle.response_schema
    )


def test_openai_request_disables_response_storage() -> None:
    request = build_request()

    bundle = (
        build_knowledge_prompt_bundle(
            request
        )
    )

    fake_sdk = (
        build_fake_sdk_client()
    )

    client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=fake_sdk,
        )
    )

    client.generate(
        bundle
    )

    call = (
        fake_sdk
        .responses
        .calls[0]
    )

    assert (
        call["store"]
        is False
    )


def test_openai_request_applies_output_token_limit() -> None:
    request = build_request()

    bundle = (
        build_knowledge_prompt_bundle(
            request
        )
    )

    fake_sdk = (
        build_fake_sdk_client()
    )

    client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=fake_sdk,
        )
    )

    client.generate(
        bundle
    )

    call = (
        fake_sdk
        .responses
        .calls[0]
    )

    assert (
        call["max_output_tokens"]
        == 2500
    )


def test_client_captures_safe_usage_metadata() -> None:
    request = build_request()

    bundle = (
        build_knowledge_prompt_bundle(
            request
        )
    )

    client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=(
                build_fake_sdk_client()
            ),
        )
    )

    client.generate(
        bundle
    )

    assert client.last_usage == (
        OpenAIKnowledgeUsage(
            input_tokens=120,
            output_tokens=80,
            total_tokens=200,
        )
    )

    assert (
        client.last_response_id
        == "resp_synthetic_123"
    )


def test_usage_metadata_contains_no_prompt_text() -> None:
    request = build_request()

    bundle = (
        build_knowledge_prompt_bundle(
            request
        )
    )

    client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=(
                build_fake_sdk_client()
            ),
        )
    )

    client.generate(
        bundle
    )

    assert (
        request.source_text
        not in repr(
            client.last_usage
        )
    )


def test_model_extractor_works_with_openai_client() -> None:
    request = build_request()

    model_client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=(
                build_fake_sdk_client()
            ),
        )
    )

    extractor = ModelKnowledgeExtractor(
        client=model_client,
        extractor_name=(
            "openai-synthetic-test"
        ),
    )

    result = extractor.extract(
        request
    )

    assert (
        result.extractor_name
        == "openai-synthetic-test"
    )

    assert (
        result.knowledge.key_concepts
        == [
            "linear equation",
            "inverse operations",
        ]
    )


def test_incomplete_response_is_rejected() -> None:
    fake_response = (
        FakeOpenAIResponse(
            output_text="",
            status="incomplete",
            usage=FakeUsage(),
        )
    )

    fake_sdk = FakeOpenAISDKClient(
        response=fake_response
    )

    client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=fake_sdk,
        )
    )

    bundle = (
        build_knowledge_prompt_bundle(
            build_request()
        )
    )

    with pytest.raises(
        OpenAIKnowledgeResponseError,
        match="did not complete",
    ):
        client.generate(
            bundle
        )


def test_empty_output_is_rejected() -> None:
    fake_response = (
        FakeOpenAIResponse(
            output_text="   ",
            usage=FakeUsage(),
        )
    )

    client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=(
                FakeOpenAISDKClient(
                    response=fake_response
                )
            ),
        )
    )

    bundle = (
        build_knowledge_prompt_bundle(
            build_request()
        )
    )

    with pytest.raises(
        OpenAIKnowledgeResponseError,
        match="structured output text",
    ):
        client.generate(
            bundle
        )


def test_malformed_json_is_rejected() -> None:
    fake_response = (
        FakeOpenAIResponse(
            output_text=(
                '{"summary": "broken"'
            ),
            usage=FakeUsage(),
        )
    )

    client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=(
                FakeOpenAISDKClient(
                    response=fake_response
                )
            ),
        )
    )

    bundle = (
        build_knowledge_prompt_bundle(
            build_request()
        )
    )

    with pytest.raises(
        OpenAIKnowledgeResponseError,
        match="parsed as JSON",
    ):
        client.generate(
            bundle
        )


def test_json_array_root_is_rejected() -> None:
    fake_response = (
        FakeOpenAIResponse(
            output_text=json.dumps(
                [
                    build_valid_response_payload()
                ]
            ),
            usage=FakeUsage(),
        )
    )

    client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=(
                FakeOpenAISDKClient(
                    response=fake_response
                )
            ),
        )
    )

    bundle = (
        build_knowledge_prompt_bundle(
            build_request()
        )
    )

    with pytest.raises(
        OpenAIKnowledgeResponseError,
        match="root must be an object",
    ):
        client.generate(
            bundle
        )


def test_api_failure_is_wrapped_without_source_text() -> None:
    private_source = (
        build_request().source_text
    )

    fake_sdk = (
        FakeOpenAISDKClient(
            error=RuntimeError(
                "Synthetic provider failure "
                f"{private_source}"
            )
        )
    )

    client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=fake_sdk,
        )
    )

    bundle = (
        build_knowledge_prompt_bundle(
            build_request()
        )
    )

    with pytest.raises(
        OpenAIKnowledgeClientError,
    ) as exc_info:
        client.generate(
            bundle
        )

    assert (
        private_source
        not in str(
            exc_info.value
        )
    )

    assert (
        "RuntimeError"
        in str(
            exc_info.value
        )
    )


def test_fake_sdk_prevents_real_network_call() -> None:
    fake_sdk = (
        build_fake_sdk_client()
    )

    client = (
        OpenAIStructuredKnowledgeModelClient(
            config=build_config(),
            sdk_client=fake_sdk,
        )
    )

    bundle = (
        build_knowledge_prompt_bundle(
            build_request()
        )
    )

    client.generate(
        bundle
    )

    assert len(
        fake_sdk.responses.calls
    ) == 1