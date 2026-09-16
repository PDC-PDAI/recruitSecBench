from __future__ import annotations

import importlib
from pathlib import Path

from rscb_questionnaire.cli import _apply_profile, _parser
from rscb_questionnaire.prompts.raw_prompts import PROMPTS
from rscb_questionnaire.schemas.experiment.schema import ResearchFront
from rscb_questionnaire.services.experiment.profile import load_experiment_profile


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
