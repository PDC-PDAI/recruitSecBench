from __future__ import annotations

from recruitsecbench.privacy.analyzers import analyze_privacy, longest_common_token_span
from recruitsecbench.privacy.derivation import derive_minimized_profile


def test_analysis_rejects_direct_identifiers_and_low_k_anonymity() -> None:
    analysis = analyze_privacy(
        "Original professional history",
        "Contact candidate@example.com",
        quasi_identifier_tuples=[("rare", "tuple")],
    )
    assert "PII_DETECTED" in analysis.reason_codes
    assert "K_ANONYMITY_TOO_LOW" in analysis.reason_codes


def test_analysis_enforces_common_span_and_similarity_thresholds() -> None:
    text = "one two three four five six seven eight nine ten"
    analysis = analyze_privacy(text, text, quasi_identifier_tuples=[("general",)] * 5)
    assert analysis.longest_common_span == 10
    assert analysis.semantic_similarity == 1.0
    assert {"COMMON_SPAN_EXCEEDED", "SEMANTIC_SIMILARITY_EXCEEDED"} <= set(analysis.reason_codes)
    assert longest_common_token_span("a b", "a b") == 2


def test_derivation_is_bounded_and_scrubs_email() -> None:
    output = derive_minimized_profile("Name: Ana\nana@example.com Python data engineering")
    assert "ana@example.com" not in output
    assert len(output.split()) < 30
