"""Agents and sources: who each AI agent plays and what it did, plus the registered law behind every quote."""

from __future__ import annotations

from collections import Counter

import streamlit as st

from common import FINAL_RUNS, chunks, institutions, label, load_run, passage, sidebar_note, sources

sidebar_note()
st.title("🏛️ Agents and sources")

tab_agents, tab_sources = st.tabs(["The AI agents", "The law they read"])

# ---------------- agents ----------------
with tab_agents:
    st.write(
        "Each institution is an AI agent running on the same small local model (`qwen3:8b`). What differs is its "
        "mandate, what it is shown, the law it can search and the actions it may take. Code enforces those limits: "
        "an agent sees only its own view of the event, searches only its own country's law plus global guidance, "
        "and can only pick an allowed action. It cannot send anything abroad itself."
    )
    profiles = institutions()
    decisions: dict[str, list[tuple[str, dict]]] = {}
    for run in FINAL_RUNS:
        for entry in load_run(run)["log"]:
            decisions.setdefault(entry.get("actor_id"), []).append((run, entry))
    side = {"AE": "🇦🇪 UAE", "CH": "🇨🇭 Switzerland", "GLOBAL": "Neutral"}
    st.dataframe(
        [{"Agent": p.get("name", pid), "Side": side.get(p.get("jurisdiction"), ""),
          "Plays": label(p.get("role")),
          "Decisions in the drills": len(decisions.get(pid, []))} for pid, p in profiles.items()]
        + [{"Agent": "AI liaison reviewer", "Side": "Neither",
            "Plays": "Checks every cross-border letter (3 questions, exact quotes)",
            "Decisions in the drills": sum(1 for r in FINAL_RUNS for e in load_run(r)["log"] if e.get("liaison_checks"))}],
        width="stretch", hide_index=True,
    )
    pick = st.selectbox("Look at one agent", list(profiles), format_func=lambda k: profiles[k].get("name", k))
    p = profiles[pick]
    left, right = st.columns(2)
    with left:
        st.markdown(f"**Mandate.** {' '.join(p.get('mandate', '').split())}")
        st.markdown("**Actions it may take**")
        for a in p.get("available_actions", []):
            st.markdown(f"- {a.get('description', a.get('name'))}")
    with right:
        taken = decisions.get(pick, [])
        st.markdown(f"**What it did in the drills ({len(taken)})**")
        if not taken:
            st.caption("Did not act in the four final drills.")
        for run, e in taken:
            with st.popover(f"Drill {FINAL_RUNS[run]['letter']} · step {e.get('step')} · `{e.get('action_taken')}`"):
                st.markdown(f"**Input:** {e.get('visible_event', '')}")
                st.markdown(f"**Output:** `{e.get('action_taken')}`: {e.get('justification', '')}")
                if e.get("cited_clauses"):
                    st.caption("Cited: " + ", ".join(e["cited_clauses"]))
    st.caption(f"Full profile: `{p['_file']}`")

# ---------------- sources ----------------
with tab_sources:
    rows = sources()
    per_doc = Counter(c["doc_id"] for c in chunks().values())
    st.write(
        f"{len(rows)} documents ({sum(r['jurisdiction'] == 'AE' for r in rows)} UAE, "
        f"{sum(r['jurisdiction'] == 'CH' for r in rows)} Swiss, {sum(r['jurisdiction'] == 'GLOBAL' for r in rows)} "
        f"global), split into {len(chunks()):,} passages. Each is registered with its official link and a SHA-256 "
        "hash of the file. Guidance and strategies can be cited but never count as a legal basis."
    )
    cid = st.text_input("Look up any passage ID you see on this site (for example in a quote)",
                        value="CH-HEALTH-TPA:p40:c1")
    if cid.strip():
        title, text = passage(cid.strip())
        st.markdown(f"**{title}**")
        if text:
            st.text(text)
        else:
            st.error("No passage with that ID.")
    st.dataframe(
        [{"Document": r["title"], "Country": r["jurisdiction"], "Status": r["binding"],
          "Passages": per_doc.get(r["doc_id"], 0), "Official source": r["source_url"], "ID": r["doc_id"],
          "SHA-256": r["sha256"]} for r in rows],
        width="stretch", hide_index=True,
        column_config={"Official source": st.column_config.LinkColumn(display_text="open")},
    )
