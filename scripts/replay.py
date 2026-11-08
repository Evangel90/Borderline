#!/usr/bin/env python3
"""Code replay of a saved drill run: re-run every code decision over the logged AI answers.

Usage:
  python scripts/replay.py --run RUN_ID [--intent intents/X.yaml] [--log path/to/log.jsonl]

No model is called. Use --log to replay an edited copy of a log (for example, to see what code
does with a changed or invented reviewer answer); the hash-chain check will report the edit.
Exit code 0 when the replay matches the log, 1 when it does not.
"""

import argparse
import json
import os
import sys
from dataclasses import asdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine.replay import replay_run  # noqa: E402

NAMES = {
    "legal_basis": "legal basis   ",
    "transfer_rules": "transfer rules",
    "counterpart": "counterpart   ",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", required=True)
    parser.add_argument("--intent", help="intent YAML; inferred from the log if omitted")
    parser.add_argument("--log", help="replay this log file instead of runs/<run>/log.jsonl")
    parser.add_argument("--out", help="write the JSON report here (default runs/<run>/replay.json)")
    args = parser.parse_args()

    report = replay_run(args.run, log_path=args.log, intent_path=args.intent, root=ROOT)

    print(f"Code replay of {args.run} (no model is called)")
    print(f"Log: {report.log_path} ({report.entries} entries)")
    print(f"Hash chain: {'verified' if report.hash_chain_ok else 'BROKEN: ' + report.hash_chain_message}")
    print(f"Intent for step check: {report.intent or 'not found (step check skipped; pass --intent)'}\n")

    for letter in report.letters:
        mark = "✓" if not letter.differences else "✗ DIFFERENT"
        data = " (patient data)" if letter.patient_data else ""
        print(f"Step {letter.step:<3} {letter.sender} → {letter.receiver}{data}")
        print(f"         logged: {letter.logged_status:<6} replayed: {letter.replayed_status:<6} {mark}")
        print(f"         decided by {letter.decided_by}")
        for answer in letter.answers:
            verified = sum(q["verified"] for q in answer["quotes"])
            change = (f"reviewer said {answer['proposed']} → code: {answer['answer']}"
                      if answer["proposed"] != answer["answer"] else answer["answer"])
            gap = f" ({answer['gap_type']})" if answer["gap_type"] else ""
            print(f"         {NAMES[answer['check']]}  {change}{gap}   "
                  f"{verified}/{len(answer['quotes'])} quotes re-verified")
            for q in answer["quotes"]:
                if not q["verified"]:
                    print(f"             quote rejected in {q['chunk_id']}: {q['failure']}")
                elif q["corrected_from"]:
                    print(f"             chunk ID corrected {q['corrected_from']} → {q['chunk_id']} (text unchanged)")
        for diff in letter.differences:
            print(f"         DIFFERENCE: {diff}")
        print()

    if report.steps:
        skipped = [row for row in report.steps if not row["ran"] and row["replayed"] == "skip"]
        print(f"Steps: {sum(row['ran'] for row in report.steps)} ran, {len(skipped)} skipped by condition; "
              f"{sum(not row['match'] for row in report.steps)} disagree with the replayed state.")
    for diff in report.differences:
        print(f"DIFFERENCE: {diff}")

    total = report.all_differences
    print(f"\n{len(report.letters)} letters, {sum(len(l.answers) for l in report.letters)} answers, "
          f"{report.quotes_checked} quotes re-checked. {len(total)} differences.")
    if not total and report.hash_chain_ok:
        scripted = any(l.decided_by and any(a["final_decided_by"].startswith("scripted reviewer")
                                            for a in l.answers) for l in report.letters)
        source = "logged scripted reference answers (not AI decisions)" if scripted else "logged AI answers"
        print(f"Every letter outcome in this run follows from the {source} and the code rules.")
    elif not total:
        print("The code reproduces this log, but the log's hash chain is broken: it was edited after the run.")

    out = args.out or os.path.join(ROOT, "runs", args.run, "replay.json")
    if os.path.isdir(os.path.dirname(out)):
        payload = {"run": report.run, "log": report.log_path, "hash_chain_ok": report.hash_chain_ok,
                   "intent": report.intent, "differences": total,
                   "letters": [asdict(letter) for letter in report.letters], "steps": report.steps}
        with open(out, "w", encoding="utf-8") as sink:
            json.dump(payload, sink, indent=2, ensure_ascii=False)
        print(f"Wrote {os.path.relpath(out, ROOT)}")
    return 0 if not total and report.hash_chain_ok else 1


if __name__ == "__main__":
    sys.exit(main())
