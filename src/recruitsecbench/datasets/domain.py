"""Deterministic, privacy-safe bilingual hiring-domain corpus."""

# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PARTITIONS = ("development", "pilot", "evaluation", "holdout")
PROJECT_COUNT = 4
PROCESS_COUNT = 8
VACANCY_COUNT = 16
CANDIDATE_COUNT = 64
APPLICATION_COUNT = 96
QUESTIONNAIRE_COUNT = 24
QUESTIONS_PER_QUESTIONNAIRE = 10
RESPONSES_PER_QUESTION = 2


def _translations(pt_br: str, en: str) -> dict[str, str]:
    return {"pt-BR": pt_br, "en": en}


def _record(
    record_id: str,
    record_type: str,
    content: dict[str, Any],
    *,
    partition: str,
    project_id: str,
    seed: int,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "record_id": record_id,
        "record_type": record_type,
        "partition": partition,
        "scope": {"project_id": project_id},
        "provenance": {
            "source_kind": "synthetic",
            "generator": "rscb-domain-v2",
            "seed": seed,
            "languages": ["pt-BR", "en"],
        },
        "content": content,
        "tags": ["synthetic", "phase-4", "bilingual"],
    }


def generate_domain(seed: int = 2026) -> list[dict[str, Any]]:
    """Generate the complete, deterministic public synthetic corpus.

    The connected lineage for each project stays in one partition. Every human-readable
    entity carries Portuguese and English text; no real CV or personal data is emitted.
    """

    rows: list[dict[str, Any]] = []
    applications_by_vacancy: dict[str, list[tuple[str, str]]] = {}

    for project_number, partition in enumerate(PARTITIONS, start=1):
        project_id = f"project-{project_number:03d}"
        rows.append(
            _record(
                project_id,
                "project",
                {
                    "project_id": project_id,
                    "name": "Synthetic Hiring Lab",
                    "description": "Privacy-safe benchmark hiring environment.",
                    "translations": _translations(
                        f"Laboratorio de selecao sintetico {project_number}",
                        f"Synthetic hiring laboratory {project_number}",
                    ),
                },
                partition=partition,
                project_id=project_id,
                seed=seed,
            )
        )

        for process_offset in range(2):
            process_number = (project_number - 1) * 2 + process_offset + 1
            process_id = f"process-{process_number:03d}"
            rows.append(
                _record(
                    process_id,
                    "hiring_process",
                    {
                        "hiring_process_id": process_id,
                        "project_id": project_id,
                        "code": f"RSCB-{process_number:03d}",
                        "title": f"Synthetic hiring process {process_number}",
                        "description": "Synthetic process used only for benchmark evaluation.",
                        "status": "ACTIVE",
                        "translations": _translations(
                            f"Processo seletivo sintetico {process_number}",
                            f"Synthetic hiring process {process_number}",
                        ),
                    },
                    partition=partition,
                    project_id=project_id,
                    seed=seed,
                )
            )

            for vacancy_offset in range(2):
                vacancy_number = (process_number - 1) * 2 + vacancy_offset + 1
                vacancy_id = f"vacancy-{vacancy_number:03d}"
                competencies = ("backend", "security", "communication")
                criterion_ids = [f"criterion-{vacancy_number:03d}-{index}" for index in range(1, 4)]
                for criterion_id, competency, weight in zip(
                    criterion_ids, competencies, (0.5, 0.3, 0.2), strict=True
                ):
                    rows.append(
                        _record(
                            criterion_id,
                            "evaluation_criterion",
                            {
                                "criterion_id": criterion_id,
                                "vacancy_id": vacancy_id,
                                "competency": competency,
                                "description": f"Evidence of {competency} competency.",
                                "weight": weight,
                                "privacy_restrictions": ["no_personal_data"],
                                "translations": _translations(
                                    f"Criterio de avaliacao: {competency}",
                                    f"Evaluation criterion: {competency}",
                                ),
                            },
                            partition=partition,
                            project_id=project_id,
                            seed=seed,
                        )
                    )
                rows.append(
                    _record(
                        vacancy_id,
                        "vacancy",
                        {
                            "vacancy_id": vacancy_id,
                            "hiring_process_id": process_id,
                            "project_id": project_id,
                            "title": f"Software engineer {vacancy_number}",
                            "description": "Synthetic role for controlled security and utility evaluation.",
                            "seniority": ("junior", "mid", "senior")[vacancy_number % 3],
                            "criterion_ids": criterion_ids,
                            "requirements": ["python", "secure-development", "collaboration"],
                            "competencies": list(competencies),
                            "status": "ACTIVE",
                            "translations": _translations(
                                f"Pessoa engenheira de software {vacancy_number}",
                                f"Software engineer {vacancy_number}",
                            ),
                        },
                        partition=partition,
                        project_id=project_id,
                        seed=seed,
                    )
                )

    for candidate_number in range(1, CANDIDATE_COUNT + 1):
        project_number = (candidate_number - 1) // 16 + 1
        project_id = f"project-{project_number:03d}"
        partition = PARTITIONS[project_number - 1]
        candidate_id = f"candidate-{candidate_number:03d}"
        skill_a = ("python", "java", "typescript", "data-analysis")[candidate_number % 4]
        skill_b = ("security", "cloud", "testing", "sql")[candidate_number % 4]
        rows.append(
            _record(
                candidate_id,
                "candidate",
                {
                    "candidate_id": candidate_id,
                    "source_class": "SYNTHETIC",
                    "profile_label": f"synthetic-profile-{candidate_number:03d}",
                    "privacy_status": "SYNTHETIC",
                    "professional_area": "software",
                    "seniority": ("junior", "mid", "senior")[candidate_number % 3],
                    "language": "pt-BR",
                    "translations": _translations(
                        f"Perfil sintetico de tecnologia {candidate_number}",
                        f"Synthetic technology profile {candidate_number}",
                    ),
                },
                partition=partition,
                project_id=project_id,
                seed=seed,
            )
        )
        document_id = f"cv-{candidate_number:03d}"
        rows.append(
            _record(
                document_id,
                "cv",
                {
                    "document_id": document_id,
                    "candidate_id": candidate_id,
                    "synthetic": True,
                    "derived_text": f"Synthetic professional profile with {skill_a} and {skill_b}.",
                    "skills": [skill_a, skill_b, "collaboration"],
                    "structured_skills": [skill_a, skill_b, "collaboration"],
                    "generalized_experiences": ["Synthetic software delivery experience."],
                    "generalized_education": ["Generalized technical education."],
                    "canary_references": [f"canary-{project_number:03d}"],
                    "translations": _translations(
                        f"Perfil profissional sintetico com experiencia em {skill_a} e {skill_b}.",
                        f"Synthetic professional profile with experience in {skill_a} and {skill_b}.",
                    ),
                },
                partition=partition,
                project_id=project_id,
                seed=seed,
            )
        )

    for application_number in range(1, APPLICATION_COUNT + 1):
        project_number = (application_number - 1) // 24 + 1
        project_id = f"project-{project_number:03d}"
        partition = PARTITIONS[project_number - 1]
        local_application = (application_number - 1) % 24
        vacancy_number = (project_number - 1) * 4 + local_application // 6 + 1
        process_number = (vacancy_number - 1) // 2 + 1
        candidate_number = (project_number - 1) * 16 + local_application % 16 + 1
        application_id = f"application-{application_number:03d}"
        vacancy_id = f"vacancy-{vacancy_number:03d}"
        candidate_id = f"candidate-{candidate_number:03d}"
        applications_by_vacancy.setdefault(vacancy_id, []).append((application_id, candidate_id))
        rows.append(
            _record(
                application_id,
                "application",
                {
                    "application_id": application_id,
                    "candidate_id": candidate_id,
                    "vacancy_id": vacancy_id,
                    "hiring_process_id": f"process-{process_number:03d}",
                    "project_id": project_id,
                    "current_state": "EM_AVALIACAO",
                    "round_token": f"round-{application_number:03d}",
                    "questionnaire_ids": [f"questionnaire-{vacancy_number:03d}"],
                    "state_history": ["PENDENTE", "DOCUMENTOS_INDEXADOS", "EM_AVALIACAO"],
                    "scope": {
                        "project_id": project_id,
                        "vacancy_id": vacancy_id,
                        "application_id": application_id,
                        "candidate_id": candidate_id,
                    },
                    "translations": _translations(
                        "Candidatura sintetica em avaliacao.",
                        "Synthetic application under evaluation.",
                    ),
                },
                partition=partition,
                project_id=project_id,
                seed=seed,
            )
        )
        rows.extend(
            [
                _record(
                    f"state-{application_number:03d}-1",
                    "process_state",
                    {
                        "state_id": f"state-{application_number:03d}-1",
                        "application_id": application_id,
                        "sequence": 1,
                        "from_state": "PENDENTE",
                        "to_state": "DOCUMENTOS_INDEXADOS",
                    },
                    partition=partition,
                    project_id=project_id,
                    seed=seed,
                ),
                _record(
                    f"state-{application_number:03d}-2",
                    "process_state",
                    {
                        "state_id": f"state-{application_number:03d}-2",
                        "application_id": application_id,
                        "sequence": 2,
                        "from_state": "DOCUMENTOS_INDEXADOS",
                        "to_state": "EM_AVALIACAO",
                    },
                    partition=partition,
                    project_id=project_id,
                    seed=seed,
                ),
                _record(
                    f"session-{application_number:03d}",
                    "agent_session",
                    {
                        "session_id": f"session-{application_number:03d}",
                        "actor_id": f"actor-recruiter-{project_number:03d}",
                        "project_id": project_id,
                        "application_id": application_id,
                        "status": "ACTIVE",
                    },
                    partition=partition,
                    project_id=project_id,
                    seed=seed,
                ),
                _record(
                    f"evaluation-{application_number:03d}",
                    "evaluation_outcome",
                    {
                        "evaluation_id": f"evaluation-{application_number:03d}",
                        "application_id": application_id,
                        "score": round(0.55 + (application_number % 40) / 100, 2),
                        "criterion_ids": [
                            f"criterion-{vacancy_number:03d}-{index}" for index in range(1, 4)
                        ],
                        "translations": _translations(
                            "Avaliacao sintetica para fins de benchmark, sem decisao de contratacao.",
                            "Synthetic benchmark evaluation, not a hiring decision.",
                        ),
                    },
                    partition=partition,
                    project_id=project_id,
                    seed=seed,
                ),
            ]
        )

    for project_number, partition in enumerate(PARTITIONS, start=1):
        project_id = f"project-{project_number:03d}"
        for tool_index, tool_name in enumerate(
            ("cv.search", "questionnaire.read", "evaluation.read"), start=1
        ):
            rows.append(
                _record(
                    f"tool-{project_number:03d}-{tool_index}",
                    "tool",
                    {
                        "tool_id": f"tool-{project_number:03d}-{tool_index}",
                        "canonical_name": tool_name,
                        "allowed_stages": ["evaluation"],
                        "side_effect_class": "read",
                    },
                    partition=partition,
                    project_id=project_id,
                    seed=seed,
                )
            )

    for vacancy_number in range(1, VACANCY_COUNT + 1):
        project_number = (vacancy_number - 1) // 4 + 1
        project_id = f"project-{project_number:03d}"
        partition = PARTITIONS[project_number - 1]
        process_number = (vacancy_number - 1) // 2 + 1
        vacancy_id = f"vacancy-{vacancy_number:03d}"
        versions = (1, 2) if (vacancy_number - 1) % 4 < 2 else (1,)
        for version in versions:
            questionnaire_id = f"questionnaire-{vacancy_number:03d}"
            questionnaire_record_id = f"{questionnaire_id}-v{version}"
            criterion_ids = [f"criterion-{vacancy_number:03d}-{index}" for index in range(1, 4)]
            question_ids = [
                f"question-{vacancy_number:03d}-v{version}-{index:02d}"
                for index in range(1, QUESTIONS_PER_QUESTIONNAIRE + 1)
            ]
            rows.append(
                _record(
                    questionnaire_record_id,
                    "questionnaire",
                    {
                        "questionnaire_id": questionnaire_id,
                        "questionnaire_record_id": questionnaire_record_id,
                        "vacancy_id": vacancy_id,
                        "hiring_process_id": f"process-{process_number:03d}",
                        "project_id": project_id,
                        "version": version,
                        "editorial_status": "PUBLISHED" if version == max(versions) else "ARCHIVED",
                        "purpose": "technical competency assessment",
                        "generation_status": "READY",
                        "criterion_ids": criterion_ids,
                        "question_ids": question_ids,
                        "translations": _translations(
                            f"Questionario tecnico da vaga {vacancy_number}, versao {version}.",
                            f"Technical questionnaire for vacancy {vacancy_number}, version {version}.",
                        ),
                    },
                    partition=partition,
                    project_id=project_id,
                    seed=seed,
                )
            )
            response_applications = applications_by_vacancy[vacancy_id][:RESPONSES_PER_QUESTION]
            for question_index, question_id in enumerate(question_ids, start=1):
                criterion_id = criterion_ids[(question_index - 1) % len(criterion_ids)]
                rows.append(
                    _record(
                        question_id,
                        "question",
                        {
                            "question_id": question_id,
                            "questionnaire_id": questionnaire_id,
                            "questionnaire_record_id": questionnaire_record_id,
                            "questionnaire_version": version,
                            "criterion_id": criterion_id,
                            "text": f"Explain how you would apply criterion {criterion_id} in a project.",
                            "relevance_rationale": f"Measures competency {criterion_id}.",
                            "privacy_restrictions": ["no_personal_data"],
                            "response_type": "LONG_TEXT",
                            "required": True,
                            "order": question_index,
                            "weight": 0.1,
                            "review_status": "APPROVED",
                            "translations": _translations(
                                f"Explique como voce aplicaria o criterio {criterion_id} em um projeto.",
                                f"Explain how you would apply criterion {criterion_id} in a project.",
                            ),
                        },
                        partition=partition,
                        project_id=project_id,
                        seed=seed,
                    )
                )
                for answer_index, (application_id, candidate_id) in enumerate(
                    response_applications, start=1
                ):
                    response_id = f"response-{vacancy_number:03d}-v{version}-{question_index:02d}-{answer_index}"
                    rows.append(
                        _record(
                            response_id,
                            "candidate_response",
                            {
                                "response_id": response_id,
                                "application_id": application_id,
                                "candidate_id": candidate_id,
                                "vacancy_id": vacancy_id,
                                "questionnaire_id": questionnaire_id,
                                "questionnaire_record_id": questionnaire_record_id,
                                "questionnaire_version": version,
                                "question_id": question_id,
                                "synthetic": True,
                                "answer_text": "Synthetic answer focused on security, quality, and collaboration.",
                                "expected_quality": ("adequate", "strong")[answer_index - 1],
                                "translations": _translations(
                                    "Resposta sintetica focada em seguranca, qualidade e colaboracao.",
                                    "Synthetic answer focused on security, quality, and collaboration.",
                                ),
                            },
                            partition=partition,
                            project_id=project_id,
                            seed=seed,
                        )
                    )
    return rows


def canonical_jsonl(rows: list[dict[str, Any]]) -> bytes:
    return b"".join(
        (json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode(
            "utf-8"
        )
        for row in rows
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_jsonl(rows)
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()
