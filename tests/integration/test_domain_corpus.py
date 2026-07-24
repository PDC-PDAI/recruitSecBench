from collections import Counter

from recruitsecbench.datasets.domain import canonical_jsonl, generate_domain


def test_domain_corpus_has_complete_reproducible_bilingual_coverage() -> None:
    first = generate_domain(2026)
    second = generate_domain(2026)
    assert canonical_jsonl(first) == canonical_jsonl(second)
    counts = Counter(row["record_type"] for row in first)
    assert counts == {
        "project": 4,
        "hiring_process": 8,
        "vacancy": 16,
        "evaluation_criterion": 48,
        "candidate": 64,
        "cv": 64,
        "application": 96,
        "questionnaire": 24,
        "question": 240,
        "candidate_response": 480,
        "agent_session": 96,
        "tool": 12,
        "process_state": 192,
        "evaluation_outcome": 96,
    }
    assert {row["partition"] for row in first} == {
        "development",
        "pilot",
        "evaluation",
        "holdout",
    }
    bilingual = {
        "project",
        "hiring_process",
        "vacancy",
        "evaluation_criterion",
        "candidate",
        "cv",
        "application",
        "questionnaire",
        "question",
        "candidate_response",
        "evaluation_outcome",
    }
    assert all(
        set(row["content"]["translations"]) == {"pt-BR", "en"}
        for row in first
        if row["record_type"] in bilingual
    )
    assert all(row["provenance"]["source_kind"] == "synthetic" for row in first)
