from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from rscb_questionnaire.schemas.benchmark.schema import BenchmarkRecord
from rscb_questionnaire.schemas.coordinator_prompt.schema import CoordinatorPromptBatch
from rscb_questionnaire.schemas.evaluation.schema import EvaluationExecution
from rscb_questionnaire.schemas.experiment.schema import ResearchFront
from rscb_questionnaire.schemas.job_description.schema import JobDescription
from rscb_questionnaire.schemas.questionnaire.schema import QuestionnaireExecution
from rscb_questionnaire.schemas.response.schema import ResponseGenerationBatch
from rscb_questionnaire.variants import Defense


class ScenarioRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    defense: Defense = Defense.BASELINE
    scenario_id: str = Field(default_factory=lambda: f"scenario-{uuid.uuid4()}")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    research_targets: list[str] = Field(
        default_factory=lambda: ["AgentDebug-RH", "RecruitSecBench"]
    )
    research_front: ResearchFront | None = None
    experiment_profile: str | None = None
    job_description: JobDescription
    coordinator_prompts: CoordinatorPromptBatch
    executions: list[QuestionnaireExecution]
    response_batches: list[ResponseGenerationBatch] = Field(default_factory=list)
    evaluation_executions: list[EvaluationExecution] = Field(default_factory=list)
    benchmark_records: list[BenchmarkRecord]
