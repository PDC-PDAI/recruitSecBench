"""Canonical, adapter-independent RecruitSecBench entities."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

CanonicalId = Annotated[
    str,
    StringConstraints(min_length=1, max_length=160, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"),
]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]

CANONICAL_ALIASES: dict[str, str] = {
    "HiringProcessOpening.id": "vacancy_id",
    "openingId": "vacancy_id",
    "vaga_id": "vacancy_id",
    "job_opening_id": "vacancy_id",
    "jobOpening_id": "vacancy_id",
    "Application.id": "application_id",
    "candidaturaId": "application_id",
    "candidatura_id": "application_id",
    "HiringProcess.id": "hiring_process_id",
    "processoSeletivoId": "hiring_process_id",
    "hiringProcessId": "hiring_process_id",
    "Questionnaire.id": "questionnaire_id",
    "questionnaireId": "questionnaire_id",
    "Question.id": "question_id",
    "questionId": "question_id",
}


class AliasConflictError(ValueError):
    """Raised when aliases disagree about one canonical identifier."""


def normalize_aliases(
    values: dict[str, Any],
    aliases: dict[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Return canonical values plus the names of aliases that were consumed."""

    alias_map = aliases or CANONICAL_ALIASES
    normalized: dict[str, Any] = {}
    consumed: dict[str, str] = {}
    for key, value in values.items():
        canonical = alias_map.get(key, key)
        if canonical in normalized and normalized[canonical] != value:
            raise AliasConflictError(f"conflicting values for canonical field: {canonical}")
        normalized[canonical] = value
        if canonical != key:
            consumed[key] = canonical
    return normalized, consumed


class CanonicalModel(BaseModel):
    """Base class that refuses undocumented aliases and fields."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Partition(StrEnum):
    DEVELOPMENT = "development"
    PILOT = "pilot"
    EVALUATION = "evaluation"
    HOLDOUT = "holdout"


class RecordType(StrEnum):
    PROJECT = "project"
    HIRING_PROCESS = "hiring_process"
    VACANCY = "vacancy"
    CANDIDATE = "candidate"
    CV = "cv"
    APPLICATION = "application"
    QUESTIONNAIRE = "questionnaire"
    QUESTION = "question"
    CANDIDATE_RESPONSE = "candidate_response"
    AGENT_SESSION = "agent_session"
    TOOL = "tool"
    PROCESS_STATE = "process_state"
    EVALUATION_CRITERION = "evaluation_criterion"
    EVALUATION_OUTCOME = "evaluation_outcome"


class SourceKind(StrEnum):
    REAL_ANONYMIZED = "real_anonymized"
    SYNTHETIC = "synthetic"
    DERIVED = "derived"
    MOCKED = "mocked"


class PiiStatus(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    PENDING_REVIEW = "pending_review"
    ANONYMIZED_REVIEWED = "anonymized_reviewed"
    RESTRICTED_PERSONAL_DATA = "restricted_personal_data"


class Provenance(CanonicalModel):
    source_kind: SourceKind
    generated_at: AwareDatetime
    content_sha256: Sha256
    pii_status: PiiStatus
    source_record_id: CanonicalId | None = None
    generator: str | None = None
    authorization_ref: str | None = None
    notes: str | None = None


class AuthorizationScope(CanonicalModel):
    project_id: CanonicalId
    hiring_process_id: CanonicalId | None = None
    vacancy_id: CanonicalId | None = None
    candidate_id: CanonicalId | None = None
    application_id: CanonicalId | None = None
    questionnaire_id: CanonicalId | None = None
    actor_id: CanonicalId | None = None
    session_id: CanonicalId | None = None


class Project(CanonicalModel):
    project_id: CanonicalId
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    synthetic: bool = True
    provenance: Provenance


class HiringProcessStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class HiringProcess(CanonicalModel):
    hiring_process_id: CanonicalId
    project_id: CanonicalId
    code: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: HiringProcessStatus
    provenance: Provenance


class EvaluationCriterion(CanonicalModel):
    criterion_id: CanonicalId
    vacancy_id: CanonicalId
    competency: str = Field(min_length=1)
    description: str = Field(min_length=1)
    weight: float = Field(gt=0)
    privacy_restrictions: list[str] = Field(default_factory=list)


class Vacancy(CanonicalModel):
    vacancy_id: CanonicalId
    hiring_process_id: CanonicalId
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    seniority: str = Field(min_length=1)
    requirements: list[str] = Field(min_length=1)
    competencies: list[str] = Field(min_length=1)
    evaluation_criteria: list[EvaluationCriterion] = Field(min_length=1)
    status: HiringProcessStatus
    provenance: Provenance
    variant_of_vacancy_id: CanonicalId | None = None

    @model_validator(mode="after")
    def unique_criteria(self) -> Vacancy:
        identifiers = [item.criterion_id for item in self.evaluation_criteria]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("criterion IDs must be unique within a vacancy")
        if any(item.vacancy_id != self.vacancy_id for item in self.evaluation_criteria):
            raise ValueError("criterion vacancy_id must match its vacancy")
        return self


class CandidateSource(StrEnum):
    SYNTHETIC = "SYNTHETIC"
    REAL_DERIVED = "REAL_DERIVED"


class PrivacyStatus(StrEnum):
    SYNTHETIC = "SYNTHETIC"
    PENDING_HUMAN_REVIEW = "PENDING_HUMAN_REVIEW"
    APPROVED_CONTROLLED = "APPROVED_CONTROLLED"
    QUARANTINED = "QUARANTINED"
    REVOKED = "REVOKED"


class Candidate(CanonicalModel):
    candidate_id: CanonicalId
    source_class: CandidateSource
    profile_label: str = Field(min_length=1)
    professional_area: str = Field(min_length=1)
    seniority: str = Field(min_length=1)
    language: str = Field(min_length=2, max_length=16)
    privacy_status: PrivacyStatus
    provenance: Provenance

    @model_validator(mode="after")
    def enforce_source_privacy(self) -> Candidate:
        if self.source_class is CandidateSource.SYNTHETIC:
            if self.privacy_status is not PrivacyStatus.SYNTHETIC:
                raise ValueError("synthetic candidates require SYNTHETIC privacy status")
        elif self.privacy_status is PrivacyStatus.SYNTHETIC:
            raise ValueError("real-derived candidates cannot use SYNTHETIC privacy status")
        return self


class ProfessionalDocument(CanonicalModel):
    document_id: CanonicalId
    candidate_id: CanonicalId
    document_type: str = Field(min_length=1)
    language: str = Field(min_length=2, max_length=16)
    derived_text: str = Field(min_length=1)
    structured_skills: list[str] = Field(default_factory=list)
    generalized_experiences: list[str] = Field(default_factory=list)
    generalized_education: list[str] = Field(default_factory=list)
    canary_references: list[CanonicalId] = Field(default_factory=list)
    privacy_review_id: CanonicalId | None = None
    source_lineage_id: CanonicalId | None = None
    synthetic: bool = True
    provenance: Provenance


class EvaluationState(StrEnum):
    PENDENTE = "PENDENTE"
    DOCUMENTOS_INDEXADOS = "DOCUMENTOS_INDEXADOS"
    EM_AVALIACAO = "EM_AVALIACAO"
    CONCLUIDO = "CONCLUIDO"
    FALHOU = "FALHOU"


class StateTransition(CanonicalModel):
    from_state: EvaluationState
    to_state: EvaluationState
    occurred_at: AwareDatetime
    round_token: CanonicalId


class Application(CanonicalModel):
    application_id: CanonicalId
    candidate_id: CanonicalId
    vacancy_id: CanonicalId
    hiring_process_id: CanonicalId
    current_state: EvaluationState
    state_history: list[StateTransition] = Field(default_factory=list)
    scope: AuthorizationScope
    questionnaire_ids: list[CanonicalId] = Field(default_factory=list)
    round_token: CanonicalId
    provenance: Provenance


class EditorialStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class GenerationStatus(StrEnum):
    GENERATING = "GENERATING"
    READY = "READY"
    FAILED = "FAILED"


class Questionnaire(CanonicalModel):
    questionnaire_id: CanonicalId
    vacancy_id: CanonicalId
    hiring_process_id: CanonicalId
    project_id: CanonicalId
    version: int = Field(ge=1)
    purpose: str = Field(min_length=1)
    editorial_status: EditorialStatus
    generation_status: GenerationStatus | None = None
    criterion_ids: list[CanonicalId] = Field(default_factory=list)
    question_ids: list[CanonicalId] = Field(default_factory=list)
    application_id: CanonicalId | None = None
    provenance: Provenance


class ResponseType(StrEnum):
    SHORT_TEXT = "SHORT_TEXT"
    LONG_TEXT = "LONG_TEXT"
    FILE_UPLOAD = "FILE_UPLOAD"


class Question(CanonicalModel):
    question_id: CanonicalId
    questionnaire_id: CanonicalId
    text: str = Field(min_length=1)
    response_type: ResponseType
    criterion_id: CanonicalId
    required: bool
    order: int = Field(ge=1)
    weight: float = Field(gt=0)
    relevance_rationale: str | None = None
    review_status: str | None = None


class CandidateResponse(CanonicalModel):
    response_id: CanonicalId
    application_id: CanonicalId
    candidate_id: CanonicalId
    vacancy_id: CanonicalId
    questionnaire_id: CanonicalId
    question_id: CanonicalId
    answer_text: str | None = None
    synthetic_file_id: CanonicalId | None = None
    expected_quality: str = Field(min_length=1)
    adversarial: bool = False
    created_at: AwareDatetime

    @model_validator(mode="after")
    def exactly_one_answer(self) -> CandidateResponse:
        if (self.answer_text is None) == (self.synthetic_file_id is None):
            raise ValueError("exactly one answer representation is required")
        return self


class DatasetEnvelope(CanonicalModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    record_id: CanonicalId
    record_type: RecordType
    partition: Partition
    scope: AuthorizationScope
    provenance: Provenance
    content: dict[str, Any]
    tags: list[str] = Field(default_factory=list)
