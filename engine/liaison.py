"""
engine/liaison.py - Liaison channel between the two countries' institutions.

A request crosses the border only if plain rules from the bridge pack answer
YES to three questions: is there a legal basis to share, is the transfer
allowed under both sides' rules, and is the receiver the right counterpart.
NO or UNCLEAR on any question blocks the request.
"""

from dataclasses import dataclass
from typing import Any

from engine.models import BridgeConfig, Institution, LiaisonRule

QUESTIONS = {
    "legal_basis": "Is there a legal basis to share?",
    "transfer_rules": "Is the transfer allowed under both sides' rules?",
    "counterpart": "Is the receiver the right counterpart?",
}


@dataclass(frozen=True)
class LiaisonDecision:
    status: str  # ROUTE or BLOCK
    checks: list[dict[str, Any]]

    @property
    def reason(self) -> str:
        failed = [check for check in self.checks if check["answer"] != "YES"]
        if not failed:
            return "All three liaison checks answered YES."
        return " ".join(f"{check['question']} {check['answer']}: {check['reason']}" for check in failed)


class LiaisonChannel:
    def __init__(self, bridge: BridgeConfig, institutions: dict[str, Institution]):
        if bridge.liaison is None:
            raise ValueError(f"Bridge pack '{bridge.id}' has no liaison rules.")
        self.config = bridge.liaison
        self.institutions = institutions

    @staticmethod
    def _check(key: str, rule: LiaisonRule) -> dict[str, Any]:
        return {
            "check": key,
            "question": QUESTIONS[key],
            "answer": rule.answer,
            "reason": rule.reason,
            "sources": list(rule.sources),
        }

    def _legal_basis(self, request_type: str) -> LiaisonRule:
        return self.config.request_types.get(request_type) or LiaisonRule(
            answer="UNCLEAR",
            reason=f"The bridge pack defines no legal basis for request type '{request_type}'.",
        )

    def _transfer_rules(self, sender: Institution, receiver: Institution,
                        payload: dict[str, Any]) -> LiaisonRule:
        if payload.get("patient_data_included") is False:
            return LiaisonRule(answer="YES", reason="The request carries no personal data.")
        direction = f"{sender.jurisdiction}->{receiver.jurisdiction}"
        return self.config.personal_data_transfers.get(direction) or LiaisonRule(
            answer="UNCLEAR",
            reason=f"The request may carry personal data and the bridge pack has no {direction} transfer rule.",
        )

    def _counterpart(self, sender: Institution, receiver: Institution) -> LiaisonRule:
        if any({sender.id, receiver.id} == set(pair) for pair in self.config.counterparts):
            return LiaisonRule(answer="YES", reason=f"{sender.id} and {receiver.id} are configured counterparts.")
        configured = sorted(
            other for pair in self.config.counterparts if receiver.id in pair
            for other in pair if other != receiver.id
        )
        return LiaisonRule(
            answer="NO",
            reason=(
                f"{sender.id} is not a configured counterpart of {receiver.id}; "
                + (f"configured: {', '.join(configured)}." if configured
                   else f"no counterpart is configured for {receiver.id}.")
            ),
        )

    def check(self, sender: Institution, receiver_id: str, request_type: str,
              payload: dict[str, Any]) -> LiaisonDecision:
        receiver = self.institutions.get(receiver_id)
        if receiver is None:
            raise ValueError(f"Liaison request names unknown receiver '{receiver_id}'.")
        if receiver.jurisdiction == sender.jurisdiction:
            raise ValueError(f"Liaison request from {sender.id} to {receiver_id} does not cross a border.")
        checks = [
            self._check("legal_basis", self._legal_basis(request_type)),
            self._check("transfer_rules", self._transfer_rules(sender, receiver, payload)),
            self._check("counterpart", self._counterpart(sender, receiver)),
        ]
        status = "ROUTE" if all(check["answer"] == "YES" for check in checks) else "BLOCK"
        return LiaisonDecision(status, checks)
