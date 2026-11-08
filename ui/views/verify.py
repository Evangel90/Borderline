"""Verify and reproduce: live integrity checks, a tamper test, and how to get the same results yourself."""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

import streamlit as st

from common import FINAL_RUNS, REPO_URL, ROOT, RUNS_DIR, TAG, sha256_file, sidebar_note, sources

from audit.hasher import HashChainedLogger  # noqa: E402  (common puts the repository root on sys.path)
from engine.replay import replay_run  # noqa: E402

sidebar_note()
st.title("🔐 Verify and reproduce")
st.write(
    "Don't take the results on trust. Each button below recomputes a check from the files in the repository, "
    "the same way the terminal commands do."
)

# ---------- 1. check ----------
st.markdown("### 1. Check the four drill records")
st.caption(
    "**Hash chain:** each log entry stores the hash of the one before, so editing any entry breaks the chain. "
    f"**Git tag:** the file's hash is compared with the one published in tag `{TAG}`. "
    "**Replay:** every code decision is re-run over the logged AI answers with no AI model. 0 differences "
    "means the outcomes come from the code, not the model."
)
if st.button("Run the checks", type="primary"):
    rows = []
    for run, info in FINAL_RUNS.items():
        path = RUNS_DIR / run / "log.jsonl"
        ok, msg, _ = HashChainedLogger.verify_log(str(path))
        rep = replay_run(run, root=str(ROOT))
        rows.append({
            "Drill": f"{info['letter']} · {info['name']}",
            "Hash chain": "✅ intact" if ok else f"❌ {msg}",
            "Matches git tag": "✅" if sha256_file(path) == info["sha"] else "❌",
            "Replay": f"✅ 0 differences" if not rep.all_differences else f"❌ {len(rep.all_differences)} differences",
            "Quotes re-checked": rep.quotes_checked,
        })
    st.dataframe(rows, width="stretch", hide_index=True)
    results = []
    for r in sources():
        for col_file, col_sha in (("file", "sha256"), ("extraction_file", "extraction_sha256")):
            f = (r.get(col_file) or "").strip()
            if f:
                path = ROOT / f
                results.append(path.exists() and sha256_file(path) == r[col_sha].strip())
    (st.success if all(results) else st.error)(
        f"Source documents: {sum(results)} of {len(results)} files match their registered SHA-256 hash.")

# ---------- 2. tamper ----------
st.markdown("### 2. Try to tamper with a record")
st.caption("This edits a temporary copy only; the real files are never touched.")
run = st.selectbox("Drill", list(FINAL_RUNS), format_func=lambda r: f"Drill {FINAL_RUNS[r]['letter']} · "
                   f"{FINAL_RUNS[r]['name']}", index=3)
entries = [json.loads(x) for x in (RUNS_DIR / run / "log.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
letters = [e for e in entries if e.get("liaison_checks")]
choices = {
    "flip": "Make the AI reviewer's first answer on the first letter say something else",
    "quote": "Change one word in a quote the AI reviewer gave",
    "explain": "Rewrite an agent's explanation of its decision",
}
mode = st.radio("Change", list(choices), format_func=choices.get)
if st.button("Tamper and re-check"):
    forged = copy.deepcopy(entries)
    target = next(e for e in forged if e.get("liaison_checks")) if letters else forged[0]
    if mode == "flip" and letters:
        chk = target["liaison_checks"][0]
        old = chk.get("proposed_answer")
        chk["proposed_answer"] = "UNCLEAR" if old == "YES" else "YES"
        what = f"step {target['step']}: reviewer's '{chk['check']}' answer {old} → {chk['proposed_answer']}"
    elif mode == "quote" and letters:
        chk = next(c for c in target["liaison_checks"] if c.get("quotes"))
        words = chk["quotes"][0]["quote"].split()
        old = words[len(words) // 2]
        words[len(words) // 2] = "never"
        chk["quotes"][0]["quote"] = " ".join(words)
        what = f"step {target['step']}: the word '{old}' in a '{chk['check']}' quote → 'never'"
    else:
        target = forged[0]
        target["justification"] = "Everything was fine; no action needed."
        what = f"step {target['step']}: {target['actor_id']}'s explanation rewritten"
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "log.jsonl"
        path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in forged), encoding="utf-8")
        ok, _, broken = HashChainedLogger.verify_log(str(path))
        rep = replay_run(run, log_path=str(path), root=str(ROOT))
    st.markdown(f"**You changed:** {what}")
    a, b = st.columns(2)
    if ok:
        a.success("Hash chain: still intact")
    else:
        where = forged[broken]["entry_id"] if 0 <= broken < len(forged) else "?"
        a.error(f"Hash chain: **broken** at `{where}`, the entry you changed")
    diffs = rep.all_differences
    if diffs:
        b.error(f"Replay: **{len(diffs)} difference(s)**. The logged outcome no longer follows from the answers.")
        with b.expander("Show the differences"):
            for d in diffs:
                st.code(d, language=None)
    else:
        b.info("Replay: 0 differences. This change does not affect any decision, but the hash chain still catches it.")

# ---------- 3. reproduce ----------
st.markdown("### 3. Reproduce it on your own machine")
st.markdown("**Install and open this dashboard** (Python 3.11):")
st.code(f"""git clone --recurse-submodules {REPO_URL}.git && cd Borderline
python3.11 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt && .venv/bin/pip install -e .
make ui                     # this dashboard at http://localhost:8501""", language="sh")
st.markdown("**Check the published results in the terminal** (no AI model needed):")
st.code("""make verify-sources                       # 49 of 49 source files match their hashes
for RUN in governed-20261108-4 ungoverned-20261108-3 insufficient-20261108-3 governed-scripted-20261108-3; do
  make verify-log RUN=$RUN && make replay RUN=$RUN   # chain intact, 0 differences
done
make assess-candidates                    # 4 of 4 gap candidates supported""", language="sh")
st.markdown("**Re-run the drills with the AI model** (needs [Ollama](https://ollama.com) and about 5 GB for the model):")
st.code("""make index                                # local search index (downloads ~220 MB once)
ollama pull qwen3:8b
export BORDERLINE_LLM_PROVIDER=ollama BORDERLINE_LLM_MODEL=qwen3:8b
make drill INTENT=retinopathy-governed RUN=repro-A
shasum -a 256 runs/repro-A/log.jsonl      # compare with the hash below""", language="sh")
st.dataframe([{"Drill": i["letter"], "Command": i["command"], "Published SHA-256 of log.jsonl": i["sha"]}
              for i in FINAL_RUNS.values()], width="stretch", hide_index=True)
st.caption(
    "Logs contain no timestamps or run IDs, so on the same setup (qwen3:8b digest 500a1f067a9f, Ollama 0.40.6, "
    "temperature 0) a re-run gives a byte-identical log. On other hardware the model's wording can differ; then "
    "`make replay RUN=repro-A` still shows the code decisions follow from the answers. The full guide, with "
    "the exact environment, is in the README under Reproducibility guide."
)
