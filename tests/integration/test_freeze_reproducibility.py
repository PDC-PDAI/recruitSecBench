from __future__ import annotations

import json
from pathlib import Path

import pytest

from recruitsecbench.cli.datasets import generate
from recruitsecbench.config.freeze import (
    FreezeCompatibilityError,
    FreezeConflictError,
    create_freeze,
    require_compatible_freezes,
)
from recruitsecbench.runner.authorization import (
    FrozenPartitionAuthorizationError,
    HoldoutCampaignRegistry,
    authorize_frozen_partition,
)


def _input_files(root: Path) -> dict[str, Path]:
    inputs = root / "inputs"
    inputs.mkdir(parents=True)
    files = {
        "config": inputs / "config.json",
        "prompt": inputs / "prompts.json",
        "policy": inputs / "policy.json",
        "model": inputs / "models.json",
        "oracle": inputs / "oracles.json",
    }
    for name, path in files.items():
        path.write_text(json.dumps({"kind": name}, sort_keys=True), encoding="utf-8")
    return files


def test_freeze_is_byte_reproducible_and_rejects_mutable_identity(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    generate(output=data_root, seed=2026)
    output_root = tmp_path / "freezes"
    first = create_freeze(
        partition="development",
        artifact_version="0.3.0",
        data_root=data_root,
        output_root=output_root,
        input_files=_input_files(tmp_path),
    )
    second = create_freeze(
        partition="development",
        artifact_version="0.3.0",
        data_root=data_root,
        output_root=output_root,
        input_files=_input_files(tmp_path / "repeat"),
    )

    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.content_sha256() == second.content_sha256()

    path = data_root / "domain" / "records.jsonl"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(FreezeConflictError):
        create_freeze(
            partition="development",
            artifact_version="0.3.0",
            data_root=data_root,
            output_root=output_root,
            input_files=_input_files(tmp_path / "changed"),
        )


def test_incompatible_freezes_cannot_aggregate_and_holdout_is_one_campaign(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    generate(output=data_root, seed=2026)
    development = create_freeze(
        partition="development",
        artifact_version="0.3.0",
        data_root=data_root,
        output_root=tmp_path / "freezes",
        input_files=_input_files(tmp_path / "development"),
    )
    pilot = create_freeze(
        partition="pilot",
        artifact_version="0.3.0",
        data_root=data_root,
        output_root=tmp_path / "freezes",
        input_files=_input_files(tmp_path / "pilot"),
    )
    with pytest.raises(FreezeCompatibilityError):
        require_compatible_freezes([development, pilot])

    holdout = create_freeze(
        partition="holdout",
        artifact_version="0.3.0",
        data_root=data_root,
        output_root=tmp_path / "freezes",
        input_files=_input_files(tmp_path / "holdout"),
    )
    registry = HoldoutCampaignRegistry(tmp_path / "holdout-campaign.json")
    with pytest.raises(FrozenPartitionAuthorizationError):
        authorize_frozen_partition(
            holdout, explicit=False, campaign_id="final-2026", registry=registry
        )
    authorize_frozen_partition(holdout, explicit=True, campaign_id="final-2026", registry=registry)
    with pytest.raises(FrozenPartitionAuthorizationError):
        authorize_frozen_partition(
            holdout, explicit=True, campaign_id="retry-2026", registry=registry
        )
