"""Authorization gates that bind runs to immutable partition freezes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from recruitsecbench.config.freeze import FreezeManifest
from recruitsecbench.config.manifests import atomic_write_bytes, canonical_json_bytes
from recruitsecbench.datasets.models import Partition


class FrozenPartitionAuthorizationError(PermissionError):
    """A run attempts to bypass a sealed-partition authorization gate."""


@dataclass(frozen=True)
class FrozenPartitionAuthorization:
    partition: Partition
    freeze_sha256: str
    campaign_id: str | None = None


class HoldoutCampaignRegistry:
    """Persistent one-campaign ledger; same campaign can resume, another cannot start."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def claim(self, *, campaign_id: str, freeze_sha256: str) -> None:
        if self.path.is_file():
            existing = json.loads(self.path.read_text(encoding="utf-8"))
            if (
                existing.get("campaign_id") == campaign_id
                and existing.get("freeze_sha256") == freeze_sha256
            ):
                return
            raise FrozenPartitionAuthorizationError("the single holdout campaign is already sealed")
        atomic_write_bytes(
            self.path,
            canonical_json_bytes({"campaign_id": campaign_id, "freeze_sha256": freeze_sha256})
            + b"\n",
        )


def authorize_frozen_partition(
    freeze: FreezeManifest,
    *,
    explicit: bool,
    campaign_id: str | None = None,
    registry: HoldoutCampaignRegistry | None = None,
) -> FrozenPartitionAuthorization:
    """Require explicit authorization for sealed partitions and claim holdout once."""

    partition = freeze.partition
    if partition in {Partition.EVALUATION, Partition.HOLDOUT} and not explicit:
        raise FrozenPartitionAuthorizationError(f"{partition.value} requires explicit confirmation")
    freeze_sha256 = freeze.content_sha256()
    if partition is Partition.HOLDOUT:
        if not campaign_id:
            raise FrozenPartitionAuthorizationError("holdout requires a named final campaign")
        if registry is None:
            raise FrozenPartitionAuthorizationError(
                "holdout requires a persistent campaign registry"
            )
        registry.claim(campaign_id=campaign_id, freeze_sha256=freeze_sha256)
    return FrozenPartitionAuthorization(partition, freeze_sha256, campaign_id)
