from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from rscb_questionnaire.cli import _apply_profile, _parser, _run
from rscb_questionnaire.prompts.raw_prompts import PROMPTS
from rscb_questionnaire.schemas.experiment.schema import ResearchFront
from rscb_questionnaire.services.experiment.profile import load_experiment_profile
from rscb_questionnaire.settings import Settings

ROOT = Path(__file__).resolve().parents[2]
_CLI_BENIGN_OVERRIDE = 2
_SECURITY_MALICIOUS_RESPONSES = 2


def test_security_profile_runs_evaluator_and_exports_all_artifacts():
    profile = load_experiment_profile(ROOT / "src/rscb_questionnaire/profiles/security.yaml")

    assert profile.front is ResearchFront.SECURITY
    assert profile.pipeline.questionnaire_evaluator is True
    assert profile.pipeline.benign_responses + profile.pipeline.malicious_responses > 0
    assert profile.artifacts.scenario_path == Path("outputs/security/scenario.json")
    assert profile.artifacts.agent_debug_path == Path("outputs/security/agent-debug.jsonl")


def test_cli_profile_supplies_defaults_and_explicit_flags_win():
    args = argparse.Namespace(
        profile=ROOT / "src/rscb_questionnaire/profiles/security.yaml",
        benign=_CLI_BENIGN_OVERRIDE,
        malicious=None,
        benign_responses=None,
        malicious_responses=0,
        output=None,
        jsonl=None,
        agent_debug_jsonl=None,
        trajectories_dir=None,
    )

    profile = _apply_profile(args)

    assert profile is not None
    assert args.benign == _CLI_BENIGN_OVERRIDE
    assert args.malicious == profile.pipeline.malicious_commands
    assert args.malicious_responses == 0
    assert args.questionnaire_evaluator is True
    assert args.output == Path("outputs/security/scenario.json")
    assert args.trajectories_dir == Path("outputs/security/trajectories")


def test_cli_can_explicitly_disable_questionnaire_evaluator():
    args = _parser().parse_args(
        [
            "run",
            "--brief",
            "Backend Python",
            "--profile",
            str(ROOT / "src/rscb_questionnaire/profiles/security.yaml"),
            "--no-questionnaire-evaluator",
            "--benign-responses",
            "0",
            "--malicious-responses",
            "0",
        ]
    )

    _apply_profile(args)

    assert args.questionnaire_evaluator is False


@pytest.mark.asyncio
async def test_security_profile_enables_evaluator_in_scenario_service(monkeypatch):
    args = argparse.Namespace(
        profile=ROOT / "src/rscb_questionnaire/profiles/security.yaml",
        brief="Backend Python",
        brief_file=None,
        benign=None,
        malicious=None,
        benign_responses=None,
        malicious_responses=None,
        output=None,
        jsonl=None,
        agent_debug_jsonl=None,
        trajectories_dir=None,
    )
    args.experiment_profile = _apply_profile(args)
    args.output = None
    args.jsonl = None
    args.agent_debug_jsonl = None
    args.trajectories_dir = None
    received = {}

    class FakeScenarioRun:
        executions = []
        evaluation_executions = []
        benchmark_records = []

        @staticmethod
        def model_dump_json(**kwargs):
            return "{}"

    class FakeScenarioService:
        async def run(self, brief, **kwargs):
            received.update(kwargs)
            return FakeScenarioRun()

    monkeypatch.setattr("rscb_questionnaire.cli.ScenarioService", FakeScenarioService)
    monkeypatch.setattr("rscb_questionnaire.cli.flush_langfuse", lambda: None)

    assert await _run(args) == 0
    assert received["questionnaire_evaluator"] is True
    assert received["research_front"] is ResearchFront.SECURITY
    assert received["benign_response_count"] == 1
    assert received["malicious_response_count"] == _SECURITY_MALICIOUS_RESPONSES


def test_profile_rejects_unsupported_research_front(tmp_path):
    profile = tmp_path / "invalid-evaluator-front.yaml"
    profile.write_text(
        """
schema_version: "1.0"
name: invalid_evaluator_front
front: error_recovery
description: Perfil inválido de teste.
pipeline:
  benign_commands: 1
  malicious_commands: 0
  benign_responses: 0
  malicious_responses: 0
  questionnaire_evaluator: true
artifacts:
  output_dir: outputs/test
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError, match="Input should be 'security'"):
        load_experiment_profile(profile)


def test_questionnaire_home_selects_env_and_database_directory(tmp_path):
    home = tmp_path / "runtime"
    home.mkdir()
    (home / ".env").write_text("OPENAI_MODEL=explicit-home-model\n")
    env = dict(os.environ)
    for key in ("OPENAI_MODEL", "API_DATABASE_PATH", "PYTHONPATH"):
        env.pop(key, None)
    env["QUESTIONNAIRE_HOME"] = str(home)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json; from rscb_questionnaire.settings import settings; "
                "print(json.dumps([settings.OPENAI_MODEL, str(settings.API_DATABASE_PATH)]))"
            ),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout) == [
        "explicit-home-model",
        str(home / "data" / "questionnaire-security.db"),
    ]


def test_runtime_config_does_not_load_parent_dotenv(tmp_path):
    (tmp_path / ".env").write_text("OPENAI_MODEL=parent-project-model\n")
    child = tmp_path / "questionnaire-experiment"
    child.mkdir()
    (child / ".env").write_text("OPENAI_MODEL=questionnaire-model\n")
    env = dict(os.environ)
    for key in ("OPENAI_MODEL", "QUESTIONNAIRE_HOME", "API_DATABASE_PATH", "PYTHONPATH"):
        env.pop(key, None)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json; from rscb_questionnaire.settings import settings; "
                "print(json.dumps([settings.OPENAI_MODEL, str(settings.API_DATABASE_PATH)]))"
            ),
        ],
        cwd=child,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout) == [
        "questionnaire-model",
        str(child / "data" / "questionnaire-security.db"),
    ]
    (child / ".env").unlink()
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            ("from rscb_questionnaire.settings import settings; print(settings.OPENAI_MODEL)"),
        ],
        cwd=child,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() != "parent-project-model"


_VERBOSE_LEVEL = 2


def test_agno_debug_level_accepts_env_strings():
    # O .env entrega strings; o Literal[1, 2] sozinho rejeitava "1".
    assert Settings(AGNO_DEBUG_LEVEL="1").AGNO_DEBUG_LEVEL == 1
    assert Settings(AGNO_DEBUG_LEVEL="2").AGNO_DEBUG_LEVEL == _VERBOSE_LEVEL
    assert Settings(AGNO_DEBUG_LEVEL=2).AGNO_DEBUG_LEVEL == _VERBOSE_LEVEL


def test_agno_debug_level_still_rejects_invalid_values():
    with pytest.raises(ValidationError):
        Settings(AGNO_DEBUG_LEVEL="3")
    with pytest.raises(ValidationError):
        Settings(AGNO_DEBUG_LEVEL="verbose")


def test_installed_default_profile_works_outside_checkout(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    args = _parser().parse_args(["run", "--brief", "Backend Python"])
    profile = _apply_profile(args)

    assert profile.front is ResearchFront.SECURITY
    assert args.benign == 1
    assert args.malicious == 3  # noqa: PLR2004
    assert args.benign_responses == 1
    assert args.malicious_responses == 2  # noqa: PLR2004
    assert args.questionnaire_evaluator is True
    assert args.output == Path("outputs/security/scenario.json")


def test_validate_profile_defaults_to_the_bundled_security_profile(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    args = _parser().parse_args(["validate-profile"])
    profile = load_experiment_profile(args.profile)
    assert profile.front is ResearchFront.SECURITY


def test_prompt_sync_is_packaged_and_uses_isolated_namespace(monkeypatch):
    sync = importlib.import_module("rscb_questionnaire.sync_prompts")
    writes = []

    class Client:
        def get_prompt(self, *args, **kwargs):
            raise LookupError("No remote prompt exists")

        def create_prompt(self, **kwargs):
            writes.append(kwargs)
            return type("Created", (), {"version": 1})()

    monkeypatch.setattr(sync, "get_langfuse_client", Client)
    monkeypatch.setattr(sync, "flush_langfuse", lambda: None)
    assert sync.sync_prompts() == 0
    assert {entry["name"] for entry in writes} == set(PROMPTS)
    assert all(entry["name"].startswith("recruitsecbench/questionnaire/") for entry in writes)
    assert all(entry["prompt"] == PROMPTS[entry["name"]] for entry in writes)
