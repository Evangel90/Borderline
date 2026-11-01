from engine.evidence import off_topic_rationale, triage_citations
from engine.models import Chunk


def chunk(text):
    return Chunk(
        chunk_id="c1", doc_id="d1", title="Synthetic", jurisdiction="AE",
        page=1, total_pages=1, chunk_index=1, text=text, source_file="synthetic",
    )


def test_unrelated_citation_is_flagged():
    status, weak = triage_citations(
        "Assess clinical screening safety after missed referrals",
        "Review screening safety",
        ["c1"], {"c1": chunk("Definitions of encryption and network access")},
    )
    assert status == "UNSUPPORTED"
    assert weak == ["c1"]


def test_overlap_requires_review_and_empty_citation_abstains():
    evidence = {"c1": chunk("Clinical screening safety requires careful monitoring")}
    assert triage_citations("Assess clinical screening safety", "Review safety", ["c1"], evidence)[0] == "PARTIALLY_SUPPORTED"
    assert triage_citations("Assess clinical screening safety", "Review safety", [], evidence)[0] == "INSUFFICIENT_EVIDENCE"


def test_advisory_and_foreign_sources_do_not_support_legal_claim_in_triage():
    advisory = chunk("Clinical screening safety may require monitoring")
    advisory.source_binding = "guidance"
    foreign = chunk("Clinical screening safety may require monitoring")
    foreign.jurisdiction = "CH"
    foreign.source_binding = "law"
    claim = "The regulator is legally mandated to monitor clinical screening safety"
    assert triage_citations(claim, "Review safety", ["c1"], {"c1": advisory}, "AE")[0] == "UNSUPPORTED"
    assert triage_citations(claim, "Review safety", ["c1"], {"c1": foreign}, "AE")[0] == "UNSUPPORTED"
    assert triage_citations(
        "The guidance establishes a vendor duty to monitor clinical screening safety",
        "Review safety", ["c1"], {"c1": advisory}, "AE",
    )[0] == "UNSUPPORTED"


def test_document_assistant_response_is_flagged():
    assert off_topic_rationale("The user has provided a set of documents and chunks for summary")
    assert off_topic_rationale("The provided citation IDs do not support the action. The model will update its knowledge base.")
    assert not off_topic_rationale("The clinic should review missed referrals and request follow-up")


def test_action_topic_rejects_generic_data_passage_even_with_word_overlap():
    evidence = {"c1": chunk("Patient data review records are maintained.")}
    status, weak = triage_citations(
        "Review patient data records", "Review patient records", ["c1"], evidence,
        "AE", "request_patient_follow_up_review",
    )
    assert status == "UNSUPPORTED"
    assert weak == ["c1"]
