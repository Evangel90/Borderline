from engine.agent import InstitutionalAgent
from engine.models import AgentProposal, AvailableAction, Chunk, Institution


class RepeatingLLM:
    model = "synthetic-test"

    def __init__(self):
        self.calls = 0

    def generate(self, *_args):
        self.calls += 1
        return AgentProposal(
            action="request_manual_review",
            rationale="Assess clinical screening safety after missed referrals",
            cited_chunk_ids=["c1"],
            confidence=0.5,
        )


def test_agent_retries_and_abstains_from_unrelated_citation():
    institution = Institution(
        id="test_clinic", name="Synthetic clinic", jurisdiction="AE", type="provider",
        role="clinical review", mandate="Review synthetic incident", powers=[],
        available_actions=[AvailableAction(name="request_manual_review", description="Review screening safety")],
    )
    evidence = Chunk(
        chunk_id="c1", doc_id="d1", title="Synthetic cyber glossary", jurisdiction="AE",
        page=1, total_pages=1, chunk_index=1,
        text="Definitions of encryption and network access", source_file="synthetic",
    )
    llm = RepeatingLLM()
    agent = InstitutionalAgent(institution, [evidence], llm=llm)
    agent.search_knowledge = lambda *_args, **_kwargs: [evidence]
    decision = agent.evaluate_step(1, "missed referrals", {}, gate=None)
    assert llm.calls == 2
    assert decision.action_taken == "request_manual_review"
    assert decision.cited_clauses == []
    assert decision.evidence_status == "INSUFFICIENT_EVIDENCE"
