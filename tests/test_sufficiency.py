import copy
import json

import pytest

from engine.models import Chunk
from engine.quotes import TRANSLATION_LABEL
from gaps.sufficiency import (
    OPEN, SUPPORTED, assess_candidate, assess_register, load_chunks, load_register,
)


def chunk(chunk_id, text, jurisdiction, language="en"):
    return Chunk(
        chunk_id=chunk_id, doc_id=chunk_id.split(":")[0], title=chunk_id, jurisdiction=jurisdiction,
        page=1, total_pages=1, chunk_index=0, text=text, source_file="synthetic",
        source_language=language,
    )


# Synthetic passages; test fixtures, not real legal text.
CHUNKS = {c.chunk_id: c for c in [
    chunk("AE-TEST:p1:c1", "Software upgrades must be certified by a recognised agency before use in clinics.", "AE"),
    chunk("CH-TEST:p1:c1", "Changes that could affect safety require prior approval by the notified body.", "CH"),
    chunk("GL-TEST:p1:c1", "Regulators should agree a protocol for planned model changes before deployment.", "GLOBAL"),
    chunk("AE-AR-TEST:p1:c1", "لا يجوز نقل البيانات الصحية خارج الدولة إلا بقرار من الجهة الصحية", "AE", "ar"),
]}


def q(chunk_id, role, words=None):
    text = " ".join(CHUNKS[chunk_id].text.split())
    return {"chunk_id": chunk_id, "role": role, "quote": text}


@pytest.fixture
def search_dir(tmp_path):
    record = {
        "search_id": "SEARCH-TEST-001",
        "found": {"software update": ["AE-TEST:p1:c1"], "change control plan": []},
        "not_found": ["change control plan"],
    }
    (tmp_path / "SEARCH-TEST-001.json").write_text(json.dumps(record), encoding="utf-8")
    return str(tmp_path)


MISSING = {
    "DOC-OBTAINABLE": {"id": "DOC-OBTAINABLE", "kind": "obtainable_not_fetched"},
    "DOC-UNOBTAINABLE": {"id": "DOC-UNOBTAINABLE", "kind": "unobtainable_after_documented_attempts",
                         "attempts": [{"date": "2026-11-07", "attempt": "portal", "outcome": "refused"}]},
    "DOC-NO-ATTEMPTS": {"id": "DOC-NO-ATTEMPTS", "kind": "unobtainable_after_documented_attempts"},
}

GOOD = {
    "id": "CAND-T",
    "title": "Synthetic candidate",
    "quotes": [q("AE-TEST:p1:c1", "host"), q("CH-TEST:p1:c1", "partner"), q("GL-TEST:p1:c1", "global_comparator")],
    "searches": [{"search_id": "SEARCH-TEST-001", "absent_terms": ["change control plan"]}],
    "could_be_refuted_by": [],
}


def assess(candidate, search_dir, missing=None):
    return assess_candidate(candidate, MISSING if missing is None else missing, CHUNKS, search_dir)


def with_(**changes):
    candidate = copy.deepcopy(GOOD)
    candidate.update(changes)
    return candidate


def conditions(result):
    return {u["condition"] for u in result.unmet}


def test_supported_only_when_all_four_conditions_hold(search_dir):
    result = assess(GOOD, search_dir)
    assert result.status == SUPPORTED
    assert result.unmet == []
    assert result.to_dict()["is_legal_conclusion"] is False
    assert result.to_dict()["reviewed_by_legal_professional"] is False


# 1. Every quote verifies.

def test_fabricated_quote_keeps_candidate_open(search_dir):
    quotes = GOOD["quotes"] + [{"chunk_id": "AE-TEST:p1:c1", "role": "host",
                                "quote": "Upgrades never need any certification at all in the UAE."}]
    result = assess(with_(quotes=quotes), search_dir)
    assert result.status == OPEN
    assert conditions(result) == {"quotes_verify"}


def test_unknown_chunk_and_unknown_role_fail(search_dir):
    quotes = GOOD["quotes"] + [
        {"chunk_id": "NOT-IN-KB:p1:c1", "role": "host", "quote": "anything at all said here verbatim"},
        {**q("CH-TEST:p1:c1", "partner"), "role": "finding"},
    ]
    result = assess(with_(quotes=quotes), search_dir)
    assert result.status == OPEN
    assert sum(not item["verified"] for item in result.quotes) == 2


def test_arabic_quote_in_candidate_needs_labelled_translation(search_dir):
    arabic = q("AE-AR-TEST:p1:c1", "host")
    without = assess(with_(quotes=GOOD["quotes"] + [arabic]), search_dir)
    assert without.status == OPEN
    translated = {**arabic, "translation": "Health data may not be transferred outside the State except by decision"}
    result = assess(with_(quotes=GOOD["quotes"] + [translated]), search_dir)
    assert result.status == SUPPORTED
    assert result.quotes[-1]["translation_label"] == TRANSLATION_LABEL


# 2. A search record exists and confirms the absences.

def test_missing_search_record_keeps_candidate_open(search_dir):
    result = assess(with_(searches=[{"search_id": "SEARCH-NOPE", "absent_terms": []}]), search_dir)
    assert result.status == OPEN and conditions(result) == {"search_record"}
    assert assess(with_(searches=[]), search_dir).status == OPEN


def test_absent_term_that_was_found_or_never_searched_fails(search_dir):
    found = assess(with_(searches=[{"search_id": "SEARCH-TEST-001", "absent_terms": ["software update"]}]), search_dir)
    assert found.status == OPEN and "was found" in found.unmet[0]["detail"]
    unsearched = assess(with_(searches=[{"search_id": "SEARCH-TEST-001", "absent_terms": ["reciproc"]}]), search_dir)
    assert unsearched.status == OPEN and "not part of this search" in unsearched.unmet[0]["detail"]


# 3. A verified global comparator.

def test_comparator_must_be_verified_and_global(search_dir):
    no_comparator = assess(with_(quotes=GOOD["quotes"][:2]), search_dir)
    assert conditions(no_comparator) == {"global_comparator"}
    national = assess(with_(quotes=GOOD["quotes"][:2] + [q("CH-TEST:p1:c1", "global_comparator")]), search_dir)
    assert conditions(national) == {"global_comparator"}
    bad = {"chunk_id": "GL-TEST:p1:c1", "role": "global_comparator", "quote": "Regulators must ban all model changes forever."}
    assert "global_comparator" in conditions(assess(with_(quotes=GOOD["quotes"][:2] + [bad]), search_dir))


# 4. Known-missing documents.

ANSWERED_DOC = {"id": "DOC-ANSWERED", "kind": "question_answered_by_registered_source",
                "answered_by": [{"chunk_id": "GL-TEST:p1:c1",
                                 "quote": "Regulators should agree a protocol for planned model changes"}],
                "limits": "Answers the status question only."}


def test_question_answered_by_verified_quotes_does_not_block(search_dir):
    result = assess(with_(could_be_refuted_by=["DOC-ANSWERED"]), search_dir, {"DOC-ANSWERED": ANSWERED_DOC})
    assert result.status == SUPPORTED
    assert result.answered_documents == ["DOC-ANSWERED"]
    assert any("Limits: Answers the status question only." in n for n in result.notes)


@pytest.mark.parametrize("answered_by", [
    [],
    [{"chunk_id": "GL-TEST:p1:c1", "quote": "Regulators must always approve every model change in advance."}],
    [{"chunk_id": "NOT-IN-KB:p1:c1", "quote": "Regulators should agree a protocol for planned model changes"}],
])
def test_answered_without_verified_quotes_counts_as_obtainable(search_dir, answered_by):
    document = {**ANSWERED_DOC, "answered_by": answered_by}
    result = assess(with_(could_be_refuted_by=["DOC-ANSWERED"]), search_dir, {"DOC-ANSWERED": document})
    assert result.status == OPEN
    assert result.blocking_documents == ["DOC-ANSWERED"]
    assert any("treated as obtainable" in n for n in result.notes)

def test_obtainable_missing_document_blocks(search_dir):
    result = assess(with_(could_be_refuted_by=["DOC-OBTAINABLE"]), search_dir)
    assert result.status == OPEN
    assert result.blocking_documents == ["DOC-OBTAINABLE"]


def test_unobtainable_after_documented_attempts_does_not_block(search_dir):
    result = assess(with_(could_be_refuted_by=["DOC-UNOBTAINABLE"]), search_dir)
    assert result.status == SUPPORTED
    assert result.unobtainable_documents == ["DOC-UNOBTAINABLE"]
    assert any("not publicly accessible to the project after documented attempts" in n for n in result.notes)


def test_unobtainable_without_attempts_is_treated_as_obtainable(search_dir):
    result = assess(with_(could_be_refuted_by=["DOC-NO-ATTEMPTS"]), search_dir)
    assert result.status == OPEN
    assert result.blocking_documents == ["DOC-NO-ATTEMPTS"]


def test_unlisted_refuter_blocks(search_dir):
    assert assess(with_(could_be_refuted_by=["DOC-UNKNOWN"]), search_dir).status == OPEN


def test_hypothetical_refuting_evidence_does_not_block(search_dir):
    result = assess(with_(refuting_evidence_to_look_for=["A memorandum not known to exist."]), search_dir)
    assert result.status == SUPPORTED
    assert any("Not known to exist" in n for n in result.notes)


def test_unobtainable_document_needs_an_accessibility_candidate(search_dir):
    register = {"missing_documents": [MISSING["DOC-UNOBTAINABLE"]], "candidates": [GOOD]}
    problems = assess_register(register, CHUNKS, search_dir)["register_problems"]
    assert problems == ["DOC-UNOBTAINABLE is unobtainable but has no accessibility candidate."]
    register["candidates"] = [GOOD, with_(id="CAND-ACC", accessibility_of="DOC-UNOBTAINABLE")]
    assert assess_register(register, CHUNKS, search_dir)["register_problems"] == []


@pytest.mark.parametrize("reason, problems", [
    ("Public and readable by people; only the text layer is defective.", 0),
    ("   ", 1),
])
def test_accessibility_candidate_exemption_needs_a_written_reason(search_dir, reason, problems):
    document = {**MISSING["DOC-UNOBTAINABLE"], "accessibility_candidate_exempt_reason": reason}
    register = {"missing_documents": [document], "candidates": [GOOD]}
    assert len(assess_register(register, CHUNKS, search_dir)["register_problems"]) == problems


def test_unobtainable_document_can_carry_its_own_status_wording(search_dir):
    document = {**MISSING["DOC-UNOBTAINABLE"], "status_note": "could not be obtained as clean text"}
    result = assess(with_(could_be_refuted_by=["DOC-UNOBTAINABLE"]), search_dir, {"DOC-UNOBTAINABLE": document})
    assert result.status == SUPPORTED
    assert any(n.startswith("DOC-UNOBTAINABLE could not be obtained as clean text") for n in result.notes)


# The checked-in register.

@pytest.fixture(scope="module")
def checked_in():
    return {c["candidate_id"]: c for c in assess_register(load_register(), load_chunks())["candidates"]}


def test_checked_in_quotes_all_verify(checked_in):
    for candidate in checked_in.values():
        failed = [q["chunk_id"] for q in candidate["quotes"] if not q["verified"]]
        assert failed == [], candidate["candidate_id"]
        assert not any(u["condition"] == "search_record" for u in candidate["unmet_conditions"])


def test_checked_in_statuses(checked_in):
    assert {cid: c["status"] for cid, c in checked_in.items()} == {
        "CAND-001": SUPPORTED, "CAND-002": SUPPORTED, "CAND-003": SUPPORTED, "CAND-004": SUPPORTED,
    }
    # The controlling Arabic text of Law 38/2024 was not searched; that limit stays visible.
    assert checked_in["CAND-002"]["unobtainable_documents"] == ["AE-FEDERAL-DECREE-LAW-38-2024-AR-CLEAN"]
    assert any("the controlling Arabic text was not searched" in n for n in checked_in["CAND-002"]["notes"])
    assert checked_in["CAND-003"]["answered_documents"] == ["CH-EU-MRA-1999"]
    assert checked_in["CAND-001"]["answered_documents"] == ["OECD-LEGAL-0352-ADHERENTS"]
    assert any("does not prove the" in n for n in checked_in["CAND-003"]["notes"])


def test_resolution_51_stays_missing_and_is_worded_as_inaccessible(checked_in):
    register = load_register()
    mr51 = next(d for d in register["missing_documents"] if d["id"] == "AE-HEALTH-DATA-EXEMPTIONS-MR51-2021")
    assert mr51["kind"] == "unobtainable_after_documented_attempts" and mr51["attempts"]
    assert "AE-HEALTH-DATA-EXEMPTIONS-MR51-2021" in checked_in["CAND-001"]["unobtainable_documents"]
    title = checked_in["CAND-004"]["title"]
    assert "not publicly accessible to the project after documented attempts" in title
    assert "does not exist" not in json.dumps(register)
    assert assess_register(register, load_chunks())["register_problems"] == []


def test_register_never_calls_a_candidate_a_finding_or_violation():
    text = open("gaps/candidate_register.yaml", encoding="utf-8").read().lower()
    assert "violation" not in text
    statuses = {c["status"] for c in assess_register(load_register(), load_chunks())["candidates"]}
    assert statuses <= {SUPPORTED, OPEN}


def test_absence_search_can_be_limited_to_named_documents():
    from scripts.search_absence import search
    result = search(["global"], ["Switzerland"], ["IMDRF-NCAR-N14-2025"])
    assert set(result["documents"]) == {"IMDRF-NCAR-N14-2025"}
    assert result["hits"]["Switzerland"] == []
