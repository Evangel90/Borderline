# International Telecommunication Union (ITU) Hackathon Criteria Audit

**Reviewed:** 3 November 2026. **Submission deadline:** 10 November 2026.  
**Purpose:** decide whether to run another drill now and define the evidence the technical report must contain.

## Criteria mapped to the final 8 November 2026 runs (supersedes the recommendation below)

Runs (all on code `e2a31f5`, local `qwen3:8b`): `governed-20261108-3` (Drill A), `ungoverned-20261108-2` (Drill B), `insufficient-20261108-2` (Drill C), and `governed-scripted-20261108-2` (Drill D, a scripted control for Drill A whose liaison answers are not AI decisions). "Section" means a section of `report/technical-report-draft.md`. Nothing here is a legal conclusion.

| Judging criterion (official requirements and evaluation emphasis) | Report section | Evidence from the new runs | Honest status |
| --- | --- | --- | --- |
| Healthcare AI use case with real need | Introduction; Use-case requirements | Fictional Swiss screening AI failing in Dubai; 47 synthetic missed patients; 12 institutions across the United Arab Emirates (UAE) and Switzerland | Synthetic scenario; no clinic integration |
| Relevant, structured knowledge base (KB) | Mapping table (SRC, C, PP rows); Local policy mapping | 49 artifacts verified, 2,286 chunks; 38 of 49 liaison quotes in the AI runs verified word for word (11 joined or cut quotes rejected); retrieval 8/10 hit@6 | Local KB, not ITU-hosted; Arabic text cannot be quoted |
| Agent capability and roles | What role does AI play?; Demo scenarios | 56 agent decisions in the AI runs (9 + 40 + 7), each by the institution's own AI agent from its allowed actions; separate AI liaison reviewer on 8 letters | 8B model: 10 audit flags; 8 explanations replaced by code; reviewer joins quotes and misreads questions |
| Progressive error scenarios | Error scenarios and results | Drill B's 16 staged events, including optional judge-injected step 13; step coverage shows no unconditional step skipped | Delivered branches reached only in Drill D (scripted) |
| Auditability and source attribution | What role does AI play? (code checks); Error scenarios | Four verified hash chains; decision trails name the decider of every answer; 11 joined or cut quotes rejected; a letter naming no receiver blocked | Code checks that quotes are real, not that they apply (Drill C) |
| Domain-specific policy and standards gaps with accurate global examples (critical) | Gap candidates table | CAND-001 to CAND-004 `SUPPORTED_CANDIDATE`, each with verified local and global quotes and an absence-search record | Candidates, unreviewed; 2 typed gap records came from the runs' liaison answers (B, C), both needing review |
| Data protection in practice | Error scenarios (patient data) | Recall list (A step 5) and patient images (B step 14) stopped by code's patient-data rule; in Drill D the recall list crossed only with verified quotes and a matching recorded human approval | Drill A shows the rule also stops data the scenario intended to pass |
| ITU-T Y.3172 and AI Readiness 2.0 alignment | Mapping table | Each pipeline node mapped to a component, 5 of 13 Readiness dimensions, and cited documents | Adaptation only; no conformance or readiness score |
| Reproducibility and open source | Scope and limitations; README | Exact Ollama commands in README; 167 tests pass; open-weight model, no API key needed; `make replay` reproduces every code decision in all four runs (0 differences); re-running A and D gave byte-identical logs | Replay does not re-ask the model |
| Five-page report in official template | Whole report | `report/technical-report-draft.md`; Word version drafted for review | Word version omits Scope and limitations and References to fit; page count not yet confirmed |

## Recommendation

The integrated drill has now been run against the reconciled scenario and citation-handling code: `retinopathy-final-itu-criteria-20261103-4`. Do not run another drill unless a material code or scenario change is made. Focus next on a five-page rendered report, complete citation review, team/contact details, and the submission package.

## Official submission requirements

The hackathon calls for an AI agent solution grounded in a use-case knowledge base; local policy and standards mapping; institutional, adviser, or multi-agent roles; progressively released error scenarios; and audit logs with source attribution. Evaluation emphasizes knowledge-base quality, agent capability, domain-specific policy/standards gaps with accurate global examples, auditability, and Y.3172 / AI Readiness alignment. The technical report is limited to five pages and the official template requests: introduction, use case, use-case requirements, Y.3172 and AI Readiness mappings, local-policy mapping, evaluation scenario, and gaps derived from the mapping. See the [official hackathon requirements and FAQ](https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/).

| Criterion | Evidence in Borderline | Status and remaining work |
| --- | --- | --- |
| Healthcare agentic use case | RetinaVision-DX is a fictional diabetic-retinopathy screening and referral agent; agents choose from authorized actions and sandbox handlers record synthetic state. | **Partial.** Stronger problem framing than the old report, but no real clinic/model integration. Keep all product/classification exhibits labeled fictional. |
| Relevant, structured knowledge base | 31 source-register entries plus a linked OCR derivative (32 tracked source/extraction artifacts); 1,859 AE/CH/global chunks. Source records carry provenance and hashes. `make verify-sources` passes all 32 artifacts. | **Partial.** The current 10-question retrieval seed reaches exact passage top-six in 9/10 and top-three in 8/10 cases. It is a small, curated seed, not a completeness or legal-accuracy result; more critical scenario questions should be added. |
| ITU reference ingestion / hosted distributed KB | `vendor/ITUAIReadiness` is pinned as a submodule. `make itu-smoke` successfully ingested the Y.3172 PDF (50 chunks plus 19 framework definitions) into a separate throwaway local index. The active Borderline index is custom hybrid retrieval in local Chroma. | **Partial.** Reference-code ingestion is demonstrated, but it is not the active Borderline KB and is not hosted in the ITU Lab or distributed. Do not claim hosted deployment. State the local prototype boundary and use sandbox deployment only if access is available. |
| Agent roles and coordination | YAML assigns distinct roles, private event views, authorized actions and staged participation across health, vendor, data, cyber and device-safety actors. | **Partial.** Final run `retinopathy-final-itu-criteria-20261103-4` completed 32 decisions with two governance assessments; all recorded actions were authorized. The audit found 14 decisions without citations and two DHA citations needing review; see its run review. |
| Progressive error scenario | The intent releases the update, false-negative signal, cyber suspicion, secondary data use, regulator request, safety tradeoff and follow-up review in sequence; an optional reserve event exists. | **Implemented in simulation.** The fictional letter establishes classification only within the drill; real-world classification and authorization remain unknown. |
| Auditability | Logs record visible event facts, selected action, citations, rationale, tool outcome, state changes and hash links; human review is separately logged. | **Partial.** Hash chain verifies. Private model chain-of-thought is neither requested nor stored; the product exposes structured rationales and evidence traces instead. Human approver identity is self-entered and unauthenticated. No external action is connected. |
| Domain-specific gaps and global examples | The latest run emits an objective-conflict assessment and an evidence-deficiency assessment. | **Partial.** Both are marked `INSUFFICIENT_EVIDENCE`; the latter has a broad global benchmark statement that is not yet passage-level validated. The six themes in the old report are candidates, not findings. Convert only supported issues into gap claims and compare each with a specific, verified global example. |
| Public repo / reproducibility | Git repository, source register, make targets, local run records, reference-code submodule. | **Partial.** Reproduction depends on the local model/index and environment. Add exact setup/run commands, source verification, index/model requirements, and a clean final run ID to the report. |
| Five-page technical report | `report/technical-report-draft.md` follows the official section order and maps the pipeline, all six factors and 13 dimensions. The official DOCX template was retrieved and reviewed. | **Draft, not final.** The report is about 1,800 words; no rendered page-count check is available yet. Team/contact fields and passage-level review of gap comparisons remain open. |

## Y.3172 mapping: healthcare adaptation, not conformance

Y.3172 defines an ML pipeline and management/orchestration functions for future networks. Borderline can map concepts to its software path, but it is not a telecom-network implementation and must not claim conformance. The official standard describes the SRC, collector (C), pre-processor (PP), model (M), policy (P), distributor (D), SINK, ML function orchestrator and ML sandbox components ([ITU-T Y.3172](https://www.itu.int/rec/T-REC-Y.3172-201906-I/en)).

| Y.3172 concept | Borderline realization | Limitation to disclose |
| --- | --- | --- |
| ML Intent | `intents/retinopathy-ae-ch.yaml`: use case, stages, actors, private views and action scopes. | Declarative scenario is adapted to a policy drill; no network service intent is deployed. |
| SRC | Synthetic incident facts plus registered source PDFs and their metadata. | No patient images, live clinic data or device telemetry enter the drill. |
| C | Source ingestion and hybrid lexical/vector retrieval in `engine/knowledge.py`. | The active pipeline is local and does not use a distributed ITU-hosted KB. |
| PP | PDF text/OCR extraction, chunking and provenance metadata. | Arabic OCR/extraction and English translation passages require human review for consequential interpretation. |
| M | Configured AI agent, backed by `qwen3:8b` in the latest local run, proposes an action and structured explanation. | No model fine-tuning; no clinical performance is measured. |
| P | Role/action allow-lists, citation triage, bridge/gate checks and human-approval state. | Not a general Y.3172 policy node; legal logic remains incomplete and some gates are configured rules. |
| D / SINK | Orchestrator dispatches the chosen action to a synthetic action handler, which records state and outcome. | No real clinical action, API, device or regulator message is executed. |
| MLFO / Sandbox | `engine/orchestrator.py` sequences agents and events; local run runtime contains synthetic state. | Staged times are labels, not a clock; no hosted ITU sandbox run is evidenced. |

## AI Readiness Framework 2.0 crosswalk

The ITU report describes six readiness factors and 13 dimensions, with domain-specific metrics rather than a universal maturity score. Borderline is a diagnostic AI governance stress test, **not a national readiness assessment**. Do not invent readiness scores. The statuses below record only what this prototype demonstrates.

| ITU factor | Borderline evidence | Current evidence status |
| --- | --- | --- |
| Data | Provenance-bearing policy sources and synthetic incident records; no patient dataset. | **Partial:** source traceability yes; clinical data availability/quality/representativeness not assessed. |
| Research | Simulated collaboration among AI, clinical, regulatory and policy roles. | **Not evidenced:** no actual domain/AI researcher collaboration or validation panel. |
| Deployment Support | Local software, local model, retrieval index and synthetic run. | **Partial:** no clinic infrastructure, service integration, hosted sandbox or deployment readiness assessment. |
| Standards | Y.3172 concept mapping, traceable policy sources and audit format. | **Partial:** adaptation only; no conformance assessment or independent standards review. |
| Open source and Code | Public repository and pinned MIT-licensed ITU reference submodule. | **Partial:** code is present; the active KB path and contribution process are not integrated with ITU tooling. |
| Sandbox Environments | Isolated synthetic actions, staged scenarios, human decision form. | **Partial:** local sandbox only; no ITU-hosted run or validation with a real/representative deployment environment. |

| Dimension (ITU AI Ready 2.0) | Evidence / gap |
| --- | --- |
| 1. Data/model Marketplace | Not implemented or measured; the KB is a source pack, not a data/model marketplace. |
| 2. Generated Content Marketplace | Not implemented; generated rationales are outputs, not an ecosystem or exchange mechanism. |
| 3. Cross-domain correlation analysis | Multi-role evidence is sequenced, but no cross-dimensional correlation analytics are implemented. |
| 4. Contextualization and Regional Impact | Dubai/UAE clinical scenario with Swiss vendor and UAE/Swiss policy packs; no local stakeholder validation or impact measurement. |
| 5. Level of Integration of AI in Workflows | Referral and clinic workflow consequences are modeled; no hospital-system integration or outcome measurement. |
| 6. Human Interface | Streamlit viewer and review form exist; accessibility, Arabic UI and usability are not evaluated. |
| 7. Strategy Alignment | UAE and Swiss strategies/policies are in the KB; no explicit measurable strategy-to-scenario mapping yet. |
| 8. Collaboration with AI | Human review and simulated approval are represented; approval is not authenticated, and collaboration quality is not measured. |
| 9. Impacts of Humans in AI Integration | False-negative and access tradeoff are represented; patient/clinician impacts are synthetic and not quantitatively measured. |
| 10. AI & Policies | Central use case: policy sources and roles are mapped; legal applicability, completeness and gap claims remain under review. |
| 11. AI for Inclusion | Not assessed; no subgroup performance, accessibility or gender/language inclusion metrics. |
| 12. Granular Priorities | Retinopathy screening and Dubai context are specified; no regional fine-tuning or priority-setting mechanism. |
| 13. Digital Infrastructure | Camera, cloud/vendor and clinic workflow appear as scenario assumptions; no infrastructure, connectivity, compute or energy metrics. |

The factor and dimension names above follow the official [ITU AI Readiness Framework Report 2.0](https://www.itu.int/epublications/publication/ai-ready-analysis-towards-a-standardized-readiness-framework). The local copy is registered and hash-verified. These mappings are prototype-level relevance statements, not measured country scores.

## Final run and report sequence

1. Reconcile the classification status everywhere: it is established only by a fabricated EDE letter inside the drill; real device status is unknown.
2. Update the five-page report to the official template, including the use-case requirements and node-by-node Y.3172 / local-policy / AI Readiness table.
3. Select two or three gap claims from the latest assessments; verify each against primary local evidence and a specific global example. Label unsupported items as evidence needs, not policy gaps.
4. Current retrieval evaluation returns 9/10 exact passages in top six and 8/10 in top three. Expand it with questions for under-retrieved statutory predicates and global comparisons.
5. The final integrated run is `retinopathy-final-itu-criteria-20261103-4`; hash chain and action authorization checks passed. The screen flags 14 decisions without citations and two DHA citations for review. The DHA passages support scope/context only; they do not establish an incident-specific duty or facility applicability. See the run review.
6. Freeze the report, repository commit, run ID, source manifest and demo steps. Render the technical report to confirm it is no more than five pages. Team/contact details and any ITU Sandbox credentials remain external inputs.

The hackathon page states that the final submission is due 10 November 2026 and asks for a maximum-five-page technical report, the GitHub repository and a policy/strategy knowledge base; demo video is optional for submission but required if shortlisted. The official template download was retrieved for local review but is not checked into the repository.
