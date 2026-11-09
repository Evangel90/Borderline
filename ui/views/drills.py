"""The drills: the cross-border letters first, the full step-by-step record one click deeper."""

from __future__ import annotations

import streamlit as st

from common import (CHECK_LABELS, FINAL_RUNS, REFERENCE_FILE, REPO_URL, STATUS_LABELS, TAG, expected_status, label,
                    cited_ids, load_run, name, passage, run_summary, sidebar_note, source_href, source_links)

sidebar_note()

runs = list(FINAL_RUNS)
requested = st.query_params.get("run", runs[0])
run = st.segmented_control(
    "Drill", runs, default=requested if requested in runs else runs[0],
    format_func=lambda r: f"Drill {FINAL_RUNS[r]['letter']} · {FINAL_RUNS[r]['name']}",
    label_visibility="collapsed",
) or runs[0]
st.query_params["run"] = run

info = FINAL_RUNS[run]
data = load_run(run)
log, replay, intent = data["log"], data["replay"], data["intent"]
s = run_summary(run)
timeline = {step["step"]: step for step in intent.get("timeline", [])}
replayed = {letter["entry_id"]: letter for letter in replay.get("letters", [])}

st.title(f"Drill {info['letter']}: {info['name']}")
st.markdown(f"**What it tests:** {info['pitch']}")
st.markdown(f"**What happened:** {info['outcome']}")
c = st.columns(4)
c[0].metric("Right call", f"{s['right_call']} of {s['letters']} letter{'s' if s['letters'] != 1 else ''}",
            help="Outcome matches what the project's reference answers say should happen.")
c[1].metric("Unsafe deliveries", s["unsafe"], help="Letters delivered that should have been stopped.")
c[2].metric("Quotes that matched the law", f"{s['verified']} of {s['quotes']}")
c[3].metric("Liaison answers by", "AI" if "AI" in info["reviewer"] else "Script")
st.caption(f"Right call: compared with the project's own reference answers in `{REFERENCE_FILE}` "
           "(delivered if all three are YES, otherwise blocked). They are the project's reading of the law, "
           "not a legal ruling.")


def answer_row(check: dict, result: dict) -> None:
    ans = check.get("answer")
    mark = {"YES": "🟢", "NO": "🔴"}.get(ans, "🟡")
    quotes = result.get("quotes", [])
    ok = sum(1 for q in quotes if q.get("verified"))
    notes = []
    if check.get("proposed_answer") and check["proposed_answer"] != ans:
        notes.append(f"AI said {check['proposed_answer']}, code changed it to {ans}")
    if quotes:
        notes.append(f"{ok} of {len(quotes)} quotes matched the law" if ok < len(quotes)
                     else f"quote{'s' if len(quotes) > 1 else ''} matched the law ✓")
    elif ans != "YES":
        notes.append("no quote")
    if check.get("gap_type"):
        notes.append(f"recorded as {label(check['gap_type']).lower()}")
    q, a, n = st.columns([4, 1, 4])
    q.markdown(CHECK_LABELS.get(check.get("check"), check.get("check")))
    a.markdown(f"{mark} **{ans}**")
    n.caption(" · ".join(notes))


def letter_card(entry: dict) -> None:
    review = entry.get("liaison_review") or {}
    result = replayed.get(entry.get("entry_id"), {})
    status = entry.get("liaison_status")
    receiver = (entry.get("visible_payload") or {}).get("target") or result.get("receiver")
    phase = timeline.get(entry.get("step"), {}).get("phase", "")
    with st.container(border=True):
        icon = "✅" if status == "ROUTE" else "⛔"
        st.markdown(f"#### {icon} {STATUS_LABELS.get(status, status)}: {name(entry.get('actor_id'))} → "
                    f"{name(receiver) if receiver else 'no receiver named'}")
        expected = expected_status(entry)
        if status == expected:
            verdict = "✓ right call"
        elif status == "BLOCK":
            verdict = "✗ too cautious: should have been delivered"
        else:
            verdict = "✗ unsafe: should have been blocked"
        st.markdown(f"Expected per reference answers: **{STATUS_LABELS[expected].lower()}** · {verdict}")
        st.caption(f"Step {entry.get('step')} · {phase} · "
                   + ("**carries patient data**" if review.get("patient_data_carried") else "no patient data"))
        checks = entry.get("liaison_checks", [])
        if not checks:
            st.markdown(f"**Why:** {review.get('status_decided_by') or entry.get('gate_reason') or 'blocked by code'}")
            return
        by_check = {a["check"]: a for a in result.get("answers", [])}
        for check in checks:
            answer_row(check, by_check.get(check.get("check"), {}))
        st.markdown(f"**Decided by:** {review.get('status_decided_by', '—')}")
        approval = review.get("human_approval")
        if approval:
            shown = approval.get("approval_id", approval) if isinstance(approval, dict) else approval
            st.caption(f"Recorded human approval: {shown}")
        with st.expander("Show the quotes and the law they were checked against"):
            for check in checks:
                st.markdown(f"**{CHECK_LABELS.get(check['check'], check['check'])}**: {check.get('answer')}")
                if check.get("reason"):
                    st.caption(f"Reviewer's reason: {check['reason']}")
                    st.caption(source_links([q["chunk_id"] for q in check.get("quotes", [])],
                                            "Where to check the reason") or "No passage cited for this reason.")
                rq = {q["chunk_id"]: q for q in by_check.get(check["check"], {}).get("quotes", [])}
                for q in check.get("quotes", []):
                    res = rq.get(q.get("chunk_id"), {})
                    verdict = ("✓ matches the passage" if res.get("verified")
                               else f"✗ rejected: {res.get('failure') or 'not found in the passage'}")
                    title, _ = passage(q["chunk_id"])
                    st.markdown(f"> {q.get('quote', '')}\n>\n> `{q['chunk_id']}` · {title} · **{verdict}** · "
                                f"[see it on the page ↗]({source_href(q['chunk_id'], q.get('quote'))})")


letters = [e for e in log if e.get("liaison_status") in ("ROUTE", "BLOCK")]
st.markdown("### Cross-border letters")
st.caption("Every letter one country's institution tried to send to the other, and what the check decided.")
if not letters:
    st.info("No cross-border letter in this drill.")
for entry in letters:
    letter_card(entry)

st.markdown("### Everything else")
with st.expander(f"Step-by-step record: every agent's input and decision ({len(timeline)} steps)"):
    st.caption("For each step: the staged event, then each agent's input (what it was shown) and output "
               "(the action it chose and why).")
    coverage = {x.get("step"): x for x in replay.get("steps", [])}
    for step in sorted(set(timeline) | {e.get("step") for e in log}):
        meta = timeline.get(step, {})
        entries = [e for e in log if e.get("step") == step]
        ran = coverage.get(step, {}).get("ran", bool(entries))
        st.markdown(f"**Step {step} · {meta.get('time_offset', '')} · {meta.get('phase', '')}**"
                    + ("" if ran else " · *did not run (depends on an earlier letter being delivered)*"))
        for e in entries:
            line = f"{name(e.get('actor_id'))} → `{e.get('action_taken')}`"
            if e.get("liaison_status") in ("ROUTE", "BLOCK"):
                line += f" · letter {STATUS_LABELS[e['liaison_status']].lower()}"
            with st.popover(line):
                st.markdown("**Input: what the agent was shown**")
                st.write(e.get("visible_event", ""))
                if e.get("visible_payload"):
                    st.json(e["visible_payload"], expanded=False)
                if e.get("authorized_actions"):
                    st.caption("Allowed actions: " + ", ".join(e["authorized_actions"]))
                if e.get("retrieved_chunk_ids"):
                    st.caption("Passages retrieved: " + ", ".join(e["retrieved_chunk_ids"]))
                st.markdown("**Output: what it decided**")
                st.markdown(f"`{e.get('action_taken')}`: {e.get('justification', '')}")
                st.markdown(source_links(cited_ids(e.get("cited_clauses", [])))
                            or "*No passage cited for this explanation.*")

if data["gaps"] or data["homework"]:
    with st.expander(f"Raised for human review: {len(data['gaps'])} gap record(s), "
                     f"{len(data['homework'])} homework item(s)"):
        for g in data["gaps"]:
            st.markdown(f"**Gap · {g.get('title', label(g.get('category')))}**: {g.get('friction_point', '')}")
        for h in data["homework"]:
            st.markdown(f"**Homework · step {h.get('step')}**, {name(h.get('sender'))} → {name(h.get('receiver'))}: "
                        f"{h.get('question', '')}")

st.caption(f"Full written trail of this drill: [{info['trail']}]({REPO_URL}/blob/{TAG}/{info['trail']})")
