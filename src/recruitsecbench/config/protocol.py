"""Versioned benchmark protocol and sealed-partition authorization gates."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import Field, StringConstraints, model_validator

from recruitsecbench.datasets.models import (
    CanonicalId,
    CanonicalModel,
    Partition,
    Sha256,
)

GitCommit = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{40}$")]


class Condition(StrEnum):
    C0 = "C0"
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"


class BenchmarkNamespace(StrEnum):
    AGENTDOJO_STANDARD = "agentdojo_standard"
    OFFICIAL_CONTROL_REPRODUCTION = "official_control_reproduction"
    RECRUITSECBENCH_SIMULATOR = "recruitsecbench_simulator"
    RECRUITSECBENCH_APPLICATION = "recruitsecbench_application"


class Provider(StrEnum):
    OPENAI = "openai"
    CEIA = "ceia"
    MOCK = "mock"


class EndpointClass(StrEnum):
    EXTERNAL_PAID = "external_paid"
    EXTERNAL_INTERNAL = "external_internal"
    LOCAL = "local"
    DETERMINISTIC_MOCK = "deterministic_mock"


class ModelIdentity(CanonicalModel):
    model_key: CanonicalId
    config_id: CanonicalId
    provider: Provider
    model_id: str = Field(min_length=1)
    settings: dict[str, Any]
    endpoint_class: EndpointClass


class FailurePolicy(CanonicalModel):
    retryable_statuses: list[
        Literal["provider_error", "transport_error", "harness_error", "timeout", "cancelled"]
    ]
    max_attempts: int = Field(ge=1, le=10)
    preserve_all_attempts: Literal[True] = True


class BudgetPolicy(CanonicalModel):
    currency: Literal["USD"] = "USD"
    max_cost: float = Field(ge=0)
    block_before_exceeding: Literal[True] = True


class RepositoryCommits(CanonicalModel):
    recruitsecbench: GitCommit
    rh_agent_agno: GitCommit
    smart_rh_platform: GitCommit
    agentrh_infra: GitCommit


class AuthorizationPolicy(CanonicalModel):
    evaluation_requires_explicit_confirmation: Literal[True] = True
    holdout_requires_explicit_confirmation: Literal[True] = True
    holdout_single_campaign: Literal[True] = True


class BenchmarkProtocol(CanonicalModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    experiment_id: CanonicalId
    benchmark_namespace: BenchmarkNamespace
    partition: Partition
    conditions: list[Condition] = Field(min_length=1)
    models: list[ModelIdentity] = Field(min_length=1)
    repetitions: int = Field(ge=1, le=100)
    seeds: list[int] = Field(min_length=1)
    evidence_ids: list[CanonicalId] = Field(min_length=1)
    artifact_manifests: dict[str, Sha256]
    repository_commits: RepositoryCommits
    failure_policy: FailurePolicy
    budget: BudgetPolicy
    authorization: AuthorizationPolicy = Field(default_factory=AuthorizationPolicy)

    @model_validator(mode="after")
    def protocol_invariants(self) -> BenchmarkProtocol:
        if len(self.conditions) != len(set(self.conditions)):
            raise ValueError("conditions must be unique")
        if set(self.conditions) != set(Condition):
            raise ValueError("the benchmark protocol must declare C0-C3")
        if len(self.seeds) != len(set(self.seeds)):
            raise ValueError("seeds must be unique")
        if len(self.seeds) < self.repetitions:
            raise ValueError("at least one seed per repetition is required")
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("evidence IDs must be unique")
        if len(self.artifact_manifests) < 5:
            raise ValueError("all five dataset manifest identities are required")
        return self

    @staticmethod
    def condition_controls(condition: Condition) -> tuple[bool, bool]:
        return {
            Condition.C0: (False, False),
            Condition.C1: (True, False),
            Condition.C2: (False, True),
            Condition.C3: (True, True),
        }[condition]


class PartitionAuthorizationError(PermissionError):
    """A sealed partition was requested without its immutable authorization."""


class PartitionAuthorization(CanonicalModel):
    partition: Partition
    authorized: bool
    protocol_sha256: Sha256 | None = None
    campaign_id: CanonicalId | None = None


def authorize_partition(
    partition: Partition,
    *,
    explicit: bool,
    protocol_sha256: str | None,
    campaign_id: str | None = None,
    holdout_consumed: bool = False,
) -> PartitionAuthorization:
    if partition in {Partition.DEVELOPMENT, Partition.PILOT}:
        return PartitionAuthorization(partition=partition, authorized=True)

    if not explicit:
        raise PartitionAuthorizationError(f"{partition.value} requires explicit confirmation")
    if protocol_sha256 is None:
        raise PartitionAuthorizationError(f"{partition.value} requires a frozen protocol hash")

    if partition is Partition.HOLDOUT:
        if campaign_id is None:
            raise PartitionAuthorizationError("holdout requires a named final campaign")
        if holdout_consumed:
            raise PartitionAuthorizationError(
                "the single holdout campaign has already been consumed"
            )

    return PartitionAuthorization(
        partition=partition,
        authorized=True,
        protocol_sha256=protocol_sha256,
        campaign_id=campaign_id,
    )


def load_protocol(path: str | Path) -> BenchmarkProtocol:
    protocol_path = Path(path)
    payload = yaml.safe_load(protocol_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("protocol must be a YAML mapping")
    return BenchmarkProtocol.model_validate(payload)
