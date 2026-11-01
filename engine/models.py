"""
engine/models.py - Core data schemas for Borderline engine.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    jurisdiction: str
    page: int
    total_pages: int
    chunk_index: int
    text: str
    source_file: str
    source_url: str = ""
    source_issuer: str = ""
    source_sha256: str = ""
    source_retrieved: str = ""
    source_language: str = ""
    source_official_language: str = ""
    source_binding: str = ""
    source_in_force_from: str = ""
    source_notes: str = ""


class AvailableAction(BaseModel):
    name: str
    description: str


class Institution(BaseModel):
    id: str
    name: str
    jurisdiction: str
    type: str
    role: str
    mandate: str
    regulatory_scope: List[str] = Field(default_factory=list)
    relevant_authorities: List[str] = Field(default_factory=list)
    powers: List[str] = Field(default_factory=list)
    available_actions: List[AvailableAction] = Field(default_factory=list)
    drill_behavior: Dict[str, Any] = Field(default_factory=dict)


class GateRule(BaseModel):
    action: str  # BLOCK, ALLOW, ROUTE
    reason: Optional[str] = None
    conditions: List[str] = Field(default_factory=list)
    path: Optional[str] = None


class BridgeConfig(BaseModel):
    id: str
    title: str
    parties: Dict[str, Any]
    adequacy_status: Dict[str, Any]
    cross_border_regimes: Dict[str, Any]
    liaison_gate_rules: Dict[str, GateRule]


class AgentView(BaseModel):
    event: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    expected_policy_checks: List[str] = Field(default_factory=list)
    visible_state_keys: List[str] = Field(default_factory=list)
    allowed_actions: Optional[List[str]] = None


class StepPayload(BaseModel):
    step: int
    phase: str
    time_offset: str = ""
    event: str
    initiator: Optional[str] = None
    payload: Dict[str, Any]
    participants: List[str] = Field(default_factory=list)
    agent_views: Dict[str, AgentView] = Field(default_factory=dict)
    gate_visible_to: List[str] = Field(default_factory=list)
    optional: bool = False
    expected_policy_checks: List[str] = Field(default_factory=list)
    requires_state: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_agent_views(self) -> "StepPayload":
        if self.participants and set(self.participants) != set(self.agent_views):
            raise ValueError(
                f"Step {self.step} participants and agent_views must contain the same actor IDs."
            )
        if len(set(self.participants)) != len(self.participants):
            raise ValueError(f"Step {self.step} lists a participant more than once.")
        unknown_gate_viewers = set(self.gate_visible_to) - set(self.participants)
        if unknown_gate_viewers:
            raise ValueError(
                f"Step {self.step} gate_visible_to contains nonparticipants: "
                f"{', '.join(sorted(unknown_gate_viewers))}."
            )
        return self


class DrillIntent(BaseModel):
    id: str
    title: str
    version: str
    standard_alignment: Dict[str, Any]
    context: Dict[str, Any]
    actors: Dict[str, List[str]]
    timeline: List[StepPayload]

    @model_validator(mode="after")
    def validate_timeline_actors(self) -> "DrillIntent":
        declared = {actor_id for actors in self.actors.values() for actor_id in actors}
        for step in self.timeline:
            participants = set(step.participants)
            if step.initiator:
                participants.add(step.initiator)
            unknown = participants - declared
            if unknown:
                raise ValueError(
                    f"Step {step.step} refers to undeclared actors: {', '.join(sorted(unknown))}."
                )
        return self


class DecisionLogEntry(BaseModel):
    entry_id: str
    step: int
    actor_id: str
    actor_name: str
    jurisdiction: str
    action_taken: str
    visible_event: Optional[str] = None
    visible_payload: Dict[str, Any] = Field(default_factory=dict)
    visible_state: Dict[str, Any] = Field(default_factory=dict)
    authorized_actions: List[str] = Field(default_factory=list)
    retrieved_chunk_ids: List[str] = Field(default_factory=list)
    cited_clauses: List[str] = Field(default_factory=list)
    evidence_status: Optional[str] = None
    evidence_note: Optional[str] = None
    rationale_quality: Optional[str] = None
    justification: str
    model_name: Optional[str] = None
    tool_name: Optional[str] = None
    tool_result: Optional[str] = None
    confidence: Optional[float] = None
    state_changes: Dict[str, Any] = Field(default_factory=dict)
    liaison_status: Optional[str] = None  # gate result for the selected action or LOCAL_ONLY
    gate_status: Optional[str] = None
    gate_reason: Optional[str] = None
    prev_hash: str
    current_hash: str


class AgentProposal(BaseModel):
    action: str
    rationale: str = Field(min_length=1, max_length=600)
    cited_chunk_ids: List[str] = Field(max_length=4)
    confidence: float = Field(ge=0, le=1)


class PolicyEvidence(BaseModel):
    source_type: str  # policy_chunk or run_log
    source_ref: str
    title: str
    jurisdiction: str
    page: Optional[int] = None
    excerpt: str
    relevance: str


class PolicyGap(BaseModel):
    gap_id: str
    category: str
    title: str
    host_jurisdiction: str
    partner_jurisdiction: str
    friction_point: str
    host_citation: str
    partner_citation: str
    global_benchmark: str
    remediation_recommendation: str
    finding_method: str
    limitations: str
    evidence: List[PolicyEvidence] = Field(default_factory=list)
    assessment_status: str = "UNASSESSED_LEGACY"
    trigger_entry_ids: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
