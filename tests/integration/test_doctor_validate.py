from __future__ import annotations

import json

from typer.testing import CliRunner

from recruitsecbench.cli.main import app

runner = CliRunner()


def test_validate_runs_all_offline_gates_and_can_write_report(tmp_path) -> None:
    report_path = tmp_path / "validation.json"
    result = runner.invoke(app, ["validate", "--json", "--report", str(report_path)])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "ok"
    assert payload["provider_calls"] == 0
    assert {
        "schemas",
        "manifests",
        "privacy_status",
        "provenance",
        "compatibility",
        "protocol",
    } <= {check["name"] for check in payload["checks"]}
    assert json.loads(report_path.read_text(encoding="utf-8"))["status"] == "ok"


def test_doctor_includes_offline_validation_without_model_calls() -> None:
    result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["checks"]["model_probe_requested"] is False
    assert payload["validation"]["provider_calls"] == 0
    assert payload["validation"]["status"] == "ok"


def test_validate_fails_closed_for_invalid_manifest(tmp_path) -> None:
    manifests = tmp_path / "manifests"
    manifests.mkdir()
    (manifests / "broken.manifest.json").write_text('{"not":"a manifest"}', encoding="utf-8")
    config = tmp_path / "rscb.json"
    config.write_text(json.dumps({"artifact_root": str(tmp_path)}), encoding="utf-8")

    result = runner.invoke(app, ["--config", str(config), "validate", "--json"])

    assert result.exit_code == 3
    payload = json.loads(result.output)
    assert payload["status"] == "error"
    manifest_check = next(check for check in payload["checks"] if check["name"] == "manifests")
    assert manifest_check["status"] == "fail"
    assert "broken.manifest.json" in json.dumps(manifest_check)