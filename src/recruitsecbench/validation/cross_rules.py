"""Referential, partition, scope, state, and version rules for the five datasets."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

REQUIRED_TYPES = {
    "project",
    "hiring_process",
    "vacancy",
    "candidate",
    "cv",
    "application",
    "questionnaire",
    "question",
    "candidate_response",
    "agent_session",
    "tool",
    "process_state",
    "evaluation_criterion",
    "evaluation_outcome",
}
PRIMARY_ID_FIELDS = {
    "project": "project_id",
    "hiring_process": "hiring_process_id",
    "vacancy": "vacancy_id",
    "candidate": "candidate_id",
    "cv": "document_id",
    "application": "application_id",
    "questionnaire": "questionnaire_record_id",
    "question": "question_id",
    "candidate_response": "response_id",
    "agent_session": "session_id",
    "tool": "tool_id",
    "process_state": "state_id",
    "evaluation_criterion": "criterion_id",
    "evaluation_outcome": "evaluation_id",
}


def cross_dataset_issues(
    domain: list[dict[str, Any]],
    benign: list[dict[str, Any]],
    deterministic: list[dict[str, Any]],
) -> list[tuple[str, str, str]]:
    issues: list[tuple[str, str, str]] = []
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    record_by_id = {row["record_id"]: row for row in domain}
    for row in domain:
        by_type[row["record_type"]].append(row)

    for missing in sorted(REQUIRED_TYPES - set(by_type)):
        issues.append(("REQUIRED_TYPE_MISSING", "domain", missing))
    for unknown in sorted(set(by_type) - REQUIRED_TYPES):
        issues.append(("RECORD_TYPE_INVALID", "domain", unknown))

    ids_by_type: dict[str, dict[str, dict[str, Any]]] = {}
    for kind, rows in by_type.items():
        primary = PRIMARY_ID_FIELDS.get(kind)
        if primary:
            ids_by_type[kind] = {row["content"][primary]: row for row in rows}

    def reference(
        row: dict[str, Any], field: str, target_type: str, *, record_id: bool = False
    ) -> dict[str, Any] | None:
        value = row["content"].get(field)
        target = (
            record_by_id.get(value) if record_id else ids_by_type.get(target_type, {}).get(value)
        )
        if target is None:
            issues.append(("RELATIONSHIP_INVALID", row["record_id"], field))
            return None
        if target["partition"] != row["partition"]:
            issues.append(("PARTITION_LEAKAGE", row["record_id"], field))
        return target

    for row in by_type.get("hiring_process", []):
        reference(row, "project_id", "project")
    for row in by_type.get("vacancy", []):
        process = reference(row, "hiring_process_id", "hiring_process")
        if process and process["content"]["project_id"] != row["content"].get("project_id"):
            issues.append(("ANCESTRY_INVALID", row["record_id"], "project_id"))
    for row in by_type.get("evaluation_criterion", []):
        reference(row, "vacancy_id", "vacancy")
    for row in by_type.get("cv", []):
        reference(row, "candidate_id", "candidate")
    for row in by_type.get("application", []):
        candidate = reference(row, "candidate_id", "candidate")
        vacancy = reference(row, "vacancy_id", "vacancy")
        process = reference(row, "hiring_process_id", "hiring_process")
        if candidate and candidate["scope"]["project_id"] != row["scope"]["project_id"]:
            issues.append(("ANCESTRY_INVALID", row["record_id"], "candidate_id"))
        if (
            vacancy
            and vacancy["content"]["hiring_process_id"] != row["content"]["hiring_process_id"]
        ):
            issues.append(("ANCESTRY_INVALID", row["record_id"], "vacancy_id"))
        if process and process["content"]["project_id"] != row["scope"]["project_id"]:
            issues.append(("ANCESTRY_INVALID", row["record_id"], "hiring_process_id"))

    questionnaire_records = ids_by_type.get("questionnaire", {})
    for row in by_type.get("questionnaire", []):
        reference(row, "vacancy_id", "vacancy")
        reference(row, "hiring_process_id", "hiring_process")
        if row["content"].get("project_id") != row["scope"]["project_id"]:
            issues.append(("ANCESTRY_INVALID", row["record_id"], "project_id"))
    for row in by_type.get("question", []):
        questionnaire = reference(row, "questionnaire_record_id", "questionnaire", record_id=True)
        reference(row, "criterion_id", "evaluation_criterion")
        if (
            questionnaire
            and row["content"]["questionnaire_id"] != questionnaire["content"]["questionnaire_id"]
        ):
            issues.append(("VERSION_REFERENCE_INVALID", row["record_id"], "questionnaire_id"))
    for row in by_type.get("candidate_response", []):
        application = reference(row, "application_id", "application")
        question = reference(row, "question_id", "question")
        reference(row, "candidate_id", "candidate")
        reference(row, "vacancy_id", "vacancy")
        questionnaire = reference(row, "questionnaire_record_id", "questionnaire", record_id=True)
        if application and (
            application["content"]["candidate_id"] != row["content"]["candidate_id"]
            or application["content"]["vacancy_id"] != row["content"]["vacancy_id"]
        ):
            issues.append(("RESPONSE_ANCESTRY_INVALID", row["record_id"], "application"))
        if (
            question
            and question["content"]["questionnaire_record_id"]
            != row["content"]["questionnaire_record_id"]
        ):
            issues.append(("RESPONSE_VERSION_INVALID", row["record_id"], "question"))
        if (
            questionnaire
            and questionnaire["content"]["questionnaire_id"] != row["content"]["questionnaire_id"]
        ):
            issues.append(("RESPONSE_VERSION_INVALID", row["record_id"], "questionnaire"))
    for row in by_type.get("process_state", []):
        reference(row, "application_id", "application")
    for row in by_type.get("evaluation_outcome", []):
        reference(row, "application_id", "application")

    for row in domain:
        content_project = row["content"].get("project_id")
        if content_project and content_project != row["scope"]["project_id"]:
            issues.append(("SCOPE_PROJECT_INVALID", row["record_id"], "project_id"))

    actors = {
        row["content"]["actor_id"]: row["scope"]["project_id"]
        for row in by_type.get("agent_session", [])
    }
    for case in benign:
        actor_project = actors.get(case["actor_id"])
        if actor_project != case["scope"]["project_id"]:
            issues.append(("ACTOR_SCOPE_INVALID", case["case_id"], case["actor_id"]))
        for record_id in case["input_record_ids"]:
            record = record_by_id.get(record_id)
            if record is None:
                issues.append(("MISSING_REFERENCE", case["case_id"], record_id))
            elif record["partition"] != case["partition"]:
                issues.append(("PARTITION_LEAKAGE", case["case_id"], record_id))

    states_by_application: dict[str, list[int]] = defaultdict(list)
    for row in by_type.get("process_state", []):
        states_by_application[row["content"]["application_id"]].append(row["content"]["sequence"])
    for application_id, sequence in states_by_application.items():
        if sorted(sequence) != list(range(1, len(sequence) + 1)):
            issues.append(("STATE_SEQUENCE_INVALID", application_id, "sequence"))

    versions: dict[str, list[int]] = defaultdict(list)
    published: dict[str, int] = defaultdict(int)
    for row in questionnaire_records.values():
        questionnaire_id = row["content"]["questionnaire_id"]
        versions[questionnaire_id].append(row["content"]["version"])
        if row["content"]["editorial_status"] == "PUBLISHED":
            published[questionnaire_id] += 1
    for questionnaire_id, values in versions.items():
        if sorted(values) != list(range(1, len(values) + 1)):
            issues.append(("VERSION_HISTORY_INVALID", questionnaire_id, "version"))
        if published[questionnaire_id] != 1:
            issues.append(("PUBLISHED_VERSION_INVALID", questionnaire_id, "editorial_status"))

    for fixture in deterministic:
        if (
            fixture.get("expected_decision") == "DENY"
            and fixture.get("expected_side_effect_count") != 0
        ):
            issues.append(("DENIED_SIDE_EFFECT", fixture["fixture_id"], "side_effect"))
        fixture_partition = fixture.get("partition")
        scope = fixture.get("scope") or fixture.get("owner_scope")
        if scope and fixture_partition:
            project = scope.get("project_id")
            partition_number = ("development", "pilot", "evaluation", "holdout").index(
                fixture_partition
            ) + 1
            expected_project = f"project-{partition_number:03d}"
            if project and project != expected_project:
                issues.append(("FIXTURE_PARTITION_INVALID", fixture["fixture_id"], "partition"))
    return issues
