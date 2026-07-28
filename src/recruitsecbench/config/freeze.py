"""Immutable partition freezes and exact compatibility gates."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import Field, model_validator

from recruitsecbench.config.manifests import atomic_write_bytes, canonical_json_bytes, sha256_bytes
from recruitsecbench.datasets.models import CanonicalModel, Partition, Sha256
from recruitsecbench.datasets.partitions import (
    lineage_sha256,
    load_partition_plan,
    validate_partition_isolation,
)
from recruitsecbench.validation.datasets import read_jsonl, validate_five_datasets
from recruitsecbench.validation.provenance import hash_file
from recruitsecbench.validation.schema import REPOSITORY_ROOT

DATASET_PATHS = {
    "domain": Path("domain/records.jsonl"),
    "benign": Path("benign/cases.jsonl"),
    "adversarial": Path("adversarial/cases.jsonl"),
    "deterministic": Path("deterministic/fixtures.jsonl"),
    "audit": Path("audit/traces.jsonl"),
}
REQUIRED_INPUT_KINDS = {"config", "prompt", "policy", "model", "oracle"}


class FreezeError(ValueError):
    """Base class for a freeze gate failure."""


class FreezeValidationError(FreezeError):
    """Freeze inputs fail an offline validation gate."""


class FreezeConflictError(FreezeError):
    """A frozen identity was reused after one of its inputs changed."""


class FreezeCompatibilityError(FreezeError):
    """Results try to aggregate evidence from different freezes."""


class FreezeManifest(CanonicalModel):
    """Content-addressed declaration of all inputs for one partition run."""

    schema_version: str = "1.0.0"
    partition: Partition
    artifact_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    dataset_manifest_sha256: Sha256
    partition_artifact_sha256: dict[str, Sha256]
    input_manifest_sha256: dict[str, Sha256]
    lineage_sha256: Sha256

    @model_validator(mode="after")
    def complete_inputs(self) -> FreezeManifest:
        if set(self.partition_artifact_sha256) != set(DATASET_PATHS):
            raise ValueError("a freeze must include all five partition dataset artifacts")
        if not set(self.input_manifest_sha256) >= REQUIRED_INPUT_KINDS:
            raise ValueError(
                "a freeze must include config, prompt, policy, model, and oracle inputs"
            )
        return self

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self) + b"\n"

    def content_sha256(self) -> str:
        return sha256_bytes(self.canonical_bytes())


@dataclass(frozen=True)
class FrozenPartition:
    manifest: FreezeManifest
    path: Path


def _partition_jsonl_sha256(path: Path, partition: Partition) -> str:
    rows = [row for row in read_jsonl(path) if row.get("partition") == partition.value]
    payload = b"".join(canonical_json_bytes(row) + b"\n" for row in rows)
    return sha256_bytes(payload)


def _read_partition_rows(data_root: Path) -> dict[str, list[dict[str, Any]]]:
    return {
        name: read_jsonl(data_root / relative_path) for name, relative_path in DATASET_PATHS.items()
    }


def _validate_inputs(
    data_root: Path, *, existing: FreezeManifest | None
) -> dict[str, list[dict[str, Any]]]:
    issues = validate_five_datasets(data_root)
    if issues:
        error_type = FreezeConflictError if existing is not None else FreezeValidationError
        raise error_type(
            "dataset validation failed; create a new artifact version after repairing inputs"
        )
    rows = _read_partition_rows(data_root)
    plan = load_partition_plan(REPOSITORY_ROOT / "protocol" / "partitions.yaml")
    partition_issues = validate_partition_isolation(
        rows["domain"],
        rows["benign"],
        rows["adversarial"],
        rows["deterministic"],
        plan,
    )
    if partition_issues:
        error_type = FreezeConflictError if existing is not None else FreezeValidationError
        raise error_type("partition isolation or coverage validation failed")
    return rows


def _input_hashes(input_files: dict[str, Path]) -> dict[str, str]:
    if not set(input_files) >= REQUIRED_INPUT_KINDS:
        missing = ", ".join(sorted(REQUIRED_INPUT_KINDS - set(input_files)))
        raise FreezeValidationError(f"missing required frozen input kinds: {missing}")
    hashes: dict[str, str] = {}
    for kind, path in input_files.items():
        if not path.is_file():
            raise FreezeValidationError(f"frozen {kind} input does not exist: {path}")
        hashes[kind] = hash_file(path)
    return hashes


def freeze_path(output_root: Path, partition: Partition, artifact_version: str) -> Path:
    return output_root / f"{partition.value}-{artifact_version}.freeze.json"


def load_freeze(path: Path) -> FreezeManifest:
    return FreezeManifest.model_validate_json(path.read_text(encoding="utf-8"))


def create_freeze(
    *,
    partition: str | Partition,
    artifact_version: str,
    data_root: Path,
    output_root: Path,
    input_files: dict[str, Path],
) -> FreezeManifest:
    """Freeze a validated partition or refuse reuse of a mutable identity."""

    normalized_partition = Partition(partition)
    destination = freeze_path(output_root, normalized_partition, artifact_version)
    existing = load_freeze(destination) if destination.is_file() else None
    rows = _validate_inputs(data_root, existing=existing)
    root_manifest = data_root / "dataset-manifest.json"
    if not root_manifest.is_file():
        raise FreezeValidationError("dataset-manifest.json is required before freezing")
    candidate = FreezeManifest(
        partition=normalized_partition,
        artifact_version=artifact_version,
        dataset_manifest_sha256=hash_file(root_manifest),
        partition_artifact_sha256={
            name: _partition_jsonl_sha256(data_root / relative_path, normalized_partition)
            for name, relative_path in DATASET_PATHS.items()
        },
        input_manifest_sha256=_input_hashes(input_files),
        lineage_sha256=lineage_sha256(rows["domain"]),
    )
    if existing is not None:
        if existing.content_sha256() != candidate.content_sha256():
            raise FreezeConflictError(
                "freeze identity already exists with different bytes; "
                "a new artifact version is required"
            )
        return existing
    atomic_write_bytes(destination, candidate.canonical_bytes())
    return candidate


def require_compatible_freezes(freezes: Iterable[FreezeManifest]) -> str:
    """Return the common freeze hash or fail closed before result aggregation."""

    values = list(freezes)
    if not values:
        raise FreezeCompatibilityError("at least one freeze is required")
    hashes = {freeze.content_sha256() for freeze in values}
    if len(hashes) != 1:
        raise FreezeCompatibilityError("incompatible freezes cannot be aggregated")
    return next(iter(hashes))
