"""Both drills load, every liaison letter is always sent, and every branch has a step."""

import glob
import os

import pytest
import yaml

from engine.models import DrillIntent, Institution

LETTER = "request_regulatory_evidence"
PATIENT_LETTER = "share_patient_data_via_liaison"
ACTION_FOR_KEY = {"regulatory_evidence_request": LETTER, "patient_data_disclosure": PATIENT_LETTER}
INTENTS = ["retinopathy-governed", "retinopathy-ae-ch", "retinopathy-insufficient-evidence"]


def load(intent_id):
    with open(f"intents/{intent_id}.yaml", encoding="utf-8") as source:
        return DrillIntent(**yaml.safe_load(source))


def institutions():
    found = {}
    for path in glob.glob("packs/*/institutions/*.yaml"):
        with open(path, encoding="utf-8") as source:
            inst = Institution(**yaml.safe_load(source))
        found[inst.id] = inst
    return found


def letters(intent, action):
    return {(s.step, a): s.agent_views[a].payload for s in intent.timeline for a in s.agent_views
            if action in (s.agent_views[a].allowed_actions or []) and not s.requires_state}


@pytest.mark.parametrize("intent_id", INTENTS)
def test_every_branch_key_comes_from_a_letter_that_is_always_sent(intent_id):
    intent, insts = load(intent_id), institutions()
    keys = {key for step in intent.timeline for key in step.requires_state}
    for key in keys:
        kind, sender = key.split(".", 1)
        action = ACTION_FOR_KEY[kind]
        letter_steps = [s for s in intent.timeline if sender in s.agent_views
                        and action in (s.agent_views[sender].allowed_actions or []) and not s.requires_state]
        assert letter_steps, f"{intent_id}: no step sends the letter behind {key}"
        for step in letter_steps:
            view = step.agent_views[sender]
            # Directed: the letter is the only choice, so the run cannot stop before the branch.
            assert view.allowed_actions == [action], (intent_id, step.step)
            assert view.payload["patient_data_included"] is (action == PATIENT_LETTER)
            assert action in {a.name for a in insts[sender].available_actions}


@pytest.mark.parametrize("intent_id", INTENTS)
def test_each_letter_has_both_a_delivered_and_a_blocked_follow_up(intent_id):
    intent = load(intent_id)
    outcomes = {}
    for step in intent.timeline:
        for key, value in step.requires_state.items():
            outcomes.setdefault(key, set()).add(value)
    assert outcomes
    for key, values in outcomes.items():
        assert values == {"delivered", "blocked_by_liaison_check"}, (intent_id, key)


def test_governed_letters_are_written_to_the_conditions_of_registered_provisions():
    governed = load("retinopathy-governed")
    by_target = {p["target"]: p for p in letters(governed, LETTER).values()}
    fdpic, swissmedic = by_target["fodio"], by_target["swissmedic"]
    assert fdpic["health_data_involved"] is False  # PDPL Art. 2(2)(e) exclusion not engaged
    for condition in ("reciprocity_assurance", "use_limited_to_data_protection_proceeding",
                      "professional_secrecy_undertaking"):  # FADP Art. 55(1)
        assert fdpic[condition]
    for condition in ("official_secrecy_assurance", "use_limited_to_therapeutic_product_enforcement"):
        assert swissmedic[condition]  # TPA Art. 64(1)(a)
    assert swissmedic["onward_disclosure"] == "none" and swissmedic["trade_secrets_requested"] is False


def test_one_patient_data_letter_is_built_to_pass_and_one_to_fail():
    (recall,) = letters(load("retinopathy-governed"), PATIENT_LETTER).values()
    assert recall["direction"] == "CH_to_AE" and recall["target"] == "ede"
    assert recall["purpose"] == "patient_recall_to_avert_serious_health_risk"  # TPA Art. 64(2)(c)
    assert recall["images_included"] is False  # only what a recall needs
    (images,) = letters(load("retinopathy-ae-ch"), PATIENT_LETTER).values()
    assert images["direction"] == "AE_to_CH" and images["outside_state_approval"] == "not_located"  # Art. 13


def test_insufficient_evidence_drill_names_what_is_missing_rather_than_asserting_absence():
    intent = load("retinopathy-insufficient-evidence")
    (request,) = letters(intent, LETTER).values()
    assert request["reciprocity_assurance"] == "not_given"
    homework = next(s for s in intent.timeline if s.step == 8).agent_views["policy_adviser"]
    assert "not treat a missing document as proof" in homework.event


@pytest.mark.skipif(not os.path.isdir("runs"), reason="no runs")
def test_coverage_script_marks_unconditional_steps_that_did_not_run(tmp_path, monkeypatch):
    import scripts.step_coverage as cov
    run = tmp_path / "runs" / "r" / "log.jsonl"
    run.parent.mkdir(parents=True)
    run.write_text('{"step": 1}\n{"step": 2}\n', encoding="utf-8")
    monkeypatch.setattr(cov, "steps_run", lambda run_id: {1, 2})
    report = cov.coverage([("retinopathy-governed", "r")])
    statuses = {row["step"]: row["status"] for row in report["runs"][0]["steps"]}
    assert statuses[3] == statuses[4] == "SKIPPED_CONDITION_NOT_MET"
    assert "retinopathy-governed step 5" in report["unconditional_steps_missing"]


# --- The liaison reviewer must see the rules on both sides of each letter (checked 2026-11-07:
# a pooled search let Swiss passages crowd out UAE Health Data Law Art. 13). ---

KEY_PROVISIONS = {
    "TPA Art. 64": "CH-HEALTH-TPA:p40:c1",
    "FADP Art. 55": "CH-DATA-FADP:p24:c1",
    "FADP Art. 16": "CH-DATA-FADP:p7:c1",
    "PDPL Art. 2": "AE-DATA-PDPL-2021-EN:p6:c2",
    "UAE Health Data Law Art. 13": "AE-HEALTH-ICT-LAW-2019:p8:c1",
}


@pytest.mark.skipif(not os.path.isdir("index/chroma"), reason="local vector index not built")
def test_reviewer_is_shown_both_sides_key_provisions_for_every_letter():
    import json

    from engine.knowledge import KnowledgeIndex
    from engine.liaison import LiaisonReviewer
    from engine.models import Chunk
    chunks = []
    for pack in ("ae", "ch", "global"):
        with open(f"packs/{pack}/chunks.jsonl", encoding="utf-8") as source:
            chunks += [Chunk(**json.loads(line)) for line in source if line.strip()]
    reviewer, insts = LiaisonReviewer(llm=None, index=KnowledgeIndex(chunks)), institutions()
    for intent_id in INTENTS:
        for action in (LETTER, PATIENT_LETTER):
            for (step, sender), payload in letters(load(intent_id), action).items():
                shown = {c.chunk_id for c in reviewer.gather_evidence(
                    insts[sender], insts[payload["target"]], payload["request_type"], payload)}
                missing = [name for name, cid in KEY_PROVISIONS.items() if cid not in shown]
                assert not missing, (intent_id, step, sender, missing)
