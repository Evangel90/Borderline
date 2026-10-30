"""
engine/orchestrator.py - Cross-Border Incident Drill Orchestrator.
Coordinates the drill timeline, agent invocations, border gate evaluation, and audit logging.
"""

import json
import os
import yaml
from typing import Dict, List, Any
from engine.models import (
    DrillIntent, Institution, Chunk, BridgeConfig, DecisionLogEntry, PolicyGap
)
from engine.gates import BorderGate
from engine.agent import InstitutionalAgent
from audit.hasher import HashChainedLogger
from gaps.register import GapRegister


class DrillOrchestrator:
    def __init__(self, intent_path: str, run_id: str):
        self.intent_path = intent_path
        self.run_id = run_id
        self.run_dir = os.path.join("runs", run_id)
        os.makedirs(self.run_dir, exist_ok=True)

        self.logger = HashChainedLogger(self.run_dir)
        self.gap_register = GapRegister(self.run_dir)

        # A run ID identifies one deterministic execution. Refuse to append to a
        # prior run so rerunning the same ID cannot silently corrupt its chain.
        if os.path.exists(self.logger.log_path) or os.path.exists(self.gap_register.gaps_path):
            raise FileExistsError(
                f"Run '{run_id}' already has output. Choose a new --run-id "
                "to preserve each run as an immutable artifact."
            )

        # Load Intent
        with open(intent_path, "r", encoding="utf-8") as f:
            raw_intent = yaml.safe_load(f)
            self.intent = DrillIntent(**raw_intent)

        # Load Bridge
        bridge_path = "packs/bridge/ae-ch.yaml"
        with open(bridge_path, "r", encoding="utf-8") as f:
            raw_bridge = yaml.safe_load(f)
            self.bridge = BridgeConfig(**raw_bridge)

        self.gate = BorderGate(self.bridge)

        # Load chunks
        self.chunks: Dict[str, List[Chunk]] = {
            "AE": self._load_chunks("packs/ae/chunks.jsonl"),
            "CH": self._load_chunks("packs/ch/chunks.jsonl"),
            "GLOBAL": self._load_chunks("packs/global/chunks.jsonl")
        }

        # Load institutions
        self.agents: Dict[str, InstitutionalAgent] = self._init_agents()

    def _load_chunks(self, path: str) -> List[Chunk]:
        chunks = []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        chunks.append(Chunk(**json.loads(line)))
        return chunks

    def _init_agents(self) -> Dict[str, InstitutionalAgent]:
        agents = {}
        # UAE institutions
        for inst_file in os.listdir("packs/ae/institutions"):
            if inst_file.endswith(".yaml"):
                with open(os.path.join("packs/ae/institutions", inst_file)) as f:
                    data = yaml.safe_load(f)
                    inst = Institution(**data)
                    agents[inst.id] = InstitutionalAgent(inst, self.chunks["AE"])

        # Swiss institutions
        for inst_file in os.listdir("packs/ch/institutions"):
            if inst_file.endswith(".yaml"):
                with open(os.path.join("packs/ch/institutions", inst_file)) as f:
                    data = yaml.safe_load(f)
                    inst = Institution(**data)
                    agents[inst.id] = InstitutionalAgent(inst, self.chunks["CH"])

        return agents

    def run(self) -> List[DecisionLogEntry]:
        print(f"\n🚀 Running Cross-Border Drill: {self.intent.title}")
        print(f"📁 Output Run Directory: {self.run_dir}")
        print("=" * 60)

        all_decisions = []

        for step in self.intent.timeline:
            print(f"\n▶ Step {step.step}: [{step.phase}]")
            print(f"  Event: {step.event}")

            # 1. Evaluate cross-border gate if payload involves transfer
            gate_status = None
            gate_reason = ""
            if "data_requested" in step.payload:
                gate_status, gate_reason = self.gate.evaluate_transfer(
                    step.payload["data_requested"], step.payload
                )
                print(f"  🚧 Border Gate Decision: {gate_status} ({gate_reason})")
            elif "target" in step.payload:
                gate_status, gate_reason = self.gate.evaluate_transfer(
                    "mutual_regulatory_notification", step.payload
                )
                print(f"  🚧 Border Gate Routing: {gate_status} ({gate_reason})")

            # 2. Trigger relevant actor agents
            # The initiator agent reacts first
            initiator_id = step.initiator
            active_actors = [initiator_id]

            if initiator_id == "ehs":
                active_actors.extend(["mohap", "uae_data_office"])
            elif initiator_id == "retina_swiss_ag":
                active_actors.extend(["uae_data_office", "fodio"])
            elif initiator_id == "mohap":
                active_actors.extend(["swissmedic"])
            elif initiator_id == "engine":
                # Step 4: Policy gap logging
                active_actors = ["mohap", "swissmedic", "uae_data_office"]

            for actor_id in active_actors:
                if actor_id in self.agents:
                    agent = self.agents[actor_id]
                    decision = agent.evaluate_step(
                        step.step, step.event, step.payload, gate_status=gate_status
                    )
                    # Record in hash-chained log
                    chained_entry = self.logger.append(decision.model_dump())
                    all_decisions.append(DecisionLogEntry(**chained_entry))
                    print(f"  🏛️  [{agent.institution.jurisdiction}] {agent.institution.id.upper()}: {decision.action_taken}")
                    print(f"     Reason: {decision.justification}")
                    print(f"     Cited: {', '.join(decision.cited_clauses[:2])}")

        # Record Policy Gap (M3 prerequisite)
        gap = PolicyGap(
            gap_id="GAP-HEALTH-001",
            category="Data Sovereignty vs. Medical Device Vigilance",
            title="Cross-Border Health Data Localization vs. Manufacturer Vigilance Reporting",
            host_jurisdiction="AE",
            partner_jurisdiction="CH",
            friction_point="UAE Health Data Law / PDPL Art. 22 restricts export of raw patient retinal scans; Swiss MedDO Art. 66 mandates manufacturer investigate serious device failures with root-cause clinical data, but DPO Annex 1 lacks bilateral adequacy.",
            host_citation="AE-DATA-PDPL-2021 (Art. 22) / AE Federal Law 2/2019",
            partner_citation="CH-HEALTH-MedDO (Art. 66) / CH-DATA-DPO (Annex 1)",
            global_benchmark="WHO Ethics & Governance of AI for Health (Clinical Post-Market Surveillance) & ITU-T Y.3172 Policy Node",
            remediation_recommendation="Implement federated zero-PII error metadata exchanges (weights and activation maps only) alongside bilateral expedited regulatory notification channels."
        )
        self.gap_register.record_gap(gap)
        print("\n" + "=" * 60)
        print(f"✅ Drill Completed! Logged {len(all_decisions)} decisions to {self.logger.log_path}")
        print(f"✅ Recorded Policy Gap to {self.gap_register.gaps_path}")
        print(f"🔒 Final Hash: {self.logger.latest_hash}")

        return all_decisions
