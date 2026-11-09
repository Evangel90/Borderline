"""Policy gaps found: the four gaps, each with local evidence and a global comparison."""

from __future__ import annotations

import json

import streamlit as st
import yaml

from common import FINAL_RUNS, ROOT, passage, sidebar_note, source_href

sidebar_note()
st.title("🧩 Policy gaps found")
st.write(
    "Running the drills against both countries' law surfaced four places where the rules are missing, unclear or "
    "out of reach. Each is paired with how other systems handle the same question. They are findings subject to "
    "expert legal review; \"missing\" means missing from this knowledge base."
)

status = json.loads((ROOT / "report" / "candidate-status.json").read_text(encoding="utf-8"))
register = yaml.safe_load((ROOT / "gaps" / "candidate_register.yaml").read_text(encoding="utf-8"))
reg_by_id = {c["id"]: c for c in register.get("candidates", [])}
ROLE = {"host": "UAE", "partner": "Switzerland", "global_comparator": "Global comparison", "context": "Context"}


def quote_block(q: dict) -> None:
    title, _ = passage(q["chunk_id"])
    st.markdown(f"> {q['quote']}\n>\n> {'✓' if q.get('verified') else '✗'} `{q['chunk_id']}` · {title} · "
                f"[see it on the page ↗]({source_href(q['chunk_id'], q['quote'])})")


def linked(text: str, links: list[dict], quotes: list[dict], seen: set[str]) -> str:
    """Link each listed phrase to its source passage, once per passage per card.

    Passages in `seen` (already linked, or quoted in the card's evidence boxes) are not linked again.
    """
    text = " ".join(text.split())
    quote_for = {q["chunk_id"]: q["quote"] for q in quotes}
    for item in links:
        phrase = item["text"]
        if phrase in text and item["chunk_id"] not in seen:
            seen.add(item["chunk_id"])
            href = source_href(item["chunk_id"], quote_for.get(item["chunk_id"]))
            text = text.replace(phrase, f"[{phrase} ↗]({href})", 1)
    return text


for cand in sorted(status.get("candidates", []), key=lambda c: c["candidate_id"]):
    reg = reg_by_id.get(cand["candidate_id"], {})
    quotes = cand.get("quotes", [])
    local = [q for q in quotes if q.get("role") in ("host", "partner")]
    global_q = [q for q in quotes if q.get("role") == "global_comparator"]
    with st.container(border=True):
        st.markdown(f"#### {cand['title']}")
        st.caption(f"{cand['candidate_id']} · Gap type: {cand.get('gap_type') or reg.get('gap_type', '')} · "
                   + ("✅ passes all four evidence checks" if cand["status"] == "SUPPORTED_CANDIDATE"
                      else "🟡 open: " + "; ".join(cand.get("unmet_conditions", []))))
        links = reg.get("links", [])
        seen = {q["chunk_id"] for q in local[:1] + global_q[:1]}  # these are quoted with a link below
        reason = reg.get("reason_from_drill") or cand.get("reason_from_drill", "")
        if reason:
            st.markdown(f"**Reason from drill:** {linked(reason, links, quotes, seen)}")
        for ref in reg.get("drill_steps", []):
            info = FINAL_RUNS.get(ref["run"], {})
            step_word = "step" if "–" not in str(ref["steps"]) else "steps"
            st.page_link("views/drills.py", icon="🎬", query_params={"run": ref["run"]},
                         label=f"See Drill {info.get('letter', '?')} · {info.get('name', ref['run'])}, {step_word} {ref['steps']}")
        recommendation = reg.get("recommendation") or cand.get("recommendation", "")
        if recommendation:
            st.markdown(f"**Recommendation from global practice:** {linked(recommendation, links, quotes, seen)}")
        left, right = st.columns(2)
        with left:
            st.markdown("**What the local law says (or does not)**")
            for q in local[:1]:
                st.caption(ROLE.get(q.get("role"), ""))
                quote_block(q)
        with right:
            st.markdown("**How it is handled elsewhere**")
            for q in global_q[:1]:
                quote_block(q)
        with st.expander("All evidence, the absence search and limits"):
            for q in quotes:
                st.caption(ROLE.get(q.get("role"), q.get("role", "")))
                quote_block(q)
            for srch in cand.get("searches", []):
                path = ROOT / "gaps" / "searches" / f"{srch['search_id']}.json"
                if path.exists():
                    rec = json.loads(path.read_text(encoding="utf-8"))
                    st.markdown(f"**Absence search** ({rec.get('date')}): {rec.get('question')}")
                    st.caption("Searched for: " + ", ".join(f"`{t}`" for t in rec.get("searched_for", []))
                               + " · Not found: " + ", ".join(f"`{t}`" for t in rec.get("not_found", [])))
            for note in cand.get("notes", []):
                st.caption(f"Limit: {note}")

with st.expander("How code decides a gap candidate is supported"):
    st.markdown("A candidate passes only when code (`make assess-candidates`) confirms all four:")
    for i, rule in enumerate(status.get("rule", []), 1):
        st.markdown(f"{i}. {rule[0].upper() + rule[1:]}")
    st.caption(status.get("disclaimer", ""))
