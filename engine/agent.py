"""
engine/agent.py - Institutional AI Agent representation.
Simulates authorities and companies making decisions grounded in legal chunks.
"""

from typing import List, Dict, Any, Optional
import json
import re
from engine.models import Institution, Chunk, DecisionLogEntry


class InstitutionalAgent:
    def __init__(self, institution: Institution, chunks: List[Chunk]):
        self.institution = institution
        self.chunks = chunks

    def search_knowledge(self, query_terms: List[str], top_k: int = 3) -> List[Chunk]:
        """Simple deterministic keyword search over this jurisdiction's chunks."""
        scores = []
        for c in self.chunks:
            score = 0
            text_lower = c.text.lower()
            for term in query_terms:
                term_lower = term.lower()
                if term_lower in text_lower:
                    score += text_lower.count(term_lower)
            if score > 0:
                scores.append((score, c))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scores[:top_k]]

    def evaluate_step(self, step: int, event: str, payload: Dict[str, Any], gate_status: Optional[str] = None) -> DecisionLogEntry:
        """Evaluate a drill event and render a legally grounded institutional decision."""
        # Query for relevant clauses based on institution role and event keywords
        keywords = self.institution.regulatory_scope + [self.institution.id]
        if "patient" in event.lower() or "data" in event.lower() or "transfer" in event.lower():
            keywords.extend(["transfer", "personal data", "disclosure", "adequate", "protection"])
        if "incident" in event.lower() or "false" in event.lower() or "safety" in event.lower():
            keywords.extend(["incident", "vigilance", "safety", "device", "adverse"])

        matched_chunks = self.search_knowledge(keywords, top_k=2)
        cited_clauses = [f"{c.doc_id} (p. {c.page})" for c in matched_chunks]

        # Determine action and justification based on role and institutional powers
        action = "MONITOR"
        justification = f"{self.institution.name} reviewed event under {', '.join(self.institution.regulatory_scope)}."
        liaison = gate_status or "LOCAL_ONLY"

        if self.institution.id == "ehs":
            action = "SUSPEND_AUTOMATED_DIAGNOSIS"
            justification = "Halted autonomous retinal screening in clinics following 23.4% false-negative divergence; initiated 100% clinician re-check."
        elif self.institution.id == "retina_swiss_ag":
            action = "REQUEST_ERROR_TELEMETRY"
            justification = "Requested diagnostic failure logs and retinal fundus images for urgent model debugging and retraining."
        elif self.institution.id == "uae_data_office":
            if gate_status == "BLOCK":
                action = "PAUSE_TRANSFER_PENDING_REVIEW"
                justification = "Paused this raw-scan transfer because no applicable UAE PDPL Arts. 22–23 basis or required safeguards were documented; the transfer route needs review before disclosure."
            else:
                action = "AUDIT_DATA_TRANSFERS"
                justification = "Audited cross-border transfer channels for compliance with data localization."
        elif self.institution.id == "mohap":
            action = "ISSUE_SAFETY_INQUIRY"
            justification = "Mandated safety review and initiated bilateral regulatory notification to Swissmedic."
        elif self.institution.id == "swissmedic":
            action = "REVIEW_FOREIGN_INCIDENT_REPORT"
            justification = "Opened a review to determine the applicable MedDO Art. 66 reporting route; the provision covers serious incidents in Switzerland and, where required, authorized representatives have trend-report duties for incidents in Switzerland and abroad."
        elif self.institution.id == "fodio":
            action = "ASSESS_TRANSFER_DIRECTION_AND_SCOPE"
            justification = "Reviewed the checked-in DPO Annex 1 list: UAE is not listed, which is relevant to disclosures from Switzerland to the UAE. This scenario requests a UAE-to-Switzerland transfer, so the list alone does not determine whether this request is permitted; assess the UAE export basis and the Swiss recipient's processing duties."

        return DecisionLogEntry(
            entry_id=f"log-{step}-{self.institution.id}",
            step=step,
            actor_id=self.institution.id,
            actor_name=self.institution.name,
            jurisdiction=self.institution.jurisdiction,
            action_taken=action,
            cited_clauses=cited_clauses if cited_clauses else self.institution.relevant_authorities,
            justification=justification,
            liaison_status=liaison,
            prev_hash="",
            current_hash=""
        )
