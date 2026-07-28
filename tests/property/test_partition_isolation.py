from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from recruitsecbench.datasets.cases import generate_adversarial_cases, generate_benign_cases
from recruitsecbench.datasets.deterministic import generate_deterministic_fixtures
from recruitsecbench.datasets.domain import generate_domain
from recruitsecbench.datasets.partitions import (
    load_partition_plan,
    partition_component_ids,
    validate_partition_isolation,
)


def test_generated_lineages_are_connected_components_isolated_by_partition() -> None:
    domain = generate_domain()
    plan = load_partition_plan(Path("protocol/partitions.yaml"))

    assert (
        validate_partition_isolation(
            domain,
            generate_benign_cases(),
            generate_adversarial_cases(generate_benign_cases()),
            generate_deterministic_fixtures(),
            plan,
        )
        == []
    )
    components = partition_component_ids(domain)
    assert len(components) == 4
    assert {partition for partition, _ in components} == {
        "development",
        "pilot",
        "evaluation",
        "holdout",
    }


def test_cross_partition_component_and_coverage_shortfall_have_stable_codes() -> None:
    domain = deepcopy(generate_domain())
    benign = generate_benign_cases()
    adversarial = generate_adversarial_cases(benign)
    fixtures = generate_deterministic_fixtures()
    plan = load_partition_plan(Path("protocol/partitions.yaml"))

    next(row for row in domain if row["record_id"] == "cv-001")["partition"] = "pilot"
    issues = validate_partition_isolation(domain, benign[:-1], adversarial, fixtures, plan)

    assert {issue.code for issue in issues} >= {
        "PARTITION_COMPONENT_LEAKAGE",
        "PARTITION_COVERAGE_SHORTFALL",
    }
