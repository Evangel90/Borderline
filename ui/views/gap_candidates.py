"""Policy gaps found: the four gap candidates, each with local evidence and a global comparison."""

from __future__ import annotations

import json

import streamlit as st
import yaml

from common import ROOT, passage, sidebar_note

sidebar_note()
st.title("🧩 Policy gaps found")
st.write(
    "Running the drills against both countries' law surfaced four places where the rules are missing, unclear or "
    "out of reach. Each is paired with how other systems handle the same question. They are **candidates for "
    "human review, not legal findings**: \"missing\" means missing from this knowledge base."
)

status = json.loads((ROOT / "report" / "candidate-status.json").read_text(encoding="utf-8"))
register = yaml.safe_load((ROOT / "gaps" / "candidate_register.yaml").read_text(encoding="utf-8"))
reg_by_id = {c["id"]: c for c in register.get("candidates", [])}
ROLE = {"host": "UAE", "partner": "Switzerland", "global_comparator": "Global comparison", "context": "Context"}


def quote_block(q: dict) -> None:
    title, _ = passage(q["chunk_id"])
    st.markdown(f"> {q['quote']}\n>\n> {'✓' if q.get('verified') else '✗'} `{q['chunk_id']}` · {title}")


for cand in sorted(status.get("candidates", []), key=lambda c: c["candidate_id"]):
    reg = reg_by_id.get(cand["candidate_id"], {})
    quotes = cand.get("quotes", [])
    local = [q for q in quotes if q.get("role") in ("host", "partner")]
    global_q = [q for q in quotes if q.get("role") == "global_comparator"]
    with st.container(border=True):
        st.markdown(f"#### {cand['title']}")
        st.caption(f"{cand['candidate_id']} · {reg.get('type', '')} gap · "
                   + ("✅ passes all four evidence checks" if cand["status"] == "SUPPORTED_CANDIDATE"
                      else "🟡 open: " + "; ".join(cand.get("unmet_conditions", []))))
        if reg.get("hypothesis"):
            st.write(" ".join(reg["hypothesis"].split()))
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
