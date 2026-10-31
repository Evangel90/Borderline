from engine.gates import BorderGate
from engine.models import BridgeConfig, GateRule


def test_gate_blocks_unspecified_cross_border_transfer():
    bridge = BridgeConfig(
        id="test",
        title="Synthetic test",
        parties={},
        adequacy_status={},
        cross_border_regimes={},
        liaison_gate_rules={"raw_patient_telemetry": GateRule(action="BLOCK")},
    )
    status, _ = BorderGate(bridge).evaluate_transfer("unclassified_payload", {})
    assert status == "BLOCK"


def test_gate_uses_explicit_rule():
    bridge = BridgeConfig(
        id="test",
        title="Synthetic test",
        parties={},
        adequacy_status={},
        cross_border_regimes={},
        liaison_gate_rules={"metrics": GateRule(action="ROUTE", path="review")},
    )
    status, reason = BorderGate(bridge).evaluate_transfer("metrics", {})
    assert status == "ROUTE"
    assert "review" in reason
