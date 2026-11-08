# Borderline

A multi-agent drill engine for cross-border medical-AI incidents, built for the
[International Telecommunication Union (ITU) AI for Good Sandbox Hackathon: United Arab Emirates](https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/).

When a medical AI product made in one country fails in another, both countries'
regulators, data-protection authorities and cyber agencies must share information
quickly, under different laws. Borderline rehearses that response before a real
incident. It records which institution decided what, which letters may legally
cross the border, and where the rules run out. The drill is wired to the United
Arab Emirates (UAE) and Switzerland (CH); country packs, a bridge pack and drill
intents are plain YAML (a readable configuration format).

**Read first:** [technical report](report/technical-report.md) ·
[final run review](report/run-review-2026-11-08-final-runs.md) ·
decision trails for drills [A](report/decision-trail-governed-20261108-4.md),
[B](report/decision-trail-ungoverned-20261108-3.md),
[C](report/decision-trail-insufficient-20261108-3.md),
[D](report/decision-trail-governed-scripted-20261108-3.md)

## How it works

Three kinds of decision-maker take part, and every log entry records which one decided:

- **Institution AI agents** (12 UAE, Swiss and neutral institutions) each see only
  their own view and choose one of their allowed actions, with citations.
- **An AI liaison reviewer** (a separate model call) answers three questions for
  every cross-border letter: is there a legal basis to share, is the transfer
  allowed under both sides' rules, and is the receiver the right counterpart.
  Every answer carries exact quotes.
- **Code makes the final check.** It verifies every quote against the source
  passage (a fabricated quote becomes UNCLEAR), stops patient data without
  verified legal-basis and transfer-rules quotes and a recorded human approval,
  delivers a letter only on three YES answers, and flags every YES for human
  review. Every UNCLEAR or NO is typed `policy_gap`, `implementation_gap`,
  `conflict` or `missing_evidence`; the last goes to a homework list.

Everything is written to a hash-chained audit log. All AI decisions run on a local
open-weight model (`qwen3:8b` through Ollama), so no prompt or passage leaves the machine.

The use case is RetinaVision-DX, a fictional diabetic-retinopathy screening service
from a fictional Swiss vendor, used at fictional Dubai clinics: a model update misses
referable disease in 47 synthetic patients, the update came from a compromised vendor
account, and UAE retinal images held in Zurich were reused for retraining.

The knowledge base holds 49 registered UAE, Swiss and global source and extraction
files (hashed in [`data/sources.csv`](data/sources.csv)), split into 2,286 passages
that keep their document, page, language and legal status.

> All scenario data is synthetic. Agent roles are simulated and do not represent any
> authority's official position. Nothing produced is a legal conclusion; policy gaps
> are called candidates.

## Results (8 November 2026)

Four runs on the same code with local `qwen3:8b`. Drill D is a scripted control
for Drill A: the same letters, with the project's reference answers in place of the
AI liaison reviewer, to show whether Drill A's outcome comes from the AI review or
from the law and the code. Drill D's liaison answers are not AI decisions.

| Drill | Run | Decisions | Letters delivered | Highlights |
|---|---|---|---|---|
| A, governed | `governed-20261108-4` | 9 | 0 of 3 | The AI reviewer found the right provisions (YES on legal basis each time); code rejected quotes it had joined from two places |
| B, ungoverned (with optional step 13) | `ungoverned-20261108-3` | 40 | 0 of 5 | Patient images stopped at the border; a letter naming no receiver blocked; 1 typed gap; 8 homework items |
| C, insufficient evidence | `insufficient-20261108-3` | 7 | 0 of 1 | Letter without a reciprocity assurance blocked; answers typed as gaps for human review |
| D, scripted control for A | `governed-scripted-20261108-3` | 11 | 3 of 3 | All 21 quotes verified; the recall list crossed only with a matching recorded human approval |

All four hash chains verify and all four replay with 0 differences. The four gap
candidates (CAND-001 to CAND-004) meet the project's four-part evidence rule
(`make assess-candidates`) and await expert review.

Check any run yourself, without calling a model:

```sh
make verify-log RUN=governed-20261108-4
make replay RUN=governed-20261108-4
```

`make replay` re-runs every code decision (quote checks, the patient-data rule,
three-YES routing, action authorization and which conditional steps run) over the
AI answers recorded in the log and reports any difference.

## Layout

```
packs/ae/, packs/ch/      country packs: institutions/*.yaml, chunks.jsonl
packs/bridge/ae-ch.yaml   what links the two countries (counterparts, reference answers)
packs/global/             global benchmarks, neutral adviser
intents/                  staged drill specs (the Y.3172 "ML intent")
engine/                   AI agents, liaison reviewer, action sandbox, orchestrator, replay
audit/                    hash-chained log and verifier
gaps/                     gap-candidate register, absence searches, evidence rule
data/raw/, data/sources.csv   source files and provenance register
runs/<run_id>/            the four final runs: log.jsonl, gaps.jsonl, homework, replay
report/                   technical report, run review, decision trails
```

## Setup

```sh
git clone --recurse-submodules https://github.com/Evangel90/Borderline.git
cd Borderline
python3.11 -m venv .venv
.venv/bin/pip install -e .
make verify-sources
make index        # downloads the local embedding model once (~220 MB)
```

To run the drills as in the final runs (local Ollama, no application programming
interface (API) key; `ollama pull qwen3:8b` first). Each run ID must be new:

```sh
export BORDERLINE_LLM_PROVIDER=ollama BORDERLINE_LLM_MODEL=qwen3:8b
make drill INTENT=retinopathy-governed RUN=<new-id-A>
make drill INTENT=retinopathy-ae-ch RUN=<new-id-B> DRILL_ARGS=--include-optional-events
make drill INTENT=retinopathy-insufficient-evidence RUN=<new-id-C>
make drill INTENT=retinopathy-governed RUN=<new-id-D> DRILL_ARGS="--reviewer scripted"
make verify-log RUN=<id>; make audit-evidence RUN=<id>; make decision-trail RUN=<id>
make step-coverage RUNS="retinopathy-governed=<A> retinopathy-ae-ch=<B> retinopathy-insufficient-evidence=<C>"
make assess-candidates
```

### Technical notes

Search combines keyword matching with the local multilingual embedding model
`paraphrase-multilingual-MiniLM-L12-v2` (through fastembed). A hosted model can be
used instead by setting `BORDERLINE_LLM_PROVIDER=openrouter`:

Create an API key from [OpenRouter](https://openrouter.ai/settings/keys) and
export it as `OPENROUTER_API_KEY`. The default model `openrouter/free` routes
requests among available free models that support structured outputs. Free
models have rate limits and availability can change; the selected model can
vary between agent decisions. The drill sends its
prompts, synthetic events, and retrieved policy excerpts to OpenRouter; do not
include real patient or confidential data. Set `BORDERLINE_LLM_MODEL` to a
specific model ID if needed, or `BORDERLINE_LLM_PROVIDER=ollama` to use local
Ollama instead (`BORDERLINE_OLLAMA_URL` and `BORDERLINE_LLM_TIMEOUT` configure
the local service and timeout).

The `RUN` value must be new each time; existing run IDs are immutable and the
engine refuses to append to them. The supplied policy chunks are checked in;
agent prompts and retrieved excerpts are sent to OpenRouter when a drill runs.
The local Chroma index is built from the checked-in chunks; it is ignored by
Git and can be recreated with `make index`. The first index build downloads the
multilingual [FastEmbed model](https://qdrant.github.io/fastembed/examples/Supported_Models/)
(about 220 MB); embedding and search then run locally. Set
`BORDERLINE_VECTOR_PATH` to change the index directory or
`BORDERLINE_EMBEDDING_MODEL` to select another supported FastEmbed text model. Each
decision log records the IDs of all chunks retrieved for its agent view.
Each `packs/*/chunks.jsonl` record retains its source URL, issuer, registered
file path and SHA-256, retrieval date, language, legal status, and provenance
notes. A decision's cited chunk ID therefore resolves to both an exact page
and its source record; `data/sources.csv` remains the register of record.
Arabic PDFs with usable embedded text are ingested directly and searched with
the multilingual embedding model. Registered Arabic scans or PDFs with broken
font extraction are skipped with an `OCR required` warning instead of adding
corrupted text. An English translation may be registered as a separate source
for retrieval assistance; the Arabic original remains controlling where the
official source says so.
For a reviewed OCR derivative, set `extraction_file` in `data/sources.csv`; the
chunk provenance continues to point to the immutable original and its hash.
Create a searchable derivative with `scripts/ocr_pdf.py` and manually inspect
important passages because OCR can alter Arabic letters, spacing, and numbers.
Set `retrieval_excluded` for a registered source that is intentionally outside
the current drill; its original and hash remain verifiable without entering the
policy pack or search index.
Use `DRILL_ARGS=--include-optional-events` with `make drill` to include the
judge-injected reserve event.
`vendor/ITUAIReadiness` contains the [ITU reference
code](https://github.com/CrashingGuru/ITUAIReadiness) (MIT), pinned as a git
submodule; `make itu-smoke` is optional and requires that project's dependencies
and a locally running Ollama embedding model.

## Commands

Run from the repo root.

| Command | What it does |
| --- | --- |
| `make verify-sources` | Re-hash sources and flag any change |
| `make ingest` | Rebuild provenance-bearing chunks and update the local vector index |
| `make index` | Build or update the local Chroma index from existing chunks |
| `make drill INTENT=<intent> RUN=<id>` | Run a drill with the configured model provider |
| `make verify-log RUN=<run_id>` | Check the hash chain; name the first broken entry |
| `make replay RUN=<run_id>` | Code replay: re-run every code decision over the logged AI answers, no model call; exit 1 on any difference |
| `make audit-evidence RUN=<run_id>` | Screen a run's citations |
| `make decision-trail RUN=<run_id>` | Write who decided what, per step and per letter, to `report/` |
| `make step-coverage RUNS="..."` | Show which steps and liaison branches ran across runs |
| `make assess-candidates` | Apply the four-part evidence rule to the gap-candidate register |
| `make evaluate-retrieval` | Measure retrieval on the ten-question seed |

## Scope

Borderline is a synthetic policy-drill prototype, not a clinical tool or legal
opinion. Actions only update drill state and the local audit log; no clinical,
regulatory or data-transfer system is connected. The hash chain is tamper-evident
but not digitally signed. Citations and actions should be checked against current
authoritative sources before any real-world use.

## License

[MIT](LICENSE)
