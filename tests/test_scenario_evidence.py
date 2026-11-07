"""Step 3: the drill feeds the new evidence questions to DHA and the policy adviser."""

import glob
import json
import os
import re

import pytest
import yaml

from engine.actions import ActionExecutor
from engine.agent import InstitutionalAgent
from engine.models import AvailableAction, Chunk, DrillIntent, Institution

PP13_475 = "AE-DHA-HEALTH-INFO-SHARING-PP13-2024:p18:c2"
NCAR_ANNEX1 = "IMDRF-NCAR-N14-2025:p16:c1"
# Section 4.2, second passage: confidentiality arrangements between participating regulators.
NCAR_42_ARRANGEMENTS = "IMDRF-NCAR-N14-2025:p9:c2"


@pytest.fixture(scope="module")
def intent():
    with open("intents/retinopathy-ae-ch.yaml", encoding="utf-8") as source:
        return DrillIntent(**yaml.safe_load(source))


def view(intent, step_no, actor):
    step = next(s for s in intent.timeline if s.step == step_no)
    assert actor in step.participants
    return step.agent_views[actor]


def text_of(v):
    return " ".join([v.event, json.dumps(v.payload), *v.expected_policy_checks]).lower()


# --- The scenario asks the questions. ---

def test_step5_policy_adviser_tests_the_research_claim(intent):
    v = view(intent, 5, "policy_adviser")
    assert v.payload["claimed_purpose"] == "research"
    for fact in ("ethics_approval", "consent_records", "deidentification_log"):
        assert v.payload[fact] == "not_located"
    assert any("PP-13" in check for check in v.expected_policy_checks)


def test_dha_is_not_told_the_research_claim_before_the_uae_learns_of_the_reuse(intent):
    # UAE authorities learn of the reuse at step 6 (T+7h); step 5 is T+6h.
    step5 = next(s for s in intent.timeline if s.step == 5)
    assert "dha" not in step5.participants


def test_step12_dha_tests_the_research_claim_with_a_matching_action(intent):
    v = view(intent, 12, "dha")
    assert v.payload["vendor_claimed_purpose"] == "research"
    assert "assess_secondary_use_claim" in v.allowed_actions
    assert any("PP-13" in check for check in v.expected_policy_checks)
    with open("packs/ae/institutions/dha.yaml", encoding="utf-8") as source:
        dha = Institution(**yaml.safe_load(source))
    assert "assess_secondary_use_claim" in {a.name for a in dha.available_actions}
    assert ActionExecutor.LOCAL_STATE_ACTIONS["assess_secondary_use_claim"][1] == "human_review_required"


@pytest.mark.parametrize("step_no", [11, 12])
def test_policy_adviser_gets_the_incident_report_exchange_question(intent, step_no):
    v = view(intent, step_no, "policy_adviser")
    assert any("NCAR" in check and "Annex 1" in check for check in v.expected_policy_checks)


@pytest.mark.parametrize("step_no, actor", [(5, "policy_adviser"), (11, "policy_adviser"),
                                            (12, "dha"), (12, "policy_adviser")])
def test_new_views_ask_questions_and_do_not_hard_code_conclusions(intent, step_no, actor):
    text = text_of(view(intent, step_no, actor))
    for conclusion in (r"\bfails?\b", r"does not meet", r"\bviolat", r"not a participant",
                       r"neither (?:country|switzerland)", r"\bunlawful\b", r"\billegal\b",
                       r"claim is (?:false|invalid)"):
        assert not re.search(conclusion, text), conclusion


# --- The agent searches with each check question, without displacing anything. ---

def chunk(chunk_id, jurisdiction="AE"):
    return Chunk(chunk_id=chunk_id, doc_id=chunk_id, title=chunk_id, jurisdiction=jurisdiction,
                 page=1, total_pages=1, chunk_index=0, text="synthetic", source_file="synthetic")


class FakeIndex:
    def __init__(self, hits):
        self.hits, self.calls = hits, []

    def search(self, query, jurisdictions, top_k=4):
        self.calls.append((query, jurisdictions, top_k))
        return self.hits.get(query, [])[:top_k]


def agent_with(index):
    inst = Institution(id="t", name="t", jurisdiction="AE", type="t", role="t", mandate="t",
                       available_actions=[AvailableAction(name="a", description="a")])
    return InstitutionalAgent(inst, [chunk("seed")], llm=object(), knowledge_index=index)


def test_check_search_appends_without_displacing_or_duplicating():
    base = [chunk("b1"), chunk("b2")]
    index = FakeIndex({"q1": [chunk("b1"), chunk("x1"), chunk("x2")], "q2": [chunk("x1"), chunk("x3")]})
    result = agent_with(index)._with_check_evidence(base, ["q1", "q2"])
    assert [c.chunk_id for c in result] == ["b1", "b2", "x1", "x3"]
    assert all(top_k == 2 for _, _, top_k in index.calls)
    assert all(j == ["AE"] for _, j, _ in index.calls)  # stays inside the agent's jurisdictions


def test_no_checks_or_no_index_leaves_evidence_unchanged():
    base = [chunk("b1")]
    assert agent_with(FakeIndex({}))._with_check_evidence(base, []) == base
    assert agent_with(None)._with_check_evidence(base, ["q"]) == base


# --- Integration: with the real local index, the agents see the passages. ---

@pytest.mark.skipif(not os.path.isdir("index/chroma"), reason="local vector index not built")
@pytest.mark.parametrize("step_no, actor, wanted", [
    (5, "policy_adviser", [PP13_475]),
    (11, "policy_adviser", [NCAR_ANNEX1, NCAR_42_ARRANGEMENTS]),
    (12, "dha", [PP13_475]),
    (12, "policy_adviser", [PP13_475, NCAR_ANNEX1, NCAR_42_ARRANGEMENTS]),
])
def test_real_retrieval_surfaces_the_new_evidence(intent, real_index, step_no, actor, wanted):
    index, chunks, institutions = real_index
    inst = institutions[actor]
    pool = (chunks["AE"] + chunks["CH"] + chunks["GLOBAL"] if inst.jurisdiction == "GLOBAL"
            else chunks[inst.jurisdiction] + chunks["GLOBAL"])
    agent = InstitutionalAgent(inst, pool, llm=object(), knowledge_index=index)
    v = view(intent, step_no, actor)
    evidence = agent.search_knowledge(
        agent._keywords(v.event, v.payload, inst),
        query_context=f"{v.event} {json.dumps(v.payload, ensure_ascii=False)}",
    )
    got = {c.chunk_id for c in agent._with_check_evidence(evidence, v.expected_policy_checks)}
    assert set(wanted) <= got


@pytest.fixture(scope="module")
def real_index():
    from engine.knowledge import KnowledgeIndex
    chunks = {}
    for pack in ("ae", "ch", "global"):
        with open(f"packs/{pack}/chunks.jsonl", encoding="utf-8") as source:
            chunks[pack.upper()] = [Chunk(**json.loads(line)) for line in source if line.strip()]
    institutions = {}
    for path in glob.glob("packs/*/institutions/*.yaml"):
        with open(path, encoding="utf-8") as source:
            inst = Institution(**yaml.safe_load(source))
        institutions[inst.id] = inst
    return KnowledgeIndex(chunks["AE"] + chunks["CH"] + chunks["GLOBAL"]), chunks, institutions


def test_evaluate_step_puts_check_passages_in_the_model_prompt():
    from engine.models import AgentProposal

    class CapturingLLM:
        model = "capture"

        def __init__(self):
            self.users = []

        def generate(self, system, user, schema, output_schema):
            self.users.append(user)
            return AgentProposal(action="a", rationale="Recording the synthetic action.",
                                 cited_chunk_ids=[], confidence=0.4)

    check = "Which conditions does the policy set for research use without consent?"
    index = FakeIndex({check: [chunk("CHECK-HIT")]})
    agent = agent_with(index)
    agent.llm = CapturingLLM()
    agent.search_knowledge = lambda *_a, **_k: [chunk("MAIN-HIT")]
    agent.action_executor = type("Exec", (), {"execute": lambda self, *a, **k: type(
        "R", (), {"action": "a", "result": "ok", "state_changes": {}, "liaison_status": "LOCAL_ONLY",
                  "liaison_checks": [], "liaison_review": {}})()})()
    decision = agent.evaluate_step(1, "event", {}, gate=None, expected_policy_checks=[check])
    shown = [item["chunk_id"] for item in json.loads(agent.llm.users[0])["evidence"]]
    assert shown == ["MAIN-HIT", "CHECK-HIT"]
    assert decision.retrieved_chunk_ids == ["MAIN-HIT", "CHECK-HIT"]
