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


@dataclass(frozen=True)
class DeploymentReadinessResult:
    assessment_status: str
    finding_class: str
    trigger_entry_ids: tuple[str, ...]
    missing_evidence: tuple[str, ...]


def assess_deployment_readiness(
    decisions: list[DecisionLogEntry],
) -> DeploymentReadinessResult | None:
    """Assess whether the primary deployment-review scenario has enough evidence to proceed."""
    transfer_review = next(
        (
            item for item in decisions
            if item.actor_id == "uae_data_office"
            and item.visible_payload.get("transfer_status") == "proposed"
            and item.action_taken in {
                "pause_transfer_pending_review",
                "assess_transfer_basis",
                "request_transfer_safeguards",
            }
        ),
        None,
    )
    clinic_review = next(
        (
            item for item in decisions
            if item.actor_id == "dubai_clinic_operator"
            and item.visible_payload.get("service_status") == "inactive"
            and item.action_taken in {"request_manual_review", "escalate_to_mohap"}
        ),
        None,
    )
    missing_record = next(
        (
            item for item in decisions
            if item.visible_payload.get("validation_package") == "missing"
            and item.visible_payload.get("cam_7_subgroup_results") == "missing"
        ),
        None,
    )
    if not (transfer_review and clinic_review and missing_record):
        return None

    supplied_packet = next(
        (
            item for item in decisions
            if item.visible_payload.get("vendor_evidence_packet_status") == "submitted_complete"
            and item.visible_payload.get("validation_package") == "supplied"
            and item.visible_payload.get("subprocessor_list") == "supplied"
        ),
        None,
    )
    if supplied_packet:
        return DeploymentReadinessResult(
            assessment_status="READY_FOR_HUMAN_REVIEW",
            finding_class="PRE_DEPLOYMENT_EVIDENCE_RECEIVED",
            trigger_entry_ids=tuple(dict.fromkeys((
                transfer_review.entry_id,
                clinic_review.entry_id,
                missing_record.entry_id,
                supplied_packet.entry_id,
            ))),
            missing_evidence=(
                "Accountable human review of the supplied vendor packet",
                "Confirmed clinic authorization and workflow fit",
                "Cross-border transfer basis and safeguards assessment",
            ),
        )

    missing = [
        "v2.4 validation package",
        "Cam-7 subgroup performance results",
        "release approval record",
        "rollback plan",
        "software bill of materials",
        "complete subprocessor list",
    ]
    return DeploymentReadinessResult(
        assessment_status="PENDING_EVIDENCE",
        finding_class="PRE_DEPLOYMENT_REVIEW_PENDING_EVIDENCE",
        trigger_entry_ids=tuple(
            dict.fromkeys((
                transfer_review.entry_id,
                clinic_review.entry_id,
                missing_record.entry_id,
            ))
        ),
        missing_evidence=tuple(missing),
    )


def assess_clinical_conflict(decisions: list[DecisionLogEntry]) -> ClinicalConflictResult:
    """Test the synthetic pause-versus-access hypothesis from visible facts and choices."""
    signal = next((item for item in decisions
                   if item.visible_payload.get("audit_result") == "false_negatives_confirmed"), None)
    if signal is None:
        return ClinicalConflictResult("NO_GAP_IDENTIFIED", "REJECTED_HYPOTHESIS", (), ())

    clinic = next((item for item in decisions if item.actor_id == "dubai_clinic_operator"
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
