from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from textbook_kb.knowledge_model import (
    StructuredKnowledgeModelClient,
)
from textbook_kb.knowledge_prompt import (
    KnowledgePromptBundle,
)
from textbook_kb.llm_config import (
    OpenAIKnowledgeConfig,
    load_openai_api_key,
)


OPENAI_KNOWLEDGE_SCHEMA_NAME = (
    "section_knowledge"
)


class OpenAIKnowledgeClientError(
    RuntimeError
):
    """
    Base error raised by the OpenAI structured knowledge client.

    Error messages intentionally avoid including prompt or response
    content because those values may contain private textbook material.
    """


class OpenAIKnowledgeResponseError(
    OpenAIKnowledgeClientError
):
    """
    Raised when an OpenAI response cannot be converted into the structured
    mapping required by StructuredKnowledgeModelClient.
    """


@dataclass(frozen=True)
class OpenAIKnowledgeUsage:
    """
    Safe token-usage metadata from one API response.

    This object contains counts only and never stores prompt or model
    response content.
    """

    input_tokens: int
    output_tokens: int
    total_tokens: int

    def __post_init__(self) -> None:
        for field_name, value in (
            (
                "input_tokens",
                self.input_tokens,
            ),
            (
                "output_tokens",
                self.output_tokens,
            ),
            (
                "total_tokens",
                self.total_tokens,
            ),
        ):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
            ):
                raise ValueError(
                    f"{field_name} must be a "
                    "non-negative integer."
                )


@dataclass
class OpenAIStructuredKnowledgeModelClient:
    """
    Real StructuredKnowledgeModelClient implementation using the
    OpenAI Responses API.

    The OpenAI SDK client is created lazily when sdk_client is omitted.
    Tests can inject a fake SDK client, keeping the test suite fully
    offline.

    Privacy properties:
      - API key is loaded only at runtime,
      - raw prompts are never logged,
      - raw responses are never persisted,
      - store=False is sent to the Responses API,
      - only parsed structured JSON is returned downstream.
    """

    config: OpenAIKnowledgeConfig = field(
        default_factory=(
            OpenAIKnowledgeConfig
        )
    )

    sdk_client: Any | None = field(
        default=None,
        repr=False,
    )

    last_usage: (
        OpenAIKnowledgeUsage
        | None
    ) = field(
        default=None,
        init=False,
    )

    last_response_id: (
        str
        | None
    ) = field(
        default=None,
        init=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.config,
            OpenAIKnowledgeConfig,
        ):
            raise TypeError(
                "config must be an "
                "OpenAIKnowledgeConfig object."
            )

        if self.sdk_client is None:
            self.sdk_client = (
                self._create_sdk_client()
            )

    def _create_sdk_client(
        self,
    ) -> Any:
        """
        Create the real OpenAI SDK client.

        Importing the SDK here keeps unit tests independent from the OpenAI
        package until real API integration is explicitly exercised.
        """

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "The OpenAI Python package is required "
                "for real API calls. Install it before "
                "creating a real OpenAI client."
            ) from exc

        api_key = load_openai_api_key()

        return OpenAI(
            api_key=api_key,
            timeout=(
                self.config.timeout_seconds
            ),
            max_retries=(
                self.config.max_retries
            ),
        )

    def _extract_prompts(
        self,
        bundle: KnowledgePromptBundle,
    ) -> tuple[str, str]:
        """
        Convert the provider-independent bundle into the system and user
        inputs expected by this OpenAI client.
        """

        system_messages = [
            message.content
            for message in bundle.messages
            if message.role == "system"
        ]

        user_messages = [
            message.content
            for message in bundle.messages
            if message.role == "user"
        ]

        if len(system_messages) != 1:
            raise OpenAIKnowledgeClientError(
                "OpenAI knowledge extraction requires "
                "exactly one system message."
            )

        if len(user_messages) != 1:
            raise OpenAIKnowledgeClientError(
                "OpenAI knowledge extraction requires "
                "exactly one user message."
            )

        return (
            system_messages[0],
            user_messages[0],
        )

    @staticmethod
    def _read_usage_value(
        usage: Any,
        field_name: str,
    ) -> int | None:
        if isinstance(
            usage,
            Mapping,
        ):
            value = usage.get(
                field_name
            )
        else:
            value = getattr(
                usage,
                field_name,
                None,
            )

        if (
            isinstance(value, int)
            and not isinstance(
                value,
                bool,
            )
            and value >= 0
        ):
            return value

        return None

    def _capture_safe_metadata(
        self,
        response: Any,
    ) -> None:
        """
        Capture response ID and token counts only.

        Prompt text, output text, and complete SDK response objects are
        intentionally not retained.
        """

        response_id = getattr(
            response,
            "id",
            None,
        )

        if (
            isinstance(response_id, str)
            and response_id.strip()
        ):
            self.last_response_id = (
                response_id
            )
        else:
            self.last_response_id = None

        usage = getattr(
            response,
            "usage",
            None,
        )

        if usage is None:
            self.last_usage = None
            return

        input_tokens = (
            self._read_usage_value(
                usage,
                "input_tokens",
            )
        )

        output_tokens = (
            self._read_usage_value(
                usage,
                "output_tokens",
            )
        )

        total_tokens = (
            self._read_usage_value(
                usage,
                "total_tokens",
            )
        )

        if (
            input_tokens is None
            or output_tokens is None
            or total_tokens is None
        ):
            self.last_usage = None
            return

        self.last_usage = (
            OpenAIKnowledgeUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
            )
        )

    def generate(
        self,
        bundle: KnowledgePromptBundle,
    ) -> Mapping[str, Any]:
        """
        Send one structured knowledge extraction request to OpenAI.

        The provider response is decoded as JSON here. Semantic and domain
        validation remain the responsibility of the existing strict
        knowledge response parser in ModelKnowledgeExtractor.
        """

        if not isinstance(
            bundle,
            KnowledgePromptBundle,
        ):
            raise TypeError(
                "bundle must be a "
                "KnowledgePromptBundle object."
            )

        (
            system_prompt,
            user_prompt,
        ) = self._extract_prompts(
            bundle
        )

        try:
            response = (
                self.sdk_client
                .responses
                .create(
                    model=(
                        self.config.model
                    ),
                    instructions=(
                        system_prompt
                    ),
                    input=user_prompt,
                    max_output_tokens=(
                        self.config
                        .max_output_tokens
                    ),
                    text={
                        "format": {
                            "type": (
                                "json_schema"
                            ),
                            "name": (
                                OPENAI_KNOWLEDGE_SCHEMA_NAME
                            ),
                            "strict": True,
                            "schema": (
                                bundle
                                .response_schema
                            ),
                        }
                    },
                    store=False,
                )
            )
        except Exception as exc:
            raise OpenAIKnowledgeClientError(
                "OpenAI request failed "
                f"({type(exc).__name__})."
            ) from exc

        self._capture_safe_metadata(
            response
        )

        status = getattr(
            response,
            "status",
            None,
        )

        if status != "completed":
            raise OpenAIKnowledgeResponseError(
                "OpenAI response did not complete "
                f"successfully. Status: {status!r}."
            )

        output_text = getattr(
            response,
            "output_text",
            None,
        )

        if (
            not isinstance(
                output_text,
                str,
            )
            or not output_text.strip()
        ):
            raise OpenAIKnowledgeResponseError(
                "OpenAI response did not contain "
                "structured output text."
            )

        try:
            payload = json.loads(
                output_text
            )
        except json.JSONDecodeError as exc:
            raise OpenAIKnowledgeResponseError(
                "OpenAI structured output could "
                "not be parsed as JSON."
            ) from exc

        if not isinstance(
            payload,
            Mapping,
        ):
            raise OpenAIKnowledgeResponseError(
                "OpenAI structured output root "
                "must be an object."
            )

        return payload