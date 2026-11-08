"""
engine/replay.py - Code replay of a saved drill run (`make replay`).

The replay never calls a model. It takes what each AI model said, as recorded in the log
(the liaison reviewer's proposed answers and quotes, each institution agent's chosen action),
and runs the code checks again:

- the action the agent chose was one its institution was offered;
- every quote is re-verified against today's checked-in chunk packs, using the passages
  the reviewer was shown (`evidence_shown`);
- each answer goes through `finalize_answer`, and each letter through `decide_liaison`,
  the same functions the drill used (so the patient-data rule and three-YES routing are
  re-applied, not re-implemented);
- the drill state is rebuilt step by step with the replayed letter outcomes, and each
  conditional step is checked: it should have run if and only if its condition held.

Any difference from the log is reported. A difference means the code, the chunk packs or
the log changed since the run. The replay shows that the outcomes follow from the logged
AI answers and the code rules; it does not show that a model would answer the same way again.
"""

from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass, field
from typing import Any

import yaml

from audit.hasher import HashChainedLogger
from engine.liaison import QUESTIONS, carries_patient_data, decide_liaison, evaluate_approval, exhibit_chunk
from engine.models import (
    Chunk, DrillIntent, LiaisonAnswer, LiaisonQuote, LiaisonReview, LiaisonRule, StandingApproval,
)

# Actions that send a cross-border letter (engine/actions.py LIAISON_REQUEST_TYPES).
LIAISON_ACTIONS = {"request_regulatory_evidence", "route_regulatory_notification", "share_patient_data_via_liaison"}

# Logged state keys for each liaison action, as written by engine/actions.py.
BLOCKED, DELIVERED = "blocked_by_liaison_check", "delivered"


@dataclass
class LetterReplay:
    entry_id: str
    step: int
    sender: str
    receiver: str
    patient_data: bool
    logged_status: str
    replayed_status: str
    decided_by: str
    answers: list[dict[str, Any]] = field(default_factory=list)
    differences: list[str] = field(default_factory=list)


@dataclass
class ReplayReport:
    run: str
    log_path: str
    hash_chain_ok: bool
    hash_chain_message: str
    entries: int = 0
    intent: str | None = None
    letters: list[LetterReplay] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    differences: list[str] = field(default_factory=list)

    @property
    def quotes_checked(self) -> int:
        return sum(len(a["quotes"]) for letter in self.letters for a in letter.answers)

    @property
    def all_differences(self) -> list[str]:
        return self.differences + [d for letter in self.letters for d in letter.differences]


def load_chunks(root: str = ".") -> dict[str, Chunk]:
    chunks: dict[str, Chunk] = {}
    for path in sorted(glob.glob(os.path.join(root, "packs", "*", "chunks.jsonl"))):
        with open(path, encoding="utf-8") as source:
            for line in source:
                if line.strip():
                    chunk = Chunk(**json.loads(line))
                    chunks[chunk.chunk_id] = chunk
    return chunks


def load_log(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def proposed_review(checks: list[dict[str, Any]], reviewer_ok: bool) -> LiaisonReview | None:
    """Rebuild the reviewer's proposed answers exactly as logged, before code checked them."""
    if not reviewer_ok:
        return None
    by_key = {check["check"]: check for check in checks}
    answers = {}
    for key in QUESTIONS:
        check = by_key[key]
        if check.get("proposed_answer") is None:
            return None
        answers[key] = LiaisonAnswer.model_construct(
            answer=check["proposed_answer"],
            reason=check.get("reason", ""),
            gap_type=check.get("proposed_gap_type"),
            quotes=[
                LiaisonQuote(
                    # The reviewer's own label: before any code correction of the chunk ID.
                    chunk_id=quote.get("chunk_id_corrected_from") or quote["chunk_id"],
                    quote=quote["quote"],
                    translation=quote.get("translation", ""),
                )
                for quote in check.get("quotes", [])
            ],
        )
    return LiaisonReview.model_construct(**answers)


def logged_reference(checks: list[dict[str, Any]]) -> dict[str, LiaisonRule]:
    return {
        check["check"]: LiaisonRule.model_construct(
            answer=check.get("reference_answer", "UNCLEAR"), reason=check.get("reference_reason", ""),
        )
        for check in checks
    }


def replay_letter(entry: dict[str, Any], chunks: dict[str, Chunk],
                  approvals: list[StandingApproval] | None = None) -> LetterReplay:
    review_log = entry.get("liaison_review") or {}
    checks = entry["liaison_checks"]
    shown_ids = review_log.get("evidence_shown", [])
    differences = [
        f"step {entry['step']} {entry['actor_id']}: passage {cid} the reviewer was shown is no longer "
        "in the chunk packs"
        for cid in shown_ids if cid not in chunks
    ]
    shown = {cid: chunks[cid] for cid in shown_ids if cid in chunks}
    review = proposed_review(checks, review_log.get("reviewer_status", "OK") == "OK")
    record = {"reviewer_model": review_log.get("reviewer_model", entry.get("model_name", ""))}
    payload = entry.get("visible_payload", {})
    approval = None
    if carries_patient_data(payload):
        request_type = payload.get("request_type") or entry.get("action_taken", "")
        approval = evaluate_approval(approvals or [], entry["actor_id"], payload.get("target", ""),
                                     request_type, payload, chunks)
    decision = decide_liaison(review, shown, payload, record, logged_reference(checks), approval)

    where = f"step {entry['step']} {entry['actor_id']}"
    if decision.status != entry.get("liaison_status"):
        differences.append(f"{where}: letter logged {entry.get('liaison_status')}, replayed {decision.status}")
    if decision.review["hard_floor_applied"] != review_log.get("hard_floor_applied"):
        differences.append(f"{where}: patient-data rule logged {review_log.get('hard_floor_applied')}, "
                           f"replayed {decision.review['hard_floor_applied']}")
    expected_state = DELIVERED if decision.status == "ROUTE" else BLOCKED
    for key, value in (entry.get("state_changes") or {}).items():
        if value in (BLOCKED, DELIVERED) and value != expected_state:
            differences.append(f"{where}: state {key} logged {value}, replayed {expected_state}")

    logged = {check["check"]: check for check in checks}
    answers = []
    for check in decision.checks:
        old = logged[check["check"]]
        for field_name in ("answer", "gap_type", "human_review_required", "final_decided_by"):
            if check.get(field_name) != old.get(field_name):
                differences.append(f"{where} {check['check']}: {field_name} logged {old.get(field_name)!r}, "
                                   f"replayed {check.get(field_name)!r}")
        for new_q, old_q in zip(check["quotes"], old.get("quotes", [])):
            if (new_q["verified"], new_q["chunk_id"]) != (old_q.get("verified"), old_q.get("chunk_id")):
                differences.append(
                    f"{where} {check['check']}: quote in {old_q.get('chunk_id')} logged "
                    f"verified={old_q.get('verified')}, replayed verified={new_q['verified']} in {new_q['chunk_id']}"
                )
        answers.append({
            "check": check["check"], "proposed": check["proposed_answer"], "answer": check["answer"],
            "gap_type": check["gap_type"], "final_decided_by": check["final_decided_by"],
            "quotes": [{"chunk_id": q["chunk_id"], "verified": q["verified"], "failure": q.get("failure", ""),
                        "corrected_from": q.get("chunk_id_corrected_from", "")} for q in check["quotes"]],
        })
    return LetterReplay(
        entry_id=entry["entry_id"], step=entry["step"], sender=entry["actor_id"],
        receiver=entry.get("visible_payload", {}).get("target", "?"),
        patient_data=decision.review["patient_data_carried"],
        logged_status=entry.get("liaison_status") or "", replayed_status=decision.status,
        decided_by=decision.review["status_decided_by"], answers=answers, differences=differences,
    )


def load_intent(path: str) -> DrillIntent:
    with open(path, encoding="utf-8") as source:
        return DrillIntent(**yaml.safe_load(source))


def infer_intent(entries: list[dict[str, Any]], intents_dir: str = "intents") -> str | None:
    """The intent whose steps and participants contain every logged (step, actor); None if not unique."""
    logged = {(e["step"], e["actor_id"]) for e in entries}
    matches = []
    for path in sorted(glob.glob(os.path.join(intents_dir, "*.yaml"))):
        intent = load_intent(path)
        offered = {(step.step, actor) for step in intent.timeline
                   for actor in list(step.participants) + list(step.agent_views)}
        if logged <= offered:
            matches.append(path)
    return matches[0] if len(matches) == 1 else None


def replay_steps(intent: DrillIntent, entries: list[dict[str, Any]],
                 letters: dict[str, LetterReplay]) -> tuple[list[dict[str, Any]], list[str]]:
    """Rebuild drill state with replayed letter outcomes; check each step ran iff it should have."""
    by_step: dict[int, list[dict[str, Any]]] = {}
    for entry in entries:
        by_step.setdefault(entry["step"], []).append(entry)
    state: dict[str, Any] = {}
    rows, differences = [], []
    for step in intent.timeline:
        ran = step.step in by_step
        enabled = all(state.get(k) == v for k, v in step.requires_state.items())
        if step.optional and not ran:
            expected = "optional, not included"
        else:
            expected = "run" if enabled else "skip"
        ok = expected.startswith("optional") or (expected == "run") == ran
        rows.append({"step": step.step, "phase": step.phase, "ran": ran, "replayed": expected,
                     "condition": dict(step.requires_state), "match": ok})
        if not ok:
            differences.append(f"step {step.step}: logged {'ran' if ran else 'skipped'}, "
                               f"replayed state says it should {expected}")
        for entry in by_step.get(step.step, []):
            changes = dict(entry.get("state_changes") or {})
            letter = letters.get(entry["entry_id"])
            if letter is not None:
                outcome = DELIVERED if letter.replayed_status == "ROUTE" else BLOCKED
                changes = {k: (outcome if v in (BLOCKED, DELIVERED) else v) for k, v in changes.items()}
            state.update(changes)
    return rows, differences


def replay_run(run: str, log_path: str | None = None, intent_path: str | None = None,
               root: str = ".") -> ReplayReport:
    log_path = log_path or os.path.join(root, "runs", run, "log.jsonl")
    ok, message, _ = HashChainedLogger.verify_log(log_path)
    entries = load_log(log_path)
    report = ReplayReport(run=run, log_path=log_path, hash_chain_ok=ok, hash_chain_message=message,
                          entries=len(entries))
    chunks = load_chunks(root)
    intent_path = intent_path or infer_intent(entries, os.path.join(root, "intents"))
    intent = load_intent(intent_path) if intent_path else None
    if intent:
        chunks.update({exhibit_chunk(e).chunk_id: exhibit_chunk(e) for e in intent.exhibits})
    approvals = intent.standing_approvals if intent else []

    for entry in entries:
        if (entry.get("action_taken") in LIAISON_ACTIONS and not entry.get("liaison_checks")
                and entry.get("liaison_status") != "BLOCK"):
            report.differences.append(
                f"step {entry['step']} {entry['actor_id']}: cross-border letter {entry['action_taken']} was "
                f"logged {entry.get('liaison_status') or entry.get('gate_status')} without the liaison check "
                "(it named no receiver); the current code blocks it"
            )
        offered = entry.get("authorized_actions") or []
        if offered and entry.get("action_taken") not in offered:
            report.differences.append(
                f"step {entry['step']} {entry['actor_id']}: action {entry.get('action_taken')} was not offered"
            )
    report.letters = [replay_letter(e, chunks, approvals) for e in entries if e.get("liaison_checks")]

    if intent:
        report.intent = os.path.basename(intent_path)
        report.steps, step_diffs = replay_steps(
            intent, entries, {letter.entry_id: letter for letter in report.letters},
        )
        report.differences.extend(step_diffs)
    return report
