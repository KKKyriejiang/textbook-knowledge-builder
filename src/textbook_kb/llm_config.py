from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


OPENAI_API_KEY_ENV = "OPENAI_API_KEY"

OPENAI_MODEL_ENV = (
    "TEXTBOOK_KB_OPENAI_MODEL"
)

OPENAI_MAX_OUTPUT_TOKENS_ENV = (
    "TEXTBOOK_KB_OPENAI_MAX_OUTPUT_TOKENS"
)

OPENAI_TIMEOUT_SECONDS_ENV = (
    "TEXTBOOK_KB_OPENAI_TIMEOUT_SECONDS"
)

OPENAI_MAX_RETRIES_ENV = (
    "TEXTBOOK_KB_OPENAI_MAX_RETRIES"
)


DEFAULT_OPENAI_MODEL = "gpt-5.6-luna"

DEFAULT_MAX_OUTPUT_TOKENS = 5000
DEFAULT_TIMEOUT_SECONDS = 90.0
DEFAULT_MAX_RETRIES = 2


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

DEFAULT_ENV_PATH = (
    PROJECT_ROOT
    / ".env"
)


def _require_non_empty_string(
    value: str,
    field_name: str,
) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise ValueError(
            f"{field_name} must be a non-empty string."
        )

    return value.strip()


def _parse_positive_integer(
    value: str,
    field_name: str,
) -> int:
    try:
        parsed = int(
            value
        )
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be an integer."
        ) from exc

    if parsed < 1:
        raise ValueError(
            f"{field_name} must be greater than 0."
        )

    return parsed


def _parse_non_negative_integer(
    value: str,
    field_name: str,
) -> int:
    try:
        parsed = int(
            value
        )
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be an integer."
        ) from exc

    if parsed < 0:
        raise ValueError(
            f"{field_name} must be greater than "
            "or equal to 0."
        )

    return parsed


def _parse_positive_float(
    value: str,
    field_name: str,
) -> float:
    try:
        parsed = float(
            value
        )
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a number."
        ) from exc

    if parsed <= 0:
        raise ValueError(
            f"{field_name} must be greater than 0."
        )

    return parsed


def load_local_environment(
    env_path: str | Path | None = None,
) -> Path:
    """
    Load local environment variables from a .env file.

    By default, the project's root-level .env file is used.

    override=False means an environment variable explicitly configured
    in the current process takes priority over the value stored in .env.

    The function returns the resolved .env path and never returns or logs
    any secret values.
    """

    if env_path is None:
        resolved_path = (
            DEFAULT_ENV_PATH
        )
    else:
        resolved_path = (
            Path(env_path)
            .resolve()
        )

    load_dotenv(
        dotenv_path=resolved_path,
        override=False,
    )

    return resolved_path


def _prepare_environment(
    load_env_file: bool,
    env_path: str | Path | None,
) -> None:
    if load_env_file:
        load_local_environment(
            env_path=env_path
        )


@dataclass(frozen=True)
class OpenAIKnowledgeConfig:
    """
    Public-safe runtime configuration for the OpenAI knowledge
    extraction client.

    API credentials are intentionally excluded from this dataclass.
    """

    model: str = DEFAULT_OPENAI_MODEL

    max_output_tokens: int = (
        DEFAULT_MAX_OUTPUT_TOKENS
    )

    timeout_seconds: float = (
        DEFAULT_TIMEOUT_SECONDS
    )

    max_retries: int = (
        DEFAULT_MAX_RETRIES
    )

    def __post_init__(self) -> None:
        _require_non_empty_string(
            self.model,
            "model",
        )

        if (
            not isinstance(
                self.max_output_tokens,
                int,
            )
            or isinstance(
                self.max_output_tokens,
                bool,
            )
            or self.max_output_tokens < 1
        ):
            raise ValueError(
                "max_output_tokens must be a "
                "positive integer."
            )

        if (
            not isinstance(
                self.timeout_seconds,
                (int, float),
            )
            or isinstance(
                self.timeout_seconds,
                bool,
            )
            or self.timeout_seconds <= 0
        ):
            raise ValueError(
                "timeout_seconds must be a "
                "positive number."
            )

        if (
            not isinstance(
                self.max_retries,
                int,
            )
            or isinstance(
                self.max_retries,
                bool,
            )
            or self.max_retries < 0
        ):
            raise ValueError(
                "max_retries must be a "
                "non-negative integer."
            )

    def to_public_dict(
        self,
    ) -> dict[str, Any]:
        return asdict(
            self
        )

    @classmethod
    def from_environment(
        cls,
        load_env_file: bool = True,
        env_path: str | Path | None = None,
    ) -> OpenAIKnowledgeConfig:
        """
        Load model configuration.

        Default behavior first loads the project's local .env file and
        then reads configuration from os.environ.
        """

        _prepare_environment(
            load_env_file=load_env_file,
            env_path=env_path,
        )

        model = os.environ.get(
            OPENAI_MODEL_ENV,
            DEFAULT_OPENAI_MODEL,
        )

        max_output_tokens_raw = (
            os.environ.get(
                OPENAI_MAX_OUTPUT_TOKENS_ENV
            )
        )

        timeout_seconds_raw = (
            os.environ.get(
                OPENAI_TIMEOUT_SECONDS_ENV
            )
        )

        max_retries_raw = (
            os.environ.get(
                OPENAI_MAX_RETRIES_ENV
            )
        )

        if max_output_tokens_raw is None:
            max_output_tokens = (
                DEFAULT_MAX_OUTPUT_TOKENS
            )
        else:
            max_output_tokens = (
                _parse_positive_integer(
                    max_output_tokens_raw,
                    OPENAI_MAX_OUTPUT_TOKENS_ENV,
                )
            )

        if timeout_seconds_raw is None:
            timeout_seconds = (
                DEFAULT_TIMEOUT_SECONDS
            )
        else:
            timeout_seconds = (
                _parse_positive_float(
                    timeout_seconds_raw,
                    OPENAI_TIMEOUT_SECONDS_ENV,
                )
            )

        if max_retries_raw is None:
            max_retries = (
                DEFAULT_MAX_RETRIES
            )
        else:
            max_retries = (
                _parse_non_negative_integer(
                    max_retries_raw,
                    OPENAI_MAX_RETRIES_ENV,
                )
            )

        return cls(
            model=model,
            max_output_tokens=(
                max_output_tokens
            ),
            timeout_seconds=(
                timeout_seconds
            ),
            max_retries=max_retries,
        )


def load_openai_api_key(
    load_env_file: bool = True,
    env_path: str | Path | None = None,
) -> str:
    """
    Load the OpenAI API key.

    The project's .env file is loaded by default. The key remains only
    in process memory and is never stored in OpenAIKnowledgeConfig.
    """

    _prepare_environment(
        load_env_file=load_env_file,
        env_path=env_path,
    )

    api_key = os.environ.get(
        OPENAI_API_KEY_ENV
    )

    if api_key is None:
        raise RuntimeError(
            f"{OPENAI_API_KEY_ENV} is not set. "
            "Configure it in the local runtime "
            "environment or project .env file "
            "before using the real OpenAI client."
        )

    api_key = api_key.strip()

    if not api_key:
        raise RuntimeError(
            f"{OPENAI_API_KEY_ENV} is empty."
        )

    return api_key


def openai_runtime_is_configured(
    load_env_file: bool = True,
    env_path: str | Path | None = None,
) -> bool:
    """
    Check whether a usable OpenAI API key exists.

    The key itself is never returned by this function.
    """

    _prepare_environment(
        load_env_file=load_env_file,
        env_path=env_path,
    )

    api_key = os.environ.get(
        OPENAI_API_KEY_ENV
    )

    return bool(
        api_key
        and api_key.strip()
    )