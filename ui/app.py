"""Streamlit viewer for saved Borderline incident drill runs."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
sys.path.insert(0, str(ROOT))

from audit.hasher import HashChainedLogger  # noqa: E402


st.set_page_config(page_title="Borderline | Drill Review", page_icon="🧭", layout="wide")


def read_jsonl(path: Path) -> list[dict]:
    """Load JSONL records, reporting malformed lines with useful context."""
    records = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}, line {line_number}: {exc.msg}") from exc
    return records


def available_runs() -> list[str]:
    if not RUNS_DIR.exists():
        return []
    return sorted(
        (path.name for path in RUNS_DIR.iterdir() if path.is_dir() and (path / "log.jsonl").is_file()),
        reverse=True,
    )


st.title("🧭 Borderline")
st.caption("Cross-border AI incident drill review · LLM-driven choices, simulated tool actions · Synthetic scenario")

runs = available_runs()
if not runs:
    st.info("No saved runs found. Run `make drill INTENT=retinopathy-ae-ch RUN=<new-run-id>` first.")
    st.stop()

selected_run = st.sidebar.selectbox("Drill run", runs)
run_dir = RUNS_DIR / selected_run

try:
    decisions = read_jsonl(run_dir / "log.jsonl")
    gaps_path = run_dir / "gaps.jsonl"
    gaps = read_jsonl(gaps_path) if gaps_path.exists() else []
except (OSError, ValueError) as exc:
    st.error(f"Could not read this run: {exc}")
    st.stop()

valid_chain, chain_message, broken_index = HashChainedLogger.verify_log(str(run_dir / "log.jsonl"))
steps = sorted({record.get("step", 0) for record in decisions})
actors = {record.get("actor_id") for record in decisions}
blocked = len({record.get("step") for record in decisions if record.get("gate_status") == "BLOCK"})
routed = len({record.get("step") for record in decisions if record.get("gate_status") == "ROUTE"})

metric_cols = st.columns(4)
metric_cols[0].metric("Scenario steps", len(steps))
metric_cols[1].metric("Agent decisions", len(decisions))
metric_cols[2].metric("Institutional actors", len(actors))
metric_cols[3].metric("Transfer blocks / routes", f"{blocked} / {routed}")

if valid_chain:
    st.success(f"Audit chain verified · {chain_message}")
else:
    st.error(f"Audit chain failed · {chain_message} (entry {broken_index})")

timeline_tab, gaps_tab, audit_tab = st.tabs(["Incident timeline", "Policy gaps", "Audit log"])

with timeline_tab:
    st.subheader("Incident timeline")
    for step in steps:
        step_decisions = [record for record in decisions if record.get("step") == step]
        with st.expander(f"Step {step} · {len(step_decisions)} decisions", expanded=True):
            for record in step_decisions:
                heading = f"{record.get('actor_name', record.get('actor_id', 'Agent'))} · {record.get('jurisdiction', '—')}"
                st.markdown(f"**{heading}**")
                st.write(f"Action: `{record.get('action_taken', '—')}`")
                st.write(record.get("justification", "No justification recorded."))
                if record.get("model_name"):
                    st.caption(f"LLM: {record['model_name']} · self-reported confidence {record.get('confidence', '—')}")
                if record.get("tool_result"):
                    st.write(f"Tool outcome: {record['tool_result']}")
                if record.get("state_changes"):
                    st.json(record["state_changes"])
                citations = record.get("cited_clauses", [])
                st.caption("Citations: " + (" · ".join(citations) if citations else "None recorded"))
                liaison = record.get("liaison_status")
                if liaison:
                    st.caption(f"Liaison status: {liaison}")
                gate_status = record.get("gate_status")
                if gate_status:
                    st.caption(f"Border gate: {gate_status} · {record.get('gate_reason', '')}")
                st.divider()

with gaps_tab:
    st.subheader("Recorded policy gaps")
    if not gaps:
        st.info("This run has no policy-gap records.")
    for gap in gaps:
        st.markdown(f"### {gap.get('title', gap.get('gap_id', 'Policy gap'))}")
        st.caption(f"{gap.get('category', 'Uncategorized')} · {gap.get('host_jurisdiction', '—')} ↔ {gap.get('partner_jurisdiction', '—')}")
        st.write(gap.get("friction_point", "No friction point recorded."))
        left, right = st.columns(2)
        with left:
            st.markdown("**Host references**")
            st.write(gap.get("host_citation", "—"))
        with right:
            st.markdown("**Partner references**")
            st.write(gap.get("partner_citation", "—"))
        st.markdown("**Global benchmark**")
        st.write(gap.get("global_benchmark", "—"))
        st.markdown("**Suggested remediation**")
        st.write(gap.get("remediation_recommendation", "—"))
        st.markdown("**How this finding was produced**")
        st.write(gap.get("finding_method", "Not recorded."))
        st.caption(gap.get("limitations", "Limitations not recorded."))

        evidence = gap.get("evidence", [])
        st.markdown(f"**Supporting evidence ({len(evidence)})**")
        if not evidence:
            st.info("No supporting evidence references were recorded for this finding.")
        for item in evidence:
            page = f" · p. {item['page']}" if item.get("page") else ""
            label = f"{item.get('title', 'Source')} · {item.get('source_ref', 'no reference')}{page}"
            with st.expander(label):
                st.caption(f"{item.get('source_type', 'source')} · {item.get('jurisdiction', '—')}")
                st.write(item.get("relevance", ""))
                st.markdown("> " + item.get("excerpt", "No excerpt recorded."))

with audit_tab:
    st.subheader("Hash-chained decisions")
    st.caption("The chain makes edits detectable; it is not signed or externally anchored.")
    st.dataframe(
        [
            {
                "step": record.get("step"),
                "actor": record.get("actor_id"),
                "action": record.get("action_taken"),
                "model": record.get("model_name"),
                "liaison": record.get("liaison_status"),
                "gate": record.get("gate_status"),
                "tool result": record.get("tool_result"),
                "current hash": record.get("current_hash"),
            }
            for record in decisions
        ],
        use_container_width=True,
        hide_index=True,
    )
    with st.expander("Raw JSONL records"):
        st.json(decisions)
