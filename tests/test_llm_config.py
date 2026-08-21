from pathlib import Path

import pytest

from textbook_kb.llm_config import (
    DEFAULT_ENV_PATH,
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_TIMEOUT_SECONDS,
    OPENAI_API_KEY_ENV,
    OPENAI_MAX_OUTPUT_TOKENS_ENV,
    OPENAI_MAX_RETRIES_ENV,
    OPENAI_MODEL_ENV,
    OPENAI_TIMEOUT_SECONDS_ENV,
    OpenAIKnowledgeConfig,
    load_local_environment,
    load_openai_api_key,
    openai_runtime_is_configured,
)


def clear_openai_environment(
    monkeypatch,
) -> None:
    environment_variables = [
        OPENAI_API_KEY_ENV,
        OPENAI_MODEL_ENV,
        OPENAI_MAX_OUTPUT_TOKENS_ENV,
        OPENAI_TIMEOUT_SECONDS_ENV,
        OPENAI_MAX_RETRIES_ENV,
    ]

    for variable in environment_variables:
        monkeypatch.delenv(
            variable,
            raising=False,
        )


def test_default_env_path_points_to_project_root() -> None:
    assert (
        DEFAULT_ENV_PATH.name
        == ".env"
    )

    assert (
        DEFAULT_ENV_PATH.parent.name
        == "textbook-knowledge-builder"
    )


def test_load_local_environment_reads_env_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    env_path = (
        tmp_path
        / ".env"
    )

    env_path.write_text(
        (
            "OPENAI_API_KEY="
            "synthetic-env-file-key\n"
            "TEXTBOOK_KB_OPENAI_MODEL="
            "synthetic-env-model\n"
        ),
        encoding="utf-8",
    )

    returned_path = (
        load_local_environment(
            env_path=env_path
        )
    )

    assert (
        returned_path
        == env_path.resolve()
    )

    assert (
        openai_runtime_is_configured(
            load_env_file=False
        )
        is True
    )

    assert (
        load_openai_api_key(
            load_env_file=False
        )
        == "synthetic-env-file-key"
    )


def test_process_environment_has_priority_over_env_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    monkeypatch.setenv(
        OPENAI_API_KEY_ENV,
        "process-key",
    )

    env_path = (
        tmp_path
        / ".env"
    )

    env_path.write_text(
        "OPENAI_API_KEY=env-file-key\n",
        encoding="utf-8",
    )

    load_local_environment(
        env_path=env_path
    )

    assert (
        load_openai_api_key(
            load_env_file=False
        )
        == "process-key"
    )


def test_default_configuration() -> None:
    config = OpenAIKnowledgeConfig()

    assert (
        config.model
        == DEFAULT_OPENAI_MODEL
    )

    assert (
        config.max_output_tokens
        == DEFAULT_MAX_OUTPUT_TOKENS
    )

    assert (
        config.timeout_seconds
        == DEFAULT_TIMEOUT_SECONDS
    )

    assert (
        config.max_retries
        == DEFAULT_MAX_RETRIES
    )


def test_config_from_empty_environment_uses_defaults(
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    config = (
        OpenAIKnowledgeConfig
        .from_environment(
            load_env_file=False
        )
    )

    assert (
        config.model
        == DEFAULT_OPENAI_MODEL
    )

    assert (
        config.max_output_tokens
        == DEFAULT_MAX_OUTPUT_TOKENS
    )

    assert (
        config.timeout_seconds
        == DEFAULT_TIMEOUT_SECONDS
    )

    assert (
        config.max_retries
        == DEFAULT_MAX_RETRIES
    )


def test_config_reads_environment_overrides(
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    monkeypatch.setenv(
        OPENAI_MODEL_ENV,
        "synthetic-model",
    )

    monkeypatch.setenv(
        OPENAI_MAX_OUTPUT_TOKENS_ENV,
        "2500",
    )

    monkeypatch.setenv(
        OPENAI_TIMEOUT_SECONDS_ENV,
        "45.5",
    )

    monkeypatch.setenv(
        OPENAI_MAX_RETRIES_ENV,
        "4",
    )

    config = (
        OpenAIKnowledgeConfig
        .from_environment(
            load_env_file=False
        )
    )

    assert (
        config.model
        == "synthetic-model"
    )

    assert (
        config.max_output_tokens
        == 2500
    )

    assert (
        config.timeout_seconds
        == 45.5
    )

    assert (
        config.max_retries
        == 4
    )


def test_config_can_load_values_from_env_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    env_path = (
        tmp_path
        / ".env"
    )

    env_path.write_text(
        (
            "TEXTBOOK_KB_OPENAI_MODEL="
            "synthetic-dotenv-model\n"
            "TEXTBOOK_KB_OPENAI_MAX_OUTPUT_TOKENS=2200\n"
            "TEXTBOOK_KB_OPENAI_TIMEOUT_SECONDS=33.5\n"
            "TEXTBOOK_KB_OPENAI_MAX_RETRIES=3\n"
        ),
        encoding="utf-8",
    )

    config = (
        OpenAIKnowledgeConfig
        .from_environment(
            env_path=env_path
        )
    )

    assert (
        config.model
        == "synthetic-dotenv-model"
    )

    assert (
        config.max_output_tokens
        == 2200
    )

    assert (
        config.timeout_seconds
        == 33.5
    )

    assert (
        config.max_retries
        == 3
    )


def test_public_config_contains_no_api_key(
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    secret = (
        "synthetic-secret-api-key"
    )

    monkeypatch.setenv(
        OPENAI_API_KEY_ENV,
        secret,
    )

    config = (
        OpenAIKnowledgeConfig
        .from_environment(
            load_env_file=False
        )
    )

    public_config = (
        config.to_public_dict()
    )

    assert (
        OPENAI_API_KEY_ENV
        not in public_config
    )

    assert (
        "api_key"
        not in public_config
    )

    assert (
        secret
        not in str(
            public_config
        )
    )


def test_config_repr_contains_no_api_key(
    monkeypatch,
) -> None:
    secret = (
        "synthetic-secret-api-key"
    )

    monkeypatch.setenv(
        OPENAI_API_KEY_ENV,
        secret,
    )

    config = OpenAIKnowledgeConfig()

    assert (
        secret
        not in repr(
            config
        )
    )


def test_load_openai_api_key_from_process_environment(
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    secret = (
        "synthetic-secret-api-key"
    )

    monkeypatch.setenv(
        OPENAI_API_KEY_ENV,
        secret,
    )

    assert (
        load_openai_api_key(
            load_env_file=False
        )
        == secret
    )


def test_load_openai_api_key_from_env_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    env_path = (
        tmp_path
        / ".env"
    )

    env_path.write_text(
        (
            "OPENAI_API_KEY="
            "synthetic-dotenv-key\n"
        ),
        encoding="utf-8",
    )

    assert (
        load_openai_api_key(
            env_path=env_path
        )
        == "synthetic-dotenv-key"
    )


def test_load_openai_api_key_strips_whitespace(
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    monkeypatch.setenv(
        OPENAI_API_KEY_ENV,
        "  synthetic-key  ",
    )

    assert (
        load_openai_api_key(
            load_env_file=False
        )
        == "synthetic-key"
    )


def test_missing_api_key_is_rejected(
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    with pytest.raises(
        RuntimeError,
        match="is not set",
    ):
        load_openai_api_key(
            load_env_file=False
        )


def test_empty_api_key_is_rejected(
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    monkeypatch.setenv(
        OPENAI_API_KEY_ENV,
        "   ",
    )

    with pytest.raises(
        RuntimeError,
        match="is empty",
    ):
        load_openai_api_key(
            load_env_file=False
        )


def test_runtime_configured_when_key_exists(
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    monkeypatch.setenv(
        OPENAI_API_KEY_ENV,
        "synthetic-key",
    )

    assert (
        openai_runtime_is_configured(
            load_env_file=False
        )
        is True
    )


def test_runtime_can_be_configured_from_env_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    env_path = (
        tmp_path
        / ".env"
    )

    env_path.write_text(
        (
            "OPENAI_API_KEY="
            "synthetic-file-key\n"
        ),
        encoding="utf-8",
    )

    assert (
        openai_runtime_is_configured(
            env_path=env_path
        )
        is True
    )


def test_runtime_not_configured_without_key(
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    assert (
        openai_runtime_is_configured(
            load_env_file=False
        )
        is False
    )


def test_runtime_not_configured_with_blank_key(
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    monkeypatch.setenv(
        OPENAI_API_KEY_ENV,
        "   ",
    )

    assert (
        openai_runtime_is_configured(
            load_env_file=False
        )
        is False
    )


def test_invalid_max_output_tokens_rejected(
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    monkeypatch.setenv(
        OPENAI_MAX_OUTPUT_TOKENS_ENV,
        "0",
    )

    with pytest.raises(
        ValueError,
        match=OPENAI_MAX_OUTPUT_TOKENS_ENV,
    ):
        (
            OpenAIKnowledgeConfig
            .from_environment(
                load_env_file=False
            )
        )


def test_invalid_max_output_tokens_type_rejected(
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    monkeypatch.setenv(
        OPENAI_MAX_OUTPUT_TOKENS_ENV,
        "many",
    )

    with pytest.raises(
        ValueError,
        match=OPENAI_MAX_OUTPUT_TOKENS_ENV,
    ):
        (
            OpenAIKnowledgeConfig
            .from_environment(
                load_env_file=False
            )
        )


def test_invalid_timeout_rejected(
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    monkeypatch.setenv(
        OPENAI_TIMEOUT_SECONDS_ENV,
        "-1",
    )

    with pytest.raises(
        ValueError,
        match=OPENAI_TIMEOUT_SECONDS_ENV,
    ):
        (
            OpenAIKnowledgeConfig
            .from_environment(
                load_env_file=False
            )
        )


def test_zero_retries_are_allowed(
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    monkeypatch.setenv(
        OPENAI_MAX_RETRIES_ENV,
        "0",
    )

    config = (
        OpenAIKnowledgeConfig
        .from_environment(
            load_env_file=False
        )
    )

    assert (
        config.max_retries
        == 0
    )


def test_negative_retries_are_rejected(
    monkeypatch,
) -> None:
    clear_openai_environment(
        monkeypatch
    )

    monkeypatch.setenv(
        OPENAI_MAX_RETRIES_ENV,
        "-1",
    )

    with pytest.raises(
        ValueError,
        match=OPENAI_MAX_RETRIES_ENV,
    ):
        (
            OpenAIKnowledgeConfig
            .from_environment(
                load_env_file=False
            )
        )