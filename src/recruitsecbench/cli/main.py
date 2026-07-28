"""Safe command shell shared by all RecruitSecBench commands."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

import typer

from recruitsecbench import __version__
from recruitsecbench.cli.datasets import datasets_app
from recruitsecbench.cli.failures import RecruitSecBenchFailure
from recruitsecbench.cli.freeze import freeze_command
from recruitsecbench.cli.privacy import privacy_app
from recruitsecbench.config import Settings, load_settings
from recruitsecbench.config.manifests import atomic_write_bytes
from recruitsecbench.validation.schema import REPOSITORY_ROOT
from recruitsecbench.validation.service import ValidationReport, ValidationService

app = typer.Typer(
    add_completion=False,
    help="RecruitSecBench reproducible security benchmark commands.",
    no_args_is_help=True,
)
app.add_typer(privacy_app, name="privacy")
app.add_typer(datasets_app, name="datasets")
app.command("freeze")(freeze_command)


@dataclass(frozen=True)
class CommandContext:
    settings: Settings
    json_output: bool


def _emit(payload: dict[str, Any], *, json_output: bool) -> None:
    if json_output:
        typer.echo(json.dumps(payload, sort_keys=True), nl=True)
        return
    summary = payload.get("summary", payload.get("message", payload.get("status", "completed")))
    typer.echo(str(summary), err=True)


def _failure_handler(
    context: typer.Context,
    error: RecruitSecBenchFailure,
    *,
    json_output: bool | None = None,
) -> None:
    command_context = context.obj
    if json_output is None:
        json_output = isinstance(command_context, CommandContext) and command_context.json_output
    _emit(
        {
            "status": "error",
            "code": error.exit_code,
            "message": error.message,
            "details": error.details,
        },
        json_output=json_output,
    )
    raise typer.Exit(error.exit_code)


@app.callback()
def configure(
    context: typer.Context,
    config: Annotated[
        Path | None, typer.Option("--config", help="JSON or TOML configuration file")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Write structured output to stdout")
    ] = False,
    log_level: Annotated[
        str | None, typer.Option("--log-level", help="DEBUG, INFO, WARNING, or ERROR")
    ] = None,
) -> None:
    """Load command-wide configuration without reading or printing secrets."""

    try:
        context.obj = CommandContext(load_settings(config, log_level=log_level), json_output)
    except RecruitSecBenchFailure as error:
        _failure_handler(context, error, json_output=json_output)


def _validation_report(settings: Settings) -> ValidationReport:
    return ValidationService(
        repository_root=REPOSITORY_ROOT,
        artifact_root=settings.artifact_root,
    ).run()


@app.command()
def doctor(
    context: typer.Context,
    probe_models: Annotated[
        bool, typer.Option("--probe-models", help="Reserved explicit model probe")
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", help="Write structured output to stdout")
    ] = False,
) -> None:
    """Inspect prerequisites and safety gates without making a provider call."""

    command_context: CommandContext = context.obj
    validation = _validation_report(command_context.settings)
    checks = {
        "python": True,
        "git": shutil.which("git") is not None,
        "docker": shutil.which("docker") is not None,
        "artifact_root_writable": _artifact_root_writable(command_context.settings.artifact_root),
        "model_probe_requested": probe_models,
        "validation_gates": validation.ok,
    }
    payload: dict[str, Any] = {
        "status": "ok" if validation.ok else "error",
        "summary": (
            "doctor completed without provider calls"
            if validation.ok
            else "doctor found one or more blocking validation failures"
        ),
        "version": __version__,
        "checks": checks,
        "validation": validation.as_dict(),
    }
    _emit(payload, json_output=command_context.json_output or json_output)
    if not validation.ok:
        raise typer.Exit(3)


@app.command("validate")
def validate_command(
    context: typer.Context,
    report: Annotated[
        Path | None,
        typer.Option("--report", help="Write the canonical JSON validation report"),
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Write structured output to stdout")
    ] = False,
) -> None:
    """Run all offline schema, manifest, privacy, provenance, and compatibility gates."""

    command_context: CommandContext = context.obj
    validation = _validation_report(command_context.settings)
    if report is not None:
        atomic_write_bytes(report, validation.canonical_bytes())
    _emit(validation.as_dict(), json_output=command_context.json_output or json_output)
    if not validation.ok:
        raise typer.Exit(3)


def _artifact_root_writable(path: Path) -> bool:
    """Report whether a configured artifact parent can be created; do not create it."""

    parent = path.expanduser().resolve().parent
    return parent.exists() and parent.is_dir()


def main() -> None:
    """Console-script entry point."""

    app()


if __name__ == "__main__":
    main()
