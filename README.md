# Borderline

**(Cross-border response to safety, security and data incidents in diabetic-retinopathy screening AI)**

A multi-agent drill engine for cross-border medical-AI incidents, built for the
[International Telecommunication Union (ITU) AI for Good Sandbox Hackathon: United Arab Emirates](https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/).

When a medical AI product made in one country fails in another, both countries'
regulators, data-protection authorities and cyber agencies must share information
quickly, under different laws, each seeing only part of the picture. Borderline
rehearses that response before a real incident. It records which institution
decided what, which letters may legally cross the border, and where the rules run
out. The drill is wired to the United Arab Emirates (UAE) and Switzerland (CH);
country packs, a bridge pack and drill intents are plain YAML (a readable
configuration format).

> All scenario data is synthetic. Agent roles are simulated and do not represent any
> authority's official position. Nothing produced is a legal conclusion; policy gaps
> are called candidates.

## Contents

1. [Start here](#start-here)
2. [The use case](#the-use-case)
3. [How it works](#how-it-works)
4. [The AI agents and their roles](#the-ai-agents-and-their-roles)
5. [The knowledge base](#the-knowledge-base)
6. [The drills](#the-drills)
7. [Results](#results-8-november-2026)
8. [Policy and standards gaps](#policy-and-standards-gaps)
9. [Reproducibility guide](#reproducibility-guide)
10. [Repository map](#repository-map)
11. [Commands](#commands)
12. [Configuration](#configuration)
13. [Scope](#scope)

## Start here

| If you want to… | Open |
|---|---|
| Read the submission | [Technical report](report/technical-report.md) |
| Explore the drills, agents, sources and audit checks in a browser | `make ui` after [installing](#1-install), then http://localhost:8501 ([`ui/`](ui/app.py)); no model needed |
| See every drill result against what was expected | [Final run review](report/run-review-2026-11-08-final-runs.md) |
| See what each AI agent does | [The AI agents and their roles](#the-ai-agents-and-their-roles) |
| See who decided what, step by step | Decision trails for drills [A](report/decision-trail-governed-20261108-4.md), [B](report/decision-trail-ungoverned-20261108-3.md), [C](report/decision-trail-insufficient-20261108-3.md), [D](report/decision-trail-governed-scripted-20261108-3.md) |
| Check the results yourself in a few minutes | [Reproducibility guide](#reproducibility-guide) |
| See the code that makes the final decision | [`engine/liaison.py`](engine/liaison.py), [`engine/quotes.py`](engine/quotes.py) |

## The use case

RetinaVision-DX is a fictional diabetic-retinopathy screening service from a
fictional Swiss vendor, RetinaSwiss AG, used at fictional Dubai clinics. A model
update misses referable disease in 47 synthetic patients; the update was pushed
from a compromised vendor account; and UAE patients' retinal images held in Zurich
were reused for retraining. Each side learns different facts at different times and
must respond under its own rules; information crosses the border only through the
liaison channel. Product background:
[synthetic product dossier](report/synthetic-product-dossier-retinavision-dx.md).

## How it works

Three kinds of decision-maker take part, and every log entry records which one decided.

**1. Institution AI agents.** Twelve institutions, each a separate agent with its
own profile, mandate and allowed actions; see
[the AI agents and their roles](#the-ai-agents-and-their-roles). Each agent sees only
its institution's view of the event and passages retrieved from its own country's
texts plus global guidance. In one stateless model call it chooses one allowed
action and explains it with citations ([`engine/agent.py`](engine/agent.py)).

**2. An AI liaison reviewer.** Every cross-border letter goes to a separate model
call that answers three questions, each YES, NO or UNCLEAR with exact quotes
([`engine/liaison.py`](engine/liaison.py), `LiaisonReviewer`):

- **Legal basis:** may the sender share this?
- **Transfer rules:** is the transfer allowed under both sides' rules?
- **Counterpart:** is the receiver the right institution? (Counterpart pairs and
  reference answers: [`packs/bridge/ae-ch.yaml`](packs/bridge/ae-ch.yaml).)

**3. Code makes the final check.** The model proposes; code decides:

| Rule | Where |
|---|---|
| Every quote must appear word for word in a passage the reviewer was shown; up to two character slips are accepted and the exact source text is logged; a fabricated, joined or uncited quote turns the answer into UNCLEAR | [`engine/quotes.py`](engine/quotes.py) (`verify_quote`), [`engine/liaison.py`](engine/liaison.py) (`finalize_answer`) |
| A legal-basis YES must rest on national law, not global guidance or a drill exhibit | [`engine/liaison.py`](engine/liaison.py) (`NOT_LAW`) |
| Patient data crosses only with two keys: verified national-law quotes behind YES on legal basis and transfer rules, and a recorded human approval that matches the letter | [`engine/liaison.py`](engine/liaison.py) (`decide_liaison`, `evaluate_approval`) |
| A letter is delivered only on three YES answers, and every YES is flagged for human review | [`engine/liaison.py`](engine/liaison.py) (`decide_liaison`) |
| A letter that names no receiver is blocked | [`engine/actions.py`](engine/actions.py) (`_block_unaddressed_letter`) |
| An agent may only take actions its institution is allowed | [`engine/actions.py`](engine/actions.py), institution profiles |
| An uncited legal claim in an agent's explanation is sent back once, then replaced by fixed wording, and the log says so | [`engine/agent.py`](engine/agent.py) (`evaluate_step`) |
| Every UNCLEAR or NO is typed `policy_gap`, `implementation_gap`, `conflict` or `missing_evidence`; the last goes to a homework list, not to the gap list | [`engine/liaison.py`](engine/liaison.py) (`finalize_answer`), [`engine/orchestrator.py`](engine/orchestrator.py) |

Every decision is written to a hash-chained audit log
([`audit/hasher.py`](audit/hasher.py)): each entry includes the hash of the one
before, so any edit breaks the chain at that entry.

All AI decisions run on a local open-weight model (`qwen3:8b` through Ollama) at
temperature 0, so no prompt, passage or patient fact leaves the machine and the same
inputs give the same log ([`engine/llm.py`](engine/llm.py)).

## The AI agents and their roles

Thirteen AI roles take part: twelve institution agents and the liaison reviewer. All
run on the same local model; what differs is each one's mandate, what it is shown, and
the actions it may take. Profiles are simulations written for the drill, not
official positions of the real institutions. Drill D uses the same agents as Drill A.

| AI agent (profile) | Side | Role in the drill | What it may do | Drills |
|---|---|---|---|---|
| [Dubai Health Authority (DHA)](packs/ae/institutions/dha.yaml) | UAE | Dubai health regulator for the clinics where the AI failed | Open a clinical incident review; request follow-up review of affected patients; assess suspending the screening service and the vendor's "research" claim; send a request or patient data abroad through the liaison channel | A, B |
| [Ministry of Health and Prevention (MoHAP)](packs/ae/institutions/mohap.yaml) | UAE | Federal health regulator, including the rule that health data stays in the UAE | Open a safety inquiry; request a device incident report; assess where patient data is held; send a regulatory notification or request abroad | B, C |
| [Emirates Drug Establishment (EDE)](packs/ae/institutions/ede.yaml) | UAE | Federal medical-products regulator | Request evidence from the manufacturer; assess a device safety action; coordinate with health authorities; send a vigilance request to Swissmedic | A, B, C |
| [UAE Data Office](packs/ae/institutions/uae_data_office.yaml) | UAE | Personal-data regulator; must first check whether it is competent for health data | Assess its own competence; assess the basis and safeguards for a transfer; pause a transfer for review; refer to the competent authority; send a request to the FDPIC | A, B, C |
| [UAE cyber incident coordination](packs/ae/institutions/uae_cyber.yaml) | UAE | Cyber responder for the compromised vendor account | Open a cyber incident review; request access and credential evidence | B |
| [Screening service](packs/ae/institutions/screening_ai.yaml) | UAE | Operator of the deployed screening AI | Report the model update; pause the service; flag cases for human review | B |
| [Clinic operator](packs/ae/institutions/dubai_clinic_operator.yaml) | UAE | Runs the Dubai clinics using the AI | Recommend halting the AI at the clinics; escalate to MoHAP; request manual review of screenings | B |
| [Swiss Agency for Therapeutic Products (Swissmedic)](packs/ch/institutions/swissmedic.yaml) | Switzerland | Medical-device regulator for the vendor's product | Review the foreign incident report; request a manufacturer report; consider a field safety action; send the 47-patient recall list to EDE | A, B, C |
| [Federal Data Protection and Information Commissioner (FDPIC)](packs/ch/institutions/fodio.yaml) | Switzerland | Data-protection authority for disclosures from Switzerland | Assess the direction and scope of a transfer; request safeguards; recommend pausing a disclosure | A, B, C |
| [National Cyber Security Centre (NCSC)](packs/ch/institutions/ncsc.yaml) | Switzerland | Cyber authority; decides whether the vendor must report the incident | Assess the vendor's reporting duty; request security evidence | B, C |
| [RetinaSwiss AG](packs/ch/institutions/retina_swiss_ag.yaml) | Switzerland | The fictional vendor of the screening AI | Confirm the model deployment; preserve security evidence; record the secondary use of images and its research claim; handle telemetry requests; roll the model back | A, B |
| [Policy and legal adviser](packs/global/institutions/policy_adviser.yaml) | Neutral | Compares both countries' sources; the only agent that sees both | Prepare gap material for human review; request missing evidence | A, B, C |
| AI liaison reviewer ([`engine/liaison.py`](engine/liaison.py)) | Neither side | Checks every cross-border letter before code decides whether it is delivered | Answer the three questions (legal basis, transfer rules, counterpart) with YES, NO or UNCLEAR and exact quotes | A, B, C (scripted reference answers in D) |

## The knowledge base

- **49 registered source and extraction files** (26 UAE, 9 Swiss, 14 global) in
  [`data/raw/`](data/raw), each with its URL, issuer, language, legal status and
  SHA-256 hash in the register [`data/sources.csv`](data/sources.csv).
- **2,286 passages** in [`packs/ae/chunks.jsonl`](packs/ae/chunks.jsonl),
  [`packs/ch/chunks.jsonl`](packs/ch/chunks.jsonl) and
  [`packs/global/chunks.jsonl`](packs/global/chunks.jsonl). Each keeps its document,
  page, language and binding status, and an ID such as `CH-HEALTH-TPA:p40:c1` that
  every citation in the report points to.
- **Search** combines keyword matching with a local multilingual embedding model
  (`paraphrase-multilingual-MiniLM-L12-v2`, through fastembed) over a Chroma index
  ([`engine/knowledge.py`](engine/knowledge.py)). On a ten-question test set it puts
  the exact passage in the top six for 8 of 10 questions
  ([evaluation](report/retrieval-evaluation-seed-20261101.md),
  [questions](data/retrieval_benchmark_seed.csv)).
- **Gaps are recorded, not guessed.** Arabic text whose extraction is garbled is
  kept out of quoting; documents that could not be obtained are registered as such;
  absence searches (what was searched for, where, and what was found) are kept in
  [`gaps/searches/`](gaps/searches).

## The drills

Drill specifications are in [`intents/`](intents) (the ITU-T Y.3172 "ML intent").

| Drill | Intent | What it tests |
|---|---|---|
| A, governed | [`retinopathy-governed.yaml`](intents/retinopathy-governed.yaml) | Three letters written to real provisions, with the senders' assurances as labelled synthetic exhibits: a vigilance request (Therapeutic Products Act (TPA) Art. 64(1)), a recall list of 47 patients with a recorded human approval (TPA Art. 64(2)(c)), and a data-protection request on staff data (Federal Act on Data Protection (FADP) Art. 55) |
| B, ungoverned | [`retinopathy-ae-ch.yaml`](intents/retinopathy-ae-ch.yaml) | A staged incident across all 12 institutions, ending with DHA trying to send patient images to Switzerland; optional step 13 is a judge-injected event |
| C, insufficient evidence | [`retinopathy-insufficient-evidence.yaml`](intents/retinopathy-insufficient-evidence.yaml) | A request whose deciding document is missing |
| D, scripted control for A | [`retinopathy-governed.yaml`](intents/retinopathy-governed.yaml) with `--reviewer scripted` | Drill A's letters with the project's reference answers in place of the AI reviewer, to show whether Drill A's outcome comes from the AI review or from the law and the code. Institution agents are still AI and every code check still runs; the liaison answers are **not AI decisions** |

## Results (8 November 2026)

Four runs, all on the same code (commit `b229477`) and model (`qwen3:8b`). Their
full logs are in [`runs/`](runs).

| Drill | Run | Decisions | Letters delivered | Quotes verified | Highlights |
|---|---|---|---|---|---|
| A | [`governed-20261108-4`](runs/governed-20261108-4) | 9 | 0 of 3 | 10 of 13 | The AI reviewer found the right provisions (YES on legal basis each time); code rejected quotes it had joined from two places |
| B | [`ungoverned-20261108-3`](runs/ungoverned-20261108-3) | 40 | 0 of 5 | 24 of 30 | Patient images stopped at the border; a letter naming no receiver blocked; 1 typed gap; 8 homework items |
| C | [`insufficient-20261108-3`](runs/insufficient-20261108-3) | 7 | 0 of 1 | 6 of 6 | Letter without a reciprocity assurance blocked; answers typed as gaps for human review |
| D (scripted) | [`governed-scripted-20261108-3`](runs/governed-scripted-20261108-3) | 11 | 3 of 3 | 21 of 21 | The recall list crossed only with a matching recorded human approval |

All four hash chains verify and all four replay with 0 differences. Drill-by-drill
discussion, including where the 8-billion-parameter model fell short, is in the
[final run review](report/run-review-2026-11-08-final-runs.md).

## Policy and standards gaps

Four policy and standards gaps, findings subject to expert legal review, are kept in
[`gaps/candidate_register.yaml`](gaps/candidate_register.yaml). Code applies a
four-part evidence rule ([`gaps/sufficiency.py`](gaps/sufficiency.py)): every quote
verifies, an absence search is recorded, a verified global comparison is quoted, and
no obtainable missing document could refute the candidate. All four currently meet
it ([`report/candidate-status.json`](report/candidate-status.json)) and await expert
review.

| ID | Gap (domain wording) | Gap type | Reason from drill |
|---|---|---|---|
| CAND-01 | No designated authority for cross-border enforcement cooperation on patient data used by diagnostic AI | Policy gap (unclear responsibilities) | UAE retinal images held in Zurich; the Swiss regulator needs a reciprocal counterpart, and the sources held do not name the UAE body for health data |
| CAND-02 | No defined threshold for when an update to a diagnostic AI model needs re-approval | Standards gap (technology) | A model update is linked to missed diagnoses; the DHA AI policy asks for certification of "major upgraded versions" without defining "major" |
| CAND-03 | No route for regulators to share AI medical-device incident reports outside a closed international exchange | Standards gap (coordination) | Neither regulator is on the participant list of the International Medical Device Regulators Forum (IMDRF) incident-report exchange |
| CAND-04 | The rules on when health data may leave the country are hard to locate and inconsistently cited | Policy gap (legislative) | The deciding resolution was not publicly accessible to the project after documented attempts and is cited under two instrument types |

Each candidate also carries a recommendation drawn from its global example (see the register).

## Reproducibility guide

Install once, then there are three levels of check. The dashboard and the terminal
checks need no language model and take a few minutes.

### Environment used for the final runs

| Item | Value |
|---|---|
| Code | commit `b229477`. Later commits change documentation, add the review dashboard, remove unused `make` targets and make `scripts/replay.py` record a relative log path; none changes how a drill runs |
| Python | 3.11.17; exact packages in [`requirements-lock.txt`](requirements-lock.txt) |
| Ollama | 0.40.6 |
| Model | `qwen3:8b`, digest `500a1f067a9f` (8.2B parameters, Q4_K_M quantisation) |
| Model settings | temperature 0, thinking off, context window 16,384 tokens ([`engine/llm.py`](engine/llm.py)) |
| Embedding model | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` through fastembed 0.9.1 |
| Machine | Apple M5 Pro, 24 GB memory, macOS 26.6.2 |

### 1. Install

```sh
git clone https://github.com/Evangel90/Borderline.git
cd Borderline
python3.11 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt   # exact versions used
.venv/bin/pip install -e .
make index        # builds the local search index; downloads the embedding model once (~220 MB)
```

### 2. Open the review dashboard (no model needed)

```sh
make ui           # then open http://localhost:8501
```

The dashboard ([`ui/`](ui/app.py)) reads the saved runs and sources and calls no AI model. It has six pages:

1. **Overview:** the scenario, how a decision is made, and what each drill showed.
2. **The drills:** every cross-border letter, the three answers, each quote and whether it matched the law;
   every agent's input and decision one click deeper.
3. **Policy gaps found:** the four gaps, each with local evidence and a global comparison.
4. **Agents and sources:** each AI agent's mandate, allowed actions and decisions; the registered sources, and
   the text behind any passage ID.
5. **Verify and reproduce:** runs the hash-chain, git-tag, replay and source-hash checks in the browser, and a
   tamper test that edits a temporary copy of a log to show what each check catches.
6. **Source passage:** every citation and quote on the other pages links here. It shows the page of the
   registered document with the cited text highlighted, the passage the agent was given, and the official link.

### 3. Check the published results in the terminal (no model needed)

```sh
make verify-sources                       # every source file still matches its registered hash
.venv/bin/python -m pytest -q             # 174 tests
for RUN in governed-20261108-4 ungoverned-20261108-3 insufficient-20261108-3 governed-scripted-20261108-3; do
  make verify-log RUN=$RUN                # hash chain intact
  make replay RUN=$RUN                    # every code decision re-run over the logged AI answers
done
make assess-candidates                    # four-part rule on the gap candidates
make evaluate-retrieval                   # 8 of 10 in the top six
```

**What to expect:** every hash chain verifies; each replay ends in `0 differences`
(13, 30, 6 and 21 quotes re-checked); `4 of 4 candidates supported`.

`make replay` takes what each model said, as recorded in the log, and runs every
code rule again: quote checks, chunk-ID corrections, the patient-data rule,
three-YES routing, action authorisation, and which conditional steps should have
run ([`engine/replay.py`](engine/replay.py)). It shows that every outcome follows
from the logged AI answers and the code. To see the code react to a changed answer,
edit a copy of a log and run `make replay RUN=<id> REPLAY_ARGS="--log edited.jsonl"`;
the hash-chain check will also report the edit.

### 4. Re-run the drills with the model

**Set up Ollama** (the local model runner; about 5 GB for the model, and 16 GB of memory or more is advisable).
Official setup guide: [Ollama quickstart](https://docs.ollama.com/quickstart) (installers for macOS, Linux and
Windows at [ollama.com/download](https://ollama.com/download)); the model used is
[`qwen3:8b`](https://ollama.com/library/qwen3).

```sh
brew install ollama        # macOS; on Linux: curl -fsSL https://ollama.com/install.sh | sh; Windows: ollama.com/download
ollama serve               # leave this running in its own terminal tab
```

In a second terminal tab:

```sh
ollama pull qwen3:8b       # one-time download of the model (8.2B parameters, Q4_K_M)
ollama list                # qwen3:8b should be listed
ollama run qwen3:8b "Reply with one word: ready" --think=false   # optional smoke test; /bye to exit
```

If `ollama serve` reports that the address is already in use, Ollama is already
running (the macOS app starts it automatically) and you can skip that step.

Then run the drills:

```sh
export BORDERLINE_LLM_PROVIDER=ollama BORDERLINE_LLM_MODEL=qwen3:8b
make drill INTENT=retinopathy-governed RUN=repro-A
make drill INTENT=retinopathy-ae-ch RUN=repro-B DRILL_ARGS=--include-optional-events
make drill INTENT=retinopathy-insufficient-evidence RUN=repro-C
make drill INTENT=retinopathy-governed RUN=repro-D DRILL_ARGS="--reviewer scripted"
shasum -a 256 runs/repro-*/log.jsonl
```

Drill D uses scripted reviewer answers and calls no model. Each AI drill takes
many model calls and can run for a long time on a laptop.

Logs contain no run IDs or timestamps, so a faithful re-run produces a
byte-identical `log.jsonl`. Compare with the published logs (also recorded in the
annotated git tag `drills-final-20261108`):

| Drill | SHA-256 of `log.jsonl` |
|---|---|
| A | `c59a3118f235f0a925e07c51e10982d9132abb2565cbdd3d7dc686348aa0a454` |
| B | `5366b97322663adb3a76bd5b2225d341d62ef284c0cb21f660ca2b58f35d6b66` |
| C | `d5f2d063953be39109588ea637c784c2868a139659671fa426a461495a1be4bd` |
| D | `7920a75722af7c65bce10313be6918f5952e401eb0b8540c099abdb5c6372395` |

On our machine, re-running all four drills on the same code gave identical logs.
On different hardware or another Ollama version, the model's wording can differ
even at temperature 0. If a hash differs, compare outcomes instead:

```sh
make decision-trail RUN=repro-A           # writes report/decision-trail-repro-A.md
make replay RUN=repro-A                   # code decisions still replay with 0 differences
make step-coverage RUNS="retinopathy-governed=repro-A retinopathy-ae-ch=repro-B retinopathy-insufficient-evidence=<C>"
```

Each run ID must be new; the engine refuses to write into an existing run.

## Repository map

```
README.md                    this guide
report/                      submission material
  technical-report.md          the technical report
  run-review-2026-11-08-final-runs.md   results against expectations, per drill
  decision-trail-*.md          who decided what, per step and per letter
  candidate-status.json        gap candidates as assessed by code
  step-coverage.json           which steps and branches ran
runs/<run_id>/               the four final runs
  log.jsonl                    hash-chained decision log
  gaps.jsonl                   typed gap records
  liaison_homework.jsonl       missing-evidence homework
  replay.json                  code-replay result
engine/                      the drill engine
  orchestrator.py              runs a drill step by step
  agent.py                     institution AI agents
  liaison.py                   liaison reviewer and the final code decision
  quotes.py                    quote verification
  actions.py                   action sandbox (drill state only)
  knowledge.py                 hybrid search
  llm.py                       Ollama / OpenRouter clients
  replay.py                    code replay
  models.py                    data models for intents, packs and logs
audit/hasher.py              hash-chained log and verifier
gaps/                        gap-candidate register, absence searches, evidence rule
intents/                     drill specifications
packs/ae/, packs/ch/         country packs: institution profiles and passages
packs/bridge/ae-ch.yaml      counterparts and reference answers between the two countries
packs/global/                global guidance and the neutral adviser
data/sources.csv, data/raw/  source register and source files
scripts/                     command-line tools behind the make targets
ui/                          review dashboard (`make ui`): reads saved files, calls no model
tests/                       unit and scenario tests
```

## Commands

Run from the repository root.

| Command | What it does |
| --- | --- |
| `make ui` | Open the review dashboard at http://localhost:8501 (overview, drills, policy gaps, agents and sources, live checks and tamper test). Reads saved files only |
| `make verify-sources` | Re-hash every registered source and flag any change |
| `make ingest` | Rebuild the provenance-bearing passages and the search index |
| `make index` | Build or update the local search index from the existing passages |
| `make drill INTENT=<intent> RUN=<id>` | Run a drill (add `DRILL_ARGS="--reviewer scripted"` for Drill D, `--include-optional-events` for the judge-injected event) |
| `make verify-log RUN=<id>` | Check the hash chain; name the first broken entry |
| `make replay RUN=<id>` | Re-run every code decision over the logged AI answers, with no model call; exits 1 on any difference |
| `make decision-trail RUN=<id>` | Write who decided what, per step and per letter, to `report/` |
| `make audit-evidence RUN=<id>` | Screen a run's citations |
| `make step-coverage RUNS="..."` | Show which steps and liaison branches ran across runs |
| `make assess-candidates` | Apply the four-part evidence rule to the gap candidates |
| `make evaluate-retrieval` | Measure retrieval on the ten-question test set |
| `make itu-smoke` | Optional: run the ITU reference ingestion on one PDF (needs the `itu` extra and an Ollama embedding model) |

## Configuration

| Variable | Default | What it sets |
|---|---|---|
| `BORDERLINE_LLM_PROVIDER` | `openrouter` | Which model service to call: `ollama` (local; used for the final runs) or `openrouter` (hosted) |
| `BORDERLINE_LLM_MODEL` | `qwen3:8b` with Ollama; `openrouter/free` with OpenRouter | Which model to use |
| `BORDERLINE_OLLAMA_URL` | `http://127.0.0.1:11434` | Address of the local Ollama service |
| `BORDERLINE_OLLAMA_NUM_CTX` | `16384` | Context window in tokens; code refuses a prompt that would not fit |
| `BORDERLINE_LLM_TIMEOUT` | `180` | Seconds to wait for each model call |
| `OPENROUTER_API_KEY` | none | Key for the hosted option; not needed with Ollama |
| `BORDERLINE_VECTOR_PATH` | `index/chroma` | Folder where the search index is built |
| `BORDERLINE_EMBEDDING_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Embedding model used for search (any fastembed text model) |

Variables can also be set in a `.env` file in the repository root (the shell takes
precedence). With the hosted option, prompts, synthetic events and retrieved
passages are sent to OpenRouter, so never include real patient or confidential data.

**Sources and Arabic text.** Each passage keeps its source URL, issuer, file path
and hash, retrieval date, language, legal status and provenance notes, so a cited
chunk ID resolves to an exact page and its source record. Arabic PDFs with usable
text are searched directly with the multilingual model; scans or PDFs with broken
text are skipped with an `OCR required` warning rather than adding corrupted text.
An English translation may be registered separately for searching; the Arabic
original stays controlling where the official source says so. A reviewed OCR
version can be attached through `extraction_file` in `data/sources.csv`
([`scripts/ocr_pdf.py`](scripts/ocr_pdf.py)); provenance still points to the
original file and its hash. `retrieval_excluded` keeps a registered source
verifiable without adding it to search.

## Scope

Borderline is a synthetic policy-drill prototype, not a clinical tool or legal
opinion. Actions only update drill state and the local audit log; no clinical,
regulatory or data-transfer system is connected. The hash chain is tamper-evident
but not digitally signed. Each log entry names the model (`qwen3:8b`) but does not
record its digest, a hash of the prompts or a seed; the digest and settings are
given under Reproducibility, and the prompts are fixed by the code commit. Citations and actions should be checked against current
authoritative sources before any real-world use.

## License

[MIT](LICENSE)
