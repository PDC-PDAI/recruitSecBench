import json
from pathlib import Path

from recruitsecbench.cli.datasets import generate
from recruitsecbench.validation.datasets import validate_five_datasets


def test_complete_generation_validates(tmp_path: Path) -> None:
    generate(output=tmp_path, seed=2026)
    assert validate_five_datasets(tmp_path) == []
    assert (tmp_path / "dataset-manifest.json").is_file()


def test_missing_reference_has_stable_code(tmp_path: Path) -> None:
    generate(output=tmp_path, seed=2026)
    path = tmp_path / "benign" / "cases.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["input_record_ids"] = ["missing-001"]
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    issues = validate_five_datasets(tmp_path)
    assert "MISSING_REFERENCE" in {issue.code for issue in issues}


def test_event_sequence_and_alias_are_rejected(tmp_path: Path) -> None:
    generate(output=tmp_path, seed=2026)
    audit_path = tmp_path / "audit" / "traces.jsonl"
    traces = [json.loads(line) for line in audit_path.read_text().splitlines()]
    traces[0]["events"][1]["sequence"] = 1
    audit_path.write_text("\n".join(json.dumps(row) for row in traces) + "\n")
    domain_path = tmp_path / "domain" / "records.jsonl"
    domain = [json.loads(line) for line in domain_path.read_text().splitlines()]
    domain[0]["content"]["projectId"] = "project-001"
    domain_path.write_text("\n".join(json.dumps(row) for row in domain) + "\n")
    codes = {issue.code for issue in validate_five_datasets(tmp_path)}
    assert {"EVENT_SEQUENCE_INVALID", "ALIAS_NOT_CANONICAL"} <= codes
