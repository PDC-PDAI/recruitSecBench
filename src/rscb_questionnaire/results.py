"""Exporta gerações da bateria de questionários para um CSV de análise."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

COLUMNS = [
    "source_dir",
    "model",
    "provider",
    "defense",
    "run_key",
    "job_id",
    "case_id",
    "is_control",
    "theme_id",
    "strategy",
    "attack_level",
    "repetition",
    "status",
    "failure_reason",
    "has_questionnaire",
    "question_count",
    "questions",
    "duration_ms",
    "prompt_tokens",
    "completion_tokens",
    "cost_usd",
]


def _read_campaign(directory: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    generations_path = directory / "generations.jsonl"
    manifest_path = directory / "manifest.json"
    if not generations_path.is_file():
        raise ValueError(f"{directory}: generations.jsonl não encontrado.")
    if not manifest_path.is_file():
        raise ValueError(f"{directory}: manifest.json não encontrado.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    lines = generations_path.read_text(encoding="utf-8").splitlines()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSONL inválido em {generations_path}:{line_number}: {exc}") from exc
        if record["run_key"] in seen:
            # Uma retomada interrompida não pode inflar os denominadores.
            raise ValueError(f"{generations_path}: run_key duplicado {record['run_key']}.")
        seen.add(record["run_key"])
        records.append(record)
    return manifest, sorted(records, key=lambda record: record["run_key"])


def _row(directory: Path, manifest: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    questionnaire = record.get("questionnaire")
    questions = [item["text"] for item in (questionnaire or {}).get("questions", [])]
    consumption = record.get("consumption") or {}
    # Zero tokens sem uso observado não comprova consumo zero: deixa a célula vazia.
    observed = bool(consumption.get("usage_count"))
    return {
        "source_dir": str(directory),
        "model": record.get("model") or manifest.get("model"),
        "provider": record.get("provider") or manifest.get("provider"),
        "defense": record.get("defense") or manifest.get("defense"),
        "run_key": record["run_key"],
        "job_id": record["job_id"],
        "case_id": record["case_id"],
        "is_control": record["is_control"],
        "theme_id": record.get("theme_id"),
        "strategy": record.get("strategy"),
        "attack_level": record.get("attack_level"),
        "repetition": record["repetition"],
        "status": record["status"],
        "failure_reason": record.get("failure_reason"),
        "has_questionnaire": questionnaire is not None,
        "question_count": len(questions),
        "questions": json.dumps(questions, ensure_ascii=False),
        "duration_ms": record.get("duration_ms"),
        "prompt_tokens": consumption.get("observed_prompt_tokens") if observed else None,
        "completion_tokens": consumption.get("observed_completion_tokens") if observed else None,
        "cost_usd": consumption.get("observed_cost_usd"),
    }


def export_results(directories: list[Path], output: Path) -> int:
    rows = []
    for directory in directories:
        manifest, records = _read_campaign(directory)
        rows.extend(_row(directory, manifest, record) for record in records)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Junta as gerações de um ou mais diretórios da bateria em um CSV, "
            "uma linha por geração, sem classificar o conteúdo."
        )
    )
    parser.add_argument(
        "directories",
        type=Path,
        nargs="+",
        help="Diretórios passados em --output-dir para rscb-questionnaire-battery.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results.csv"),
        help="Arquivo CSV de saída (default: results.csv).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        count = export_results(args.directories, args.output)
    except (OSError, ValueError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    print(f"{count} gerações exportadas para {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
