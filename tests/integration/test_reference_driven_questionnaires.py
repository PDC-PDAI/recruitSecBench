import json
from pathlib import Path

from recruitsecbench.datasets.domain import generate_domain


def test_domain_questions_use_reference_design_without_exporting_source_text() -> None:
    source_path = Path("data/questionnaire_rewritten.jsonl")
    source_row = json.loads(source_path.read_text(encoding="utf-8").splitlines()[0])
    source_text = source_row["rewritten_questionnaire"]["questions"][0]["rewritten_text"]

    domain = generate_domain()
    questions = [row["content"] for row in domain if row["record_type"] == "question"]
    questionnaires = [row["content"] for row in domain if row["record_type"] == "questionnaire"]
    generated_text = "\n".join(question["text"] for question in questions)

    assert {question["response_type"] for question in questions} == {"LONG_TEXT", "SHORT_TEXT"}
    assert all(len(question["reference_text_sha256"]) == 64 for question in questions)
    assert all("source_id" not in question for question in questions)
    assert all(
        len(questionnaire["reference_corpus_sha256"]) == 64 for questionnaire in questionnaires
    )
    assert source_text not in generated_text
