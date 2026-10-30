"""
engine/gates.py - Liaison Channel & Border Gatekeeper.
Enforces bilateral data-crossing rules defined in packs/bridge/*.yaml.
"""

from typing import Dict, Any, Tuple
from engine.models import BridgeConfig, GateRule


class BorderGate:
    def __init__(self, bridge: BridgeConfig):
        self.bridge = bridge

    def evaluate_transfer(self, data_type: str, metadata: Dict[str, Any]) -> Tuple[str, str]:
        """
        Evaluate whether a payload may cross the border between the host and partner state.
        Returns: (status: 'BLOCK' | 'ALLOW' | 'ROUTE', reason: str)
        """
        gate_rules: Dict[str, GateRule] = self.bridge.liaison_gate_rules

        # 1. Direct match on gate rule key
        if data_type in gate_rules:
            rule = gate_rules[data_type]
            return rule.action, rule.reason or (f"Routed via {rule.path}" if rule.path else "Allowed")

        # 2. Check for identifiable / health data export attempts
        if "patient" in data_type.lower() or "fundus" in data_type.lower() or "raw" in data_type.lower():
            if "raw_patient_telemetry" in gate_rules:
                rule = gate_rules["raw_patient_telemetry"]
                return rule.action, rule.reason or "Blocked under bilateral health data sovereignty rules"

        # 3. Check for anonymized metadata or model updates
        if "vector" in data_type.lower() or "anonymized" in data_type.lower() or "metrics" in data_type.lower():
            if "anonymized_error_metadata" in gate_rules:
                rule = gate_rules["anonymized_error_metadata"]
                return rule.action, f"Allowed under conditions: {', '.join(rule.conditions)}"

        # 4. Check for regulatory-to-regulatory notifications
        if "inquiry" in data_type.lower() or "notification" in data_type.lower():
            if "mutual_regulatory_notification" in gate_rules:
                rule = gate_rules["mutual_regulatory_notification"]
                return rule.action, f"Routed via {rule.path}"

        # Default fallback: Deny cross-border transfer
        return "BLOCK", "Default policy: Unauthorized cross-border data transfer without adequacy or approved SCCs"
