"""Overview: the problem, how a decision is made, and what the four drills showed."""

from __future__ import annotations

import streamlit as st

from common import FINAL_RUNS, REFERENCE_FILE, run_summary, sidebar_note

sidebar_note()

st.title("🧭 Borderline")
st.markdown(
    "##### When a medical AI fails across a border, can regulators share what they need, and only what the law allows?"
)

st.markdown(
    "**The scenario (fictional).** A Swiss company's eye-screening AI is used at clinics in Dubai. A bad update misses "
    "sight-threatening disease in 47 patients. UAE and Swiss regulators now need to exchange incident information, a "
    "patient recall list and data-protection help."
)
st.markdown(
    "**What Borderline does.** Each real institution (12 in all) is played by an AI agent with its own mandate. "
    "Every letter that would cross the border is checked against **real, registered law**, and **code, not the AI, "
    "makes the final call**. Every step is logged in a tamper-evident record you can check on page 5."
)

st.graphviz_chart(
    """
digraph G {
  rankdir=LR; bgcolor="transparent"; nodesep=0.25;
  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=12, fillcolor="#eef2f7", color="#8796a8", margin="0.15,0.08"];
  edge [color="#8796a8", fontname="Helvetica", fontsize=10];
  a [label="Incident event", fillcolor="#fff4e0"];
  b [label="Institution AI agent\\nreads its country's law,\\npicks an allowed action"];
  c [label="AI liaison reviewer\\nanswers 3 questions\\nwith exact quotes"];
  d [label="Code decides\\nquotes must match the law\\nword for word", fillcolor="#e7f5ea"];
  e [label="Delivered", fillcolor="#d4f0da"];
  f [label="Blocked\\n(gap or homework)", fillcolor="#fbe0e0"];
  b2 [label="Local action"];
  a -> b; b -> c [label="letter abroad"]; b -> b2 [label="stays local"]; c -> d; d -> e; d -> f;
}
""",
    width="stretch",
)
st.caption("The three questions: may the sender share it? Do both countries' transfer rules allow it? "
           "Is the receiver the right institution? A letter is delivered only on three verified YES answers. "
           "Patient data also needs a recorded human approval.")

st.markdown("### What the four drills showed")
for run, info in FINAL_RUNS.items():
    s = run_summary(run)
    with st.container(border=True):
        left, right = st.columns([5, 1])
        left.markdown(f"**Drill {info['letter']} · {info['name']}**: {info['pitch']}")
        left.markdown(f"→ {info['outcome']}")
        right.metric("Right call", f"{s['right_call']} of {s['letters']}",
                     help="Letters whose outcome (delivered or blocked) matches what the project's reference "
                          "answers say should happen.")
        right.caption(f"Unsafe deliveries: **{s['unsafe']}**")
        left.page_link("views/drills.py", label=f"See Drill {info['letter']}", icon="🎬", query_params={"run": run})

st.caption(
    "**Right call** compares each letter's outcome with what the project's own reference answers to the three "
    f"questions say should happen (`{REFERENCE_FILE}`): delivered if all three are YES, otherwise blocked. "
    "**Unsafe delivery** means a letter got through that should have been stopped. The reference answers are the "
    "project's reading of the law, not a legal ruling."
)
st.success(
    "**In short:** no drill delivered anything it should have stopped, and patient data never crossed without "
    "both keys (verified law and a recorded human approval). Drills B, C and D made the right call on every "
    "letter. The one miss is Drill A, and it is the safe kind: the small local AI reviewer's answers did not hold "
    "up (UNCLEAR answers, quotes stitched together), so code blocked three letters that should have gone through. "
    "With correct answers (Drill D) the same code delivered them."
)
