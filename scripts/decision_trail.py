"""Write a plain-language table of who made each decision in a drill run.

Three kinds of decision-maker appear in a run:
  - an institution's AI agent chooses the institution's action;
  - the AI liaison reviewer answers the three questions on every cross-border letter;
  - code rules check quotes, apply the patient-data rule and route or block the letter,
    and may replace an agent's explanation with fixed wording.

Usage: python scripts/decision_trail.py --run RUN_ID [--out report/decision-trail-RUN_ID.md]
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.liaison import SCRIPTED_REVIEWER, reviewer_label  # noqa: E402

WORDING = {
    "MODEL_EXPLANATION": "agent's own words",
    "RULE_CONSTRAINED_EXPLANATION": "explanation replaced by fixed wording (code rule)",
    "FALLBACK_REVIEW_REQUIRED": "explanation failed screening; code chose a review action",
}


def cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def final_by(check: dict, model: str) -> str:
    if "final_decided_by" in check:
        return check["final_decided_by"]
    if check.get("proposed_answer") is None:
        return "code: reviewer gave no usable answer"
    if check["answer"] != check["proposed_answer"]:
        return "code: answer changed by code check"
    return reviewer_label(model)


def trail(run_id: str) -> str:
    with open(ROOT / "runs" / run_id / "log.jsonl", encoding="utf-8") as source:
        entries = [json.loads(line) for line in source if line.strip()]
    lines = [
        f"# Decision trail: {run_id}",
        "",
        "Unreviewed synthetic drill output; nothing here is a legal conclusion. Every AI decision "
        "was made by a model that sees only what its institution can see, and it may have missed "
        "things a person would consider.",
        "",
        "## Institution decisions (each made by that institution's AI agent)",
        "",
        "| Step | Institution | Decided by | Action chosen | Explanation | Evidence status |",
        "|---|---|---|---|---|---|",
    ]
    letters = []
    for e in entries:
        model = e.get("model_name", "unknown model")
        lines.append(
            f"| {e['step']} | {cell(e.get('actor_name', e['actor_id']))} | AI agent ({cell(model)}) | "
            f"`{e['action_taken']}` | {WORDING.get(e.get('rationale_quality'), e.get('rationale_quality'))} | "
            f"{e.get('evidence_status', '')} |"
        )
        if e.get("liaison_checks"):
            letters.append(e)
    lines += ["", "## Cross-border letters", ""]
    if not letters:
        lines.append("No letter was sent in this run.")
    for e in letters:
        review = e.get("liaison_review", {})
        model = review.get("reviewer_model", "unknown model")
        payload = e.get("visible_payload", {})
        lines += [
            f"### Step {e['step']}: {cell(e.get('actor_name', e['actor_id']))} → {payload.get('target')} "
            f"({'carries patient data' if payload.get('patient_data_included') is not False else 'no patient data'})",
            "",
            ("- Sending the letter: directed by the scenario (the only action offered to the "
             f"{e['actor_id']} AI agent at this step)."
             if len(e.get("authorized_actions") or []) == 1
             else f"- Sending the letter: chosen by the {e['actor_id']} AI agent from "
                  f"{len(e.get('authorized_actions') or [])} offered actions."),
            f"- Result: **{e.get('liaison_status')}**, decided by "
            f"{review.get('status_decided_by', 'code routing rule')}.",
            f"- Quotes: {review.get('quotes_verified', 0)} of {review.get('quotes_checked', 0)} verified by code.",
            "",
            f"| Question | {'Scripted reviewer (not AI) proposed' if model == SCRIPTED_REVIEWER else 'AI liaison reviewer proposed'} "
            "| Final | Final answer decided by | Needs human check |",
            "|---|---|---|---|---|",
        ]
        for c in e["liaison_checks"]:
            final = c["answer"] + (f" ({c['gap_type']})" if c.get("gap_type") else "")
            lines.append(
                f"| {cell(c['question'])} | {c.get('proposed_answer')} | {final} | {cell(final_by(c, model))} | "
                f"{'yes' if c.get('human_review_required') else 'no'} |"
            )
        corrections = [q.get("correction") for c in e["liaison_checks"] for q in c["quotes"] if q.get("correction")]
        for note in corrections:
            lines.append(f"\n- Code correction: {cell(note)}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    out = Path(ROOT / (args.out or f"report/decision-trail-{args.run}.md"))
    out.write_text(trail(args.run), encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
