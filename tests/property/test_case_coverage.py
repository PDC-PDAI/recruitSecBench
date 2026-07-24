from collections import Counter

from recruitsecbench.datasets.cases import (
    ATTACK_FAMILIES,
    PARTITION_CASE_COUNTS,
    generate_adversarial_cases,
    generate_benign_cases,
)


def test_case_coverage_has_complete_pairing_partitions_and_bilingual_content() -> None:
    benign = generate_benign_cases()
    adversarial = generate_adversarial_cases(benign)
    assert len(benign) == 64
    assert len(adversarial) == 192
    assert Counter(case["partition"] for case in benign) == Counter(PARTITION_CASE_COUNTS)
    assert Counter(case["partition"] for case in adversarial) == Counter(
        {partition: count * 3 for partition, count in PARTITION_CASE_COUNTS.items()}
    )
    assert {case["attack_family"] for case in adversarial} == set(ATTACK_FAMILIES)
    benign_ids = {case["case_id"] for case in benign}
    assert all(case["benign_counterpart"] in benign_ids for case in adversarial)
    assert all(case["oracles"] and case["prohibited_outcome"] for case in adversarial)
    assert all(set(case["translations"]) == {"pt-BR", "en"} for case in benign + adversarial)
