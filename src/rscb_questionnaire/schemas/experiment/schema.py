from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

_MAX_RESPONSES_PER_QUESTIONNAIRE = 20
_MAX_EVALUATIONS_PER_SCENARIO = 200


class ResearchFront(str, Enum):
    SECURITY = "security"


class PipelineProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    benign_commands: int = Field(default=3, ge=0, le=100)
    malicious_commands: int = Field(default=3, ge=0, le=100)
    benign_responses: int = Field(default=1, ge=0, le=20)
    malicious_responses: int = Field(default=1, ge=0, le=20)
    questionnaire_evaluator: bool = True

    @model_validator(mode="after")
    def validate_counts(self) -> PipelineProfile:
        command_total = self.benign_commands + self.malicious_commands
        response_total = self.benign_responses + self.malicious_responses
        if command_total < 1:
            raise ValueError("O perfil precisa gerar ao menos um comando.")
        if response_total > _MAX_RESPONSES_PER_QUESTIONNAIRE:
            raise ValueError("O perfil aceita no máximo 20 respostas por questionário.")
        if command_total * response_total > _MAX_EVALUATIONS_PER_SCENARIO:
            raise ValueError("O perfil aceita no máximo 200 avaliações potenciais.")
        if not self.questionnaire_evaluator and response_total:
            raise ValueError(
                "Sem questionnaire_evaluator, benign_responses e malicious_responses "
                "devem ser zero."
            )
        return self


class ArtifactProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output_dir: Path
    scenario_json: str = "scenario.json"
    benchmark_jsonl: str = "benchmark.jsonl"
    agent_debug_jsonl: str = "agent-debug.jsonl"
    trajectories_dir: str = "trajectories"

    @model_validator(mode="after")
    def validate_relative_names(self) -> ArtifactProfile:
        for field_name in (
            "scenario_json",
            "benchmark_jsonl",
            "agent_debug_jsonl",
            "trajectories_dir",
        ):
            value = Path(getattr(self, field_name))
            if value.is_absolute() or ".." in value.parts:
                raise ValueError(f"{field_name} deve ser relativo a output_dir.")
        return self

    @property
    def scenario_path(self) -> Path:
        return self.output_dir / self.scenario_json

    @property
    def benchmark_path(self) -> Path:
        return self.output_dir / self.benchmark_jsonl

    @property
    def agent_debug_path(self) -> Path:
        return self.output_dir / self.agent_debug_jsonl

    @property
    def trajectory_path(self) -> Path:
        return self.output_dir / self.trajectories_dir


class ExperimentProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="1.0", pattern=r"^1\.0$")
    name: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    front: ResearchFront
    description: str = Field(min_length=1)
    pipeline: PipelineProfile
    artifacts: ArtifactProfile
