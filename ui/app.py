"""Borderline review dashboard for judges.

Run with `make ui`, then open http://localhost:8501.
Reads saved files only; no language model, no network access, no writes to runs/.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Borderline", page_icon="🧭", layout="wide")

VIEWS = Path(__file__).resolve().parent / "views"

st.navigation([
    st.Page(VIEWS / "start.py", title="1. Overview", icon="🧭", default=True),
    st.Page(VIEWS / "drills.py", title="2. The drills", icon="🎬"),
    st.Page(VIEWS / "gap_candidates.py", title="3. Policy gaps found", icon="🧩"),
    st.Page(VIEWS / "agents.py", title="4. Agents and sources", icon="🏛️"),
    st.Page(VIEWS / "verify.py", title="5. Verify and reproduce", icon="🔐"),
    st.Page(VIEWS / "source.py", title="6. Source passage", icon="📄", url_path="source"),
]).run()
