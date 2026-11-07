"""Both drills load, every liaison letter is always sent, and every branch has a step."""

import glob
import os

import pytest
import yaml

from engine.models import DrillIntent, Institution

LETTER = "request_regulatory_evidence"
INTENTS = ["retinopathy-ae-ch", "retinopathy-ae-ch-cooperation"]


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


@pytest.mark.parametrize("intent_id", INTENTS)
def test_every_branch_key_comes_from_a_letter_that_is_always_sent(intent_id):
    intent, insts = load(intent_id), institutions()
    keys = {key for step in intent.timeline for key in step.requires_state}
    for key in keys:
        sender = key.split(".", 1)[1]
        letter_steps = [s for s in intent.timeline if sender in s.agent_views
                        and LETTER in (s.agent_views[sender].allowed_actions or []) and not s.requires_state]
        assert letter_steps, f"{intent_id}: no step sends the letter behind {key}"
        for step in letter_steps:
            view = step.agent_views[sender]
            # Directed: the letter is the only choice, so the run cannot stop before the branch.
            assert view.allowed_actions == [LETTER], (intent_id, step.step)
            assert view.payload["patient_data_included"] is False
            assert LETTER in {a.name for a in insts[sender].available_actions}


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


def test_together_the_drills_have_a_delivered_path_written_to_meet_the_swiss_conditions():
    companion = load("retinopathy-ae-ch-cooperation")
    letters = {s.agent_views[a].payload["target"]: s.agent_views[a].payload
               for s in companion.timeline for a in s.agent_views
               if LETTER in (s.agent_views[a].allowed_actions or [])}
    fdpic, swissmedic = letters["fodio"], letters["swissmedic"]
    assert fdpic["health_data_involved"] is False  # PDPL Art. 2(2)(e) exclusion not engaged
    for condition in ("reciprocity_assurance", "use_limited_to_data_protection_proceeding",
                      "professional_secrecy_undertaking"):  # FADP Art. 55(1)
        assert fdpic[condition]
    for condition in ("official_secrecy_assurance", "use_limited_to_therapeutic_product_enforcement"):
        assert swissmedic[condition]  # TPA Art. 64(1)(a)
    assert swissmedic["onward_disclosure"] == "none" and swissmedic["trade_secrets_requested"] is False


@pytest.mark.skipif(not os.path.isdir("runs"), reason="no runs")
def test_coverage_script_marks_unconditional_steps_that_did_not_run(tmp_path, monkeypatch):
    import scripts.step_coverage as cov
    run = tmp_path / "runs" / "r" / "log.jsonl"
    run.parent.mkdir(parents=True)
    run.write_text('{"step": 1}\n{"step": 2}\n', encoding="utf-8")
    monkeypatch.setattr(cov, "steps_run", lambda run_id: {1, 2})
    report = cov.coverage([("retinopathy-ae-ch-cooperation", "r")])
    statuses = {row["step"]: row["status"] for row in report["runs"][0]["steps"]}
    assert statuses[3] == statuses[4] == "SKIPPED_CONDITION_NOT_MET"
    assert "retinopathy-ae-ch-cooperation step 5" in report["unconditional_steps_missing"]
