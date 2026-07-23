from __future__ import annotations

import pytest

from recruitsecbench.config.protocol import (
    Condition,
    PartitionAuthorizationError,
    authorize_partition,
    load_protocol,
)
from recruitsecbench.datasets.models import Partition


def test_protocol_declares_complete_factorial_conditions_and_stable_evidence_ids() -> None:
    protocol = load_protocol("protocol/experiment.yaml")

    assert protocol.conditions == [Condition.C0, Condition.C1, Condition.C2, Condition.C3]
    assert protocol.condition_controls(Condition.C0) == (False, False)
    assert protocol.condition_controls(Condition.C3) == (True, True)
    assert len(protocol.evidence_ids) == len(set(protocol.evidence_ids))


def test_evaluation_requires_explicit_confirmation_and_frozen_protocol() -> None:
    with pytest.raises(PartitionAuthorizationError):
        authorize_partition(Partition.EVALUATION, explicit=False, protocol_sha256=None)

    authorization = authorize_partition(
        Partition.EVALUATION,
        explicit=True,
        protocol_sha256="a" * 64,
    )
    assert authorization.authorized is True


def test_holdout_requires_one_unconsumed_named_campaign() -> None:
    with pytest.raises(PartitionAuthorizationError):
        authorize_partition(
            Partition.HOLDOUT,
            explicit=True,
            protocol_sha256="a" * 64,
            campaign_id=None,
        )

    with pytest.raises(PartitionAuthorizationError):
        authorize_partition(
            Partition.HOLDOUT,
            explicit=True,
            protocol_sha256="a" * 64,
            campaign_id="final-2026",
            holdout_consumed=True,
        )
