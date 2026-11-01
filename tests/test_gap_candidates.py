from types import SimpleNamespace

from engine.orchestrator import DrillOrchestrator
from gaps.candidates import evidence_sharing_trigger


def decision(action, liaison=None, use=None):
    return SimpleNamespace(
        action_taken=action,
        liaison_status=liaison,
        visible_payload={"use": use} if use else {},
    )


def test_candidate_requires_observed_secondary_use_and_routed_request():
    secondary = decision("record_secondary_use_for_review", use="model_retraining")
    routed = decision("request_regulatory_evidence", liaison="ROUTE")
    assert evidence_sharing_trigger([secondary, routed]) == (secondary, routed)
    assert evidence_sharing_trigger([secondary, decision("request_regulatory_evidence", "BLOCK")]) is None
    assert evidence_sharing_trigger([routed]) is None


def test_orchestrator_does_not_build_gap_without_trigger():
    orchestrator = object.__new__(DrillOrchestrator)
    assert orchestrator._build_policy_gap([]) is None
