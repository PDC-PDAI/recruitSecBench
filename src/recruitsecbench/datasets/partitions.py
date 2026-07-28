"""Lineage-aware partition isolation and coverage gates."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from recruitsecbench.config.manifests import canonical_json_bytes
from recruitsecbench.datasets.models import Partition

PARTITION_NAMES = tuple(item.value for item in Partition)
METRICS = (
    "domain_records",
    "benign_cases",
    "adversarial_cases",
    "deterministic_fixtures",
)


@dataclass(frozen=True)
class PartitionCoverage:
    domain_records: int
    benign_cases: int
    adversarial_cases: int
    deterministic_fixtures: int

    def as_dict(self) -> dict[str, int]:
        return {metric: getattr(self, metric) for metric in METRICS}


@dataclass(frozen=True)
class PartitionPlan:
    schema_version: str
    coverage: dict[str, PartitionCoverage]


@dataclass(frozen=True)
class PartitionIssue:
    code: str
    location: str
    message: str


class _UnionFind:
    def __init__(self, values: list[str]) -> None:
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        root = self.parent[value]
        if root != value:
            self.parent[value] = self.find(root)
        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def load_partition_plan(path: Path) -> PartitionPlan:
    """Load explicit partition coverage targets from the frozen protocol input."""

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != "1.0.0":
        raise ValueError("partition plan must use schema_version 1.0.0")
    partitions = payload.get("partitions")
    if not isinstance(partitions, dict) or set(partitions) != set(PARTITION_NAMES):
        raise ValueError("partition plan must declare development, pilot, evaluation, and holdout")
    coverage: dict[str, PartitionCoverage] = {}
    for partition, values in partitions.items():
        raw_coverage = values.get("coverage") if isinstance(values, dict) else None
        if not isinstance(raw_coverage, dict) or set(raw_coverage) != set(METRICS):
            raise ValueError(f"partition plan coverage is invalid for {partition}")
        if any(
            not isinstance(raw_coverage[name], int) or raw_coverage[name] < 1 for name in METRICS
        ):
            raise ValueError(
                f"partition plan coverage must contain positive integers for {partition}"
            )
        coverage[partition] = PartitionCoverage(**raw_coverage)
    return PartitionPlan(schema_version="1.0.0", coverage=coverage)


def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for child in value.values() for item in _strings(child)]
    if isinstance(value, list):
        return [item for child in value for item in _strings(child)]
    return []


def _identifier_to_record(domain: list[dict[str, Any]]) -> dict[str, str]:
    identifiers: dict[str, str] = {}
    for row in domain:
        record_id = row["record_id"]
        identifiers[record_id] = record_id
        for key, value in row.get("content", {}).items():
            if key.endswith("_id") and isinstance(value, str):
                identifiers[value] = record_id
    return identifiers


def partition_component_ids(domain: list[dict[str, Any]]) -> list[tuple[str, tuple[str, ...]]]:
    """Return each connected lineage component together with its sole partition."""

    record_ids = [row["record_id"] for row in domain]
    union_find = _UnionFind(record_ids)
    identifiers = _identifier_to_record(domain)
    for row in domain:
        record_id = row["record_id"]
        references = _strings(row.get("content", {})) + _strings(row.get("scope", {}))
        for reference in references:
            target = identifiers.get(reference)
            if target is not None:
                union_find.union(record_id, target)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in domain:
        grouped[union_find.find(row["record_id"])].append(row)

    result: list[tuple[str, tuple[str, ...]]] = []
    for rows in grouped.values():
        partitions = {row["partition"] for row in rows}
        partition = next(iter(partitions)) if len(partitions) == 1 else "MIXED"
        result.append((partition, tuple(sorted(row["record_id"] for row in rows))))
    return sorted(result, key=lambda item: (item[0], item[1]))


def lineage_sha256(domain: list[dict[str, Any]]) -> str:
    """Return a stable fingerprint of connected components and their partition."""

    value = [
        {"partition": partition, "record_ids": record_ids}
        for partition, record_ids in partition_component_ids(domain)
    ]
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _coverage(
    domain: list[dict[str, Any]],
    benign: list[dict[str, Any]],
    adversarial: list[dict[str, Any]],
    deterministic: list[dict[str, Any]],
) -> dict[str, PartitionCoverage]:
    counts: dict[str, Counter[str]] = {partition: Counter() for partition in PARTITION_NAMES}
    for metric, rows in (
        ("domain_records", domain),
        ("benign_cases", benign),
        ("adversarial_cases", adversarial),
        ("deterministic_fixtures", deterministic),
    ):
        for row in rows:
            partition = row.get("partition")
            if partition in counts:
                counts[partition][metric] += 1
    return {
        partition: PartitionCoverage(**{metric: counts[partition][metric] for metric in METRICS})
        for partition in PARTITION_NAMES
    }


def validate_partition_isolation(
    domain: list[dict[str, Any]],
    benign: list[dict[str, Any]],
    adversarial: list[dict[str, Any]],
    deterministic: list[dict[str, Any]],
    plan: PartitionPlan,
) -> list[PartitionIssue]:
    """Reject split lineages and insufficient partition coverage deterministically."""

    issues: list[PartitionIssue] = []
    for partition, record_ids in partition_component_ids(domain):
        if partition == "MIXED":
            issues.append(
                PartitionIssue(
                    "PARTITION_COMPONENT_LEAKAGE",
                    record_ids[0],
                    "a connected lineage component spans more than one partition",
                )
            )

    actual = _coverage(domain, benign, adversarial, deterministic)
    for partition in PARTITION_NAMES:
        expected = plan.coverage[partition]
        for metric in METRICS:
            if getattr(actual[partition], metric) < getattr(expected, metric):
                expected_count = getattr(expected, metric)
                actual_count = getattr(actual[partition], metric)
                issues.append(
                    PartitionIssue(
                        "PARTITION_COVERAGE_SHORTFALL",
                        f"{partition}:{metric}",
                        f"expected at least {expected_count}, found {actual_count}",
                    )
                )
    return issues
