"""Validation for the complete bilingual five-dataset RecruitSecBench corpus."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from recruitsecbench.datasets.cases import ATTACK_FAMILIES, PARTITION_CASE_COUNTS
from recruitsecbench.validation.cross_rules import cross_dataset_issues
from recruitsecbench.validation.oracles import questionnaire_oracles

EXPECTED_DOMAIN_COUNTS = {
    "project": 4,
    "hiring_process": 8,
    "vacancy": 16,
    "evaluation_criterion": 48,
    "candidate": 64,
    "cv": 64,
    "application": 96,
    "questionnaire": 24,
    "question": 240,
    "candidate_response": 480,
    "agent_session": 96,
    "tool": 12,
    "process_state": 192,
    "evaluation_outcome": 96,
}
BILINGUAL_TYPES = {
    "project",
    "hiring_process",
    "vacancy",
    "evaluation_criterion",
    "candidate",
    "cv",
    "application",
    "questionnaire",
    "question",
    "candidate_response",
    "evaluation_outcome",
}


@dataclass(frozen=True)
class DatasetIssue:
    code: str
    location: str
    message: str


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _bilingual(value: object) -> bool:
    return isinstance(value, dict) and all(
        isinstance(value.get(language), str) and bool(value[language].strip())
        for language in ("pt-BR", "en")
    )


def _add_count_issues(
    issues: list[DatasetIssue], rows: list[dict[str, Any]], expected: dict[str, int]
) -> None:
    counts = Counter(row["record_type"] for row in rows)
    for record_type, count in expected.items():
        if counts[record_type] != count:
            issues.append(
                DatasetIssue(
                    "DOMAIN_COUNT_INVALID",
                    record_type,
                    f"expected {count}, found {counts[record_type]}",
                )
            )


def _validate_manifest(path: Path, data_path: Path, issues: list[DatasetIssue]) -> None:
    if not path.is_file():
        issues.append(DatasetIssue("MANIFEST_MISSING", str(path), "manifest is required"))
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    expected_hash = hashlib.sha256(data_path.read_bytes()).hexdigest()
    if manifest.get("sha256") != expected_hash:
        issues.append(DatasetIssue("MANIFEST_HASH_INVALID", str(path), "sha256"))
    if manifest.get("languages") != ["pt-BR", "en"]:
        issues.append(DatasetIssue("MANIFEST_LANGUAGE_INVALID", str(path), "languages"))
    if set(manifest.get("partitions", [])) != {
        "development",
        "pilot",
        "evaluation",
        "holdout",
    }:
        issues.append(DatasetIssue("MANIFEST_PARTITIONS_INVALID", str(path), "partitions"))


def validate_five_datasets(root: Path) -> list[DatasetIssue]:
    issues: list[DatasetIssue] = []
    paths = {
        "domain": root / "domain" / "records.jsonl",
        "benign": root / "benign" / "cases.jsonl",
        "adversarial": root / "adversarial" / "cases.jsonl",
        "deterministic": root / "deterministic" / "fixtures.jsonl",
        "audit": root / "audit" / "traces.jsonl",
    }
    try:
        domain = read_jsonl(paths["domain"])
        benign = read_jsonl(paths["benign"])
        adversarial = read_jsonl(paths["adversarial"])
        deterministic = read_jsonl(paths["deterministic"])
        audit = read_jsonl(paths["audit"])
    except FileNotFoundError as error:
        return [DatasetIssue("DATASET_FILE_MISSING", str(error.filename), "required dataset")]

    _add_count_issues(issues, domain, EXPECTED_DOMAIN_COUNTS)
    domain_ids = {row["record_id"] for row in domain}
    if len(domain_ids) != len(domain):
        issues.append(DatasetIssue("DUPLICATE_ID", "domain", "record IDs must be unique"))
    if {row["partition"] for row in domain} != {
        "development",
        "pilot",
        "evaluation",
        "holdout",
    }:
        issues.append(DatasetIssue("DOMAIN_PARTITIONS_INVALID", "domain", "partitions"))

    for row in domain:
        content = row["content"]
        if any(key.endswith("Id") for key in content):
            issues.append(
                DatasetIssue("ALIAS_NOT_CANONICAL", row["record_id"], "aliases forbidden")
            )
        if row["record_type"] in BILINGUAL_TYPES and not _bilingual(content.get("translations")):
            issues.append(
                DatasetIssue("BILINGUAL_CONTENT_MISSING", row["record_id"], "translations")
            )

    expected_benign = PARTITION_CASE_COUNTS
    if len(benign) != sum(expected_benign.values()):
        issues.append(DatasetIssue("BENIGN_COUNT_INVALID", "benign", str(len(benign))))
    if Counter(item["partition"] for item in benign) != Counter(expected_benign):
        issues.append(DatasetIssue("BENIGN_PARTITION_INVALID", "benign", "partition counts"))
    required_benign = {
        "actor_id",
        "scope",
        "input_record_ids",
        "fixture_ids",
        "initial_state",
        "request",
        "allowed_actions",
        "allowed_data_classes",
        "expected_outcome",
        "utility_oracles",
        "final_state",
        "max_side_effects",
        "metrics",
        "translations",
    }
    for case in benign:
        missing = required_benign - set(case)
        if missing:
            issues.append(
                DatasetIssue("BENIGN_FIELDS_MISSING", case["case_id"], ",".join(sorted(missing)))
            )
        if not _bilingual(case.get("translations")):
            issues.append(
                DatasetIssue("BILINGUAL_CONTENT_MISSING", case["case_id"], "translations")
            )
        for reference in case["input_record_ids"]:
            if reference not in domain_ids:
                issues.append(DatasetIssue("MISSING_REFERENCE", case["case_id"], reference))

    benign_ids = {case["case_id"] for case in benign}
    if len(adversarial) != len(benign) * 3:
        issues.append(
            DatasetIssue("ADVERSARIAL_COUNT_INVALID", "adversarial", str(len(adversarial)))
        )
    if Counter(item["partition"] for item in adversarial) != Counter(
        {partition: count * 3 for partition, count in expected_benign.items()}
    ):
        issues.append(
            DatasetIssue("ADVERSARIAL_PARTITION_INVALID", "adversarial", "partition counts")
        )
    attack_coverage = {case["attack_family"] for case in adversarial}
    if attack_coverage != set(ATTACK_FAMILIES):
        issues.append(DatasetIssue("ATTACK_COVERAGE_INVALID", "adversarial", "attack families"))
    for case in adversarial:
        if case["benign_counterpart"] not in benign_ids:
            issues.append(DatasetIssue("MISSING_BENIGN_COUNTERPART", case["case_id"], "missing"))
        if not _bilingual(case.get("translations")):
            issues.append(
                DatasetIssue("BILINGUAL_CONTENT_MISSING", case["case_id"], "translations")
            )

    questions_by_questionnaire: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for question in (row for row in domain if row["record_type"] == "question"):
        questions_by_questionnaire[question["content"]["questionnaire_record_id"]].append(question)
    for questionnaire in (row for row in domain if row["record_type"] == "questionnaire"):
        result = questionnaire_oracles(
            questionnaire,
            questions_by_questionnaire[questionnaire["content"]["questionnaire_record_id"]],
        )
        for name, passed in result.items():
            if not passed:
                issues.append(
                    DatasetIssue(
                        f"ORACLE_{name.upper()}_FAILED",
                        questionnaire["record_id"],
                        name,
                    )
                )

    if len(deterministic) != 132:
        issues.append(
            DatasetIssue("FIXTURE_COUNT_INVALID", "deterministic", str(len(deterministic)))
        )
    if not all(
        fixture.get("kind") == "canary" or _bilingual(fixture.get("translations"))
        for fixture in deterministic
    ):
        issues.append(DatasetIssue("FIXTURE_BILINGUAL_MISSING", "deterministic", "translations"))

    all_cases = {case["case_id"]: case for case in benign + adversarial}
    if len(audit) != len(all_cases):
        issues.append(DatasetIssue("AUDIT_COUNT_INVALID", "audit", str(len(audit))))
    trace_case_ids = set()
    for trace in audit:
        trace_case = all_cases.get(trace["case_id"])
        if trace_case is None:
            issues.append(DatasetIssue("MISSING_CASE", trace["trace_id"], trace["case_id"]))
            continue
        trace_case_ids.add(trace["case_id"])
        if trace.get("partition") != trace_case["partition"]:
            issues.append(DatasetIssue("AUDIT_PARTITION_INVALID", trace["trace_id"], "partition"))
        sequences = [event["sequence"] for event in trace["events"]]
        if sequences != list(range(1, len(sequences) + 1)):
            issues.append(DatasetIssue("EVENT_SEQUENCE_INVALID", trace["trace_id"], "sequence"))
        if not trace.get("sanitized"):
            issues.append(DatasetIssue("TRACE_NOT_SANITIZED", trace["trace_id"], "privacy"))
        required_trace = {
            "model_id",
            "configuration_id",
            "seed",
            "tools",
            "policy_decision",
            "initial_state",
            "final_state",
            "side_effect_count",
            "canary_status",
            "outcomes",
        }
        if required_trace - set(trace):
            issues.append(
                DatasetIssue("AUDIT_FIELDS_MISSING", trace["trace_id"], "required fields")
            )
    if trace_case_ids != set(all_cases):
        issues.append(DatasetIssue("AUDIT_CASE_COVERAGE_INVALID", "audit", "one trace per case"))

    for code, location, message in cross_dataset_issues(domain, benign, deterministic):
        issues.append(DatasetIssue(code, location, message))
    for _name, data_path in paths.items():
        _validate_manifest(data_path.parent / "manifest.json", data_path, issues)
    return issues
