"""Show which drill steps each run reached, and which liaison branches have been exercised.

Usage:
  python scripts/step_coverage.py retinopathy-ae-ch=RUN_A retinopathy-ae-ch-cooperation=RUN_B

A conditional step runs only when an earlier letter was delivered (or blocked), so one run can
never reach both branches of the same letter. This report shows, across all the runs given,
which branches have run at least once and which have not.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from engine.models import DrillIntent  # noqa: E402


def load_intent(intent_id: str) -> DrillIntent:
    with open(ROOT / "intents" / f"{intent_id}.yaml", encoding="utf-8") as source:
        return DrillIntent(**yaml.safe_load(source))


def steps_run(run_id: str) -> set[int]:
    path = ROOT / "runs" / run_id / "log.jsonl"
    with open(path, encoding="utf-8") as source:
        return {json.loads(line)["step"] for line in source if line.strip()}


def coverage(pairs: list[tuple[str, str]]) -> dict:
    report = {"runs": [], "branches": {}}
    branches: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for intent_id, run_id in pairs:
        intent, ran = load_intent(intent_id), steps_run(run_id)
        rows = []
        for step in intent.timeline:
            if step.step in ran:
                status = "RAN"
            elif step.optional:
                status = "OPTIONAL_NOT_RUN"
            elif step.requires_state:
                status = "SKIPPED_CONDITION_NOT_MET"
            else:
                status = "MISSING"  # an unconditional step that did not run: the run stopped early
            for key, value in step.requires_state.items():
                branches[key][value].append(f"{intent_id} step {step.step}: {status}")
            rows.append({"step": step.step, "phase": step.phase, "status": status,
                         "requires_state": step.requires_state})
        report["runs"].append({"intent": intent_id, "run_id": run_id, "steps": rows})
    for key, outcomes in branches.items():
        report["branches"][key] = {
            value: {"covered": any(item.endswith(": RAN") for item in items), "where": items}
            for value, items in outcomes.items()
        }
    report["unconditional_steps_missing"] = [
        f"{run['intent']} step {row['step']}" for run in report["runs"]
        for row in run["steps"] if row["status"] == "MISSING"
    ]
    report["branches_not_covered"] = [
        f"{key} = {value}" for key, outcomes in report["branches"].items()
        for value, info in outcomes.items() if not info["covered"]
    ]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pairs", nargs="+", help="INTENT=RUN_ID")
    parser.add_argument("--out", default="report/step-coverage.json")
    args = parser.parse_args()
    pairs = [tuple(pair.split("=", 1)) for pair in args.pairs]
    report = coverage(pairs)
    for run in report["runs"]:
        print(f"\n{run['intent']} ({run['run_id']})")
        for row in run["steps"]:
            condition = ", ".join(f"{k}={v}" for k, v in row["requires_state"].items())
            print(f"  step {row['step']:>2}  {row['status']:<26} {row['phase']}"
                  + (f"  [if {condition}]" if condition else ""))
    print("\nLiaison branches across these runs:")
    for key, outcomes in report["branches"].items():
        for value, info in outcomes.items():
            print(f"  {key} = {value}: {'covered' if info['covered'] else 'NOT covered'}")
    Path(ROOT / args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {args.out}")
    return 1 if report["unconditional_steps_missing"] else 0


if __name__ == "__main__":
    sys.exit(main())
