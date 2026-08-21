from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from textbook_kb.knowledge_extraction import (
    KnowledgeExtractionRequest,
    KnowledgeExtractionResult,
)
from textbook_kb.knowledge_prompt import (
    KnowledgePromptBundle,
    build_knowledge_prompt_bundle,
)
from textbook_kb.knowledge_response import (
    parse_knowledge_response_payload,
)
from textbook_kb.knowledge_spec import (
    DEFAULT_KNOWLEDGE_EXTRACTION_SPEC,
    KnowledgeExtractionSpec,
)


def _require_non_empty_string(
    value: str,
    field_name: str,
) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise ValueError(
            f"{field_name} must be a non-empty string."
        )


@runtime_checkable
class StructuredKnowledgeModelClient(Protocol):
    """
    Provider-independent contract for a model client.

    A concrete client receives a fully prepared KnowledgePromptBundle
    and returns one parsed structured response object.

    Future implementations may call:
      - OpenAI,
      - another hosted provider,
      - a local model,
      - or an offline fake model.

    The core extraction pipeline does not need to know which provider
    produced the structured response.
    """

    def generate(
        self,
        bundle: KnowledgePromptBundle,
    ) -> Mapping[str, Any]:
        ...


@dataclass
class ModelKnowledgeExtractor:
    """
    KnowledgeExtractor implementation backed by a structured model client.

    Flow:

        KnowledgeExtractionRequest
            ->
        KnowledgePromptBundle
            ->
        StructuredKnowledgeModelClient
            ->
        structured response payload
            ->
        strict response parser
            ->
        SectionKnowledge
            ->
        KnowledgeExtractionResult
    """

    client: StructuredKnowledgeModelClient
    extractor_name: str
    spec: KnowledgeExtractionSpec = (
        DEFAULT_KNOWLEDGE_EXTRACTION_SPEC
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.client,
            StructuredKnowledgeModelClient,
        ):
            raise TypeError(
                "client must implement the "
                "StructuredKnowledgeModelClient protocol."
            )

        _require_non_empty_string(
            self.extractor_name,
            "extractor_name",
        )

        if not isinstance(
            self.spec,
            KnowledgeExtractionSpec,
        ):
            raise TypeError(
                "spec must be a "
                "KnowledgeExtractionSpec object."
            )

    def extract(
        self,
        request: KnowledgeExtractionRequest,
    ) -> KnowledgeExtractionResult:
        if not isinstance(
            request,
            KnowledgeExtractionRequest,
        ):
            raise TypeError(
                "request must be a "
                "KnowledgeExtractionRequest object."
            )

        bundle = (
            build_knowledge_prompt_bundle(
                request=request,
                spec=self.spec,
            )
        )

        payload = self.client.generate(
            bundle
        )

        if not isinstance(
            payload,
            Mapping,
        ):
            raise TypeError(
                "Structured model client must return "
                "a mapping object."
            )

        knowledge = (
            parse_knowledge_response_payload(
                payload=payload,
                spec=self.spec,
            )
        )

        return KnowledgeExtractionResult(
            knowledge=knowledge,
            extractor_name=(
                self.extractor_name
            ),
        )


@dataclass
class FakeStructuredKnowledgeModelClient:
    """
    Deterministic offline model client used for integration testing.

    This class performs no network calls and contains no real textbook
    content. It simulates a structured-output-capable model provider.

    A default synthetic payload is returned for every request unless an
    explicit response has been registered for a knowledge_id.
    """

    default_response: Mapping[
        str,
        Any
    ]
    responses_by_knowledge_id: dict[
        str,
        Mapping[str, Any]
    ] = field(
        default_factory=dict
    )

    received_bundles: list[
        KnowledgePromptBundle
    ] = field(
        default_factory=list,
        init=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.default_response,
            Mapping,
        ):
            raise TypeError(
                "default_response must be a mapping."
            )

        if not isinstance(
            self.responses_by_knowledge_id,
            dict,
        ):
            raise TypeError(
                "responses_by_knowledge_id must "
                "be a dictionary."
            )

        for knowledge_id, response in (
            self.responses_by_knowledge_id.items()
        ):
            _require_non_empty_string(
                knowledge_id,
                "responses_by_knowledge_id key",
            )

            if not isinstance(
                response,
                Mapping,
            ):
                raise TypeError(
                    "Each registered fake response "
                    "must be a mapping."
                )

    def generate(
        self,
        bundle: KnowledgePromptBundle,
    ) -> Mapping[str, Any]:
        if not isinstance(
            bundle,
            KnowledgePromptBundle,
        ):
            raise TypeError(
                "bundle must be a "
                "KnowledgePromptBundle object."
            )

        self.received_bundles.append(
            bundle
        )

        response = (
            self.responses_by_knowledge_id.get(
                bundle.knowledge_id,
                self.default_response,
            )
        )

        return copy.deepcopy(
            response
        )