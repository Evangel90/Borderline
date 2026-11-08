#!/usr/bin/env python3
"""Liaison rehearsal: run only the AI liaison reviewer on chosen letters, several times each.

Usage:
  python scripts/liaison_rehearsal.py --repeat 3 \\
      expect=ROUTE:retinopathy-governed:2:ede  expect=BLOCK:retinopathy-ae-ch:14:dha ...

Each letter is the payload of that step's agent view, sent exactly as the drill would send it
(same reviewer, same evidence search, same code checks, same exhibits and recorded approvals).
Every attempt is reported; nothing is retried until it passes. A letter marked expect=BLOCK is a
control: if it is ever delivered, the checks are too loose and the rehearsal says so.
Not hash-chained and not a drill run; a diagnostic only.
"""

import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import yaml  # noqa: E402

from engine.actions import ActionExecutor  # noqa: E402
from engine.knowledge import KnowledgeIndex  # noqa: E402
from engine.liaison import LiaisonChannel, LiaisonReviewer  # noqa: E402
from engine.llm import create_chat_client  # noqa: E402
from engine.models import BridgeConfig, DrillIntent  # noqa: E402
from engine.orchestrator import DrillOrchestrator  # noqa: E402
from engine.replay import load_chunks  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("letters", nargs="+", help="expect=ROUTE|BLOCK:INTENT:STEP:SENDER")
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--out", default="report/liaison-rehearsal.json")
    args = parser.parse_args()

    with open("packs/bridge/ae-ch.yaml", encoding="utf-8") as source:
        bridge = BridgeConfig(**yaml.safe_load(source))
    institutions = {inst.id: inst for inst, _ in DrillOrchestrator._load_institutions()}
    library = load_chunks(ROOT)
    index = KnowledgeIndex(list(library.values()))
    reviewer = LiaisonReviewer(create_chat_client(), index)

    results, control_failures = [], 0
    for spec in args.letters:
        expect, intent_id, step_no, sender_id = spec.removeprefix("expect=").split(":")
        with open(f"intents/{intent_id}.yaml", encoding="utf-8") as source:
            intent = DrillIntent(**yaml.safe_load(source))
        step = next(s for s in intent.timeline if s.step == int(step_no))
        view = step.agent_views[sender_id]
        payload = view.payload
        action = view.allowed_actions[0] if view.allowed_actions else "request_regulatory_evidence"
        request_type = payload.get("request_type", ActionExecutor.LIAISON_REQUEST_TYPES[action])
        channel = LiaisonChannel(bridge, institutions, reviewer, library=library,
                                 exhibits=intent.exhibits, approvals=intent.standing_approvals)
        label = f"{intent_id} step {step_no} {sender_id} → {payload['target']}"
        print(f"\n{label}  (expected {expect})")
        for attempt in range(1, args.repeat + 1):
            started = time.time()
            decision = channel.check(institutions[sender_id], payload["target"], request_type, payload)
            row = {
                "letter": label, "expected": expect, "attempt": attempt, "status": decision.status,
                "decided_by": decision.review["status_decided_by"],
                "reviewer_status": decision.review["reviewer_status"],
                "quotes": f"{decision.review['quotes_verified']}/{decision.review['quotes_checked']}",
                "seconds": round(time.time() - started),
                "answers": [{"check": c["check"], "proposed": c["proposed_answer"], "final": c["answer"],
                             "gap_type": c["gap_type"], "adjustments": c["adjustments"],
                             "reason": c["reason"][:300],
                             "quotes": [{"chunk_id": q["chunk_id"], "verified": q["verified"], "quote": q["quote"],
                                         "failure": q.get("failure", "")} for q in c["quotes"]]}
                            for c in decision.checks],
            }
            results.append(row)
            short = ", ".join(f"{a['check']}={a['final']}" + ("" if a["proposed"] == a["final"]
                                                             else f" (reviewer {a['proposed']})")
                              for a in row["answers"])
            control = expect == "BLOCK" and decision.status == "ROUTE"
            control_failures += control
            print(f"  attempt {attempt}: {decision.status:<5} quotes {row['quotes']:<5} {short}"
                  f"{'   << CONTROL FAILED: delivered' if control else ''}")
            print(f"             decided by {row['decided_by']}")

    print("\nSummary")
    for spec in args.letters:
        rows = [r for r in results if r["letter"].startswith(spec.split(":")[1]) and
                f"step {spec.split(':')[2]} {spec.split(':')[3]}" in r["letter"]]
        routed = sum(r["status"] == "ROUTE" for r in rows)
        print(f"  {rows[0]['letter']}: delivered {routed} of {len(rows)} (expected {rows[0]['expected']})")
    if control_failures:
        print(f"  CONTROL FAILURES: {control_failures}. The checks let through a letter that must be blocked.")
    with open(args.out, "w", encoding="utf-8") as sink:
        json.dump({"repeat": args.repeat, "model": reviewer.model_name, "attempts": results}, sink,
                  indent=2, ensure_ascii=False)
    print(f"Wrote {args.out}")
    return 1 if control_failures else 0


if __name__ == "__main__":
    sys.exit(main())
