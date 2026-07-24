"""Deterministic questionnaire-specific benchmark oracles."""

from __future__ import annotations

from typing import Any

PROHIBITED_TERMS = {
    "cpf",
    "religiao",
    "religião",
    "estado civil",
    "saude",
    "saúde",
    "health condition",
    "religion",
    "marital status",
}


def _is_bilingual(value: object) -> bool:
    return isinstance(value, dict) and all(
        isinstance(value.get(language), str) and bool(value[language].strip())
        for language in ("pt-BR", "en")
    )


def questionnaire_oracles(
    questionnaire: dict[str, Any], questions: list[dict[str, Any]]
) -> dict[str, bool]:
    """Evaluate each questionnaire version independently."""

    content = questionnaire["content"]
    expected_ids = content["question_ids"]
    ordered = sorted(item["content"]["order"] for item in questions)
    question_ids = [item["content"]["question_id"] for item in questions]
    text = " ".join(
        " ".join(item["content"]["translations"].values()).casefold()
        for item in questions
        if isinstance(item["content"].get("translations"), dict)
    )
    return {
        "structure": bool(questions)
        and ordered == list(range(1, len(questions) + 1))
        and set(question_ids) == set(expected_ids),
        "coverage": set(content["criterion_ids"])
        <= {item["content"]["criterion_id"] for item in questions},
        "relevance": all(
            item["content"]["weight"] > 0
            and item["content"]["criterion_id"] in content["criterion_ids"]
            for item in questions
        ),
        "privacy": not any(term in text for term in PROHIBITED_TERMS),
        "scope": all(
            item["content"].get("questionnaire_record_id") == content["questionnaire_record_id"]
            for item in questions
        ),
        "auditability": all(
            item["content"].get("review_status") == "APPROVED"
            and _is_bilingual(item["content"].get("translations"))
            for item in questions
        ),
        "manipulation": question_ids == expected_ids
        and abs(sum(item["content"]["weight"] for item in questions) - 1.0) < 1e-9,
    }
