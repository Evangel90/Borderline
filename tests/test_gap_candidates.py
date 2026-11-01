from types import SimpleNamespace

from engine.orchestrator import DrillOrchestrator
from engine.models import StepPayload
from gaps.candidates import assess_clinical_conflict, evidence_sharing_trigger


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


def clinical_decision(entry_id, actor_id, action, payload):
    return SimpleNamespace(
        entry_id=entry_id, actor_id=actor_id, action_taken=action,
        visible_payload=payload, step=1, actor_name=actor_id,
        jurisdiction="AE", visible_event="Synthetic clinical event",
    )


def test_clinical_hypothesis_rejected_without_failure_signal():
    result = assess_clinical_conflict([clinical_decision(
        "clinic", "ehs", "recommend_clinic_ai_halt", {"known_safety_signal": True}
    )])
    assert result.category == "NO_GAP_IDENTIFIED"
    assert result.assessment_status == "REJECTED_HYPOTHESIS"


def test_clinical_conflict_depends_on_clinic_choice_and_missing_capacity():
    signal = clinical_decision("signal", "screening_ai", "flag_cases_for_human_review",
                               {"audit_result": "false_negatives_confirmed"})
    access = clinical_decision("access", "dha", "assess_screening_suspension",
                               {"suspension_impact": "screening_delays"})
    clinic = clinical_decision("clinic", "ehs", "recommend_clinic_ai_halt",
                               {"known_safety_signal": True,
                                "manual_review_capacity": "to_be_assessed"})
    result = assess_clinical_conflict([signal, access, clinic])
    assert result.category == "OBJECTIVE_CONFLICT"
    assert result.assessment_status == "INSUFFICIENT_EVIDENCE"
    assert "Validated manual screening capacity" in result.missing_evidence
    assert result.trigger_entry_ids == ("signal", "access", "clinic")

    clinic.action_taken = "request_manual_review"
    assert assess_clinical_conflict([signal, access, clinic]).category == "EVIDENCE_DEFICIENCY"


def test_capacity_follow_up_branch_requires_halt_recommendation_state():
    step = StepPayload(
        step=8, phase="Capacity review", event="Synthetic follow-up",
        payload={}, requires_state={"clinic_ai_halt_recommendation": "human_approval_required"},
    )
    assert not DrillOrchestrator._step_enabled(step, {})
    assert not DrillOrchestrator._step_enabled(step, {"clinic_ai_halt_recommendation": "rejected"})
    assert DrillOrchestrator._step_enabled(step, {"clinic_ai_halt_recommendation": "human_approval_required"})
