import json

from typer.testing import CliRunner

from recruitsecbench.cli.main import app
from recruitsecbench.config import load_settings

runner = CliRunner()


def test_cli_overrides_config_and_environment(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "rscb.toml"
    config_path.write_text('log_level = "WARNING"\nproject_name = "from-file"\n', encoding="utf-8")
    monkeypatch.setenv("RSCB_LOG_LEVEL", "ERROR")

    settings = load_settings(config_path, log_level="debug")

    assert settings.log_level == "DEBUG"
    assert settings.project_name == "from-file"


def test_rejects_unknown_configuration_fields(tmp_path) -> None:
    config_path = tmp_path / "unsafe.json"
    config_path.write_text('{"api_key": "must-not-be-supported"}', encoding="utf-8")

    result = runner.invoke(app, ["--config", str(config_path), "doctor"])

    assert result.exit_code == 2
    assert "invalid configuration" in result.output
    assert "must-not-be-supported" not in result.output


def test_json_configuration_failure_is_structured_without_input_value(tmp_path) -> None:
    config_path = tmp_path / "unsafe.json"
    config_path.write_text('{"api_key": "must-not-be-supported"}', encoding="utf-8")

    result = runner.invoke(app, ["--json", "--config", str(config_path), "doctor"])

    assert result.exit_code == 2
    payload = json.loads(result.output)
    assert payload["status"] == "error"
    assert payload["code"] == 2
    assert payload["message"] == "invalid configuration"
    assert "must-not-be-supported" not in result.output


def test_doctor_json_is_safe_and_does_not_probe_models() -> None:
    result = runner.invoke(app, ["--json", "doctor"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "ok"
    assert payload["checks"]["model_probe_requested"] is False
