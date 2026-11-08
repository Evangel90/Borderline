"""
engine/orchestrator.py - Cross-Border Incident Drill Orchestrator.
Coordinates the drill timeline, agent invocations, border gate evaluation, and audit logging.
"""

import json
import os
import yaml
from typing import Dict, List, Any
from engine.models import (
    DrillIntent, Institution, Chunk, BridgeConfig, DecisionLogEntry, StepPayload,
    PolicyEvidence, PolicyGap,
)
from engine.gates import BorderGate
from engine.liaison import NOT_LAW, CANDIDATE_GAP_TYPES, LiaisonChannel, LiaisonReviewer, ScriptedReviewer
from engine.agent import InstitutionalAgent
from engine.actions import ActionExecutor
from engine.knowledge import KnowledgeIndex
from engine.llm import create_chat_client
from audit.hasher import HashChainedLogger
from gaps.register import GapRegister
from gaps.candidates import (
    assess_clinical_conflict,
    assess_deployment_readiness,
    evidence_sharing_trigger,
)


class DrillOrchestrator:
    @staticmethod
    def _step_enabled(step: StepPayload, state: Dict[str, Any]) -> bool:
        return all(state.get(key) == value for key, value in step.requires_state.items())

    def __init__(self, intent_path: str, run_id: str, reviewer: str = "ai"):
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
        institutions = self._load_institutions()

        # Load chunks
        self.chunks: Dict[str, List[Chunk]] = {
            "AE": self._load_chunks("packs/ae/chunks.jsonl"),
            "CH": self._load_chunks("packs/ch/chunks.jsonl"),
            "GLOBAL": self._load_chunks("packs/global/chunks.jsonl")
        }
        self.knowledge_index = KnowledgeIndex(
            self.chunks["AE"] + self.chunks["CH"] + self.chunks["GLOBAL"]
        )

        # An AI liaison reviewer answers the three liaison questions; code verifies its quotes.
        # reviewer="scripted" swaps in the labelled scripted reviewer (not an AI decision).
        if reviewer not in ("ai", "scripted"):
            raise ValueError(f"Unknown reviewer '{reviewer}'; use 'ai' or 'scripted'.")
        if reviewer == "scripted" and not self.intent.scripted_reviews:
            raise ValueError(f"Intent '{self.intent.id}' has no scripted_reviews for a scripted run.")
        liaison_reviewer = (ScriptedReviewer(self.intent.scripted_reviews) if reviewer == "scripted"
                            else LiaisonReviewer(self.llm, self.knowledge_index))
        self.liaison = (
            LiaisonChannel(
                self.bridge, {inst.id: inst for inst, _ in institutions},
                liaison_reviewer,
                library={c.chunk_id: c for pack in self.chunks.values() for c in pack},
                exhibits=self.intent.exhibits,
                approvals=self.intent.standing_approvals,
            )
            if self.bridge.liaison else None
        )
        if isinstance(liaison_reviewer, ScriptedReviewer) and self.liaison:
            liaison_reviewer.bind(self.liaison)
        self.action_executor = ActionExecutor(self.simulation_state, self.liaison)

        self.agents: Dict[str, InstitutionalAgent] = self._init_agents(institutions)

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
            "AE", "AE-DATA-PDPL-2021-EN",
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
            finding_class="EVIDENCE_LIMITED_CANDIDATE",
            conclusion=(
                "The observed simulated events justify a coordination question, but do not "
                "support a conclusion that a policy, legal, or standards gap exists."
            ),
            trigger_entry_ids=[secondary_decision.entry_id, route_decision.entry_id],
            missing_evidence=[
                "Verified controller and processor roles",
                "Identifiability and provenance of the retinal images",
                "Applicable processing and transfer basis",
                "Authority for the configured liaison route",
                "Passage-level support and institutional applicability review",
            ],
        )

    @staticmethod
    def _build_deployment_readiness_assessment(
        decisions: List[DecisionLogEntry],
    ) -> PolicyGap | None:
        result = assess_deployment_readiness(decisions)
        if result is None:
            return None
        packet_received = result.assessment_status == "READY_FOR_HUMAN_REVIEW"
        by_id = {item.entry_id: item for item in decisions}
        evidence = [
            PolicyEvidence(
                source_type="run_log",
                source_ref=entry_id,
                title=f"Step {by_id[entry_id].step} decision by {by_id[entry_id].actor_name}",
                jurisdiction=by_id[entry_id].jurisdiction,
                excerpt=(
                    f"Visible event: {by_id[entry_id].visible_event}. "
                    f"Visible facts: {by_id[entry_id].visible_payload}. "
                    f"Selected action: {by_id[entry_id].action_taken}."
                ),
                relevance="Observed synthetic deployment-review fact or action.",
            )
            for entry_id in result.trigger_entry_ids
        ]
        return PolicyGap(
            gap_id="DEPLOYMENT-READINESS-001",
            category="OPERATIONAL_EVIDENCE_DEFICIENCY",
            title=(
                "Vendor evidence received; remote screening awaits accountable review"
                if packet_received else
                "Remote screening deployment is pending missing vendor evidence"
            ),
            host_jurisdiction="AE",
            partner_jurisdiction="CH",
            friction_point=(
                "The fictional vendor supplied the requested validation, release, rollback, "
                "software-component and subprocessor exhibits. The clinic must now complete "
                "human review, workflow fit and transfer safeguards before activation."
                if packet_received else
                "The proposed UAE-to-Switzerland screening flow has an identified data path, "
                "but the fictional vendor has not supplied the validation, release, rollback, "
                "software-component and subprocessor records needed for accountable review."
            ),
            host_citation="This assessment records scenario facts and simulated actions; it does not assert a UAE legal duty.",
            partner_citation="This assessment records scenario facts and simulated actions; it does not assert a Swiss legal duty.",
            global_benchmark="No global policy comparison is claimed until a passage-level comparison is reviewed.",
            remediation_recommendation=(
                "Keep activation pending accountable human review. Review the supplied packet, "
                "confirm workflow fit and transfer safeguards, then document the activation decision."
                if packet_received else
                "Keep activation pending accountable human review. Obtain and review the listed "
                "vendor records, then document the transfer, clinical-workflow and access decisions."
            ),
            finding_method=(
                "Deterministic check for a proposed transfer review, a clinic review, an "
                "initially incomplete packet, and any later supplied vendor exhibits."
            ),
            limitations=(
                "The conclusion is limited to fictional scenario exhibits and does not establish "
                "legal applicability, real-world product quality, or a policy-gap conclusion."
            ),
            evidence=evidence,
            assessment_status=result.assessment_status,
            finding_class=result.finding_class,
            conclusion=(
                "The simulated clinic has received the requested vendor exhibits and can move to "
                "accountable human review; receipt does not approve activation or establish a legal duty."
                if packet_received else
                "The simulated clinic has a concrete reason to keep activation pending: specified "
                "vendor evidence is missing. This does not establish that a policy or law has a gap."
            ),
            trigger_entry_ids=list(result.trigger_entry_ids),
            missing_evidence=list(result.missing_evidence),
        )

    @staticmethod
    def _build_clinical_assessment(decisions: List[DecisionLogEntry]) -> PolicyGap:
        result = assess_clinical_conflict(decisions)
        if result.category == "NO_GAP_IDENTIFIED":
            finding_class = "REJECTED_HYPOTHESIS"
            conclusion = (
                "The recorded run does not establish the proposed diagnostic-safety versus "
                "screening-access conflict. No policy-gap conclusion is made."
            )
        elif result.category == "OBJECTIVE_CONFLICT" and result.missing_evidence:
            finding_class = "OPERATIONAL_DECISION_WITH_EVIDENCE_GAPS"
            conclusion = (
                "The run establishes a simulated operational tradeoff. Missing operational "
                "facts prevent a recommendation or a policy-gap conclusion."
            )
        elif result.category == "OBJECTIVE_CONFLICT":
            finding_class = "OPERATIONAL_DECISION_READY_FOR_HUMAN_REVIEW"
            conclusion = (
                "The run establishes a simulated operational tradeoff ready for accountable "
                "human review. It does not establish a policy or legal gap."
            )
        else:
            finding_class = "EVIDENCE_LIMITED_CANDIDATE"
            conclusion = (
                "The run raises a candidate operational or coordination question, but the "
                "available facts do not support a policy-gap conclusion."
            )
        by_id = {item.entry_id: item for item in decisions}
        evidence = [
            PolicyEvidence(
                source_type="run_log",
                source_ref=entry_id,
                title=f"Step {by_id[entry_id].step} decision by {by_id[entry_id].actor_name}",
                jurisdiction=by_id[entry_id].jurisdiction,
                excerpt=(
                    f"Visible event: {by_id[entry_id].visible_event}. "
                    f"Visible facts: {by_id[entry_id].visible_payload}. "
                    f"Selected action: {by_id[entry_id].action_taken}."
                ),
                relevance="Observed synthetic fact or action used to test the clinical safety tradeoff.",
            )
            for entry_id in result.trigger_entry_ids
        ]
        return PolicyGap(
            gap_id="CLINICAL-CONFLICT-001",
            category=result.category,
            title="Diagnostic safety versus screening access",
            host_jurisdiction="AE",
            partner_jurisdiction="N/A",
            friction_point=(
                "Confirmed synthetic false negatives and a clinic halt recommendation coexist with "
                "possible screening delays. The safe operational choice remains unresolved."
                if result.category == "OBJECTIVE_CONFLICT" else
                "The recorded facts or response do not establish the proposed pause-versus-access conflict."
            ),
            host_citation="Run facts and actions are listed below; applicable clinical authority is unreviewed.",
            partner_citation="Not applicable to this clinical operations question.",
            global_benchmark="No global comparison has been validated for this candidate.",
            remediation_recommendation=(
                "Assess manual screening capacity, patient follow-up, and rollback safety before "
                "a human approves any operational intervention."
                if result.category != "NO_GAP_IDENTIFIED" else
                "No gap recommendation from this rejected hypothesis."
            ),
            finding_method="Deterministic test of recorded safety signal, access impact, and clinic action.",
            limitations="Synthetic operational assessment; no policy duty or suspension authority is established.",
            evidence=evidence,
            assessment_status=result.assessment_status,
            finding_class=finding_class,
            conclusion=conclusion,
            trigger_entry_ids=list(result.trigger_entry_ids),
            missing_evidence=list(result.missing_evidence),
        )

    @staticmethod
    def _load_institutions() -> List[tuple[Institution, str]]:
        institutions = []
        seen = set()
        for pack_id, jurisdiction in (("ae", "AE"), ("ch", "CH"), ("global", "GLOBAL")):
            institution_dir = os.path.join("packs", pack_id, "institutions")
            if not os.path.isdir(institution_dir):
                continue
            for inst_file in sorted(os.listdir(institution_dir)):
                if not inst_file.endswith(".yaml"):
                    continue
                with open(os.path.join(institution_dir, inst_file), encoding="utf-8") as source:
                    inst = Institution(**yaml.safe_load(source))
                if inst.id in seen:
                    raise ValueError(f"Duplicate institution id '{inst.id}' across packs.")
                seen.add(inst.id)
                institutions.append((inst, jurisdiction))
        return institutions

    def _init_agents(
        self, institutions: List[tuple[Institution, str]],
    ) -> Dict[str, InstitutionalAgent]:
        agents = {}
        for inst, jurisdiction in institutions:
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

    @staticmethod
    def _build_liaison_gaps(decisions: List[DecisionLogEntry]) -> List[PolicyGap]:
        """Turn blocked liaison requests into gap candidates.

        Only NO / UNCLEAR answers typed policy_gap, implementation_gap or conflict can
        become candidates; their verified quotes are the evidence. missing_evidence is
        our own homework and is listed by _liaison_homework instead.
        """
        gaps = []
        for decision in decisions:
            if decision.liaison_status != "BLOCK":
                continue
            typed = [
                check for check in decision.liaison_checks
                if check["answer"] != "YES" and check.get("gap_type") in CANDIDATE_GAP_TYPES
            ]
            if not typed:
                continue
            target = decision.visible_payload.get("target", "unknown")
            verified = [
                quote for check in typed for quote in check.get("quotes", []) if quote["verified"]
            ]
            own = decision.jurisdiction
            gaps.append(PolicyGap(
                gap_id=f"LIAISON-{decision.step}-{decision.actor_id}",
                category="LIAISON_BLOCKED",
                title=f"Cross-border request from {decision.actor_id} to {target} could not be delivered",
                host_jurisdiction=own,
                partner_jurisdiction="CH" if own == "AE" else "AE",
                friction_point=" ".join(
                    f"{check['question']} {check['answer']} ({check['gap_type']}): {check['reason']}"
                    for check in typed
                ),
                host_citation=", ".join(sorted({q["chunk_id"] for q in verified if q["jurisdiction"] == own})) or "None recorded.",
                partner_citation=", ".join(sorted({q["chunk_id"] for q in verified if q["jurisdiction"] not in {own} | NOT_LAW})) or "None recorded.",
                global_benchmark=", ".join(sorted({q["chunk_id"] for q in verified if q["jurisdiction"] == "GLOBAL"})) or "No global example paired yet.",
                remediation_recommendation="Establish who may exchange incident evidence across the border, on what legal basis, and through which counterpart.",
                finding_method=(
                    "An AI liaison reviewer answered the three liaison questions; code verified each "
                    "quote verbatim against its chunk and typed every NO or UNCLEAR."
                ),
                limitations=(
                    "Unreviewed candidate, not a legal conclusion. Quotes are verified as exact text only; "
                    "whether they support the answer has not been reviewed by anyone with legal standing. "
                    "An instrument absent from this knowledge base may still exist."
                ),
                evidence=[
                    PolicyEvidence(
                        source_type="policy_chunk",
                        source_ref=quote["chunk_id"],
                        title=quote["doc_id"],
                        jurisdiction=quote["jurisdiction"],
                        excerpt=quote["quote"] + (
                            f" [{quote['translation_label']}: {quote['translation']}]"
                            if quote.get("translation") else ""
                        ),
                        relevance="Verified verbatim quote relied on by the liaison reviewer.",
                    )
                    for quote in verified
                ],
                assessment_status="BLOCKED_BY_LIAISON_CHECK",
                finding_class="potential_gap",
                conclusion=f"The request was blocked; {len(typed)} of 3 liaison checks carry a gap type.",
                trigger_entry_ids=[decision.entry_id],
                missing_evidence=[
                    check["question"] for check in decision.liaison_checks
                    if check["answer"] != "YES" and check.get("gap_type") == "missing_evidence"
                ],
                gap_types=sorted({check["gap_type"] for check in typed}),
            ))
        return gaps

    @staticmethod
    def _liaison_homework(decisions: List[DecisionLogEntry]) -> List[Dict[str, Any]]:
        """List missing_evidence answers: documents we lack, not gaps in the law."""
        return [
            {
                "entry_id": decision.entry_id,
                "step": decision.step,
                "sender": decision.actor_id,
                "receiver": decision.visible_payload.get("target", "unknown"),
                "question": check["question"],
                "reason": check["reason"],
                "code_adjustments": check.get("adjustments", []),
            }
            for decision in decisions
            for check in decision.liaison_checks
            if check["answer"] != "YES" and check.get("gap_type") == "missing_evidence"
        ]

    def run(self, include_optional: bool = False) -> List[DecisionLogEntry]:
        print(f"\n🚀 Running Cross-Border Drill: {self.intent.title}")
        print(f"📁 Output Run Directory: {self.run_dir}")
        print("=" * 60)

        all_decisions = []

        for step in self.intent.timeline:
            if step.optional and not include_optional:
                continue
            if not self._step_enabled(step, self.simulation_state):
                print(f"  ↪ Skipping conditional step {step.step}: required state not present")
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
                print(f"     Agent model: {decision.model_name} (self-reported confidence {decision.confidence})")
                print(f"     Tool result: {decision.tool_result}")
                print(f"     State changes: {decision.state_changes}")

        # Record only a triggered candidate question, with explicit evidence status.
        deployment_assessment = self._build_deployment_readiness_assessment(all_decisions)
        candidates = [deployment_assessment] if deployment_assessment else [
            self._build_clinical_assessment(all_decisions)
        ]
        sharing_candidate = self._build_policy_gap(all_decisions)
        if sharing_candidate is not None:
            candidates.append(sharing_candidate)
        candidates.extend(self._build_liaison_gaps(all_decisions))
        for candidate in candidates:
            self.gap_register.record_gap(candidate)
        homework = self._liaison_homework(all_decisions)
        homework_path = os.path.join(self.run_dir, "liaison_homework.jsonl")
        with open(homework_path, "w", encoding="utf-8") as output:
            for item in homework:
                output.write(json.dumps(item, ensure_ascii=False) + "\n")
        print("\n" + "=" * 60)
        print(f"✅ Drill Completed! Logged {len(all_decisions)} decisions to {self.logger.log_path}")
        print(f"✅ Recorded {len(candidates)} governance assessments to {self.gap_register.gaps_path}")
        print(f"📝 Recorded {len(homework)} missing-evidence liaison answers to {homework_path}")
        print(f"🔒 Final Hash: {self.logger.latest_hash}")

        return all_decisions
