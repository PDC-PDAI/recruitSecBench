import json

import pytest
from agno.models.message import Message
from openai.types.chat import ChatCompletionChunk

from rscb_questionnaire import battery, cli
from rscb_questionnaire.agents.model import (
    ModelConfigurationError,
    _role_config,
    build_model,
    validate_model_configuration,
)
from rscb_questionnaire.agents.openrouter import OpenRouterChat
from rscb_questionnaire.settings import settings


def test_role_model_inherits_global_configuration(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_MODEL", "global-model")
    monkeypatch.setattr(settings, "EVALUATOR_LLM_PROVIDER", None)
    monkeypatch.setattr(settings, "EVALUATOR_MODEL", None)

    assert _role_config("evaluator") == ("openai", "global-model")


def test_role_model_can_override_provider_and_model(monkeypatch):
    monkeypatch.setattr(settings, "RESPONSE_GENERATOR_LLM_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "RESPONSE_GENERATOR_MODEL", "attack-generator")

    assert _role_config("response_generator") == ("ollama", "attack-generator")


def test_openrouter_uses_reasoning_parameter(monkeypatch):
    max_retries = 12
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai_like")
    monkeypatch.setattr(settings, "OPENAI_MODEL", "z-ai/glm-5.2:free")
    monkeypatch.setattr(settings, "OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "OPENAI_REASONING_EFFORT", "high")
    monkeypatch.setattr(settings, "OPENAI_MAX_RETRIES", max_retries)

    model = build_model()

    assert isinstance(model, OpenRouterChat)
    assert model.reasoning_effort is None
    assert model.max_retries == max_retries
    assert model.extra_body == {"reasoning": {"effort": "high", "exclude": False}}


def test_openrouter_preserves_streamed_reasoning_details_for_tool_continuation():
    model = OpenRouterChat(id="z-ai/glm-5.2:free")
    chunk = ChatCompletionChunk.model_validate(
        {
            "id": "response-1",
            "created": 1,
            "model": "z-ai/glm-5.2:free",
            "object": "chat.completion.chunk",
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "role": "assistant",
                        "reasoning_details": [
                            {
                                "type": "reasoning.text",
                                "text": "bloco intacto",
                                "format": "unknown",
                                "index": 0,
                            }
                        ],
                    },
                    "finish_reason": None,
                }
            ],
        }
    )

    response = model._parse_provider_response_delta(chunk)
    details = response.provider_data["reasoning_details"]
    formatted = model._format_message(
        Message(role="assistant", content="", provider_data={"reasoning_details": details})
    )

    assert formatted["reasoning_details"] == details
    assert formatted["reasoning_details"][0]["text"] == "bloco intacto"


@pytest.mark.parametrize("provider", ["openai", "openai_responses", "openai_like"])
def test_missing_key_reports_configuration_source(monkeypatch, provider):
    monkeypatch.setattr(settings, "LLM_PROVIDER", provider)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "  ")
    with pytest.raises(ModelConfigurationError, match="QUESTIONNAIRE_HOME"):
        validate_model_configuration()


def test_local_model_does_not_need_openai_key_but_evaluator_override_does(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(settings, "EVALUATOR_LLM_PROVIDER", "openai")
    validate_model_configuration()
    with pytest.raises(ModelConfigurationError, match="evaluator"):
        validate_model_configuration("evaluator")


def test_cli_fails_before_creating_scenario(monkeypatch, capsys):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr("sys.argv", ["rscb-questionnaire", "run", "--brief", "Vaga Python"])

    def unexpected_service(*args, **kwargs):
        pytest.fail("Scenario must not start without credentials")

    monkeypatch.setattr(cli, "ScenarioService", unexpected_service)
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2  # noqa: PLR2004
    error = capsys.readouterr().err
    assert "OPENAI_API_KEY ausente" in error
    assert "JSONDecodeError" not in error


@pytest.mark.asyncio
async def test_battery_preflight_does_not_persist_failed_runs(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    output = tmp_path / "campaign"
    args = battery._parser().parse_args(["--output-dir", str(output), "--repetitions", "4"])
    with pytest.raises(ModelConfigurationError):
        await battery._run(args)
    assert not output.exists()

    args.dry_run = True
    assert await battery._run(args) == 0
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["planned_generations"] == 1520  # noqa: PLR2004
    assert not (output / "generations.jsonl").exists()
