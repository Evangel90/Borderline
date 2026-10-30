"""
engine/orchestrator.py - Cross-Border Incident Drill Orchestrator.
Coordinates the drill timeline, agent invocations, border gate evaluation, and audit logging.
"""

import json
import os
import yaml
from typing import Dict, List, Any
from engine.models import (
    DrillIntent, Institution, Chunk, BridgeConfig, DecisionLogEntry,
    PolicyEvidence, PolicyGap,
)
from engine.gates import BorderGate
from engine.agent import InstitutionalAgent
from engine.actions import ActionExecutor
from engine.llm import OllamaChatClient
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
        self.llm = OllamaChatClient()
        self.simulation_state: Dict[str, Any] = {}
        self.action_executor = ActionExecutor(self.simulation_state)

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

    def _retrieve_evidence(
        self,
        jurisdiction: str,
        doc_id: str,
        terms: List[str],
        relevance: str,
        limit: int = 1,
        required_terms: List[str] | None = None,
    ) -> List[PolicyEvidence]:
        """Retrieve citation-ready chunks with deterministic lexical ranking."""
        candidates = []
        for chunk in self.chunks.get(jurisdiction, []):
            if chunk.doc_id != doc_id:
                continue
            text_lower = chunk.text.lower()
            if required_terms and not all(term.lower() in text_lower for term in required_terms):
                continue
            score = sum(text_lower.count(term.lower()) for term in terms)
            if score:
                candidates.append((score, chunk))

        candidates.sort(key=lambda item: (-item[0], item[1].page, item[1].chunk_index))
        return [
            PolicyEvidence(
                source_type="policy_chunk",
                source_ref=chunk.chunk_id,
                title=chunk.title,
                jurisdiction=chunk.jurisdiction,
                page=chunk.page,
                excerpt=" ".join(chunk.text.split())[:700],
                relevance=relevance,
            )
            for _, chunk in candidates[:limit]
        ]

    @staticmethod
    def _decision_evidence(
        decisions: List[DecisionLogEntry], step: int, status: str,
        actor_id: str, relevance: str,
    ) -> List[PolicyEvidence]:
        return [
            PolicyEvidence(
                source_type="run_log",
                source_ref=decision.entry_id,
                title=f"Step {step} decision by {decision.actor_name}",
                jurisdiction=decision.jurisdiction,
                excerpt=(
                    f"{decision.action_taken}: {decision.justification} "
                    f"Gate status: {decision.gate_status}; liaison status: {decision.liaison_status}."
                ),
                relevance=relevance,
            )
            for decision in decisions
            if decision.step == step
            and decision.gate_status == status
            and decision.actor_id == actor_id
        ]

    def _build_policy_gap(self, decisions: List[DecisionLogEntry]) -> PolicyGap:
        evidence = []
        evidence.extend(self._decision_evidence(
            decisions, 2, "BLOCK", "uae_data_office",
            "The run paused the raw-image transfer pending documented legal basis and safeguards."
        ))
        evidence.extend(self._decision_evidence(
            decisions, 3, "ROUTE", "mohap",
            "The run routed the regulator-to-regulator notification."
        ))
        evidence.extend(self._retrieve_evidence(
            "AE", "AE-DATA-PDPL-2021",
            ["adequate level of protection", "transferred outside the State", "approved by the Office"],
            "UAE PDPL Articles 22–23 set conditions and exceptions for transfers outside the State.",
            limit=2,
        ))
        evidence.extend(self._retrieve_evidence(
            "CH", "CH-HEALTH-MedDO",
            ["Art. 66", "Reporting obligation", "serious incidents", "occurred in Switzerland"],
            "Swiss MedDO Article 66 specifies device incident reporting duties and territorial scope.",
        ))
        evidence.extend(self._retrieve_evidence(
            "CH", "CH-DATA-FADP",
            ["Art. 16", "disclosed abroad", "adequate level of protection", "standard contractual clauses"],
            "Swiss FADP Article 16 sets conditions for disclosures abroad by Swiss controllers; applicability depends on role and transfer direction.",
        ))

        # Annex 1 is a multi-page enumerated list. Retain the relevant list pages
        # together so the non-listing observation is auditable rather than based
        # on a single search result.
        dpo_annex = [
            chunk for chunk in self.chunks["CH"]
            if chunk.doc_id == "CH-DATA-DPO"
            and ((chunk.page == 16 and chunk.chunk_index == 1) or chunk.page == 17)
        ]
        annex_text = " ".join(chunk.text for chunk in dpo_annex).lower()
        uae_listed = "united arab emirates" in annex_text or "\nuae\n" in annex_text
        for chunk in dpo_annex:
            evidence.append(PolicyEvidence(
                source_type="policy_chunk",
                source_ref=chunk.chunk_id,
                title=chunk.title,
                jurisdiction=chunk.jurisdiction,
                page=chunk.page,
                excerpt=" ".join(chunk.text.split())[:700],
                relevance=(
                    "Swiss DPO Annex 1 enumerated adequacy list; UAE appears in the list, relevant to Switzerland-origin disclosures."
                    if uae_listed else
                    "Swiss DPO Annex 1 enumerated adequacy list; UAE is absent from the checked list pages. This does not by itself decide a UAE-to-Switzerland export."
                ),
            ))
        evidence.extend(self._retrieve_evidence(
            "GLOBAL", "WHO-GUIDELINES-AI-HEALTH",
            ["federated data-sharing", "maintaining local control", "informed consent", "secondary uses"],
            "WHO notes that federated sharing can preserve local control but does not itself resolve consent concerns.",
            required_terms=["federated data-sharing", "maintaining local control"],
        ))

        return PolicyGap(
            gap_id="GAP-HEALTH-001",
            category="Health data transfer and medical device incident reporting",
            title="Cross-border evidence sharing and vigilance coordination",
            host_jurisdiction="AE",
            partner_jurisdiction="CH",
            friction_point=(
                "In this run, the UAE gate blocks a request for raw retinal images and the "
                "regulator notification is routed. The cited UAE PDPL provisions make "
                "cross-border personal-data transfers conditional, while Swiss MedDO "
                "Article 66 specifies reporting obligations for incidents in Switzerland "
                "and, where required, authorized representatives report trends including "
                "incidents abroad. The checked Swiss DPO Annex 1 list pages do not include "
                "the UAE; that list concerns Switzerland-origin disclosures and does not "
                "itself decide this UAE-to-Switzerland request. These sources leave "
                "the lawful basis, minimum evidence set, and operational pathway for this "
                "UAE incident to be established before any disclosure. This is a scenario "
                "coordination gap, not a conclusion that the laws are incompatible."
            ),
            host_citation="AE-DATA-PDPL-2021 (Arts. 22–23; chunks cited below)",
            partner_citation="CH-HEALTH-MedDO (Art. 66), CH-DATA-FADP (Art. 16), and CH-DATA-DPO (Annex 1; chunks cited below)",
            global_benchmark=(
                "WHO Ethics and Governance of Artificial Intelligence for Health: "
                "federated data-sharing may maintain local control but does not by itself resolve consent concerns."
            ),
            remediation_recommendation=(
                "Define a regulator-approved incident exchange protocol that specifies the "
                "reporting route, lawful transfer basis, minimum necessary evidence, and "
                "privacy and security review. Treat federated analysis as an option for "
                "assessment, not as a substitute for consent or transfer authorization."
            ),
            finding_method=(
                "Deterministic scenario rule: connect the recorded BLOCK and ROUTE outcomes "
                "to lexical retrieval from the UAE PDPL, Swiss MedDO, Swiss FADP / DPO, "
                "and WHO health-AI guidance. No LLM-generated legal conclusion is used."
            ),
            limitations=(
                "This is a synthetic drill finding, not legal advice. Retrieval is keyword-based; "
                "the DPO Annex 1 check uses the checked-in 2023 text; source currency and "
                "application to a real incident require human review."
            ),
            evidence=evidence,
        )

    def _init_agents(self) -> Dict[str, InstitutionalAgent]:
        agents = {}
        # UAE institutions
        for inst_file in os.listdir("packs/ae/institutions"):
            if inst_file.endswith(".yaml"):
                with open(os.path.join("packs/ae/institutions", inst_file)) as f:
                    data = yaml.safe_load(f)
                    inst = Institution(**data)
                    agents[inst.id] = InstitutionalAgent(
                        inst, self.chunks["AE"] + self.chunks["GLOBAL"],
                        self.llm, self.action_executor,
                    )

        # Swiss institutions
        for inst_file in os.listdir("packs/ch/institutions"):
            if inst_file.endswith(".yaml"):
                with open(os.path.join("packs/ch/institutions", inst_file)) as f:
                    data = yaml.safe_load(f)
                    inst = Institution(**data)
                    agents[inst.id] = InstitutionalAgent(
                        inst, self.chunks["CH"] + self.chunks["GLOBAL"],
                        self.llm, self.action_executor,
                    )

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
                        step.step,
                        step.event,
                        step.payload,
                        gate=self.gate,
                        gate_status=gate_status,
                        gate_reason=gate_reason,
                        expected_policy_checks=step.expected_policy_checks,
                    )
                    # Record in hash-chained log
                    chained_entry = self.logger.append(decision.model_dump())
                    all_decisions.append(DecisionLogEntry(**chained_entry))
                    print(f"  🏛️  [{agent.institution.jurisdiction}] {agent.institution.id.upper()}: {decision.action_taken}")
                    print(f"     Reason: {decision.justification}")
                    print(f"     Cited: {', '.join(decision.cited_clauses[:2])}")
                    print(f"     LLM: {decision.model_name} (self-reported confidence {decision.confidence})")
                    print(f"     Tool result: {decision.tool_result}")
                    print(f"     State changes: {decision.state_changes}")

        # Record a scenario finding grounded in this run and retrieved source chunks.
        gap = self._build_policy_gap(all_decisions)
        self.gap_register.record_gap(gap)
        print("\n" + "=" * 60)
        print(f"✅ Drill Completed! Logged {len(all_decisions)} decisions to {self.logger.log_path}")
        print(f"✅ Recorded Policy Gap to {self.gap_register.gaps_path}")
        print(f"🔒 Final Hash: {self.logger.latest_hash}")

        return all_decisions
