"""Privacy-safe reference ingestion for rewritten questionnaire corpora.

The source corpus may contain real job descriptions and organization-specific wording.
It therefore remains an input to local generation only. Public benchmark artifacts use
only a question's order, skill tag, response type, and a one-way content fingerprint.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from recruitsecbench.datasets.models import ResponseType

DEFAULT_REFERENCE_PATH = Path("data/questionnaire_rewritten.jsonl")
QUESTIONS_PER_REFERENCE = 10


class QuestionnaireReferenceError(ValueError):
    """Raised when a rewritten-questionnaire corpus cannot be safely consumed."""


@dataclass(frozen=True)
class ReferenceQuestion:
    """Non-identifying design signals extracted from one source question."""

    position: int
    skill_tag: str
    response_type: str
    rewritten_text_sha256: str


@dataclass(frozen=True)
class QuestionnaireReference:
    """A validated, privacy-minimized questionnaire design blueprint."""

    questions: tuple[ReferenceQuestion, ...]


@dataclass(frozen=True)
class ReferenceCorpus:
    """Validated local corpus plus a stable fingerprint for provenance."""

    path: Path
    sha256: str
    questionnaires: tuple[QuestionnaireReference, ...]


def _normalized_skill_tag(value: object, *, line_number: int, position: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise QuestionnaireReferenceError(
            f"line {line_number}, question {position}: skillTag must be a non-empty string"
        )
    normalized = value.strip().casefold().replace(" ", "_")
    if not all(character.isalnum() or character == "_" for character in normalized):
        raise QuestionnaireReferenceError(
            f"line {line_number}, question {position}: unsupported skillTag"
        )
    return normalized


def _parse_questionnaire(row: dict[str, Any], *, line_number: int) -> QuestionnaireReference:
    payload = row.get("rewritten_questionnaire")
    questions = payload.get("questions") if isinstance(payload, dict) else None
    if not isinstance(questions, list) or len(questions) != QUESTIONS_PER_REFERENCE:
        raise QuestionnaireReferenceError(
            f"line {line_number}: expected exactly {QUESTIONS_PER_REFERENCE} rewritten questions"
        )

    parsed: list[ReferenceQuestion] = []
    for expected_position, item in enumerate(questions, start=1):
        if not isinstance(item, dict):
            raise QuestionnaireReferenceError(
                f"line {line_number}, question {expected_position}: expected an object"
            )
        position = item.get("position")
        if position != expected_position:
            raise QuestionnaireReferenceError(
                f"line {line_number}: positions must be ordered from 1 to {QUESTIONS_PER_REFERENCE}"
            )
        rewritten_text = item.get("rewritten_text")
        if not isinstance(rewritten_text, str) or not rewritten_text.strip():
            raise QuestionnaireReferenceError(
                f"line {line_number}, question {position}: rewritten_text must be non-empty"
            )
        response_type = item.get("type")
        if response_type not in {member.value for member in ResponseType}:
            raise QuestionnaireReferenceError(
                f"line {line_number}, question {position}: unsupported response type"
            )
        parsed.append(
            ReferenceQuestion(
                position=position,
                skill_tag=_normalized_skill_tag(
                    item.get("skillTag"), line_number=line_number, position=position
                ),
                response_type=response_type,
                rewritten_text_sha256=hashlib.sha256(
                    rewritten_text.strip().encode("utf-8")
                ).hexdigest(),
            )
        )
    return QuestionnaireReference(questions=tuple(parsed))


def load_reference_corpus(path: Path = DEFAULT_REFERENCE_PATH) -> ReferenceCorpus:
    """Validate a local corpus without retaining job or question text in outputs."""

    if not path.is_file():
        raise QuestionnaireReferenceError(f"questionnaire reference corpus not found: {path}")
    raw = path.read_bytes()
    questionnaires: list[QuestionnaireReference] = []
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise QuestionnaireReferenceError(
                f"line {line_number}: invalid JSON ({error.msg})"
            ) from error
        if not isinstance(row, dict):
            raise QuestionnaireReferenceError(f"line {line_number}: expected an object")
        questionnaires.append(_parse_questionnaire(row, line_number=line_number))
    if not questionnaires:
        raise QuestionnaireReferenceError("questionnaire reference corpus is empty")
    return ReferenceCorpus(
        path=path,
        sha256=hashlib.sha256(raw).hexdigest(),
        questionnaires=tuple(questionnaires),
    )


def select_questionnaires(
    corpus: ReferenceCorpus, *, count: int, seed: int
) -> tuple[QuestionnaireReference, ...]:
    """Select stable blueprints without exposing source row identifiers or text."""

    if count < 1:
        raise ValueError("count must be positive")
    selected: list[QuestionnaireReference] = []
    for index in range(count):
        digest = hashlib.sha256(f"{corpus.sha256}:{seed}:{index}".encode("ascii")).digest()
        selected_index = int.from_bytes(digest[:8], "big") % len(corpus.questionnaires)
        selected.append(corpus.questionnaires[selected_index])
    return tuple(selected)
