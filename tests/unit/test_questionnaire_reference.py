import json
from pathlib import Path

import pytest

from recruitsecbench.datasets.questionnaire_reference import (
    QuestionnaireReferenceError,
    load_reference_corpus,
    select_questionnaires,
)


def _row() -> dict:
    return {
        "source_id": "do-not-export",
        "job": {"title": "Sensitive source title"},
        "rewritten_questionnaire": {
            "questions": [
                {
                    "position": position,
                    "skillTag": "analise de dados",
                    "type": "LONG_TEXT" if position % 2 else "SHORT_TEXT",
                    "rewritten_text": f"Question text {position} that must not be exported",
                }
                for position in range(1, 11)
            ]
        },
    }


def test_reference_loader_minimizes_source_content_and_is_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "questionnaires.jsonl"
    path.write_text(json.dumps(_row()) + "\n", encoding="utf-8")

    corpus = load_reference_corpus(path)
    selected = select_questionnaires(corpus, count=3, seed=2026)

    assert len(corpus.sha256) == 64
    assert len(corpus.questionnaires) == 1
    assert len(selected) == 3
    question = selected[0].questions[0]
    assert question.skill_tag == "analise_de_dados"
    assert question.response_type == "LONG_TEXT"
    assert len(question.rewritten_text_sha256) == 64
    assert "Question text" not in repr(corpus)
    assert "Sensitive source title" not in repr(corpus)


def test_reference_loader_rejects_wrong_question_count(tmp_path: Path) -> None:
    row = _row()
    row["rewritten_questionnaire"]["questions"].pop()
    path = tmp_path / "invalid.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    with pytest.raises(QuestionnaireReferenceError, match="exactly 10"):
        load_reference_corpus(path)
