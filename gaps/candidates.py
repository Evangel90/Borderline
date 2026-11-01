"""Observed synthetic actions that can trigger a governance question."""

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
