# ITU AI for Good Sandbox Hackathon
# Borderline Diagnostic AI Governance Milestone Tracker

**Version:** 0.3 · **Updated:** 8 November 2026 · **Submission deadline:** 10 November 2026  
**Solution:** Borderline · **Repository:** https://github.com/Evangel90/Borderline  
**Status:** Not started / In progress / Blocked / Done · **Priority:** P0 / P1 / P2

## 0. Purpose and how to use this tracker

This is the working source of truth for delivery status, task ownership, acceptance criteria, and evidence. The repository remains the source of truth for code, source records, run results, and reports. Each task has an ID so that work can be assigned and discussed without relying on an unstructured checklist.

The tracker feeds three deliverables: the five-page technical report (Section 9), proof of work (Section 8), and the demonstration. Update status only when the acceptance criteria are met and the evidence link points to an artifact or command result. If a figure changes, update the report and this tracker together.

**Product scope.** Borderline is a synthetic AI diagnostic safety and governance stress-testing platform. The hackathon use case is a fictional UAE diabetic-retinopathy screening incident involving a Swiss vendor. The system simulates institutional decisions and records evidence and uncertainty; it does not provide clinical advice, issue legal opinions, or operate real clinical, regulatory, or data-transfer systems. See the [product specification](PRODUCT_SPEC.md) and [README](../README.md).

**Working rules**

- Use real, public, traceable policy and standards sources. Scenario and patient-impact facts must remain synthetic.
- Keep facts, assumptions, and unknowns distinct. Do not infer legal applicability, powers, or reporting duties from retrieval alone.
- A successful run, citation ID, or hash check is not evidence of policy accuracy or exact citation support.
- Describe global guidance as advisory where appropriate and separate it from binding local law.
- Do not claim broader diagnostic AI support, formal Y.3172 conformance, or measured national readiness unless separately demonstrated.
- Owners are shown as roles because named team assignments have not been provided. Fill in names in the owner column before work begins.

## 1. Y.3172 sandbox pipeline mapped to Borderline

Y.3172 describes an ML pipeline and management/orchestration concepts for future networks. Borderline adapts the pipeline vocabulary to a local healthcare governance simulation; it is not a telecom implementation and does not claim formal Y.3172 conformance. The demo pipeline runs on public policy sources and synthetic events, not a live underlay.

### 1A. Pipeline node implementation and remaining work

| Y.3172 node | Borderline meaning | Implementation and integration | Work item / evidence |
| --- | --- | --- | --- |
| ML Intent / MLFO | Intent defines the task; orchestrator coordinates pipeline stages. | `intents/retinopathy-ae-ch.yaml` defines actors, staged events, visibility, actions, and checks. `engine/orchestrator.py` runs the stages. | **PIPE-01 Done:** flagship intent. **PIPE-02 P1 In progress:** document event-to-agent-to-state flow in demo notes. Evidence: intent and [final run review](../report/run-review-retinopathy-final-itu-criteria-20261103-4.md). |
| SRC | Source and event inputs. | Public policy files, provenance register, and synthetic incident events. No patient images, live telemetry, or real incident records. | **SRC-01 In progress:** close source scope/currency review (Section 2). Evidence: `data/sources.csv`, `data/raw/`, source review reports. |
| C | Collection, parsing, and provenance. | `scripts/verify_sources.py`, `scripts/ingest.py` verify and prepare source material. | **PIPE-03 Done:** re-run `make verify-sources` before freeze; preserve output with submission evidence. |
| PP | Pre-processing and normalization. | Text/PDF extraction, reviewed OCR derivatives, chunking, metadata, multilingual embeddings. | **PIPE-04 In progress:** verify Arabic OCR/translation passages used in final claims with a qualified human reviewer. Evidence: linked extraction metadata and `report/arabic-ede-passage-review-20261103.md`. |
| M | Model and knowledge resources. | Jurisdiction-filtered hybrid lexical/vector search over provenance-bearing chunks; configured LLM proposes structured role decisions. | **PIPE-05 In progress:** expand reviewed retrieval and citation-support cases (Section 6). Evidence: `engine/knowledge.py`, `engine/agent.py`, retrieval benchmark. |
| P | Policy, authorization, and safety guardrails. | Institution action allow-lists, evidence triage, cross-border/notification gates, and simulated human review. | **PIPE-06 In progress:** complete passage-level review of final run’s claims and exceptions. Existing checks are partial and are not a legal rules engine. Evidence: `engine/actions.py`, `engine/gates.py`, `engine/evidence.py`. |
| D | Distribution of proposed or authorized outputs. | Orchestrator dispatches an action to a synthetic handler and records its outcome/state change. | **PIPE-07 Done:** synthetic dispatch is exercised in the final run. No external regulator message or real clinical action occurs. Evidence: `engine/orchestrator.py`, run log. |
| SINK | Target/output and audit trail. | Run decisions, evidence references, tool results, state, and hash-chained audit log; Streamlit viewer displays saved runs. | **PIPE-08 In progress:** prepare a judge-friendly walkthrough and verify the UI against the final run. Evidence: `ui/app.py`, `runs/`, `audit/`. |
| Sandbox / MLFO | Isolated execution and lifecycle management. | Local run artifacts are immutable by run ID; fresh LLM output can vary. | **PIPE-09 Done 8 Nov (code replay):** `make replay RUN=<id>` re-runs every code decision over the logged AI answers without a model call; 0 differences on all three 8 November runs. Fresh model output is still not reproducible. |

**Flow in one line:** synthetic incident and registered sources (SRC) → collection and provenance (C) → extraction/chunking (PP) → hybrid policy retrieval and agents (M) → role and evidence gates (P) → synthetic action dispatch (D) → decisions, findings, and audit trail (SINK).

### 1B. Pipeline concept cross-reference

| Concept | Borderline implementation | Tracker / evidence |
| --- | --- | --- |
| ML Intent | Staged incident configuration | `PIPE-01`, `intents/retinopathy-ae-ch.yaml` |
| SRC | UAE/Swiss/global sources and synthetic event facts | `SRC-01`–`SRC-05`, Table 2A |
| C and PP | Verify, extract, OCR, chunk, annotate, embed | `PIPE-03`, `PIPE-04`; `scripts/` and `packs/*/chunks.jsonl` |
| M | Hybrid retrieval and role-specific agent proposals | `PIPE-05`; Section 3 and Section 4 |
| P | Authorized action gate, evidence warnings, human-review state | `PIPE-06`; Section 4 |
| D and SINK | Synthetic dispatch, outcome, saved run and audit | `PIPE-07`, `PIPE-08`; Section 5 |
| Sandbox | Isolated local run; no production connection | `PIPE-09`; reproducibility instructions |

## 2. Source and knowledge-base tracker

`data/sources.csv` is the source register of record. On 8 November 2026 `make verify-sources` verified all 49 registered source and extraction files (26 UAE, 9 Swiss, 14 global rows), and the packs hold 2,286 chunks (UAE 888, Swiss 411, global 987); 9 files are registered but kept out of retrieval (for example, garbled Arabic text layers). Refresh these counts if the register changes.

### 2A. Source coverage and provenance

| ID | Dataset / source work | Status | Owner | Acceptance criteria and evidence |
| --- | --- | --- | --- | --- |
| SRC-01 | UAE medical-products, EDE, DHA, health-data, and cybersecurity material | In progress | Evidence lead (assign) | Each retrieved source has issuer, title, date/status, jurisdiction, language, source URL/path, hash, scope note, and limitations in `data/sources.csv`. Check whether the current pack answers the final use-case questions. |
| SRC-02 | Swiss medical-device, therapeutic-products, research, data-protection, and cyber material | In progress | Evidence lead (assign) | Scope notes distinguish applicable entities and conditional reporting requirements. Evidence: `data/sources.csv`, `packs/ch/`, `report/source-coverage-review-20261101.md`. |
| SRC-03 | Global sources: WHO, ITU, UN, G7 and other relevant guidance | In progress | Evidence lead (assign) | Each comparison cites an exact passage and labels binding/advisory status. Do not use generic global guidance as proof of UAE/Swiss legal duty. Evidence: `packs/global/`, technical report. |
| SRC-04 | UAE health-ICT implementing/exemption sources | Blocked on source acquisition/review | Evidence lead (assign) | Locate and register authoritative current documents or retain an explicit source-coverage limitation. No unsupported conclusion about their content. Mentioned in technical report as not archived in the local pack. |
| SRC-05 | DPO Annex 1 currency and Swiss cyber entity-scope review | In progress | Evidence lead (assign) | Confirm source date/current status and record which entity facts are needed before applying obligations. Evidence: source register and final evidence review. |
| SRC-06 | Arabic original and OCR/translation passage review | In progress | Arabic-capable reviewer (assign) | Human compare the Arabic source and English passage for every Arabic-derived decisive claim; record reviewer/date and any correction. Current review is provisional and machine-assisted. |
| SRC-07 | Source hashes and pack rebuild | In progress | Data/KB owner (assign) | `make verify-sources` succeeds; record artifact count and `make ingest` or index-build result; no unregistered material appears in retrieval. Current recorded snapshot: 32 artifacts verified. |
| SRC-08 | Retrieval provenance round-trip | In progress | Data/KB owner (assign) | For a sample of retrieved/cited IDs, trace chunk → source record → exact file/page/passage and hash; document sample size and failures. `scripts/verify_sources.py`, chunks, and run log are evidence. |

### 2B. Knowledge-base pipeline

| ID | Stage | Status | Dependencies | Implementation / acceptance |
| --- | --- | --- | --- | --- |
| KB-01 | Register source metadata and hashes | Done | — | `data/sources.csv`; re-verify at freeze. |
| KB-02 | Extract PDF/text and retain source association | Done | KB-01 | `scripts/ingest.py`; extraction files are linked to original sources. Review OCR where material. |
| KB-03 | Chunk and attach provenance metadata | Done | KB-02 | AE/CH/global chunk JSONL includes source/chunk references and metadata. |
| KB-04 | Build local multilingual index and hybrid search | Done | KB-03 | `engine/knowledge.py`; retrieval evaluation reports 9/10 exact passages in top six for the curated ten-question seed. |
| KB-05 | Scope and filter jurisdiction/document candidates | Done | KB-04 | Focused test coverage exists; retain filter behavior during any change. |
| KB-06 | Evaluate query coverage beyond curated seed | Not started | KB-04 | Add reviewed questions for statutory predicates, licensing scope, safety lifecycle, data use/transfer, cyber, and global comparison. Publish the question set, expected passage, hit@3/hit@6, misses, and limits. |
| KB-07 | Evaluate source quality and freshness | In progress | SRC-01–SRC-06 | Report missing/currentness issues and source limitations; passing hash checks alone is insufficient. |
| KB-08 | Connect retrieval evidence to claim support | In progress | KB-06, EVAL-03 | Manually adjudicate claim/citation pairs; lexical flags are triage, not semantic validation. Track false partials and missed unsupported claims. |

## 3. Borderline component and integration milestones

| ID | Deliverable | Priority / status | Dependencies | Owner | Acceptance criteria / verification |
| --- | --- | --- | --- | --- | --- |
| COMP-01 | Synthetic incident specification | P0 / Done | — | Project team | Progressive release, uneven role visibility, fictional facts and unknowns are explicit. Evidence: `intents/retinopathy-ae-ch.yaml`, `report/synthetic-product-dossier-retinavision-dx.md`. |
| COMP-02 | Institution profiles and role-authorized actions | P0 / Done | COMP-01 | Project team | Each configured actor has a profile and action allow-list; final integrated run reports all actions authorized. Evidence: `packs/*/institutions/`, run review. |
| COMP-03 | Agent structured output and bounded fallback | P0 / Done | COMP-02 | Project team | Agent decision schema and off-topic/evidence warnings are covered by tests; no hidden chain-of-thought is requested or stored. Evidence: `engine/agent.py`, `engine/models.py`, tests. |
| COMP-04 | Evidence triage and audit command | P0 / In progress | COMP-03 | Agent/evaluation owner (assign) | Reproduce the final audit; classify every flagged citation as supported, unsupported, or unresolved with reviewer rationale. Current screen flags 14 no-citation decisions and two DHA citations. Evidence: `scripts/audit_evidence.py`, final run review. |
| COMP-05 | Action and cross-border gates | P0 / Done | COMP-02 | Project team | Invalid actor actions are rejected and synthetic data-transfer/notification actions follow configured gates; tests cover allowed and denied paths. Evidence: `engine/gates.py`, `tests/`. |
| COMP-06 | Simulated human approval | P1 / Done | COMP-05 | Project team | Approval is recorded separately and visibly affects only synthetic display state. Report unauthenticated/self-entered status. Evidence: `ui/app.py`, `human_approvals/` artifacts where present. |
| COMP-07 | Hash-chained audit and verifier | P0 / Done | — | Project team | `make verify-log RUN=retinopathy-final-itu-criteria-20261103-4` succeeds; explain that log is not signed or externally anchored. Evidence: `audit/`, `scripts/verify_log.py`. |
| COMP-08 | Candidate governance assessment | P1 / In progress | COMP-04, KB-08 | Gap-analysis owner (assign) | Preserve `INSUFFICIENT_EVIDENCE` when evidence is missing; record scenario triggers and evidence refs; do not state a policy gap without reviewed support. Evidence: `gaps/candidates.py`, `runs/.../gaps.jsonl`, report. |
| COMP-09 | Finding classification and rejection path | P1 / In progress | COMP-08 | Gap-analysis owner (assign) | Distinguish policy, implementation, operational, coordination, and evidence deficiencies; include a counterfactual/negative control that rejects an unsupported candidate. Existing no-signal clinical-conflict test is a starting point. |
| COMP-10 | Governance-centered run viewer | P2 / In progress | COMP-07, COMP-08 | UI owner (assign) | From one saved run, a reviewer can locate timeline, actor, visible facts, action, citations, uncertainty, assessments, and audit status. Evidence: `ui/app.py`; manual review not yet recorded. |
| COMP-11 | Demo walkthrough and screenshots | P2 / Not started | COMP-10, EVAL-01 | Demo owner (assign) | Capture a short sequence using the final run: incident → institutional response → safety/access conflict → evidence limits → finding status → audit verification. Keep all facts synthetic. |
| COMP-12 | README and reproducibility cleanup | P2 / In progress | COMP-07, EVAL-01 | Release owner (assign) | One documented clean setup path, exact model/provider requirements, source validation, run command, and log verification; identify commands that are not implemented. |

## 4. Agent model and scenario plan

### 4A. Roles and responsibilities

| Role group | What the simulated role contributes | Guardrail / evaluation question | Evidence |
| --- | --- | --- | --- |
| Dubai clinic operator | Incident awareness, care continuity, pause/review recommendation | Is clinic licensing and manual capacity known? Does a pause require human review? | `packs/ae/institutions/dubai_clinic_operator.yaml`, final run |
| Swiss manufacturer | Model/update evidence, investigation response, corrective-action information | Are product, authorization, holder, and statutory predicates known? | `packs/ch/institutions/retina_swiss_ag.yaml`, synthetic dossier |
| EDE / medical-product regulator role | Conditional product-evidence and classification fact-finding within simulation | Keep Articles 68(7)/70(2) predicates conditional; fictional letter is not a real decision. | `packs/ae/institutions/ede.yaml`, EDE run review |
| DHA / health-policy roles | Healthcare policy context and scoped pathways | Do not infer licensing, incident-specific duties, or mandate from a general policy passage. | DHA profiles, citation adjudication |
| UAE cyber / NCSC roles | Cyber evidence and incident coordination questions | Confirm entity, incident, and reporting scope before asserting an obligation. | Institution profiles and staged cyber events |
| Neutral policy adviser | Evidence synthesis and candidate assessment | Advisory analysis only; distinguish source evidence from legal interpretation. | `packs/global/institutions/policy_adviser.yaml` |

### 4B. Scenario and stress-test coverage

| ID | Stress test / event | Status | Dependencies | Acceptance criteria / evidence |
| --- | --- | --- | --- | --- |
| SCN-01 | Post-update missed referable cases; synthetic 47-case signal | Done | COMP-01 | Event is progressive; facts are fictional; case follow-up is explicitly unknown. Evidence: intent, product dossier, final run. |
| SCN-02 | Safety pause versus screening access | Done | SCN-01 | Competing objectives are visible and produce a human-review recommendation; service is not actually stopped. Evidence: `CLINICAL-CONFLICT-001` in final run. |
| SCN-03 | Suspected stolen vendor credentials / compromised update | Done | SCN-01 | Cyber investigation and evidence preservation questions appear without assuming breach attribution or duty. Evidence: intent stage and run log. |
| SCN-04 | Secondary use of UAE-origin images for retraining; claimed research purpose | Done | SCN-01 | Unknown controller, purpose/legal basis, identifiability, and transfer path remain unknown unless supplied. Evidence: intent, run log, `GAP-HEALTH-001`. |
| SCN-05 | Conditional EDE manufacturer-evidence request | Done | SCN-01, registered source | Three EDE decisions reference conditional provisions and state unresolved predicates; demonstrate this as synthetic fact-finding, not a legal duty. Evidence: final run review. |
| SCN-06 | Negative control for policy-gap claim | In progress | COMP-08, COMP-09 | Run at least one scenario with trigger evidence absent and show the gap hypothesis is rejected or remains unsupported. Preserve existing focused counterfactual test and add run-level evidence. |
| SCN-07 | Independent model-lifecycle/safety stress test | Not started | SCN-01, evaluation fixtures | Add a distinct incident variation with predeclared expected evidence/action checks; execute and manually review before claiming it as evaluated. |
| SCN-08 | Data/cyber cross-border variation | Not started | SCN-03, SCN-04 | Add distinct controlled variation and expected outcomes; avoid treating repeated events from the same run as a second validated stress test. |

Current evidence supports one integrated flagship scenario, not three independently validated stress tests. Any additional scenarios are future work until implemented and reviewed.

## 5. Proof of work and actual run results

### 5A. Recorded baseline and latest evaluated run

| Item | Recorded result | Evidence / interpretation |
| --- | --- | --- |
| Drill A, governed | `governed-20261108-1`, local `qwen3:8b`, 8 November 2026 | 9 decisions, hash chain verified, 0 audit-screen flags. **0 of 3 letters delivered (3 expected)**: the AI liaison reviewer answered UNCLEAR on legal basis each time; the recall list of 47 synthetic patients was stopped by code's patient-data rule. 5 homework items. Reported as a finding, not forced. |
| Drill B, ungoverned | `ungoverned-20261108-1` (with optional step 13) | 40 decisions, 12 institutions, hash chain verified, 8 audit-screen flags (6 no citation, 2 citation needs review), 7 explanations replaced by code. 0 of 4 letters delivered; patient images stopped; 1 typed gap (`policy_gap`, MoHAP); 5 homework items. Step 13 request bypassed the liaison check (known defect, not fixed). |
| Drill C, insufficient evidence | `insufficient-20261108-1` | 7 decisions, hash chain verified, 1 audit-screen flag. As expected: 1 letter blocked, 2 homework items, no candidate created. |
| Drill A, run 2 after fixes | `governed-20261108-2` | 9 decisions, hash chain verified, 1 audit-screen flag, 10 of 13 quotes verified, **0 of 3 letters delivered**: the reviewer misread the no-data transfer question (step 2) and joined quotes across provisions (steps 5, 8), which code rejected. 5 homework items. Replay 0 differences. |
| Drill D, scripted control for A | `governed-scripted-20261108-1` (`--reviewer scripted`) | Not an AI decision: same letters as Drill A, but the project's hand-written reference answers stand in for the AI liaison reviewer, to test whether Drill A's blocks come from the AI review or from the law and the code. 11 decisions, hash chain verified, 21 of 21 quotes verified, 3 of 3 letters delivered, recall list crossed with a matching recorded human approval, replay 0 differences, 2 audit-screen flags. |
| Quote check | Drills A, B and C | 52 of 54 liaison quotes verified; the 2 failures were invented by the reviewer (a misspelling; a page header stitched to FADP Art. 55). Two real quotes had their chunk IDs corrected by code (5 corrections). |
| Step coverage | `report/step-coverage.json` | No unconditional step skipped or failed. All 5 blocked liaison branches covered by the AI runs; **delivered branches covered only by Drill D** (scripted). |
| Gap candidates | `make assess-candidates` | CAND-001 to CAND-004 all `SUPPORTED_CANDIDATE` under the four-part rule; unreviewed, not legal conclusions. |
| Retrieval seed | `make evaluate-retrieval`, 8 November 2026 | 8/10 exact-passage hit@6; 7/10 hit@3. Ten curated questions; retrieval only. |
| Tests | `.venv/bin/python -m pytest -q` | 147 passed. |

Full review: [`report/run-review-2026-11-08-three-drills.md`](../report/run-review-2026-11-08-three-drills.md). Earlier runs (`retinopathy-final-itu-criteria-20261103-4`, `retinopathy-evidence-packet-20261105-1`) predate the liaison channel and are historical only.

### 5B. Reproduction and verification checklist

| ID | Command / check | Status | Required recorded evidence |
| --- | --- | --- | --- |
| RUN-01 | `make verify-sources` | Done 8 Nov | 49 of 49 artifacts verified. |
| RUN-02 | `.venv/bin/python -m pytest -q` | Done 8 Nov | 147 passed at `f6f3ba1`. |
| RUN-03 | `make verify-log RUN=<A, B, C>` | Done 8 Nov | All three hash chains verified (`governed-20261108-1`, `ungoverned-20261108-1`, `insufficient-20261108-1`). |
| RUN-04 | `make audit-evidence RUN=<A, B, C>` | Done 8 Nov; flags not yet adjudicated | 0, 8 and 1 flags; listed in the 8 November run review. |
| RUN-05 | `make evaluate-retrieval` | Done 8 Nov | 8/10 hit@6, 7/10 hit@3. |
| RUN-06 | `make evaluate-claims` | In progress | Record metrics against manual labels and list false positives/negatives; do not present selected seed as accuracy. |
| RUN-07 | Three full drills (Ollama `qwen3:8b`) | Done 8 Nov | Run IDs above; decision trails in `report/decision-trail-*-20261108-1.md`. |
| RUN-08 | Code replay | Done 8 Nov | `make replay` on A, B and C: 8 letters, 24 answers, 54 quotes re-checked, 0 differences. It does not re-run the model. |

**Do not run evaluation commands and fill these rows with historical values as if freshly verified.** Enter the date, command output location, model/provider, code revision, and run ID when executing the final pass.

## 6. Evaluation design and acceptance criteria

| ID | Evaluation area | Status | Work required | Completion evidence |
| --- | --- | --- | --- | --- |
| EVAL-01 | Source and passage integrity | In progress | Verify source hashes; sample passage-to-page/source round trips; review OCR and translated text used in claims. | Command output plus passage-review notes. |
| EVAL-02 | Retrieval | In progress | Keep the ten-question seed as smoke test; add independently selected questions and hard cases, including negative/no-answer cases. | Dataset, expected IDs, hit@3/hit@6, misses, and limits. |
| EVAL-03 | Citation support | In progress | Adjudicate cited claims at exact passage level; label support, partial, unsupported, or insufficient; record reviewer and rationale. | Updated manual claim set and citation review report. |
| EVAL-04 | Legal applicability and mandate | Not started | For any obligation claim, record jurisdiction, actor, entity scope, product status, triggering event, statutory predicate, and source status. Use unresolved when a predicate is unknown. | Applicability matrix for claims shown in report/demo. |
| EVAL-05 | Agent relevance and role discipline | In progress | Review rationale topic, actor scope, action permission, missing facts, and abstention for every final-run decision or a declared sample. | Reviewed decision matrix with denominator and sampling method. |
| EVAL-06 | Gap detection and refutation | In progress | For each candidate, state hypothesis, trigger, local evidence, global comparator, evidence deficits, alternative explanation, status, and rejection rule. | Assessment record and one negative-control result. |
| EVAL-07 | Action authorization and audit | Done for final run | Reproduce action checks and hash verification after any relevant code change. | `RUN-02`, `RUN-03`, final run review. |
| EVAL-08 | Human review and UI | Not started | Manually inspect pause/approval flow and saved run; confirm approval is unauthenticated and synthetic in on-screen explanation. | Dated UI review notes or screenshots. |
| EVAL-09 | Readiness/standards mapping | In progress | Verify every claimed mapping points to implemented component/artifact; keep qualitative and state non-conformance. | Criteria audit and technical report mapping. |
| EVAL-10 | Report and demo consistency | Not started | Check every number and claim against frozen run/source evidence; align terminology and limitations. | Review checklist with report version and run ID. |

## 7. Recommended technical choices and project constraints

| Need | Current choice | Why / constraint | Follow-up |
| --- | --- | --- | --- |
| Application and orchestration | Python, Pydantic, local orchestrator | Existing working engine and structured decisions; avoid unnecessary rewrite. | Preserve tested interfaces. |
| Knowledge retrieval | Chroma, FastEmbed embeddings, hybrid lexical/vector search | Local index and provenance-bearing chunks; first setup may download embedding model. | Broaden reviewed benchmark; do not infer accuracy from top-k alone. |
| Agent model | OpenRouter configurable; final integrated run used local Ollama `qwen3:8b` | Availability and output vary by provider/model; prompts may include synthetic events and retrieved excerpts. | Record provider/model per run; never send real or confidential data. |
| Policy and safety enforcement | Python action allow-lists and configured gates | Deterministic action validation; legal interpretation remains out of scope. | Add explicit missing-fact checks where high consequence. |
| Audit | Local hash-chained JSONL | Tamper-evident local trace; not a signature or external timestamp. | Verify final run and state limitation. |
| UI | Streamlit | Fast local inspection of runs and human review state. | Improve judge-facing narrative only after evidence is stable. |
| Evaluation | Pytest, retrieval seed, claim seed, run audit | Existing regression and curated review harnesses. | Add independent questions and manual semantic labels before broad claims. |
| Replay | Code replay implemented (`engine/replay.py`) | Fresh LLM inference is nondeterministic, so only code decisions are replayed. | Say "code replay", never "deterministic replay of the model". |

## 8. Work log and decision log

### 8A. Work log

Add one row for each material work session. Use links to committed artifacts, not summaries without evidence.

| Date | Milestone | What changed | Evidence | Owner |
| --- | --- | --- | --- | --- |
| 2026-11-01–02 | M1–M4 | Evidence triage, manual claim/retrieval seeds, source coverage, scenario branches, and UAE/Swiss source work. | `docs/HACKATHON_EXECUTION_PLAN.md`; dated reports in `report/`. | Team (confirm) |
| 2026-11-03 | M5 | Added simulation-only product classification and corrective-action artifacts; completed final integrated drill and review. | `report/synthetic-product-dossier-retinavision-dx.md`; final run review. | Team (confirm) |
| 2026-11-04 | Submission planning | Recast tracker as numbered task plan with owners, dependencies, acceptance criteria, and evidence pointers. | This document. | Team (confirm) |
| 2026-11-07 | M3–M4 | Liaison channel with AI liaison reviewer and code quote check; evidence-sufficiency rule for gap candidates; three-drill split. | `docs/HANDOFF_2026-11-07.md`; `report/candidate-status.json`. | Team (confirm) |
| 2026-11-08 | M5–M6 | Ran Drills A, B and C; reviewed actual against expected; updated technical report, demo walkthrough, README and this tracker from the new runs; drafted the filled submission document. | `report/run-review-2026-11-08-three-drills.md`; `report/technical-report-draft.md`. | Team (confirm) |
| YYYY-MM-DD | M__ | Add completed work and actual result. | Link artifact/commit/run. | Assign name |

### 8B. Open decision log

| ID | Decision needed | Options / context | Decision | Status / owner |
| --- | --- | --- | --- | --- |
| DEC-01 | Who owns each open source, evaluation, UI, and submission task? | Assign team members; current tracker uses role placeholders. | — | Open / team lead |
| DEC-02 | Whether to run another full drill before freeze | Drill A delivered no letter; Drill B step 13 bypassed the liaison check. Options: submit as is, fix the bypass and re-run B, or add quotable synthetic assurances and re-run A and B. | 8 Nov: submit the current runs; report Drill A's blocks as a finding and the bypass as a known defect. | Decided / user |
| DEC-03 | How to address two flagged DHA citations and 14 uncited decisions | Remove, replace with reviewed evidence, or retain as uncited operational choice with explicit limits. | Case-by-case adjudication; do not imply the referral passage establishes AI duty. | Open / evidence lead |
| DEC-04 | Which candidate findings appear in submission | Safety/access; incident evidence and coordination; secondary-use questions. | Keep as evidence questions unless passage-level review supports stronger classification. | Open / gap-analysis owner |
| DEC-05 | Team and contact fields | Names, affiliation, leader, contact. | — | Open / team lead |
| DEC-06 | Final report/template rendering and page limit | Markdown draft exists; final layout not verified. | Render with official template and record page count. | Open / report owner |
| DEC-07 | Demo format | Live UI walkthrough, screenshots, or recording. | Use final saved run; no live model call required unless chosen. | Open / demo owner |
| DEC-08 | Freeze point | Repository revision, source manifest, run ID, demo steps. | Freeze after report, verification, and claim review. | Open / release owner |

### 8C. Milestone gates

| Milestone | Gate | Status | Evidence to close |
| --- | --- | --- | --- |
| M0 — Scope and baseline | One domain-specific evaluated use case and explicit limits | Done | Product spec, README, baseline/run reviews. |
| M1 — Source corpus | Relevant sources registered, provenance-bearing, and verified | In progress | SRC-01–SRC-08 and fresh `make verify-sources`. |
| M2 — Processing and retrieval | Search reproduces reviewed passages and exposes misses | In progress | KB-06, EVAL-01/02 and current benchmark output. |
| M3 — Agents and gates | Role decisions, authorizations, uncertainty, and human review are inspectable | In progress | COMP-02–COMP-06, EVAL-04/05/08. |
| M4 — Scenario and findings | Staged conflict and candidate findings are tested, including negative control | In progress | SCN-06, COMP-08/09, EVAL-06. |
| M5 — Evaluation | Current run, source, tests, citations, and hash chain reviewed | Done 8 Nov, except adjudication of 9 audit flags | RUN-01–RUN-07 and EVAL-01–EVAL-10. |
| M6 — Submission | Five-page report, demo, team metadata, and frozen artifacts ready | In progress: report and demo rewritten 8 Nov; team fields and page count open | SUB-01–SUB-07 in Section 10. |

## 9. Map from tracker to the technical report

The report is limited to five pages. Distill from evidence; do not copy the tracker wholesale.

| Report section | Pull from | Suggested budget |
| --- | --- | --- |
| Header: team, affiliation, contact, repository | Team details and submission metadata | 3 lines |
| Introduction and importance | Product scope and why diagnostic AI incident response matters | 0.5 page |
| Use case: problem, existing response, solution and value | SCN-01–SCN-05, synthetic dossier, conflict | 0.75 page |
| Local policy corpus and Y.3172 mapping | Sections 1–2; criteria audit; verified sources | 1 page |
| Architecture and implementation | Sections 1 and 3; retrieval, gates, agents, audit and UI | 1 page |
| Evaluation scenarios and results | Sections 4–6; final run and curated benchmark with limits | 0.75 page |
| Findings, limitations, conclusion, scalability | Evidence-reviewed candidate findings; Section 11 future work | 1 page |

The current draft is [`report/technical-report-draft.md`](../report/technical-report-draft.md). Its rendered length, final passage-level review, and team/contact fields remain open. Each reported count must match the frozen source/run artifacts.

## 10. Submission deliverables and final checklist

| ID | Deliverable | Priority / status | Owner | Acceptance criteria / evidence |
| --- | --- | --- | --- | --- |
| SUB-01 | Technical report in official template, no more than five pages | P0 / In progress | Report owner (assign) | Render final file; record page count; verify names, citations, tables, and all numerical claims against frozen artifacts. |
| SUB-02 | Public repository and reproducible instructions | P0 / In progress | Release owner (assign) | README specifies setup, model/provider, source verification, run and audit commands; explains what `make replay` does and does not show; notes `make report-figures` is not implemented. |
| SUB-03 | Policy/strategy knowledge base and provenance | P0 / In progress | Evidence lead (assign) | Fresh source validation; source manifest and limitations are in repository; no confidential/patient data. |
| SUB-04 | Y.3172 and AI Readiness mapping | P1 / Done with limits | Report owner (assign) | Mappings point to implemented components; state adaptation, qualitative relevance, and no formal conformance/national scores. |
| SUB-05 | Final evaluation artifacts | P0 / In progress | Evaluation owner (assign) | Current tests, source hashes, run hash, run audit, benchmark outputs, manual review and limits saved with dates. |
| SUB-06 | Demo script and visual evidence | P1 / Script done 8 Nov ([walkthrough](../report/DEMO_WALKTHROUGH.md)); UI not checked against new runs | Demo owner (assign) | Show incident, role differences, safety/access conflict, evidence limits, finding status, and audit trace in a short narrative. |
| SUB-07 | Team names, affiliation, leader, contact | P0 / Not started | Team lead (assign) | Replace placeholders in report and submission materials; confirm team eligibility separately. |
| SUB-08 | Final freeze | P0 / Not started | Release owner (assign) | Record commit SHA, source-manifest state, final run ID, verification outputs, report version, and demo steps. |
| SUB-09 | Demo video | P2 / Not started | Demo owner (assign) | Optional for initial submission and required if shortlisted according to project notes; record only synthetic scenario content. |

## 11. Retargeting guide: reuse the pipeline for another diagnostic AI use case

Keep the provenance, retrieval, agent/action interfaces, gates, audit logging, and evaluation harness. Change and revalidate the use-case-specific materials below. Prior metrics and source conclusions do not transfer to a new domain or jurisdiction.

| Layer | Current retinopathy demo | Example future change | Checks before reuse |
| --- | --- | --- | --- |
| Use case | Diabetic-retinopathy screening incident after model update | Radiology, pathology, or another diagnostic AI incident | Define workflow, harm pathway, existing response, and unknown facts. |
| Domain source pack | UAE/Swiss health, device, data and cyber sources plus global guidance | Current authorities for relevant device and care setting | Public primary sources, status, scope, language, date, and passage review. |
| Synthetic data | Fictional product, vendor, clinics, and case counts | Synthetic system and incident timeline | No patient data; ensure values are labeled synthetic. |
| Agents | Clinic operator, vendor, UAE/Swiss roles, adviser | Roles relevant to new incident | Verify mandate and permitted actions; do not copy authorities across jurisdictions. |
| Scenario | Eight-stage progressive incident and optional event | New stage design and negative controls | Uneven role knowledge, competing objective, trigger and counterfactual. |
| Evaluation | Curated 10-question retrieval seed and selected claim labels | New questions, gold passages, claims, and human labels | Rebuild from scratch; report denominator, reviewer, and limitations. |
| Findings | Safety/access and coordination/evidence assessments | Domain-specific governance hypotheses | Test, qualify, or reject each candidate; distinguish policy from implementation/evidence gaps. |

## 12. Prioritized work queue

### P0 — Submission-critical correctness and reproducibility

| ID | Task | Depends on | Acceptance / evidence |
| --- | --- | --- | --- |
| P0-01 | Assign named owners and fill team/contact fields | Team availability | All open P0/P1 work has a named owner; report placeholders removed. |
| P0-02 | Run current tests, source verification, final log verification, retrieval and claim audits | Stable workspace | Fresh outputs are saved with date, code revision, and actual counts; no historical result is presented as fresh. |
| P0-03 | Adjudicate final-run citations and uncited decisions | P0-02, EVAL-03 | Each legal/policy assertion shown in report/demo is supported, qualified, or removed; unsupported cases and operational uncited decisions are labeled. |
| P0-04 | Passage-level applicability matrix for report claims | SRC-01–SRC-06, EVAL-04 | Each asserted obligation has jurisdiction, actor, scope, trigger, predicate, source, and unresolved facts recorded. |
| P0-05 | Render and review five-page report | P0-03, P0-04 | Official template used; page count documented; every metric ties to a saved artifact. |
| P0-06 | Freeze report, source state, code revision, and run references | P0-02–P0-05 | Commit SHA, run ID, source count/hash result and exact demo commands recorded. |

### P1 — Evidence quality and defensible findings

| ID | Task | Depends on | Acceptance / evidence |
| --- | --- | --- | --- |
| P1-01 | Expand retrieval benchmark beyond curated seed | KB-06 | Reviewed, broader query set includes no-answer and hard-scope cases; publish misses and limits. |
| P1-02 | Expand exact claim-support review | EVAL-03 | Include known false partials and missed unsupported claims; report confusion counts only for the reviewed set. |
| P1-03 | Complete source currency and Arabic review | SRC-04–SRC-06 | Explicitly resolve or carry forward each source limitation; Arabic-derived decisive passages checked by human reviewer if available. |
| P1-04 | Improve negative-control and candidate-rejection evidence | SCN-06, COMP-09 | A reproducible no-trigger case rejects or retains insufficiency for candidate finding. |
| P1-05 | Validate global comparator passages | SRC-03, EVAL-06 | Each comparator is exact-passage grounded, relevant, and distinguished from local binding requirements. |

### P2 — Communication and future capability

| ID | Task | Depends on | Acceptance / evidence |
| --- | --- | --- | --- |
| P2-01 | Judge-facing UI walkthrough | COMP-10 | Reviewer can follow incident, role actions, evidence and limitations without reading raw JSONL. |
| P2-02 | Add second and third independently evaluated stress tests | SCN-07, SCN-08 | Each has distinct intent, expected checks, negative control, run review, and evidence; no claim before completion. |
| P2-03 | Implement deterministic replay and report figures if time permits | Stable schemas and run artifacts | Reproducible from saved inputs; distinguish replay from fresh LLM inference. |
| P2-04 | Accessibility, Arabic UI, and stakeholder usability review | Stable UI | Record evaluation method and findings before claiming usability or inclusion. |

## References and project records

- [Project README](../README.md)
- [Product specification](PRODUCT_SPEC.md)
- [Hackathon criteria audit](HACKATHON_CRITERIA_AUDIT.md)
- [Execution plan and progress log](HACKATHON_EXECUTION_PLAN.md)
- [Technical report draft](../report/technical-report-draft.md)
- [Synthetic product dossier](../report/synthetic-product-dossier-retinavision-dx.md)
- [Final integrated run review](../report/run-review-retinopathy-final-itu-criteria-20261103-4.md)
- [Retrieval seed evaluation](../report/retrieval-evaluation-seed-20261101.md)
- [Source register](../data/sources.csv)
- [ITU-T Y.3172](https://www.itu.int/rec/T-REC-Y.3172-201906-I/en)
- [ITU AI Readiness Framework Report 2.0](https://www.itu.int/epublications/publication/ai-ready-analysis-towards-a-standardized-readiness-framework)
