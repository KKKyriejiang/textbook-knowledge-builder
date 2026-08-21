from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from textbook_kb.knowledge_extraction import (
    KnowledgeExtractionRequest,
)
from textbook_kb.knowledge_model import (
    ModelKnowledgeExtractor,
    StructuredKnowledgeModelClient,
)
from textbook_kb.llm_config import (
    OpenAIKnowledgeConfig,
)
from textbook_kb.openai_model_client import (
    OpenAIKnowledgeUsage,
    OpenAIStructuredKnowledgeModelClient,
)


SYNTHETIC_SMOKE_KNOWLEDGE_ID = (
    "kb-synthetic-openai-smoke-test"
)


@dataclass(frozen=True)
class OpenAISmokeResult:
    """
    Public-safe result from one synthetic OpenAI smoke test.

    The result stores derived metadata only. Prompt text, synthetic source
    text, raw model responses, and credentials are intentionally excluded.
    """

    model: str
    knowledge_id: str
    summary: str

    key_concept_count: int
    definition_count: int
    formula_count: int
    skill_count: int
    worked_example_pattern_count: int

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    response_id: str | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.model, str)
            or not self.model.strip()
        ):
            raise ValueError(
                "model must be a non-empty string."
            )

        if (
            not isinstance(
                self.knowledge_id,
                str,
            )
            or not self.knowledge_id.strip()
        ):
            raise ValueError(
                "knowledge_id must be a "
                "non-empty string."
            )

        if (
            not isinstance(self.summary, str)
            or not self.summary.strip()
        ):
            raise ValueError(
                "summary must be a non-empty string."
            )

        count_fields = (
            (
                "key_concept_count",
                self.key_concept_count,
            ),
            (
                "definition_count",
                self.definition_count,
            ),
            (
                "formula_count",
                self.formula_count,
            ),
            (
                "skill_count",
                self.skill_count,
            ),
            (
                "worked_example_pattern_count",
                self.worked_example_pattern_count,
            ),
        )

        for field_name, value in count_fields:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
            ):
                raise ValueError(
                    f"{field_name} must be a "
                    "non-negative integer."
                )

        token_fields = (
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
        )

        for field_name, value in token_fields:
            if value is None:
                continue

            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 0
            ):
                raise ValueError(
                    f"{field_name} must be a "
                    "non-negative integer or None."
                )

    def to_public_dict(
        self,
    ) -> dict[str, Any]:
        return asdict(
            self
        )


def build_synthetic_openai_smoke_request(
) -> KnowledgeExtractionRequest:
    """
    Build a tiny synthetic educational section for the first real
    provider smoke test.

    The source is authored specifically for this repository and contains
    no real textbook material.
    """

    return KnowledgeExtractionRequest(
        knowledge_id=(
            SYNTHETIC_SMOKE_KNOWLEDGE_ID
        ),
        grade="10",
        course_id="SYNTH-MATH10",
        course_name=(
            "Synthetic Mathematics"
        ),
        textbook=(
            "Synthetic Test Textbook"
        ),
        unit="Synthetic Unit 1",
        chapter="Synthetic Chapter 1",
        section=(
            "1.1 Variables and Simple Equations"
        ),
        page_start=1,
        page_end=1,
        source_file=(
            "synthetic_smoke_test.pdf"
        ),
        page_numbers=[
            1,
        ],
        source_text=(
            "--- PAGE 1 ---\n"
            "A variable is a symbol that represents a value. "
            "A simple equation states that two expressions have "
            "the same value. To solve x + 3 = 8, subtract 3 from "
            "both sides to obtain x = 5. The result can be checked "
            "by substituting 5 into the original equation."
        ),
        trace_ids=[
            "tr-synthetic-p1",
        ],
    )


def run_openai_synthetic_smoke(
    config: OpenAIKnowledgeConfig | None = None,
    model_client: (
        StructuredKnowledgeModelClient
        | None
    ) = None,
) -> OpenAISmokeResult:
    """
    Execute one synthetic structured knowledge extraction.

    Passing model_client allows unit tests to remain fully offline.

    When model_client is omitted, one real OpenAI request is made.
    """

    resolved_config = (
        config
        if config is not None
        else OpenAIKnowledgeConfig.from_environment()
    )

    if not isinstance(
        resolved_config,
        OpenAIKnowledgeConfig,
    ):
        raise TypeError(
            "config must be an "
            "OpenAIKnowledgeConfig object."
        )

    if model_client is None:
        resolved_client = (
            OpenAIStructuredKnowledgeModelClient(
                config=resolved_config
            )
        )
    else:
        if not isinstance(
            model_client,
            StructuredKnowledgeModelClient,
        ):
            raise TypeError(
                "model_client must implement "
                "StructuredKnowledgeModelClient."
            )

        resolved_client = model_client

    request = (
        build_synthetic_openai_smoke_request()
    )

    extractor = ModelKnowledgeExtractor(
        client=resolved_client,
        extractor_name=(
            f"openai-smoke:{resolved_config.model}"
        ),
    )

    extraction_result = (
        extractor.extract(
            request
        )
    )

    knowledge = (
        extraction_result.knowledge
    )

    usage = getattr(
        resolved_client,
        "last_usage",
        None,
    )

    if isinstance(
        usage,
        OpenAIKnowledgeUsage,
    ):
        input_tokens = (
            usage.input_tokens
        )
        output_tokens = (
            usage.output_tokens
        )
        total_tokens = (
            usage.total_tokens
        )
    else:
        input_tokens = None
        output_tokens = None
        total_tokens = None

    response_id = getattr(
        resolved_client,
        "last_response_id",
        None,
    )

    if not isinstance(
        response_id,
        str,
    ):
        response_id = None

    return OpenAISmokeResult(
        model=resolved_config.model,
        knowledge_id=(
            request.knowledge_id
        ),
        summary=knowledge.summary,
        key_concept_count=len(
            knowledge.key_concepts
        ),
        definition_count=len(
            knowledge.definitions
        ),
        formula_count=len(
            knowledge.formulas
        ),
        skill_count=len(
            knowledge.skills
        ),
        worked_example_pattern_count=len(
            knowledge
            .worked_example_patterns
        ),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        response_id=response_id,
    )