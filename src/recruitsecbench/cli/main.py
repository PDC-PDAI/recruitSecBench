import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

import typer

from recruitsecbench import __version__
from recruitsecbench.cli.failures import RecruitSecBenchFailure
from recruitsecbench.config import Settings, load_settings

app = typer.Typer(
    add_completion=False,
    help="RecruitSecBench reproducible security benchmark commands.",
    no_args_is_help=True,
)


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


@app.command()
def doctor(
    context: typer.Context,
    probe_models: Annotated[
        bool, typer.Option("--probe-models", help="Reserved explicit model probe")
    ] = False,
) -> None:
    """Inspect local prerequisites without making a model or provider call."""

    command_context: CommandContext = context.obj
    checks = {
        "python": True,
        "git": shutil.which("git") is not None,
        "docker": shutil.which("docker") is not None,
        "artifact_root_writable": _artifact_root_writable(command_context.settings.artifact_root),
        "model_probe_requested": probe_models,
    }
    _emit(
        {
            "status": "ok",
            "summary": "doctor completed without provider calls",
            "version": __version__,
            "checks": checks,
        },
        json_output=command_context.json_output,
    )


def _artifact_root_writable(path: Path) -> bool:
    """Report whether a configured artifact parent can be created; do not create it."""

    parent = path.expanduser().resolve().parent
    return parent.exists() and parent.is_dir()


def main() -> None:
    """Console-script entry point."""

    app()


if __name__ == "__main__":
    main()
