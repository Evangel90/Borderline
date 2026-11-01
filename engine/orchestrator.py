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
from engine.knowledge import KnowledgeIndex
from engine.llm import create_chat_client
from audit.hasher import HashChainedLogger
from gaps.register import GapRegister
from gaps.candidates import evidence_sharing_trigger


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
        self.llm = create_chat_client()
        self.simulation_state: Dict[str, Any] = {}
        self.action_executor = ActionExecutor(self.simulation_state)

        # Load chunks
        self.chunks: Dict[str, List[Chunk]] = {
            "AE": self._load_chunks("packs/ae/chunks.jsonl"),
            "CH": self._load_chunks("packs/ch/chunks.jsonl"),
            "GLOBAL": self._load_chunks("packs/global/chunks.jsonl")
        }
        self.knowledge_index = KnowledgeIndex(
            self.chunks["AE"] + self.chunks["CH"] + self.chunks["GLOBAL"]
        )

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
        """Retrieve scoped vector candidates and rank them by configured legal terms."""
        candidates = []
        query = " ".join(terms + (required_terms or []))
        matches = self.knowledge_index.search(
            query,
            [jurisdiction],
            top_k=max(50, limit * 20),
            doc_id=doc_id,
        )
        for chunk in matches:
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
        decisions: List[DecisionLogEntry], step: int, status: str | None,
        actor_id: str, relevance: str,
    ) -> List[PolicyEvidence]:
        return [
            PolicyEvidence(
                source_type="run_log",
                source_ref=decision.entry_id,
                title=f"Step {step} decision by {decision.actor_name}",
                jurisdiction=decision.jurisdiction,
                excerpt=(
                    f"Visible event: {decision.visible_event}. "
                    f"Visible facts: {decision.visible_payload}. "
                    f"{decision.action_taken}: {decision.justification} "
                    f"Gate status: {decision.gate_status}; liaison status: {decision.liaison_status}."
                ),
                relevance=relevance,
            )
            for decision in decisions
            if decision.step == step
            and (status is None or decision.gate_status == status)
            and decision.actor_id == actor_id
        ]

    def _build_policy_gap(self, decisions: List[DecisionLogEntry]) -> PolicyGap | None:
        trigger = evidence_sharing_trigger(decisions)
        if trigger is None:
            return None
        secondary_decision, route_decision = trigger
        evidence = []
        evidence.extend(self._decision_evidence(
            decisions, route_decision.step, "ROUTE", route_decision.actor_id,
            "The run routed MoHAP's request for a cross-border account to Swissmedic through the configured liaison gate."
        ))
        evidence.extend(self._decision_evidence(
            decisions, secondary_decision.step, None, secondary_decision.actor_id,
            "The synthetic drill exposed this data-use fact to the vendor agent; its real-world truth is not independently established."
        ))
        evidence.extend(self._decision_evidence(
            decisions, secondary_decision.step, None, "fodio",
            "The synthetic drill exposed this data-use fact to the FDPIC agent; its real-world truth is not independently established."
        ))
        evidence.extend(self._retrieve_evidence(
            "AE", "AE-DATA-PDPL-2021",
            ["adequate level of protection", "transferred outside the State", "approved by the Office"],
            "Candidate passage for outbound UAE transfer scope; exact support and applicability unreviewed.",
            limit=2,
        ))
        evidence.extend(self._retrieve_evidence(
            "CH", "CH-HEALTH-MedDO",
            ["Art. 66", "Reporting obligation", "serious incidents", "occurred in Switzerland"],
            "Candidate medical-device reporting passage; territorial and product scope unreviewed.",
        ))
        evidence.extend(self._retrieve_evidence(
            "CH", "CH-DATA-FADP",
            ["Art. 16", "disclosed abroad", "adequate level of protection", "standard contractual clauses"],
            "Candidate Swiss disclosure provision; controller role and transfer direction unreviewed.",
        ))
        evidence.extend(self._retrieve_evidence(
            "CH", "CH-HEALTH-HRA",
            ["further use", "health-related personal data", "research", "informed consent"],
            "Candidate research provision; application to this vendor processing is unreviewed.",
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
            "Candidate advisory comparison; relevance to this data flow requires review.",
            required_terms=["federated data-sharing", "maintaining local control"],
        ))

        return PolicyGap(
            gap_id="GAP-HEALTH-001",
            category="EVIDENCE_DEFICIENCY",
            title="Unresolved evidence-sharing and incident-coordination question",
            host_jurisdiction="AE",
            partner_jurisdiction="CH",
            friction_point=(
                "The synthetic vendor recorded UAE-origin retinal images used for model retraining, "
                "and a simulated regulator request was routed for an account of that use. "
                "Controller roles, identifiability, processing basis, and the route's authority "
                "remain unresolved. These missing facts prevent a supported policy-gap conclusion."
            ),
            host_citation="Candidate UAE passages are listed below; exact support is unverified.",
            partner_citation="Candidate Swiss passages are listed below; exact support is unverified.",
            global_benchmark="WHO guidance is an advisory comparison candidate, subject to passage-level review.",
            remediation_recommendation=(
                "Define a regulator-approved incident exchange protocol that specifies the "
                "reporting route, lawful transfer basis, minimum necessary evidence, and "
                "privacy and security review. Treat federated analysis as an option for "
                "assessment, not as a substitute for consent or transfer authorization."
            ),
            finding_method=(
                "An observed secondary-use action and an observed routed evidence request trigger "
                "this question. Jurisdiction- and document-scoped retrieval supplies candidate passages; "
                "their exact support has not been validated."
            ),
            limitations=(
                "This is a synthetic drill finding, not legal advice. Vector similarity and "
                "keyword ranking do not verify that each selected passage supports its "
                "assigned relevance statement; "
                "the DPO Annex 1 check uses the checked-in 2023 text; source currency and "
                "application to a real incident require human review."
            ),
            evidence=evidence,
            assessment_status="INSUFFICIENT_EVIDENCE",
            trigger_entry_ids=[secondary_decision.entry_id, route_decision.entry_id],
            missing_evidence=[
                "Verified controller and processor roles",
                "Identifiability and provenance of the retinal images",
                "Applicable processing and transfer basis",
                "Authority for the configured liaison route",
                "Passage-level support and institutional applicability review",
            ],
        )

    def _init_agents(self) -> Dict[str, InstitutionalAgent]:
        agents = {}
        for pack_id, jurisdiction in (("ae", "AE"), ("ch", "CH"), ("global", "GLOBAL")):
            institution_dir = os.path.join("packs", pack_id, "institutions")
            if not os.path.isdir(institution_dir):
                continue
            for inst_file in sorted(os.listdir(institution_dir)):
                if not inst_file.endswith(".yaml"):
                    continue
                with open(os.path.join(institution_dir, inst_file), encoding="utf-8") as source:
                    inst = Institution(**yaml.safe_load(source))
                if inst.id in agents:
                    raise ValueError(f"Duplicate institution id '{inst.id}' across packs.")
                jurisdiction_chunks = (
                    self.chunks["AE"] + self.chunks["CH"] + self.chunks["GLOBAL"]
                    if jurisdiction == "GLOBAL"
                    else self.chunks[jurisdiction] + self.chunks["GLOBAL"]
                )
                agents[inst.id] = InstitutionalAgent(
                    inst, jurisdiction_chunks, self.llm, self.action_executor,
                    self.knowledge_index,
                )

        return agents

    def run(self, include_optional: bool = False) -> List[DecisionLogEntry]:
        print(f"\n🚀 Running Cross-Border Drill: {self.intent.title}")
        print(f"📁 Output Run Directory: {self.run_dir}")
        print("=" * 60)

        all_decisions = []

        for step in self.intent.timeline:
            if step.optional and not include_optional:
                continue
            print(f"\n▶ Step {step.step}: [{step.phase}]")
            if step.time_offset:
                print(f"  Time: {step.time_offset}")
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

            # Each agent receives only its explicit view of this event.
            active_actors = step.participants or ([step.initiator] if step.initiator else [])
            for actor_id in active_actors:
                if actor_id not in self.agents:
                    raise ValueError(
                        f"Step {step.step} names unknown participant '{actor_id}'."
                    )
                view = step.agent_views.get(actor_id)
                if view is None:
                    raise ValueError(
                        f"Step {step.step} is missing a private agent view for '{actor_id}'."
                    )
                visible_gate_status = gate_status if actor_id in step.gate_visible_to else None
                visible_gate_reason = gate_reason if visible_gate_status else ""
                agent = self.agents[actor_id]
                decision = agent.evaluate_step(
                    step.step,
                    view.event,
                    view.payload,
                    gate=self.gate,
                    gate_status=visible_gate_status,
                    gate_reason=visible_gate_reason,
                    expected_policy_checks=view.expected_policy_checks,
                    visible_state={
                        key: self.simulation_state[key]
                        for key in view.visible_state_keys
                        if key in self.simulation_state
                    },
                    allowed_actions=view.allowed_actions,
                )
                chained_entry = self.logger.append(decision.model_dump())
                all_decisions.append(DecisionLogEntry(**chained_entry))
                print(f"  🏛️  [{agent.institution.jurisdiction}] {agent.institution.id.upper()}: {decision.action_taken}")
                print(f"     Reason: {decision.justification}")
                print(f"     Cited: {', '.join(decision.cited_clauses[:2])}")
                print(f"     LLM: {decision.model_name} (self-reported confidence {decision.confidence})")
                print(f"     Tool result: {decision.tool_result}")
                print(f"     State changes: {decision.state_changes}")

        # Record only a triggered candidate question, with explicit evidence status.
        gap = self._build_policy_gap(all_decisions)
        if gap is not None:
            self.gap_register.record_gap(gap)
        print("\n" + "=" * 60)
        print(f"✅ Drill Completed! Logged {len(all_decisions)} decisions to {self.logger.log_path}")
        if gap is not None:
            print(f"✅ Recorded evidence-limited candidate to {self.gap_register.gaps_path}")
        else:
            print("ℹ️  No evidence-sharing candidate was triggered")
        print(f"🔒 Final Hash: {self.logger.latest_hash}")

        return all_decisions
