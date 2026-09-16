from __future__ import annotations

import importlib
import json

import httpx
import pytest
from fastapi import status

from rscb_questionnaire import battery
from rscb_questionnaire.api.app import create_app
from rscb_questionnaire.repositories.sqlite import SQLiteRepository
from rscb_questionnaire.services.scenario.service import ScenarioService
from rscb_questionnaire.settings import settings
from rscb_questionnaire.variants import DEFENSE_REVISIONS, Defense, variant_prompts

from .test_api import FakeEvaluationService as ManualEvaluator
from .test_api import _scenario
from .test_scenario_evaluation import (
    FakeCoordinatorService,
    FakeEvaluationService,
    FakeJobService,
    FakeQuestionnaireService,
    FakeResponseService,
)


@pytest.mark.parametrize("defense", list(Defense))
def test_selects_both_real_services(defense, monkeypatch):
    monkeypatch.setattr(settings, "QUESTIONNAIRE_DEFENSE", Defense.CAMEL)
    service = ScenarioService(defense=defense)
    prefix = (
        "rscb_questionnaire.services"
        if defense is Defense.BASELINE
        else f"rscb_questionnaire.variants.{defense.value}"
    )
    assert type(service.questionnaire_service).__module__.startswith(prefix + ".questionnaire")
    assert type(service.evaluation_service).__module__.startswith(prefix + ".evaluation")
    assert ScenarioService().defense is Defense.CAMEL


@pytest.mark.asyncio
@pytest.mark.parametrize("defense", list(Defense))
async def test_pipeline_persists_defense_on_all_stages(defense):
    service = ScenarioService(
        defense=defense,
        job_service=FakeJobService(),
        coordinator_service=FakeCoordinatorService(),
        questionnaire_service=FakeQuestionnaireService(),
        response_service=FakeResponseService(),
        evaluation_service=FakeEvaluationService(),
    )
    result = await service.run("Backend Python")
    assert result.defense is defense
    assert result.evaluation_executions
    assert {record.task_type for record in result.benchmark_records} == {
        "questionnaire_generation",
        "response_generation",
        "questionnaire_evaluation",
    }
    for record in result.benchmark_records:
        assert record.provenance["defense"] == defense.value
        assert record.provenance["defense_source_commit"] == DEFENSE_REVISIONS[defense.value]


@pytest.mark.asyncio
async def test_manual_evaluation_uses_persisted_defense_after_restart(tmp_path, monkeypatch):
    repo = SQLiteRepository(tmp_path / "api.db")
    scenario = _scenario()
    scenario.defense = Defense.FIDES
    repo.save_scenario(scenario)
    repo.close()
    repo = SQLiteRepository(tmp_path / "api.db")
    monkeypatch.setattr(settings, "QUESTIONNAIRE_DEFENSE", Defense.CAMEL)
    calls = []
    evaluator = ManualEvaluator()

    def select(defense, role):
        calls.append((defense, role))
        return evaluator

    monkeypatch.setattr(
        importlib.import_module("rscb_questionnaire.api.app"), "build_service", select
    )
    app = create_app(repository=repo)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            submitted = await client.post(
                "/api/v1/questionnaires/questionnaire-1/submissions",
                json={
                    "answers": [
                        {"question_number": 1, "text": "Separaria rotas e serviços testáveis."}
                    ]
                },
            )
            submission_id = submitted.json()["submission_id"]
            for _ in range(2):
                response = await client.post(f"/api/v1/submissions/{submission_id}/evaluate")
                assert response.status_code == status.HTTP_200_OK
            assert calls == [(Defense.FIDES, "evaluation")]
            assert evaluator.calls == 1
    finally:
        repo.close()


@pytest.mark.parametrize("defense", list(Defense))
def test_sync_selects_variant_prompts(defense, monkeypatch):
    sync = importlib.import_module("rscb_questionnaire.sync_prompts")
    writes = []

    class Client:
        def get_prompt(self, *args, **kwargs):
            raise LookupError("Missing")

        def create_prompt(self, **kwargs):
            writes.append(kwargs)
            return type("Created", (), {"version": 1})()

    monkeypatch.setattr(sync, "get_langfuse_client", Client)
    monkeypatch.setattr(sync, "flush_langfuse", lambda: None)
    assert sync.sync_prompts(defense) == 0
    assert {entry["name"]: entry["prompt"] for entry in writes} == variant_prompts(defense)
    if defense is not Defense.BASELINE:
        assert all(f"/questionnaire/{defense.value}/" in entry["name"] for entry in writes)


@pytest.mark.asyncio
async def test_battery_dry_run_and_resume_reject_mixed_defenses(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    args = battery._parser().parse_args(["--dry-run", "--defense", "fides"])
    assert await battery._run(args) == 0
    manifest_path = args.output_dir / "manifest.json"
    original = manifest_path.read_bytes()
    manifest = json.loads(original)
    assert manifest["planned_generations"] == 380  # noqa: PLR2004 - matriz histórica 5 × 76
    assert manifest["defense"] == "fides"
    assert manifest["evaluation_enabled"] is False
    assert manifest["classification_enabled"] is False
    assert await battery._run(args) == 0
    assert manifest_path.read_bytes() == original
    args.defense = Defense.CAMEL
    with pytest.raises(ValueError, match="another output directory"):
        await battery._run(args)
    assert manifest_path.read_bytes() == original
    args.defense = Defense.FIDES
    args.repetitions = 2
    with pytest.raises(ValueError, match="another output directory"):
        await battery._run(args)


@pytest.mark.asyncio
async def test_battery_executes_selected_generator_and_resumes(tmp_path, monkeypatch):
    monkeypatch.setattr(battery.settings, "OPENAI_API_KEY", "test-key")
    calls = []

    def select(defense, role):
        calls.append((defense, role))
        return FakeQuestionnaireService()

    monkeypatch.setattr(battery, "build_service", select)
    monkeypatch.setattr(battery, "flush_langfuse", lambda: None)
    args = battery._parser().parse_args(
        ["--defense", "camel", "--limit", "1", "--output-dir", str(tmp_path)]
    )
    assert await battery._run(args) == 0
    first = json.loads((tmp_path / "generations.jsonl").read_text())
    assert first["defense"] == "camel"
    assert first["defense_source_commit"] == DEFENSE_REVISIONS["camel"]
    assert first["status"] in {"succeeded", "refused"}
    assert await battery._run(args) == 0
    records = battery._records(tmp_path / "generations.jsonl")
    assert len({r["run_key"] for r in records}) == 2  # noqa: PLR2004 - duas retomadas
    assert calls == [(Defense.CAMEL, "questionnaire")] * 2
