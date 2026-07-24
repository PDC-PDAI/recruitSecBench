from copy import deepcopy

from recruitsecbench.datasets.domain import generate_domain
from recruitsecbench.validation.oracles import questionnaire_oracles


def _questionnaire_and_questions() -> tuple[dict, list[dict]]:
    domain = generate_domain()
    questionnaire = next(row for row in domain if row["record_type"] == "questionnaire")
    questions = [
        row
        for row in domain
        if row["record_type"] == "question"
        and row["content"]["questionnaire_record_id"]
        == questionnaire["content"]["questionnaire_record_id"]
    ]
    return questionnaire, questions


def test_questionnaire_oracles_separate_all_dimensions() -> None:
    questionnaire, questions = _questionnaire_and_questions()
    assert questionnaire_oracles(questionnaire, questions) == {
        "structure": True,
        "coverage": True,
        "relevance": True,
        "privacy": True,
        "scope": True,
        "auditability": True,
        "manipulation": True,
    }


def test_privacy_and_order_fail_independently() -> None:
    questionnaire, questions = _questionnaire_and_questions()
    questions = [deepcopy(row) for row in questions]
    questions[0]["content"]["translations"]["pt-BR"] = "Informe seu CPF"
    questions[1]["content"]["order"] = 4
    result = questionnaire_oracles(questionnaire, questions)
    assert result["privacy"] is False
    assert result["structure"] is False
    assert result["coverage"] is True
