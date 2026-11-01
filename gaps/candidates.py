"""Observed synthetic actions that can trigger a governance question."""

from dataclasses import dataclass

from engine.models import DecisionLogEntry


def evidence_sharing_trigger(
    decisions: list[DecisionLogEntry],
) -> tuple[DecisionLogEntry, DecisionLogEntry] | None:
    """Require both recorded secondary use and a routed evidence request."""
    secondary = next((item for item in decisions
                      if item.action_taken == "record_secondary_use_for_review"
                      and item.visible_payload.get("use") == "model_retraining"), None)
    route = next((item for item in decisions
                  if item.action_taken == "request_regulatory_evidence"
                  and item.liaison_status == "ROUTE"), None)
    return (secondary, route) if secondary and route else None


@dataclass(frozen=True)
class ClinicalConflictResult:
    category: str
    assessment_status: str
    trigger_entry_ids: tuple[str, ...]
    missing_evidence: tuple[str, ...]


def assess_clinical_conflict(decisions: list[DecisionLogEntry]) -> ClinicalConflictResult:
    """Test the synthetic pause-versus-access hypothesis from visible facts and choices."""
    signal = next((item for item in decisions
                   if item.visible_payload.get("audit_result") == "false_negatives_confirmed"), None)
    if signal is None:
        return ClinicalConflictResult("NO_GAP_IDENTIFIED", "REJECTED_HYPOTHESIS", (), ())

    clinic = next((item for item in decisions if item.actor_id == "ehs"
                   and item.visible_payload.get("known_safety_signal")), None)
    access = next((item for item in decisions
                   if item.visible_payload.get("suspension_impact") == "screening_delays"
                   or item.visible_payload.get("screening_access_impact") == "possible"), None)
    if clinic is None or access is None:
        return ClinicalConflictResult(
            "EVIDENCE_DEFICIENCY", "INSUFFICIENT_EVIDENCE", (signal.entry_id,),
            ("Screening access impact and clinic response",),
        )

    category = (
        "OBJECTIVE_CONFLICT" if clinic.action_taken == "recommend_clinic_ai_halt"
        else "EVIDENCE_DEFICIENCY"
    )
    missing = []
    if clinic.visible_payload.get("manual_review_capacity") in {None, "to_be_assessed", "unknown"}:
        missing.append("Validated manual screening capacity")
    if not any(item.visible_payload.get("rollback_safety_validated") is True for item in decisions):
        missing.append("Validated safety of any rollback version")
    if not any(item.visible_payload.get("patient_follow_up_status") == "confirmed" for item in decisions):
        missing.append("Confirmed patient follow-up plan")
    return ClinicalConflictResult(
        category, "INSUFFICIENT_EVIDENCE" if missing else "READY_FOR_HUMAN_REVIEW",
        tuple(dict.fromkeys((signal.entry_id, access.entry_id, clinic.entry_id))), tuple(missing),
    )
