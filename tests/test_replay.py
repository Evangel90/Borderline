"""Code replay (`make replay`): re-running code decisions over logged AI answers."""

import copy

from engine.liaison import decide_liaison
from engine.models import (
    Chunk, DrillIntent, LiaisonAnswer, LiaisonQuote, LiaisonReview, LiaisonRule, StepPayload,
)
from engine.replay import replay_letter, replay_steps


def chunk(chunk_id, text, jurisdiction):
    return Chunk(chunk_id=chunk_id, doc_id=chunk_id.split(":")[0], title=chunk_id,
                 jurisdiction=jurisdiction, page=1, total_pages=1, chunk_index=0, text=text,
                 source_file="synthetic")


# Synthetic passages; test fixtures, not real legal text.
BASIS = chunk("CH-TEST-LAW:p1:c1", "The authority may disclose non-public information to foreign "
              "authorities that enforce therapeutic product rules, if the requester keeps official secrecy.", "CH")
TRANSFER = chunk("AE-TEST-LAW:p1:c1", "Health data may be transferred outside the State where a resolution "
                 "of the Health Authority permits the transfer for the stated purpose.", "AE")
COUNTERPART = chunk("CH-TEST-ORD:p2:c1", "Requests from foreign health regulators are answered by the "
                    "national therapeutic products agency.", "CH")
CHUNKS = {c.chunk_id: c for c in (BASIS, TRANSFER, COUNTERPART)}
REFERENCE = {key: LiaisonRule(answer="UNCLEAR", reason="test") for key in
             ("legal_basis", "transfer_rules", "counterpart")}


def yes(source, text=None):
    return LiaisonAnswer(answer="YES", reason="shown",
                         quotes=[LiaisonQuote(chunk_id=source.chunk_id, quote=text or source.text)])


def logged_entry(review, payload, step=3, sender="ae_health"):
    """A log entry as the drill writes it, from a live decision."""
    decision = decide_liaison(review, CHUNKS, payload,
                              {"reviewer_model": "fake", "reviewer_status": "OK",
                               "evidence_shown": list(CHUNKS)}, REFERENCE)
    outcome = "delivered" if decision.status == "ROUTE" else "blocked_by_liaison_check"
    return {
        "entry_id": f"log-{step}-{sender}", "step": step, "actor_id": sender,
        "visible_payload": payload, "liaison_status": decision.status,
        "liaison_checks": decision.checks, "liaison_review": decision.review,
        "state_changes": {"regulatory_evidence_request": outcome,
                          f"regulatory_evidence_request.{sender}": outcome},
    }


def all_yes():
    return LiaisonReview(legal_basis=yes(BASIS), transfer_rules=yes(TRANSFER), counterpart=yes(COUNTERPART))


NO_DATA = {"target": "ch_device", "patient_data_included": False}
PATIENT_DATA = {"target": "ch_device", "patient_data_included": True}


def test_replay_reproduces_a_logged_delivery_and_block():
    for review in (all_yes(), all_yes().model_copy(update={"counterpart": LiaisonAnswer(
            answer="UNCLEAR", reason="unsure", gap_type="missing_evidence")})):
        entry = logged_entry(review, NO_DATA)
        letter = replay_letter(entry, CHUNKS)
        assert letter.differences == []
        assert letter.replayed_status == entry["liaison_status"]


def test_replay_reports_an_edited_answer():
    entry = logged_entry(all_yes(), NO_DATA)
    assert entry["liaison_status"] == "ROUTE"
    edited = copy.deepcopy(entry)
    basis = next(c for c in edited["liaison_checks"] if c["check"] == "legal_basis")
    basis["proposed_answer"], basis["proposed_gap_type"] = "UNCLEAR", "missing_evidence"
    letter = replay_letter(edited, CHUNKS)
    assert letter.replayed_status == "BLOCK"
    assert any("logged ROUTE, replayed BLOCK" in d for d in letter.differences)


def test_invented_quote_in_a_log_cannot_move_patient_data():
    review = all_yes().model_copy(update={"transfer_rules": yes(
        TRANSFER, "Health data may be transferred outside the State to any foreign regulator without conditions.")})
    entry = logged_entry(review, PATIENT_DATA)
    assert entry["liaison_status"] == "BLOCK"
    letter = replay_letter(entry, CHUNKS)
    assert letter.differences == []
    assert letter.replayed_status == "BLOCK"
    assert "patient-data rule" in letter.decided_by


def test_chunk_id_correction_is_replayed_from_the_reviewers_own_label():
    review = all_yes().model_copy(update={"legal_basis": LiaisonAnswer(
        answer="YES", reason="mislabelled",
        quotes=[LiaisonQuote(chunk_id=COUNTERPART.chunk_id, quote=BASIS.text)])})
    entry = logged_entry(review, NO_DATA)
    quote = next(c for c in entry["liaison_checks"] if c["check"] == "legal_basis")["quotes"][0]
    assert quote["chunk_id_corrected_from"] == COUNTERPART.chunk_id
    assert replay_letter(entry, CHUNKS).differences == []


def test_passage_missing_from_today_s_packs_is_a_difference():
    entry = logged_entry(all_yes(), NO_DATA)
    fewer = {k: v for k, v in CHUNKS.items() if k != TRANSFER.chunk_id}
    letter = replay_letter(entry, fewer)
    assert any("no longer in the chunk packs" in d for d in letter.differences)
    assert letter.replayed_status == "BLOCK"


def test_conditional_steps_follow_the_replayed_letter():
    entry = logged_entry(all_yes(), NO_DATA, step=1)
    letter = replay_letter(entry, CHUNKS)

    def step(n, requires=None):
        return StepPayload(step=n, phase=f"step {n}", event="e", payload={},
                           requires_state=requires or {})

    intent = DrillIntent.model_construct(timeline=[
        step(1),
        step(2, {"regulatory_evidence_request.ae_health": "delivered"}),
        step(3, {"regulatory_evidence_request.ae_health": "blocked_by_liaison_check"}),
    ])
    ran_delivered_branch = [entry, {"entry_id": "log-2-x", "step": 2, "actor_id": "x", "state_changes": {}}]
    rows, diffs = replay_steps(intent, ran_delivered_branch, {entry["entry_id"]: letter})
    assert diffs == [] and [r["replayed"] for r in rows] == ["run", "run", "skip"]

    ran_blocked_branch = [entry, {"entry_id": "log-3-x", "step": 3, "actor_id": "x", "state_changes": {}}]
    rows, diffs = replay_steps(intent, ran_blocked_branch, {entry["entry_id"]: letter})
    assert len(diffs) == 2  # step 2 should have run; step 3 should not
