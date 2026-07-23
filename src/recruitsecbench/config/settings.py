import json
import os
import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from recruitsecbench.cli.failures import ConfigurationFailure

ENV_PREFIX = "RSCB_"


class Settings(BaseModel):
    """Non-secret settings that may be recorded in an artifact manifest."""

    model_config = ConfigDict(extra="forbid")

    artifact_root: Path = Field(default=Path("artifacts"))
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR)$")
    safe_mode: bool = True
    project_name: str = Field(default="recruitsecbench", min_length=1)


def _read_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigurationFailure(f"configuration file does not exist: {path}")

    try:
        if path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
        elif path.suffix.lower() == ".toml":
            with path.open("rb") as config_file:
                payload = tomllib.load(config_file)
        else:
            raise ConfigurationFailure("configuration must use a .json or .toml extension")
    except (OSError, json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
        raise ConfigurationFailure(f"cannot read configuration: {path}") from error

    if not isinstance(payload, dict):
        raise ConfigurationFailure("configuration must be an object/table")
    return payload


def _environment_values() -> dict[str, Any]:
    values: dict[str, Any] = {}
    mapping = {
        "ARTIFACT_ROOT": "artifact_root",
        "LOG_LEVEL": "log_level",
        "SAFE_MODE": "safe_mode",
        "PROJECT_NAME": "project_name",
    }
    for environment_name, field_name in mapping.items():
        value = os.getenv(f"{ENV_PREFIX}{environment_name}")
        if value is not None:
            values[field_name] = value
    return values


def load_settings(config_path: Path | None = None, *, log_level: str | None = None) -> Settings:
    """Load defaults, then non-secret environment values, config, and CLI overrides."""

    values: dict[str, Any] = _environment_values()
    if config_path is not None:
        values.update(_read_config(config_path))
    if log_level is not None:
        values["log_level"] = log_level.upper()

    try:
        return Settings.model_validate(values)
    except ValidationError as error:
        details = [dict(item) for item in error.errors(include_input=False)]
        raise ConfigurationFailure("invalid configuration", details=details) from error
