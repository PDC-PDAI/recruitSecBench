"""CLI surface for creating immutable partition freezes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from recruitsecbench.config.freeze import FreezeError, create_freeze
from recruitsecbench.datasets.models import Partition
from recruitsecbench.runner.authorization import (
    HoldoutCampaignRegistry,
    authorize_frozen_partition,
)
from recruitsecbench.validation.schema import REPOSITORY_ROOT


def _default_inputs() -> dict[str, Path]:
    return {
        "config": REPOSITORY_ROOT / "protocol" / "experiment.yaml",
        "prompt": REPOSITORY_ROOT / "data" / "benign" / "cases.jsonl",
        "policy": REPOSITORY_ROOT / "protocol" / "experiment.yaml",
        "model": REPOSITORY_ROOT / "protocol" / "experiment.yaml",
        "oracle": REPOSITORY_ROOT / "src" / "recruitsecbench" / "validation" / "oracles.py",
    }


def freeze_command(
    partition: Partition,
    artifact_version: Annotated[str, typer.Option(help="Immutable semantic artifact version")],
    data_root: Annotated[Path, typer.Option(help="Root of the generated five datasets")] = Path(
        "data"
    ),
    output_root: Annotated[
        Path, typer.Option(help="Directory for immutable freeze manifests")
    ] = Path("artifacts/freezes"),
    confirm: Annotated[
        bool, typer.Option(help="Explicitly authorize evaluation or holdout freeze")
    ] = False,
    campaign_id: Annotated[
        str | None, typer.Option(help="Named final campaign required for holdout")
    ] = None,
) -> None:
    """Freeze a validated partition and all experiment-defining inputs."""

    try:
        freeze = create_freeze(
            partition=partition,
            artifact_version=artifact_version,
            data_root=data_root,
            output_root=output_root,
            input_files=_default_inputs(),
        )
        registry = (
            HoldoutCampaignRegistry(output_root / "holdout-campaign.json")
            if partition is Partition.HOLDOUT
            else None
        )
        authorization = authorize_frozen_partition(
            freeze,
            explicit=confirm,
            campaign_id=campaign_id,
            registry=registry,
        )
    except (FreezeError, PermissionError) as error:
        typer.echo(json.dumps({"status": "error", "message": str(error)}), err=True)
        raise typer.Exit(8) from error

    typer.echo(
        json.dumps(
            {
                "status": "ok",
                "partition": partition.value,
                "freeze_sha256": freeze.content_sha256(),
                "authorization": authorization.freeze_sha256,
            },
            sort_keys=True,
        )
    )
