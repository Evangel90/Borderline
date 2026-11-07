import pytest
import yaml

from engine.actions import ActionExecutor
from engine.gates import BorderGate
from engine.liaison import LiaisonChannel
from engine.models import (
    AvailableAction, BridgeConfig, Institution, LiaisonConfig, LiaisonRule,
)


def institution(inst_id, jurisdiction, actions=()):
    return Institution(
        id=inst_id, name=inst_id, jurisdiction=jurisdiction, type="test", role="test",
        mandate="test",
        available_actions=[AvailableAction(name=name, description=name) for name in actions],
    )


INSTITUTIONS = {
    "ae_health": institution("ae_health", "AE", ["request_regulatory_evidence"]),
    "ae_emirate_health": institution("ae_emirate_health", "AE", ["request_regulatory_evidence"]),
    "ch_device": institution("ch_device", "CH"),
}


def bridge(legal_basis="YES", transfers=None):
    return BridgeConfig(
        id="test", title="Synthetic test", parties={}, adequacy_status={},
        cross_border_regimes={}, liaison_gate_rules={},
        liaison=LiaisonConfig(
            counterparts=[["ae_health", "ch_device"]],
            request_types={
                "cross_border_evidence_request": LiaisonRule(answer=legal_basis, reason="test basis"),
            },
            personal_data_transfers=transfers or {},
        ),
    )


def answers(decision):
    return {check["check"]: check["answer"] for check in decision.checks}


def test_request_routes_only_when_all_three_checks_answer_yes():
    channel = LiaisonChannel(bridge(), INSTITUTIONS)
    decision = channel.check(
        INSTITUTIONS["ae_health"], "ch_device", "cross_border_evidence_request",
        {"patient_data_included": False},
    )
    assert decision.status == "ROUTE"
    assert answers(decision) == {"legal_basis": "YES", "transfer_rules": "YES", "counterpart": "YES"}


def test_unconfigured_counterpart_blocks_and_names_the_configured_one():
    channel = LiaisonChannel(bridge(), INSTITUTIONS)
    decision = channel.check(
        INSTITUTIONS["ae_emirate_health"], "ch_device", "cross_border_evidence_request",
        {"patient_data_included": False},
    )
    assert decision.status == "BLOCK"
    assert answers(decision)["counterpart"] == "NO"
    assert "configured: ae_health" in decision.reason


def test_unclear_legal_basis_blocks():
    channel = LiaisonChannel(bridge(legal_basis="UNCLEAR"), INSTITUTIONS)
    decision = channel.check(
        INSTITUTIONS["ae_health"], "ch_device", "cross_border_evidence_request",
        {"patient_data_included": False},
    )
    assert decision.status == "BLOCK"
    assert answers(decision)["legal_basis"] == "UNCLEAR"


def test_possible_personal_data_uses_directional_transfer_rule():
    rule = LiaisonRule(answer="UNCLEAR", reason="no exemption", sources=["AE-LAW"])
    channel = LiaisonChannel(bridge(transfers={"AE->CH": rule}), INSTITUTIONS)
    decision = channel.check(INSTITUTIONS["ae_health"], "ch_device", "cross_border_evidence_request", {})
    assert decision.status == "BLOCK"
    transfer = next(check for check in decision.checks if check["check"] == "transfer_rules")
    assert transfer["answer"] == "UNCLEAR"
    assert transfer["sources"] == ["AE-LAW"]


def test_missing_rule_is_unclear_not_allowed():
    channel = LiaisonChannel(bridge(), INSTITUTIONS)
    decision = channel.check(INSTITUTIONS["ae_health"], "ch_device", "unknown_request", {})
    assert decision.status == "BLOCK"
    assert answers(decision) == {"legal_basis": "UNCLEAR", "transfer_rules": "UNCLEAR", "counterpart": "YES"}


def test_same_country_request_is_rejected():
    channel = LiaisonChannel(bridge(), INSTITUTIONS)
    with pytest.raises(ValueError, match="does not cross a border"):
        channel.check(INSTITUTIONS["ae_health"], "ae_emirate_health", "cross_border_evidence_request", {})


def test_invalid_answer_is_rejected():
    with pytest.raises(ValueError):
        LiaisonRule(answer="MAYBE", reason="test")


@pytest.mark.parametrize("legal_basis, expected_state", [
    ("YES", "delivered"), ("UNCLEAR", "blocked_by_liaison_check"),
])
def test_executor_sends_requests_through_the_channel(legal_basis, expected_state):
    config = bridge(legal_basis=legal_basis)
    executor = ActionExecutor({}, LiaisonChannel(config, INSTITUTIONS))
    result = executor.execute(
        INSTITUTIONS["ae_health"], "request_regulatory_evidence",
        {"target": "ch_device", "patient_data_included": False}, BorderGate(config),
    )
    assert result.state_changes == {
        "regulatory_evidence_request": expected_state,
        "regulatory_evidence_request.ae_health": expected_state,
    }
    assert len(result.liaison_checks) == 3


def test_per_sender_state_survives_a_later_request():
    config = bridge()
    executor = ActionExecutor({}, LiaisonChannel(config, INSTITUTIONS))
    payload = {"target": "ch_device", "patient_data_included": False}
    executor.execute(INSTITUTIONS["ae_health"], "request_regulatory_evidence", payload, BorderGate(config))
    executor.execute(INSTITUTIONS["ae_emirate_health"], "request_regulatory_evidence", payload, BorderGate(config))
    assert executor.state["regulatory_evidence_request.ae_health"] == "delivered"
    assert executor.state["regulatory_evidence_request.ae_emirate_health"] == "blocked_by_liaison_check"
    assert executor.state["regulatory_evidence_request"] == "blocked_by_liaison_check"


def checked_in_channel():
    with open("packs/bridge/ae-ch.yaml", encoding="utf-8") as source:
        config = BridgeConfig(**yaml.safe_load(source))
    institutions = {}
    for path in ("packs/ae/institutions/dha.yaml", "packs/ae/institutions/mohap.yaml",
                 "packs/ae/institutions/uae_data_office.yaml",
                 "packs/ch/institutions/swissmedic.yaml", "packs/ch/institutions/fodio.yaml"):
        with open(path, encoding="utf-8") as source:
            inst = Institution(**yaml.safe_load(source))
        institutions[inst.id] = inst
    return LiaisonChannel(config, institutions), institutions


@pytest.mark.parametrize("sender, receiver, request_type, expected", [
    ("dha", "swissmedic", "cross_border_evidence_request",
     {"legal_basis": "UNCLEAR", "transfer_rules": "YES", "counterpart": "NO"}),
    ("mohap", "swissmedic", "cross_border_evidence_request",
     {"legal_basis": "UNCLEAR", "transfer_rules": "YES", "counterpart": "YES"}),
    ("uae_data_office", "fodio", "data_protection_assistance_request",
     {"legal_basis": "UNCLEAR", "transfer_rules": "YES", "counterpart": "YES"}),
])
def test_checked_in_bridge_blocks_each_uae_request(sender, receiver, request_type, expected):
    channel, institutions = checked_in_channel()
    decision = channel.check(institutions[sender], receiver, request_type, {"patient_data_included": False})
    assert decision.status == "BLOCK"
    assert answers(decision) == expected
