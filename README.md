# Borderline

A prototype for policy-grounded deployment and incident drills, built for the
[International Telecommunication Union (ITU) AI for Good Lab Hackathon: United Arab Emirates](https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/).

Borderline rehearses how two countries' institutions respond when a medical AI
product made in one country fails in the other. The drill is wired to the
United Arab Emirates (UAE) and Switzerland (CH); country packs, a bridge pack
and drill intents are plain YAML. Adding a new country pack does not yet
configure a new drill automatically.

Three kinds of decision-maker take part, and every log entry records which one decided:

- **Institution AI agents** (12 institutions) each see only their own view and
  choose one of their allowed actions, with citations.
- **An AI liaison reviewer** (a separate model call) answers three questions for
  every cross-border letter (legal basis, both sides' transfer rules, right
  counterpart), with exact quotes.
- **Code makes the final check.** It verifies every quote word for word (a
  fabricated quote becomes UNCLEAR), stops patient data without verified
  legal-basis and transfer-rules quotes, delivers a letter only on three YES
  answers, and flags every YES for human review. Every UNCLEAR or NO is typed
  `policy_gap`, `implementation_gap`, `conflict` or `missing_evidence`; the last
  goes to a homework list, not to gap candidates.

Everything is written to a hash-chained audit log.

The use case is a fictional Swiss diabetic-retinopathy screening service,
RetinaVision-DX, used at fictional Dubai clinics: a model update misses
referable disease in 47 synthetic patients, the update came from a compromised
vendor account, and UAE retinal images held in Zurich were reused for retraining.

> All scenario data is synthetic. Agent roles are simulated and never represent
> any authority's official position. Nothing produced is a legal conclusion;
> policy gaps are called candidates.

The UAE, Swiss and global policy materials are a local, provenance-bearing
knowledge base (49 registered source and extraction files, 2,286 chunks), not a
complete legal collection and not hosted by ITU. See the [use-case and knowledge-base note](report/USE_CASE_AND_KB_CONTRIBUTION.md).

## Status (8 November 2026)

Three AI drills (A, B, C) were run on local Ollama `qwen3:8b`, plus **Drill D, a scripted
control for Drill A**: same letters as Drill A, but the project's hand-written reference answers stand in for the AI liaison reviewer, to test whether Drill A's blocks come from the AI review or from the law and the code. Drill D's liaison answers are not AI decisions. Drill A was run a second time after fixes. All five hash chains verify.
Full comparison of actual against expected: [run review](report/run-review-2026-11-08-three-drills.md).

| Drill | Run | Decisions | Letters delivered | Result |
|---|---|---|---|---|
| A, governed (`retinopathy-governed`) | `governed-20261108-1` | 9 | 0 of 3 (3 expected) | The AI liaison reviewer answered UNCLEAR on legal basis for every letter; reported as a finding, not forced |
| A, run 2 after fixes | `governed-20261108-2` | 9 | 0 of 3 (3 expected) | The AI liaison reviewer said YES on legal basis each time, but misread the no-data transfer question (step 2) and joined quotes from two places (steps 5, 8); code rejected those |
| B, ungoverned (`retinopathy-ae-ch`, optional step 13) | `ungoverned-20261108-1` | 40 | 0 of 4 | Patient images stopped; 1 typed gap (`policy_gap`); 5 homework items |
| C, insufficient evidence (`retinopathy-insufficient-evidence`) | `insufficient-20261108-1` | 7 | 0 of 1 | As expected: 2 homework items, no candidate created |
| **D, scripted control for A (not an AI decision)** (`retinopathy-governed`, `--reviewer scripted`) | `governed-scripted-20261108-1` | 11 | 3 of 3 | Reference answers stood in for the AI liaison reviewer; code still checked all 21 quotes and the human approval for the recall list. Shows the route works; says nothing about the AI review |

After the Drill A run we wrote its assurances as labelled synthetic exhibits, had
each letter name the provision it relies on, accepted quotes with at most two
character slips (logging the exact source text), and required a recorded human
approval matching the letter before patient data crosses. A rehearsal of the AI
liaison reviewer on the three Drill A letters (Emirates Drug Establishment to
Swissmedic, Swissmedic to the Emirates Drug Establishment, UAE Data Office to the
Swiss Federal Data Protection and Information Commissioner) (3 attempts each, plus two controls
that must block) still delivered 0 of 9; both controls stayed blocked
([`report/liaison-rehearsal-20261108.json`](report/liaison-rehearsal-20261108.json)).

In the AI runs, patient data never crossed the border. Code rejected two invented quotes. In Drill B
step 13 a request without a named receiver was routed by an older fixed rule,
without the liaison check. Fixed after the run (`engine/actions.py`): such a
letter is now blocked; `make replay` on that log flags step 13. Drill B was not re-run. The four gap
candidates (CAND-001 to CAND-004) are all `SUPPORTED_CANDIDATE` under the
project's four-part rule (`make assess-candidates`); they are unreviewed.
Submission material: [technical report](report/technical-report-draft.md),
[demo walkthrough](report/DEMO_WALKTHROUGH.md),
[criteria audit](docs/HACKATHON_CRITERIA_AUDIT.md).

The Streamlit viewer (`make ui`) was built for an earlier pre-deployment run and
has not been checked against the 8 November runs. `make report-figures` is not
implemented.

`make replay RUN=<id>` is a **code replay**: without calling any model, it re-runs
every code decision over the AI answers recorded in the log (quote checks, chunk-ID
corrections, the patient-data rule, three-YES routing, action authorization and
which conditional steps should run) and reports any difference. All three
8 November AI runs replayed with 0 differences under the code they ran with; under the
current code Drill A shows 5 differences, all from one misspelt quote now accepted as a
slip, with no outcome changed. It does not show that a model would
answer the same way again. Replaying an edited copy of a log
(`REPLAY_ARGS="--log edited.jsonl"`) shows what code does with a changed answer;
the hash-chain check reports the edit.

## Layout

```
packs/ae/, packs/ch/      country packs: documents/, institutions/*.yaml, chunks.jsonl
packs/bridge/ae-ch.yaml   what links the two countries (adequacy, treaties)
packs/global/             global benchmarks, neutral adviser, ITU standards
intents/                  staged drill specs (the Y.3172 "ML intent")
engine/                   AI agents, action sandbox, orchestrator, gates
audit/                    hash-chained log and verifier
gaps/                     gap register
data/raw/, data/sources.csv   source files and provenance register
runs/<run_id>/            log.jsonl, gaps.jsonl
ui/                       Streamlit timeline
report/, video/           submission material
```

## Setup and demo

```sh
git clone --recurse-submodules https://github.com/Evangel90/Borderline.git
cd Borderline
python3.11 -m venv .venv
.venv/bin/pip install -e .
export OPENROUTER_API_KEY=your-key
make verify-sources
make index  # downloads the embedding model once (~220 MB)
make drill INTENT=retinopathy-ae-ch RUN=demo-2026-10-30
make verify-log RUN=demo-2026-10-30
```

To reproduce the 8 November drills fully offline with local Ollama (no API key;
needs `ollama pull qwen3:8b` and `ollama pull nomic-embed-text`). Each run ID must be new:

```sh
export BORDERLINE_LLM_PROVIDER=ollama BORDERLINE_LLM_MODEL=qwen3:8b
make drill INTENT=retinopathy-governed RUN=<new-id-A>
make drill INTENT=retinopathy-ae-ch RUN=<new-id-B> DRILL_ARGS=--include-optional-events
make drill INTENT=retinopathy-insufficient-evidence RUN=<new-id-C>
make drill INTENT=retinopathy-governed RUN=<new-id> DRILL_ARGS="--reviewer scripted"  # Drill D, not an AI decision
python scripts/liaison_rehearsal.py --repeat 3 expect=ROUTE:retinopathy-governed:2:ede expect=BLOCK:retinopathy-ae-ch:14:dha
make verify-log RUN=<id>; make audit-evidence RUN=<id>; make decision-trail RUN=<id>
make step-coverage RUNS="retinopathy-governed=<A> retinopathy-ae-ch=<B> retinopathy-insufficient-evidence=<C>"
make assess-candidates
```

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

To review saved drill runs in the Streamlit timeline, install the optional UI
dependency and start the viewer:

```sh
.venv/bin/pip install -e '.[ui]'
make ui
```

## Commands

Run from the repo root.

| Command | What it does |
| --- | --- |
| `make fetch` | Not implemented yet |
| `make verify-sources` | Re-hash sources and flag any change |
| `make ingest` | Rebuild provenance-bearing chunks and update the local vector index |
| `make index` | Build or update the local Chroma index from existing chunks |
| `make drill INTENT=retinopathy-ae-ch` | Run the AI-agent drill; requires a configured model provider and API key for OpenRouter |
| `make verify-log RUN=<run_id>` | Check the hash chain; name the first broken entry |
| `make audit-evidence RUN=<run_id>` | Screen a run's citations (lexical and metadata only) |
| `make decision-trail RUN=<run_id>` | Write who decided what, per step and per letter, to `report/` |
| `make step-coverage RUNS="..."` | Show which steps and liaison branches ran across runs |
| `make assess-candidates` | Apply the four-part rule to the gap-candidate register |
| `make replay RUN=<run_id>` | Code replay: re-run every code decision over the logged AI answers, no model call; exit 1 on any difference |
| `make report-figures RUN=<run_id>` | Not implemented yet |
| `make ui` | Start the Streamlit run viewer (install `.[ui]` first) |

## Scope and limitations

This is a synthetic policy-drill prototype, not a clinical tool or legal
opinion. Each AI agent chooses from actions declared in its institution profile;
Python validates the chosen action and runs a corresponding sandbox tool. The
border gate has veto authority over transfers and external notifications. These
tools only update in-memory drill state and the local audit log. The model's
short rationale is logged; private chain-of-thought is neither requested nor
stored. The hash chain is tamper-evident but not digitally signed or externally
anchored. Gap evidence is scenario-specific and retrieved from selected source
documents; it is not an autonomous legal conclusion. Review citations and actions against current
authoritative sources before real-world use.

## License

[MIT](LICENSE)
