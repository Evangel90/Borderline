import json

import pytest
import yaml

from audit.hasher import HashChainedLogger
from engine.actions import ActionExecutor
from engine.gates import BorderGate
from engine.liaison import (
    TRANSLATION_LABEL, LiaisonChannel, LiaisonReviewer, finalize_answer, garbled_arabic,
    verify_quote,
)
from engine.models import (
    AvailableAction, BridgeConfig, Chunk, DecisionLogEntry, Institution, LiaisonAnswer,
    LiaisonConfig, LiaisonQuote, LiaisonReview, LiaisonRule,
)
from engine.orchestrator import DrillOrchestrator


def institution(inst_id, jurisdiction, actions=()):
    return Institution(
        id=inst_id, name=inst_id, jurisdiction=jurisdiction, type="test", role="test",
        mandate="test",
        available_actions=[AvailableAction(name=name, description=name) for name in actions],
    )


INSTITUTIONS = {
    "ae_health": institution("ae_health", "AE", ["request_regulatory_evidence"]),
    "ae_emirate_health": institution("ae_emirate_health", "AE", ["request_regulatory_evidence"]),
    "ch_device": institution("ch_device", "CH"),
}


def chunk(chunk_id, text, jurisdiction="CH", language="en", doc_id=None):
    return Chunk(
        chunk_id=chunk_id, doc_id=doc_id or chunk_id.split(":")[0], title=chunk_id,
        jurisdiction=jurisdiction, page=1, total_pages=1, chunk_index=0, text=text,
        source_file="synthetic", source_language=language,
    )


# Synthetic passages; these are test fixtures, not real legal text.
CH_BASIS = chunk(
    "CH-TEST-LAW:p1:c1",
    "The authority may disclose\n non-public information to foreign authorities that enforce "
    "therapeutic product rules, if the requester is bound by official secrecy.",
)
AE_TRANSFER = chunk(
    "AE-TEST-LAW:p1:c1",
    "Health data may be transferred outside the State where a resolution of the Health Authority "
    "permits the transfer for the stated purpose.", jurisdiction="AE",
)
CH_COUNTERPART = chunk(
    "CH-TEST-ORDINANCE:p2:c1",
    "Requests from foreign health regulators are answered by the national therapeutic products agency.",
)
AE_CONFLICT = chunk(
    "AE-TEST-POLICY:p3:c1",
    "Protected health information should not be transferred to a country or territory outside the State.",
    jurisdiction="AE",
)
# Correctly written Arabic (synthetic test sentence).
AR_CLEAN = chunk(
    "AE-TEST-AR:p1:c1",
    "لا يجوز تخزين أو معالجة أو نقل البيانات والمعلومات الصحية خارج الدولة إلا بقرار من الجهة الصحية",
    jurisdiction="AE", language="ar",
)
# Same sentence with the PyMuPDF faults seen in the UAE PDFs: a broken lam-alef and
# a letter-reversed word.
AR_GARBLED = chunk(
    "AE-TEST-AR-GARBLED:p1:c1",
    "لا يجوز نقل البيانات الصحية خارج دولة اإلمارات ةدحتملا إلا بقرار من الجهة الصحية",
    jurisdiction="AE", language="ar",
)
EVIDENCE = [CH_BASIS, AE_TRANSFER, CH_COUNTERPART, AE_CONFLICT, AR_CLEAN, AR_GARBLED]


def quote(source, words=None, translation=""):
    text = " ".join(source.text.split())
    if words:
        text = " ".join(text.split()[:words])
    return LiaisonQuote(chunk_id=source.chunk_id, quote=text, translation=translation)


def yes(source):
    return LiaisonAnswer(answer="YES", reason="The passage shows it.", quotes=[quote(source)])


def all_yes():
    return LiaisonReview(legal_basis=yes(CH_BASIS), transfer_rules=yes(AE_TRANSFER),
                         counterpart=yes(CH_COUNTERPART))


class FakeReviewer:
    """Stands in for the AI liaison reviewer so tests need no model."""
    model_name = "fake-reviewer"

    def __init__(self, review=None, error=None, evidence=None):
        self._review, self._error = review, error
        self._evidence = EVIDENCE if evidence is None else evidence

    def gather_evidence(self, sender, receiver, request_type, payload):
        return list(self._evidence)

    def review(self, sender, receiver, request_type, payload, evidence):
        if self._error:
            raise self._error
        return self._review


def bridge(legal_basis="YES", transfers=None):
    return BridgeConfig(
        id="test", title="Synthetic test", parties={}, adequacy_status={},
        cross_border_regimes={}, liaison_gate_rules={},
        liaison=LiaisonConfig(
            counterparts=[["ae_health", "ch_device"]],
            request_types={
                "cross_border_evidence_request": LiaisonRule(answer=legal_basis, reason="test basis"),
            },
            personal_data_transfers=transfers or {},
        ),
    )


def channel(review=None, error=None, evidence=None, config=None):
    return LiaisonChannel(config or bridge(), INSTITUTIONS, FakeReviewer(review, error, evidence))


def send(chan, payload=None, sender="ae_health"):
    return chan.check(INSTITUTIONS[sender], "ch_device", "cross_border_evidence_request",
                      {"patient_data_included": False} if payload is None else payload)


def answers(decision):
    return {check["check"]: check["answer"] for check in decision.checks}


def by_key(decision, key):
    return next(check for check in decision.checks if check["check"] == key)


# --- Verified quotes route. ---

def test_verified_quotes_on_all_three_questions_route():
    decision = send(channel(all_yes()))
    assert decision.status == "ROUTE"
    assert answers(decision) == {"legal_basis": "YES", "transfer_rules": "YES", "counterpart": "YES"}
    assert all(q["verified"] for check in decision.checks for q in check["quotes"])
    assert decision.review["quotes_verified"] == 3
    assert decision.review["hard_floor_applied"] is False


def test_quote_check_normalizes_whitespace_only():
    spaced = CH_BASIS.text.replace(" ", "   \n ")
    assert verify_quote(CH_BASIS.chunk_id, spaced, "", {CH_BASIS.chunk_id: CH_BASIS})["verified"]
    # One capital letter changed is a copy slip: accepted, but the logged quote is the exact source text.
    lowered = CH_BASIS.text.lower()
    slipped = verify_quote(CH_BASIS.chunk_id, lowered, "", {CH_BASIS.chunk_id: CH_BASIS})
    assert slipped["verified"] and slipped["quote"] == " ".join(CH_BASIS.text.split())
    assert slipped["quote_corrected_from"] == lowered
    # Three slips are too many.
    three = CH_BASIS.text.replace("authority", "authorty").replace("foreign", "foriegn")
    assert not verify_quote(CH_BASIS.chunk_id, three, "", {CH_BASIS.chunk_id: CH_BASIS})["verified"]


# --- Fabricated, altered or uncited quotes become UNCLEAR / missing_evidence. ---

@pytest.mark.parametrize("bad_quote, failure", [
    (LiaisonQuote(chunk_id=CH_BASIS.chunk_id,
                  quote="The authority must disclose all information to any foreign authority on request."),
     "verbatim"),
    (LiaisonQuote(chunk_id=CH_BASIS.chunk_id,
                  quote=CH_BASIS.text.replace("may disclose", "shall disclose")),
     "verbatim"),
    (LiaisonQuote(chunk_id="CH-NOT-SHOWN:p9:c9",
                  quote="The authority may disclose information to any foreign body without conditions."),
     "not among the passages available"),
    (LiaisonQuote(chunk_id=CH_BASIS.chunk_id, quote="The authority may disclose"),
     "shorter than"),
])
def test_fabricated_or_altered_quote_becomes_unclear(bad_quote, failure):
    review = all_yes().model_copy(update={"legal_basis": LiaisonAnswer(
        answer="YES", reason="Invented support.", quotes=[bad_quote],
    )})
    decision = send(channel(review))
    basis = by_key(decision, "legal_basis")
    assert decision.status == "BLOCK"
    assert basis["proposed_answer"] == "YES"
    assert basis["answer"] == "UNCLEAR"
    assert basis["gap_type"] == "missing_evidence"
    assert failure in basis["quotes"][0]["failure"]
    assert basis["adjustments"]


def test_one_bad_quote_spoils_an_answer_with_good_ones():
    review = all_yes().model_copy(update={"legal_basis": LiaisonAnswer(
        answer="YES", reason="Mixed.",
        quotes=[quote(CH_BASIS), LiaisonQuote(chunk_id=CH_BASIS.chunk_id,
                                              quote="this sentence is not in the chunk at all")],
    )})
    basis = by_key(send(channel(review)), "legal_basis")
    assert basis["answer"] == "UNCLEAR" and basis["gap_type"] == "missing_evidence"


@pytest.mark.parametrize("answer", ["YES", "NO"])
def test_uncited_yes_or_no_becomes_unclear(answer):
    review = all_yes().model_copy(update={"counterpart": LiaisonAnswer(
        answer=answer, reason="No quote given.", gap_type="policy_gap" if answer == "NO" else None,
    )})
    check = by_key(send(channel(review)), "counterpart")
    assert check["answer"] == "UNCLEAR"
    assert check["gap_type"] == "missing_evidence"


def test_reviewer_failure_blocks_and_never_uses_yaml_answers():
    decision = send(channel(error=RuntimeError("model offline")))
    assert decision.status == "BLOCK"
    assert decision.review["reviewer_status"] == "REVIEWER_FAILED"
    assert "model offline" in decision.review["reviewer_error"]
    # The YAML reference says YES to all three here; it is logged, not used.
    assert all(check["reference_answer"] == "YES" for check in decision.checks)
    assert answers(decision) == {key: "UNCLEAR" for key in ("legal_basis", "transfer_rules", "counterpart")}
    assert {check["gap_type"] for check in decision.checks} == {"missing_evidence"}


# --- Patient data never crosses without a verified legal basis. ---

@pytest.mark.parametrize("payload", [{"patient_data_included": True}, {}])
def test_patient_data_without_verified_basis_is_always_blocked(payload):
    review = all_yes().model_copy(update={"legal_basis": LiaisonAnswer(
        answer="YES", reason="Says yes without a real quote.",
        quotes=[LiaisonQuote(chunk_id=CH_BASIS.chunk_id, quote="Any data may always be sent abroad freely.")],
    )})
    decision = send(channel(review), payload)
    assert decision.status == "BLOCK"
    assert decision.review["patient_data_carried"] is True
    assert decision.review["hard_floor_applied"] is True
    assert "Patient-data floor" in decision.reason


RECALL = {"patient_data_included": True, "purpose": "patient_recall", "data_subjects": 3,
          "data_fields": ["case_reference", "clinic"], "images_included": False}


def approval(**changes):
    from engine.models import ApprovalBasis, StandingApproval
    fields = dict(id="APPROVAL-1", approved_by="test legal officer (role)", sender="ae_health",
                  receiver="ch_device", request_type="cross_border_evidence_request",
                  purpose="patient_recall", data_fields=["clinic", "case_reference"], data_subjects=3,
                  images_included=False,
                  legal_basis=ApprovalBasis(chunk_id=CH_BASIS.chunk_id, quote=CH_BASIS.text))
    fields.update(changes)
    return StandingApproval(**fields)


def approved_channel(review, approvals):
    return LiaisonChannel(bridge(), INSTITUTIONS, FakeReviewer(review),
                          library={c.chunk_id: c for c in EVIDENCE}, approvals=approvals)


def test_patient_data_with_verified_quotes_but_no_human_approval_is_blocked():
    decision = send(channel(all_yes()), RECALL)
    assert answers(decision) == {"legal_basis": "YES", "transfer_rules": "YES", "counterpart": "YES"}
    assert decision.status == "BLOCK"
    assert decision.review["hard_floor_applied"] is True
    assert "no matching recorded human approval" in decision.review["status_decided_by"]


def test_patient_data_routes_with_verified_quotes_and_a_matching_approval():
    decision = send(approved_channel(all_yes(), [approval()]), RECALL)
    assert decision.status == "ROUTE"
    assert decision.review["hard_floor_applied"] is False
    assert decision.review["human_approval"]["approval_id"] == "APPROVAL-1"
    assert "APPROVAL-1" in decision.review["status_decided_by"]


@pytest.mark.parametrize("change", [
    {"data_fields": ["case_reference", "clinic", "retinal_image"]},
    {"data_subjects": 4},
    {"images_included": True},
    {"receiver": "ae_emirate_health"},
    {"purpose": "research"},
])
def test_an_approval_with_a_different_scope_does_not_count(change):
    decision = send(approved_channel(all_yes(), [approval(**change)]), RECALL)
    assert decision.status == "BLOCK"
    assert decision.review["human_approval"]["checked"][0]["scope_mismatches"]


def test_an_approval_resting_on_an_invented_quote_does_not_count():
    from engine.models import ApprovalBasis
    fake = approval(legal_basis=ApprovalBasis(
        chunk_id=CH_BASIS.chunk_id, quote="The authority may send any patient data abroad without conditions."))
    decision = send(approved_channel(all_yes(), [fake]), RECALL)
    assert decision.status == "BLOCK"


def test_patient_data_needs_national_law_not_only_an_exhibit():
    from engine.models import DrillExhibit
    exhibit = DrillExhibit(id="EXH-TEST", title="assurance", issued_by="ae_health",
                           text="We confirm that the requesting authority is bound by official secrecy in this matter.")
    chan = LiaisonChannel(bridge(), INSTITUTIONS, FakeReviewer(None), library={c.chunk_id: c for c in EVIDENCE},
                          exhibits=[exhibit], approvals=[approval()])
    shown = {**{c.chunk_id: c for c in EVIDENCE}, "EXH-TEST:p1:c1": chan.library["EXH-TEST:p1:c1"]}
    review = all_yes().model_copy(update={"legal_basis": LiaisonAnswer(
        answer="YES", reason="exhibit only", quotes=[LiaisonQuote(chunk_id="EXH-TEST:p1:c1",
                                                                  quote=exhibit.text)])})
    basis = finalize_answer("legal_basis", review.legal_basis, shown)
    assert basis["answer"] == "UNCLEAR"
    assert "non-national" in " ".join(basis["adjustments"])


def test_letter_evidence_always_shows_the_relied_on_provision_and_exhibits():
    from engine.models import DrillExhibit
    exhibit = DrillExhibit(id="EXH-TEST", title="assurance", issued_by="ae_health",
                           text="We confirm that the requesting authority is bound by official secrecy in this matter.")
    shown_to_reviewer = {}

    class Recording(FakeReviewer):
        def review(self, sender, receiver, request_type, payload, evidence):
            shown_to_reviewer.update({c.chunk_id: c for c in evidence})
            return all_yes()

    chan = LiaisonChannel(bridge(), INSTITUTIONS, Recording(evidence=[]),
                          library={c.chunk_id: c for c in EVIDENCE}, exhibits=[exhibit])
    send(chan, {"patient_data_included": False, "relied_on": [CH_BASIS.chunk_id], "exhibits": ["EXH-TEST"]})
    assert {CH_BASIS.chunk_id, "EXH-TEST:p1:c1"} <= set(shown_to_reviewer)
    assert shown_to_reviewer["EXH-TEST:p1:c1"].title.startswith("Drill exhibit")
    with pytest.raises(ValueError, match="do not exist"):
        send(chan, {"patient_data_included": False, "relied_on": ["CH-NOPE:p1:c1"]})


def test_letter_facts_are_copied_from_the_letter_in_plain_words():
    from engine.liaison import letter_facts
    facts = letter_facts({"patient_data_included": False, "health_data_involved": False,
                          "data_category": "staff_contact_and_login_data", "target": "x"})
    assert facts == ["Patient data in this letter: none.", "Health data involved: no.",
                     "Data category: staff contact and login data."]


def test_floor_holds_even_if_the_routing_rule_is_bypassed(monkeypatch):
    # Simulate a future bug that marks every check YES after the quote check.
    import engine.liaison as liaison

    real = liaison.finalize_answer

    def always_yes(key, proposed, shown):
        check = real(key, proposed, shown)
        return {**check, "answer": "YES", "gap_type": None}

    monkeypatch.setattr(liaison, "finalize_answer", always_yes)
    review = all_yes().model_copy(update={"legal_basis": LiaisonAnswer(answer="YES", reason="none")})
    decision = send(channel(review), {"patient_data_included": True})
    assert decision.status == "BLOCK"
    assert decision.review["hard_floor_applied"] is True


# --- Every NO / UNCLEAR is typed. ---

@pytest.mark.parametrize("proposed, quotes, expected", [
    ("policy_gap", [CH_BASIS], "policy_gap"),
    ("implementation_gap", [AE_TRANSFER], "implementation_gap"),
    ("conflict", [AE_TRANSFER, AE_CONFLICT], "conflict"),
    ("missing_evidence", [], "missing_evidence"),
    (None, [CH_BASIS], "missing_evidence"),
    ("legal_conclusion", [CH_BASIS], "missing_evidence"),
    ("policy_gap", [], "missing_evidence"),
    ("implementation_gap", [], "missing_evidence"),
    ("conflict", [AE_TRANSFER], "missing_evidence"),
])
def test_every_unclear_or_no_carries_a_type_the_quotes_can_support(proposed, quotes, expected):
    shown = {c.chunk_id: c for c in EVIDENCE}
    for answer in ("NO", "UNCLEAR"):
        check = finalize_answer("legal_basis", LiaisonAnswer(
            answer=answer, reason="test", quotes=[quote(c) for c in quotes], gap_type=proposed,
        ), shown)
        assert check["answer"] in {"NO", "UNCLEAR"}
        assert check["gap_type"] == expected


def test_yes_has_no_gap_type_and_unknown_answer_is_unclear():
    shown = {c.chunk_id: c for c in EVIDENCE}
    assert finalize_answer("legal_basis", LiaisonAnswer(
        answer="YES", reason="test", quotes=[quote(CH_BASIS)], gap_type="policy_gap"), shown)["gap_type"] is None
    check = finalize_answer("legal_basis", LiaisonAnswer(
        answer="MAYBE", reason="test", quotes=[quote(CH_BASIS)], gap_type="policy_gap"), shown)
    assert check["answer"] == "UNCLEAR" and check["gap_type"] == "policy_gap"


def test_every_non_yes_check_in_a_decision_is_typed():
    review = LiaisonReview(
        legal_basis=LiaisonAnswer(answer="UNCLEAR", reason="silent", quotes=[quote(CH_BASIS)], gap_type="policy_gap"),
        transfer_rules=LiaisonAnswer(answer="NO", reason="?", quotes=[quote(AE_CONFLICT)]),
        counterpart=LiaisonAnswer(answer="UNCLEAR", reason="no doc", gap_type="missing_evidence"),
    )
    decision = send(channel(review))
    for check in decision.checks:
        if check["answer"] != "YES":
            assert check["gap_type"] in {"policy_gap", "implementation_gap", "conflict", "missing_evidence"}


# --- Arabic quotes. ---

def test_arabic_quote_verifies_against_arabic_chunk_with_labelled_translation():
    shown = {AR_CLEAN.chunk_id: AR_CLEAN}
    record = verify_quote(AR_CLEAN.chunk_id, AR_CLEAN.text,
                          "Health data may not be stored, processed or transferred outside the State "
                          "except by a decision of the health authority", shown)
    assert record["verified"], record["failure"]
    assert record["translation_label"] == TRANSLATION_LABEL
    assert record["language"] == "ar"


def test_arabic_quote_without_translation_fails():
    record = verify_quote(AR_CLEAN.chunk_id, AR_CLEAN.text, "", {AR_CLEAN.chunk_id: AR_CLEAN})
    assert not record["verified"]
    assert "translation" in record["failure"]


def test_english_translation_alone_cannot_cite_an_arabic_chunk():
    record = verify_quote(AR_CLEAN.chunk_id,
                          "Health data may not be stored, processed or transferred outside the State",
                          "", {AR_CLEAN.chunk_id: AR_CLEAN})
    assert not record["verified"]
    assert "quote the Arabic original" in record["failure"]


def test_arabic_quote_against_english_chunk_fails():
    record = verify_quote(CH_BASIS.chunk_id, AR_CLEAN.text, "translation", {CH_BASIS.chunk_id: CH_BASIS})
    assert not record["verified"]
    assert "non-Arabic chunk" in record["failure"]


def test_garbled_arabic_is_never_accepted_as_verbatim():
    record = verify_quote(AR_GARBLED.chunk_id, AR_GARBLED.text, "translation",
                          {AR_GARBLED.chunk_id: AR_GARBLED})
    assert not record["verified"]
    assert "extraction errors" in record["failure"]


@pytest.mark.parametrize("text, garbled", [
    ("قرار وزاري رقم ( 51 ) لسنة 2021م بشأن الحالات التي يجوز فيها تخزين أو نقل البيانات", False),
    ("دولة اإلمارات العربية", True),           # broken lam-alef
    ("الدليل املتعلق بالتقارير", True),         # broken lam-meem
    ("مرسوم ﻟﺴﻨﺔ 2024", True),                 # presentation-form glyphs
    ("تارامإلا ةيبرعلا ةدحتملا", True),          # letters reversed within words
])
def test_garbled_arabic_signs(text, garbled):
    assert garbled_arabic(text) is garbled


def test_arabic_answer_in_a_decision_carries_label_and_routes_basis():
    review = all_yes().model_copy(update={"transfer_rules": LiaisonAnswer(
        answer="YES", reason="Arabic passage.",
        quotes=[quote(AR_CLEAN, translation="Health data may not be transferred outside the State except by decision")],
    )})
    check = by_key(send(channel(review)), "transfer_rules")
    assert check["answer"] == "YES"
    assert check["quotes"][0]["translation_label"] == TRANSLATION_LABEL


# --- Logging. ---

def test_quote_checks_are_in_the_hash_chained_log(tmp_path):
    review = all_yes().model_copy(update={"legal_basis": LiaisonAnswer(
        answer="YES", reason="Invented.",
        quotes=[LiaisonQuote(chunk_id=CH_BASIS.chunk_id, quote="This text was invented by the reviewer model.")],
    )})
    config = bridge()
    executor = ActionExecutor({}, channel(review, config=config))
    result = executor.execute(
        INSTITUTIONS["ae_health"], "request_regulatory_evidence",
        {"target": "ch_device", "patient_data_included": False}, BorderGate(config),
    )
    entry = DecisionLogEntry(
        entry_id="log-1-ae_health", step=1, actor_id="ae_health", actor_name="ae_health",
        jurisdiction="AE", action_taken=result.action, justification="test",
        visible_payload={"target": "ch_device"}, liaison_status=result.liaison_status,
        liaison_checks=result.liaison_checks, liaison_review=result.liaison_review,
        prev_hash="", current_hash="",
    )
    logger = HashChainedLogger(str(tmp_path))
    logger.append(entry.model_dump())
    assert HashChainedLogger.verify_log(logger.log_path)[0] is True

    record = json.loads(open(logger.log_path, encoding="utf-8").read())
    basis = next(c for c in record["liaison_checks"] if c["check"] == "legal_basis")
    assert basis["quotes"][0]["verified"] is False
    assert basis["answer"] == "UNCLEAR"
    assert record["liaison_review"]["reviewer_model"] == "fake-reviewer"

    # Rewriting the quote check result breaks the chain.
    basis["quotes"][0]["verified"] = True
    with open(logger.log_path, "w", encoding="utf-8") as output:
        output.write(json.dumps(record) + "\n")
    assert HashChainedLogger.verify_log(logger.log_path)[0] is False


def test_disagreement_with_yaml_reference_is_logged():
    decision = send(channel(all_yes(), config=bridge(legal_basis="UNCLEAR")))
    assert decision.status == "ROUTE"
    assert by_key(decision, "legal_basis")["reference_answer"] == "UNCLEAR"
    assert decision.review["disagreements_with_reference"] == ["legal_basis"]


# --- Gap candidates: only typed gaps; missing_evidence is homework. ---

def logged(decision, entry_id="log-5-ae_health"):
    return DecisionLogEntry(
        entry_id=entry_id, step=5, actor_id="ae_health", actor_name="ae_health", jurisdiction="AE",
        action_taken="request_regulatory_evidence", justification="test",
        visible_payload={"target": "ch_device"}, liaison_status=decision.status,
        liaison_checks=decision.checks, liaison_review=decision.review,
        prev_hash="", current_hash="",
    )


def test_only_typed_gaps_become_candidates_with_verified_quotes_as_evidence():
    review = LiaisonReview(
        legal_basis=LiaisonAnswer(answer="UNCLEAR", reason="silent", quotes=[quote(CH_BASIS)], gap_type="policy_gap"),
        transfer_rules=yes(AE_TRANSFER),
        counterpart=LiaisonAnswer(answer="UNCLEAR", reason="no doc", gap_type="missing_evidence"),
    )
    entry = logged(send(channel(review)))
    gaps = DrillOrchestrator._build_liaison_gaps([entry])
    assert len(gaps) == 1
    assert gaps[0].gap_types == ["policy_gap"]
    assert [e.source_ref for e in gaps[0].evidence] == [CH_BASIS.chunk_id]
    assert "not a legal conclusion" in gaps[0].limitations
    homework = DrillOrchestrator._liaison_homework([entry])
    assert [item["question"] for item in homework] == ["Is the receiver the right counterpart?"]


def test_missing_evidence_alone_is_not_a_candidate():
    entry = logged(send(channel(error=RuntimeError("down"))))
    assert DrillOrchestrator._build_liaison_gaps([entry]) == []
    assert len(DrillOrchestrator._liaison_homework([entry])) == 3


# --- Channel plumbing (unchanged behaviour). ---

def test_same_country_request_is_rejected():
    with pytest.raises(ValueError, match="does not cross a border"):
        channel(all_yes()).check(INSTITUTIONS["ae_health"], "ae_emirate_health",
                                 "cross_border_evidence_request", {})


def test_invalid_reference_answer_is_rejected():
    with pytest.raises(ValueError):
        LiaisonRule(answer="MAYBE", reason="test")


@pytest.mark.parametrize("review, expected_state", [
    (all_yes(), "delivered"), (None, "blocked_by_liaison_check"),
])
def test_executor_sends_requests_through_the_channel(review, expected_state):
    config = bridge()
    executor = ActionExecutor({}, channel(review, config=config))
    result = executor.execute(
        INSTITUTIONS["ae_health"], "request_regulatory_evidence",
        {"target": "ch_device", "patient_data_included": False}, BorderGate(config),
    )
    assert result.state_changes == {
        "regulatory_evidence_request": expected_state,
        "regulatory_evidence_request.ae_health": expected_state,
    }
    assert len(result.liaison_checks) == 3
    assert result.liaison_review["reviewer_model"] == "fake-reviewer"


def test_per_sender_state_survives_a_later_request():
    config = bridge()
    good = ActionExecutor({}, channel(all_yes(), config=config))
    payload = {"target": "ch_device", "patient_data_included": False}
    good.execute(INSTITUTIONS["ae_health"], "request_regulatory_evidence", payload, BorderGate(config))
    good.liaison = channel(None, config=config)
    good.execute(INSTITUTIONS["ae_emirate_health"], "request_regulatory_evidence", payload, BorderGate(config))
    assert good.state["regulatory_evidence_request.ae_health"] == "delivered"
    assert good.state["regulatory_evidence_request.ae_emirate_health"] == "blocked_by_liaison_check"
    assert good.state["regulatory_evidence_request"] == "blocked_by_liaison_check"


# --- The AI reviewer's call. ---

class FakeLLM:
    model = "fake-llm"

    def __init__(self, result):
        self.result, self.calls = result, []

    def generate(self, system, user, schema, output_schema):
        self.calls.append((system, user, schema, output_schema))
        return self.result


class FakeIndex:
    def __init__(self, chunks):
        self.chunks, self.queries = chunks, []

    def search(self, query, jurisdictions, top_k=4):
        self.queries.append((query, jurisdictions))
        return [c for c in self.chunks if c.jurisdiction in jurisdictions][:top_k]


def test_ai_reviewer_sees_full_passages_and_is_restricted_to_shown_chunk_ids():
    llm = FakeLLM(all_yes())
    index = FakeIndex([CH_BASIS, AE_TRANSFER, CH_COUNTERPART])
    reviewer = LiaisonReviewer(llm, index)
    chan = LiaisonChannel(bridge(), INSTITUTIONS, reviewer)
    decision = send(chan)
    assert decision.status == "ROUTE"
    assert decision.review["reviewer_model"] == "fake-llm"
    # Each side is searched on its own, so one country's passages cannot crowd out the other's.
    assert sorted({tuple(j) for _, j in index.queries}) == [("AE",), ("CH",), ("GLOBAL",)]
    system, user, schema, output_schema = llm.calls[0]
    assert schema is LiaisonReview
    allowed = output_schema["$defs"]["LiaisonQuote"]["properties"]["chunk_id"]["enum"]
    assert sorted(allowed) == sorted(c.chunk_id for c in index.chunks)
    answer_schema = output_schema["$defs"]["LiaisonAnswer"]
    assert answer_schema["properties"]["quotes"]["minItems"] == 1
    assert "quotes" in answer_schema["required"]
    passages = json.loads(user)["passages"]
    shown_basis = next(p for p in passages if p["chunk_id"] == CH_BASIS.chunk_id)
    assert shown_basis["text"] == " ".join(CH_BASIS.text.split())  # not truncated
    assert "not legal conclusions" in system


def test_ai_reviewer_invalid_output_blocks():
    reviewer = LiaisonReviewer(FakeLLM("not a review"), FakeIndex([CH_BASIS]))
    decision = send(LiaisonChannel(bridge(), INSTITUTIONS, reviewer))
    assert decision.status == "BLOCK"
    assert decision.review["reviewer_status"] == "REVIEWER_FAILED"


# --- Checked-in bridge pack: YAML answers as a reference fixture. ---

def checked_in():
    with open("packs/bridge/ae-ch.yaml", encoding="utf-8") as source:
        config = BridgeConfig(**yaml.safe_load(source))
    institutions = {}
    for path in ("packs/ae/institutions/dha.yaml", "packs/ae/institutions/mohap.yaml",
                 "packs/ae/institutions/uae_data_office.yaml",
                 "packs/ch/institutions/swissmedic.yaml", "packs/ch/institutions/fodio.yaml"):
        with open(path, encoding="utf-8") as source:
            inst = Institution(**yaml.safe_load(source))
        institutions[inst.id] = inst
    return LiaisonChannel(config, institutions, FakeReviewer()), institutions


@pytest.mark.parametrize("sender, receiver, request_type, expected", [
    ("dha", "swissmedic", "cross_border_evidence_request",
     {"legal_basis": "UNCLEAR", "transfer_rules": "YES", "counterpart": "NO"}),
    ("mohap", "swissmedic", "cross_border_evidence_request",
     {"legal_basis": "UNCLEAR", "transfer_rules": "YES", "counterpart": "YES"}),
    ("uae_data_office", "fodio", "data_protection_assistance_request",
     {"legal_basis": "UNCLEAR", "transfer_rules": "YES", "counterpart": "YES"}),
])
def test_checked_in_yaml_reference_answers(sender, receiver, request_type, expected):
    chan, institutions = checked_in()
    reference = chan.reference(institutions[sender], institutions[receiver], request_type,
                               {"patient_data_included": False})
    assert {key: rule.answer for key, rule in reference.items()} == expected


def test_checked_in_reference_for_possible_patient_data_uses_directional_rule():
    chan, institutions = checked_in()
    reference = chan.reference(institutions["mohap"], institutions["swissmedic"],
                               "cross_border_evidence_request", {})
    assert reference["transfer_rules"].answer == "UNCLEAR"
    assert reference["transfer_rules"].sources == ["AE-HEALTH-ICT-LAW-2019"]


# --- Run review 2026-11-07: an exact quote is not proof that it answers the question. ---

GLOBAL_GUIDANCE = chunk(
    "GLOBAL-TEST-RECOMMENDATION:p1:c1",
    "Member countries should take steps to improve the ability of their authorities to co-operate.",
    jurisdiction="GLOBAL",
)


def test_legal_basis_resting_only_on_global_guidance_is_unclear():
    review = all_yes().model_copy(update={"legal_basis": yes(GLOBAL_GUIDANCE)})
    decision = send(channel(review, evidence=EVIDENCE + [GLOBAL_GUIDANCE]))
    basis = by_key(decision, "legal_basis")
    assert (basis["answer"], basis["gap_type"]) == ("UNCLEAR", "missing_evidence")
    assert any("global" in note for note in basis["adjustments"])
    assert decision.status == "BLOCK"


def test_global_guidance_may_still_back_other_questions():
    review = all_yes().model_copy(update={"counterpart": yes(GLOBAL_GUIDANCE)})
    decision = send(channel(review, evidence=EVIDENCE + [GLOBAL_GUIDANCE]))
    assert answers(decision)["counterpart"] == "YES"


def test_every_yes_is_flagged_for_human_review_and_others_are_not():
    review = all_yes().model_copy(update={"counterpart": LiaisonAnswer(
        answer="UNCLEAR", reason="Not shown.", quotes=[quote(CH_COUNTERPART)], gap_type="policy_gap")})
    decision = send(channel(review))
    flags = {c["check"]: c["human_review_required"] for c in decision.checks}
    assert flags == {"legal_basis": True, "transfer_rules": True, "counterpart": False}
    assert by_key(decision, "legal_basis")["human_review_note"]
    assert decision.review["yes_answers_for_human_review"] == ["legal_basis", "transfer_rules"]


# --- Option 1 (2026-11-07): a real quote with the wrong passage label is relabelled, never rewritten. ---

def test_real_quote_with_wrong_chunk_id_is_moved_to_the_right_passage():
    review = all_yes().model_copy(update={"legal_basis": LiaisonAnswer(
        answer="YES", reason="Mislabelled.",
        quotes=[LiaisonQuote(chunk_id=CH_COUNTERPART.chunk_id, quote=" ".join(CH_BASIS.text.split()))])})
    decision = send(channel(review))
    basis = by_key(decision, "legal_basis")
    q = basis["quotes"][0]
    assert q["verified"] and q["chunk_id"] == CH_BASIS.chunk_id
    assert q["chunk_id_corrected_from"] == CH_COUNTERPART.chunk_id
    assert any("chunk ID corrected by code" in note for note in basis["adjustments"])
    assert basis["answer"] == "YES" and basis["human_review_required"]
    assert decision.status == "ROUTE"


def test_altered_quote_is_not_relocated():
    altered = " ".join(CH_BASIS.text.split()).replace("may disclose", "shall disclose")
    review = all_yes().model_copy(update={"legal_basis": LiaisonAnswer(
        answer="YES", reason="Altered.", quotes=[LiaisonQuote(chunk_id=CH_COUNTERPART.chunk_id, quote=altered)])})
    basis = by_key(send(channel(review)), "legal_basis")
    assert not basis["quotes"][0]["verified"] and basis["answer"] == "UNCLEAR"
    assert "chunk_id_corrected_from" not in basis["quotes"][0]


def test_quote_found_in_two_other_passages_is_ambiguous_and_fails():
    twin = chunk("CH-TEST-TWIN:p1:c1", CH_BASIS.text)
    review = all_yes().model_copy(update={"legal_basis": LiaisonAnswer(
        answer="YES", reason="Ambiguous.",
        quotes=[LiaisonQuote(chunk_id=CH_COUNTERPART.chunk_id, quote=" ".join(CH_BASIS.text.split()))])})
    basis = by_key(send(channel(review, evidence=EVIDENCE + [twin])), "legal_basis")
    assert not basis["quotes"][0]["verified"]
    assert "2 other passages" in basis["quotes"][0]["failure"]


def test_arabic_rules_still_apply_after_relocation():
    no_translation = LiaisonQuote(chunk_id=CH_BASIS.chunk_id, quote=" ".join(AR_CLEAN.text.split()))
    review = all_yes().model_copy(update={"transfer_rules": LiaisonAnswer(
        answer="YES", reason="Arabic without translation.", quotes=[no_translation])})
    rules = by_key(send(channel(review)), "transfer_rules")
    assert not rules["quotes"][0]["verified"] and rules["answer"] == "UNCLEAR"
    garbled = LiaisonQuote(chunk_id=CH_BASIS.chunk_id, quote=" ".join(AR_GARBLED.text.split()),
                           translation="test translation")
    review = all_yes().model_copy(update={"transfer_rules": LiaisonAnswer(
        answer="YES", reason="Garbled.", quotes=[garbled])})
    assert by_key(send(channel(review)), "transfer_rules")["answer"] == "UNCLEAR"


def test_each_final_answer_and_the_status_say_who_decided():
    review = all_yes().model_copy(update={"legal_basis": LiaisonAnswer(
        answer="YES", reason="Invented.", quotes=[LiaisonQuote(
            chunk_id=CH_BASIS.chunk_id, quote="The authority must disclose all information to anyone.")])})
    decision = send(channel(review))
    assert by_key(decision, "legal_basis")["final_decided_by"].startswith("code:")
    assert by_key(decision, "counterpart")["final_decided_by"] == "AI liaison reviewer (fake-reviewer)"
    assert decision.review["status_decided_by"].startswith("code routing rule")
    floor = send(channel(LiaisonReview(legal_basis=LiaisonAnswer(answer="UNCLEAR", reason="r", quotes=[]),
                                       transfer_rules=yes(AE_TRANSFER), counterpart=yes(CH_COUNTERPART))),
                 {"patient_data_included": True})
    assert floor.review["status_decided_by"].startswith("code: patient-data rule")


def test_reviewer_is_told_what_the_transfer_question_means_for_this_letter():
    from engine.liaison import question_notes
    assert "no personal or patient data" in question_notes({"patient_data_included": False})["transfer_rules"]
    assert "carries patient" in question_notes({"patient_data_included": True})["transfer_rules"]
    assert "carries patient" in question_notes({})["transfer_rules"]  # not stated: treat as carrying data
