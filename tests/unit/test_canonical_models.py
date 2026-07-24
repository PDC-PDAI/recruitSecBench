from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from recruitsecbench.datasets.models import (
    AliasConflictError,
    AuthorizationScope,
    DatasetEnvelope,
    Partition,
    Project,
    Provenance,
    RecordType,
    normalize_aliases,
)
from recruitsecbench.validation.schema import SchemaValidationFailure, validate_instance


def _provenance() -> Provenance:
    return Provenance(
        source_kind="synthetic",
        generated_at="2026-07-22T12:00:00Z",
        content_sha256="a" * 64,
        pii_status="not_applicable",
    )


def test_canonical_models_forbid_product_aliases() -> None:
    with pytest.raises(ValidationError):
        Project.model_validate(
            {
                "project_id": "project-alpha",
                "name": "Alpha",
                "description": "Synthetic project",
                "synthetic": True,
                "provenance": _provenance().model_dump(mode="json"),
                "openingId": "alias-must-not-enter-canonical-data",
            }
        )


def test_alias_normalization_is_one_way_and_rejects_conflicts() -> None:
    normalized, aliases = normalize_aliases({"openingId": "vacancy-1", "application_id": "app-1"})

    assert normalized == {"vacancy_id": "vacancy-1", "application_id": "app-1"}
    assert aliases == {"openingId": "vacancy_id"}

    with pytest.raises(AliasConflictError):
        normalize_aliases({"vacancy_id": "vacancy-1", "vaga_id": "vacancy-2"})


def test_dataset_envelope_uses_canonical_ids_and_partition() -> None:
    envelope = DatasetEnvelope(
        record_id="domain-project-alpha",
        record_type=RecordType.PROJECT,
        partition=Partition.DEVELOPMENT,
        scope=AuthorizationScope(project_id="project-alpha"),
        provenance=_provenance(),
        content={"project_id": "project-alpha"},
    )

    assert envelope.schema_version == "1.0.0"
    assert envelope.partition is Partition.DEVELOPMENT


def test_draft_202012_validator_accepts_example_and_reports_stable_paths() -> None:
    example = json.loads(Path("schemas/examples/domain.example.json").read_text(encoding="utf-8"))
    validate_instance(example, "domain.schema.json")

    example["record_id"] = "contains spaces"
    with pytest.raises(SchemaValidationFailure) as raised:
        validate_instance(example, "domain.schema.json")

    assert raised.value.issues[0].instance_path == "/record_id"
