"""Generate and validate complete bilingual RecruitSecBench datasets."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Annotated, Any

import typer

from recruitsecbench.datasets.audit import generate_audit_records
from recruitsecbench.datasets.cases import generate_adversarial_cases, generate_benign_cases
from recruitsecbench.datasets.deterministic import generate_deterministic_fixtures
from recruitsecbench.datasets.domain import generate_domain, write_jsonl
from recruitsecbench.validation.datasets import validate_five_datasets

datasets_app = typer.Typer(help="Generate and validate the five canonical bilingual datasets.")


def _write_manifest(
    path: Path,
    *,
    dataset: str,
    rows: list[dict[str, Any]],
    sha256: str,
    seed: int,
    artifact_version: str,
) -> None:
    manifest = {
        "dataset": dataset,
        "artifact_version": artifact_version,
        "schema_version": "1.0.0",
        "count": len(rows),
        "partitions": ["development", "pilot", "evaluation", "holdout"],
        "partition_counts": dict(sorted(Counter(row["partition"] for row in rows).items())),
        "sha256": sha256,
        "source_kind": "synthetic",
        "privacy_status": "synthetic_public_safe",
        "seed": seed,
        "languages": ["pt-BR", "en"],
    }
    path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


@datasets_app.command("generate")
def generate(
    output: Annotated[Path, typer.Option(help="Dataset root")] = Path("data"),
    seed: Annotated[int, typer.Option(help="Deterministic seed")] = 2026,
    artifact_version: Annotated[
        str, typer.Option(help="Version for this generated synthetic artifact")
    ] = "0.2.0",
) -> None:
    """Generate the complete public synthetic corpus without personal data."""

    benign = generate_benign_cases()
    adversarial = generate_adversarial_cases(benign)
    payloads = {
        "domain": ("records.jsonl", generate_domain(seed)),
        "benign": ("cases.jsonl", benign),
        "adversarial": ("cases.jsonl", adversarial),
        "deterministic": ("fixtures.jsonl", generate_deterministic_fixtures()),
        "audit": ("traces.jsonl", generate_audit_records(benign + adversarial, seed)),
    }
    hashes: dict[str, str] = {}
    counts: dict[str, int] = {}
    for dataset, (filename, rows) in payloads.items():
        data_path = output / dataset / filename
        digest = write_jsonl(data_path, rows)
        _write_manifest(
            data_path.parent / "manifest.json",
            dataset=dataset,
            rows=rows,
            sha256=digest,
            seed=seed,
            artifact_version=artifact_version,
        )
        hashes[f"{dataset}/{filename}"] = digest
        counts[dataset] = len(rows)
    root_manifest = {
        "artifact_version": artifact_version,
        "schema_version": "1.0.0",
        "seed": seed,
        "languages": ["pt-BR", "en"],
        "files": hashes,
        "counts": counts,
    }
    root_data = json.dumps(root_manifest, sort_keys=True, indent=2, ensure_ascii=False).encode(
        "utf-8"
    )
    (output / "dataset-manifest.json").write_bytes(root_data)
    typer.echo(
        json.dumps(
            {
                "generated": len(payloads),
                "counts": counts,
                "manifest_sha256": hashlib.sha256(root_data).hexdigest(),
            },
            ensure_ascii=False,
        )
    )


@datasets_app.command("validate")
def validate(output: Annotated[Path, typer.Option(help="Dataset root")] = Path("data")) -> None:
    """Validate counts, links, partitions, bilingual text, and manifests."""

    issues = validate_five_datasets(output)
    typer.echo(
        json.dumps(
            {"valid": not issues, "issues": [issue.__dict__ for issue in issues]},
            ensure_ascii=False,
        )
    )
    if issues:
        raise typer.Exit(3)
