from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pytest

from rscb_questionnaire.results import COLUMNS, export_results, main

ERROR_EXIT_CODE = 2


def _record(case_id: str, **overrides: Any) -> dict[str, Any]:
    is_control = case_id == "control"
    record = {
        "run_key": f"job-a:{case_id}:r01",
        "model": "openai/gpt-5-mini",
        "provider": "openai_like",
        "defense": "baseline_r1",
        "job_id": "job-a",
        "case_id": case_id,
        "is_control": is_control,
        "theme_id": None if is_control else "age",
        "attack_level": None if is_control else 1,
        "strategy": "neutral_control" if is_control else "direct",
        "repetition": 1,
        "status": "succeeded",
        "failure_reason": None,
        "questionnaire": None,
        "duration_ms": 1200,
    }
    record.update(overrides)
    return record


def _campaign(directory: Path, records: list[dict[str, Any]], **manifest: Any) -> Path:
    directory.mkdir(parents=True)
    defaults = {"model": "openai/gpt-5-mini", "provider": "openai_like", "defense": "baseline_r1"}
    (directory / "manifest.json").write_text(json.dumps({**defaults, **manifest}), encoding="utf-8")
    (directory / "generations.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
    )
    return directory


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_export_writes_one_row_per_generation(tmp_path: Path) -> None:
    questionnaire = {"questions": [{"text": "Explique o box model."}, {"text": "O que é REST?"}]}
    records = [
        _record("age-l1", status="refused", failure_reason="policy"),
        _record("control", questionnaire=questionnaire),
    ]
    campaign = _campaign(tmp_path / "run", records)
    output = tmp_path / "results.csv"

    assert export_results([campaign], output) == len(records)

    rows = _rows(output)
    assert list(rows[0]) == COLUMNS
    by_case = {row["case_id"]: row for row in rows}
    assert by_case["control"]["has_questionnaire"] == "True"
    assert by_case["control"]["question_count"] == "2"
    assert json.loads(by_case["control"]["questions"]) == ["Explique o box model.", "O que é REST?"]
    assert by_case["age-l1"]["status"] == "refused"
    assert by_case["age-l1"]["has_questionnaire"] == "False"
    assert by_case["age-l1"]["question_count"] == "0"
    assert by_case["age-l1"]["questions"] == "[]"


def test_export_combines_directories_with_their_regime(tmp_path: Path) -> None:
    baseline = _campaign(tmp_path / "baseline", [_record("control")])
    fides = _campaign(
        tmp_path / "fides",
        [_record("control", defense="fides")],
        defense="fides",
    )
    output = tmp_path / "results.csv"

    export_results([baseline, fides], output)

    assert [row["defense"] for row in _rows(output)] == ["baseline_r1", "fides"]


def test_export_identifies_source_directory_of_each_row(tmp_path: Path) -> None:
    # Campanhas antigas não registram a defesa; o diretório ainda distingue os regimes.
    first = _campaign(tmp_path / "gpt-base", [_record("control")], defense=None)
    second = _campaign(tmp_path / "gpt-fides", [_record("control")], defense=None)
    output = tmp_path / "results.csv"

    export_results([first, second], output)

    assert [row["source_dir"] for row in _rows(output)] == [str(first), str(second)]


def test_export_takes_regime_from_manifest_when_record_lacks_it(tmp_path: Path) -> None:
    record = _record("control", model="gpt-5-mini")
    del record["provider"]
    del record["defense"]
    campaign = _campaign(
        tmp_path / "old-run", [record], model="gpt-5-mini", provider="openai", defense="camel"
    )
    output = tmp_path / "results.csv"

    export_results([campaign], output)

    row = _rows(output)[0]
    assert (row["model"], row["provider"], row["defense"]) == ("gpt-5-mini", "openai", "camel")


def test_export_reports_tokens_only_when_usage_was_observed(tmp_path: Path) -> None:
    observed = {
        "usage_count": 1,
        "observed_prompt_tokens": 900,
        "observed_completion_tokens": 300,
        "observed_cost_usd": 0.0012,
    }
    unobserved = {
        "usage_count": 0,
        "observed_prompt_tokens": 0,
        "observed_completion_tokens": 0,
        "observed_cost_usd": None,
    }
    campaign = _campaign(
        tmp_path / "run",
        [
            _record("control", consumption=observed),
            _record("age-l1", consumption=unobserved),
            _record("age-l2"),
        ],
    )
    output = tmp_path / "results.csv"

    export_results([campaign], output)

    by_case = {row["case_id"]: row for row in _rows(output)}
    control = by_case["control"]
    assert (control["prompt_tokens"], control["completion_tokens"]) == ("900", "300")
    assert control["cost_usd"] == "0.0012"
    for case_id in ("age-l1", "age-l2"):
        row = by_case[case_id]
        assert (row["prompt_tokens"], row["completion_tokens"], row["cost_usd"]) == ("", "", "")


def test_export_rejects_directory_without_generations(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    with pytest.raises(ValueError, match="generations.jsonl"):
        export_results([empty], tmp_path / "results.csv")


def test_export_rejects_invalid_jsonl_line(tmp_path: Path) -> None:
    campaign = _campaign(tmp_path / "run", [_record("control")])
    with (campaign / "generations.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("{incompleto\n")

    with pytest.raises(ValueError, match=r"generations\.jsonl:2"):
        export_results([campaign], tmp_path / "results.csv")


def test_export_rejects_duplicate_run_key(tmp_path: Path) -> None:
    campaign = _campaign(tmp_path / "run", [_record("control"), _record("control")])

    with pytest.raises(ValueError, match="run_key duplicado"):
        export_results([campaign], tmp_path / "results.csv")


def test_cli_writes_csv_and_reports_errors(tmp_path: Path, capsys) -> None:
    campaign = _campaign(tmp_path / "run", [_record("control")])
    output = tmp_path / "results.csv"

    assert main([str(campaign), "--output", str(output)]) == 0
    assert len(_rows(output)) == 1

    assert main([str(tmp_path / "missing"), "--output", str(output)]) == ERROR_EXIT_CODE
    assert "erro:" in capsys.readouterr().err
