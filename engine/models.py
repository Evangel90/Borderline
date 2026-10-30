"""
engine/models.py - Core data schemas for Borderline engine.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


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


class StepPayload(BaseModel):
    step: int
    phase: str
    event: str
    initiator: str
    payload: Dict[str, Any]
    expected_policy_checks: List[str] = Field(default_factory=list)


class DrillIntent(BaseModel):
    id: str
    title: str
    version: str
    standard_alignment: Dict[str, Any]
    context: Dict[str, Any]
    actors: Dict[str, List[str]]
    timeline: List[StepPayload]


class DecisionLogEntry(BaseModel):
    entry_id: str
    step: int
    actor_id: str
    actor_name: str
    jurisdiction: str
    action_taken: str
    cited_clauses: List[str] = Field(default_factory=list)
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
    cited_chunk_ids: List[str] = Field(min_length=1, max_length=4)
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
