"""Bounded action execution for the synthetic incident sandbox."""

from dataclasses import dataclass, field
from typing import Any

from engine.gates import BorderGate
from engine.models import Institution


@dataclass
class ActionResult:
    action: str
    liaison_status: str
    result: str
    state_changes: dict[str, Any] = field(default_factory=dict)


class ActionExecutor:
    """Execute only declared actions, with the border gate as a mandatory veto."""

    GATED_ACTIONS = {
        "request_raw_telemetry": "raw_patient_telemetry",
        "propose_minimized_telemetry": "anonymized_error_metadata",
        "route_regulatory_notification": "mutual_regulatory_notification",
        "request_regulatory_evidence": "mutual_regulatory_notification",
    }

    LOCAL_STATE_ACTIONS = {
        "report_model_update": ("screening_model_update", "recorded"),
        "pause_screening_service": ("screening_service_status", "paused_pending_human_review"),
        "flag_cases_for_human_review": ("patient_cohort_review", "requested"),
        "open_clinical_incident_review": ("clinical_incident_review", "opened"),
        "request_patient_follow_up_review": ("patient_follow_up_review", "requested"),
        "assess_screening_suspension": ("screening_suspension_review", "human_review_required"),
        "request_ede_manufacturer_evidence": ("ede_manufacturer_evidence", "requested"),
        "assess_ede_device_safety_action": ("ede_device_safety_review", "human_review_required"),
        "coordinate_ede_health_review": ("ede_health_coordination", "requested"),
        "open_uae_cyber_review": ("uae_cyber_review", "opened"),
        "request_uae_security_evidence": ("uae_security_evidence", "requested"),
        "assess_ncsc_reporting_duty": ("ncsc_reporting_review", "human_review_required"),
        "request_ncsc_security_evidence": ("ncsc_security_evidence", "requested"),
        "prepare_policy_gap_review": ("policy_gap_review", "human_review_required"),
        "request_gap_supporting_evidence": ("gap_supporting_evidence", "requested"),
        "halt_clinic_ai": ("clinical_ai_status", "paused"),
        "escalate_to_mohap": ("safety_escalation", "created"),
        "request_manual_review": ("manual_review", "required"),
        "pause_transfer_pending_review": ("data_transfer_status", "paused_pending_review"),
        "assess_transfer_basis": ("transfer_basis_review", "in_progress"),
        "request_transfer_safeguards": ("transfer_safeguards", "requested"),
        "initiate_model_rollback": ("model_rollback", "requested"),
        "issue_safety_inquiry": ("safety_inquiry", "opened"),
        "request_device_incident_report": ("manufacturer_report", "requested"),
        "review_foreign_incident_report": ("foreign_incident_review", "in_progress"),
        "request_manufacturer_report": ("manufacturer_report", "requested"),
        "consider_field_safety_action": ("field_safety_action_review", "requested"),
        "assess_transfer_direction_scope": ("transfer_scope_review", "in_progress"),
        "request_safeguards": ("swiss_safeguards", "requested"),
        "recommend_pause_disclosure": ("disclosure_recommendation", "pause_pending_review"),
    }

    def __init__(self, state: dict[str, Any] | None = None) -> None:
        self.state = state if state is not None else {}

    def _record(self, key: str, value: Any) -> dict[str, Any]:
        self.state[key] = value
        return {key: value}

    def execute(
        self,
        institution: Institution,
        action: str,
        payload: dict[str, Any],
        gate: BorderGate,
        observed_gate_status: str | None = None,
        observed_gate_reason: str = "",
    ) -> ActionResult:
        allowed = {item.name for item in institution.available_actions}
        if action not in allowed:
            raise ValueError(f"{institution.id} is not authorized for action '{action}'.")

        if action in self.GATED_ACTIONS:
            data_type = self.GATED_ACTIONS[action]
            status, reason = gate.evaluate_transfer(data_type, payload)
            if status == "BLOCK":
                attempt_key = {
                    "request_raw_telemetry": "vendor_transfer_request",
                    "propose_minimized_telemetry": "reduced_data_transfer_request",
                    "route_regulatory_notification": "regulatory_notification",
                    "request_regulatory_evidence": "regulatory_evidence_request",
                }[action]
                changes = self._record(attempt_key, "blocked_by_gate")
                return ActionResult(
                    action,
                    status,
                    f"Tool call vetoed by the border gate; no transfer or message was sent. {reason}",
                    changes,
                )
            if status == "ROUTE" and action not in {
                "route_regulatory_notification",
                "request_regulatory_evidence",
            }:
                changes = self._record("reduced_data_transfer_request", "pending_review")
                return ActionResult(
                    action,
                    status,
                    f"Tool call requires the configured review and safeguards; no data was transferred. {reason}",
                    changes,
                )
            if action in {"route_regulatory_notification", "request_regulatory_evidence"}:
                if status != "ROUTE":
                    record_key = (
                        "regulatory_evidence_request"
                        if action == "request_regulatory_evidence"
                        else "regulatory_notification"
                    )
                    changes = self._record(record_key, "not_routed_by_gate")
                    return ActionResult(
                        action,
                        status,
                        f"The configured gate did not provide a routing decision; no notification was sent. {reason}",
                        changes,
                    )
                notices = self.state.setdefault("regulatory_notifications", [])
                notice = {"payload": payload, "status": "simulated_route"}
                notices.append(notice)
                return ActionResult(
                    action,
                    status,
                    f"Request recorded on the simulated liaison route; no external message or data was sent. {reason}",
                    {"regulatory_notifications": notice},
                )
            return ActionResult(
                action,
                status,
                f"Transfer action recorded in the simulation; no external data was sent. {reason}",
                {},
            )

        if action not in self.LOCAL_STATE_ACTIONS:
            raise ValueError(f"No sandbox tool is registered for action '{action}'.")
        key, value = self.LOCAL_STATE_ACTIONS[action]
        changes = self._record(key, value)
        observed = (
            f" The scenario gate separately reports {observed_gate_status}: {observed_gate_reason}"
            if observed_gate_status else ""
        )
        return ActionResult(
            action,
            "LOCAL_ONLY",
            "Action executed in the synthetic drill state; no external service or real system was changed."
            + observed,
            changes,
        )
