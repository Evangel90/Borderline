# AI for Good Sandbox Hackathon: United Arab Emirates — Borderline

**Cross-border incident response for medical AI**

**Team:** Borderline · **Team leader:** Oladipo Evangel · **Members:** Oladipo Evangel, Professor James Agajo
**Contact:** [oladipoevangel90@gmail.com](mailto:oladipoevangel90@gmail.com), +2348135001380 · **GitHub:** [github.com/Evangel90/Borderline](https://github.com/Evangel90/Borderline/tree/incident-drill) (branch `incident-drill`)
**Status:** draft, 8 November 2026. Results come from four runs on commit `b229477` (listed under Error scenarios); Drill D's liaison answers are scripted, **not AI decisions**. Nothing here is a legal conclusion or has had legal review; policy gaps are **candidates**.

## Introduction

When a medical AI made in one country fails in another, both countries' regulators, data-protection authorities and cyber agencies must share information fast, under different laws, each seeing part of the picture. Borderline is a multi-agent drill engine that rehearses this response in advance, recording which institution AI agent decided what, which letters may legally cross the border, and where the rules run out.

Use case: RetinaVision-DX, a fictional diabetic-retinopathy screening AI from a fictional Swiss vendor, used at fictional Dubai clinics. An update pushed from a compromised vendor account misses referable disease in 47 synthetic patients; UAE retinal images held in Zurich were reused for retraining. The jurisdictions are the United Arab Emirates (UAE) and Switzerland (CH). Facts are synthetic; policy sources are real, public and registered with file hashes.

## What role does AI play?

Three decision-makers take part, and each log entry names which one decided: **institution AI agents**, an **AI liaison reviewer**, and **code**. People decide whatever the drill flags.

**Local language models.**

- `qwen3:8b` (open-weight, 8 billion parameters) makes every AI decision, on a laptop through Ollama: no application programming interface (API) key, and nothing leaves the machine. Temperature 0 (always the most likely next word) makes the same inputs give the same log. Context is 16,384 tokens; code refuses an oversized prompt rather than let it be truncated.
- Search combines keywords with a local multilingual embedding model (`paraphrase-multilingual-MiniLM-L12-v2`, through fastembed).
- Two roles:
  1. **12 institution AI agents.** UAE: Dubai Health Authority (DHA), Ministry of Health and Prevention (MoHAP), Emirates Drug Establishment (EDE), UAE Data Office, UAE cyber incident coordination, the screening service and the clinic operator. Switzerland: Swiss Agency for Therapeutic Products (Swissmedic), Federal Data Protection and Information Commissioner (FDPIC), National Cyber Security Centre (NCSC) and the vendor. Neutral: a policy adviser. Each stateless call picks one action and cites its reasons.
  2. **An AI liaison reviewer**, separate from the sender, answers three questions for every cross-border letter (legal basis to share? transfer allowed under both sides' rules? right counterpart?) with YES, NO or UNCLEAR and exact quotes.
- The model is swappable by one setting; at this size it joins quotes and misreads questions (see results).

**Context provided by the knowledge base (KB).**

- 49 hashed files (26 UAE, 9 Swiss, 14 global; see SRC below) split into 2,286 passages, each with document, page, language, binding status and an ID such as `CH-HEALTH-TPA:p40:c1`.
- An agent sees only its institution's view, mandate and allowed actions, and passages from its own country plus global guidance (the adviser sees both countries); it may cite only these. The reviewer sees passages searched per country, the provision the letter relies on, and any drill exhibits (labelled synthetic documents).
- Gaps are recorded, not guessed (garbled Arabic is not quoted; a missing document becomes homework). Retrieval puts the exact passage in the top six for 8 of 10 test questions.

**Policy guidelines to be applied**, at three levels:

1. **Mandates:** an agent may choose only its institution's listed actions (DHA, for example: open a clinical incident review, request a patient follow-up review). Profiles are simulations, not official positions.
2. **Cross-border law, through the three questions:** legal basis (Swiss Therapeutic Products Act (TPA) Art. 64; Federal Act on Data Protection (FADP) Art. 55); transfer rules (UAE Federal Law No. 2 of 2019 Art. 13; FADP Art. 16); counterpart (pairs in [`packs/bridge/ae-ch.yaml`](../packs/bridge/ae-ch.yaml)).
3. **Rules enforced by code, not AI:**
   - A quote must appear word for word in a shown passage; up to two character slips (wrong, missing or extra characters, spaces included) are accepted, and the exact source text is logged. A fabricated, joined or uncited quote makes the answer UNCLEAR. A real quote under the wrong chunk ID is relabelled only if its text is in exactly one shown passage.
   - A legal-basis YES needs national law, not global guidance or a drill exhibit.
   - Patient data needs two keys: verified national-law quotes behind YES on legal basis and transfer rules, and a recorded human approval matching the letter's scope.
   - A letter with no receiver is blocked; delivery needs three YES answers, each flagged for human review.
   - An uncited legal claim in an agent's explanation is returned once, then replaced by fixed wording or a review action, and logged.
   - Every UNCLEAR or NO is typed `policy_gap`, `implementation_gap`, `conflict` (possible gap candidates) or `missing_evidence` (homework).

## Use-case requirements

- It is **critical** that every claim has an exact, code-verified quote and chunk ID, and that no output is presented as a legal conclusion.
- It is **critical** that patient data never crosses the border without verified legal-basis and transfer-rules quotes and a recorded human approval.
- It is **critical** that each institution acts only on what it sees, within its mandate, and that the log shows who decided.
- It is **expected** that missing documents become homework, not proof of absence, and that each gap candidate has a verified global comparison.
- It is **of added value** that the engine is country-agnostic: country packs, a bridge pack and drill intents are plain YAML (a readable configuration format) and can be swapped.

## Demo scenarios: three AI drills and one scripted control

| Drill | What it tests | Steps | Expected | Actual (8 November 2026) |
|---|---|---|---|---|
| A, governed (`retinopathy-governed`) | 3 letters written to real provisions, assurances as labelled synthetic exhibits: EDE → Swissmedic vigilance request (TPA Art. 64(1)); Swissmedic → EDE recall list of 47 patients (TPA Art. 64(2)(c)), with a recorded human approval; UAE Data Office → FDPIC on staff data (FADP Art. 55) | 11 | 3 delivered | **0 delivered**: legal basis YES each time, but one question misread and joined quotes rejected by code |
| B, ungoverned (`retinopathy-ae-ch`, optional step 13) | Staged incident, 12 institutions; DHA tries to send patient images to Switzerland | 16 | letters blocked with typed gaps; images stopped | 4 of 4 blocked, plus a letter with no receiver blocked by code; images stopped; 1 typed gap (`policy_gap`); 8 homework items |
| C, insufficient evidence (`retinopathy-insufficient-evidence`) | Questions whose deciding document is missing | 8 | homework, not candidates | **Not as expected**: letter blocked, but answers typed `policy_gap` and `implementation_gap`; no homework |
| D, scripted control for A (`--reviewer scripted`) | A's letters, with hand-written reference answers replacing the AI reviewer: do A's blocks come from the AI or from law and code? Agents still AI; code checks unchanged | 11 | 3 delivered if law and code allow | 3 delivered; not an AI result |

## Mapping to ITU-T Y.3172 and the AI Readiness Framework 2.0

Y.3172 is the International Telecommunication Union (ITU) architecture for machine learning (ML) in future networks; Borderline borrows its pipeline vocabulary, is **not a telecom implementation and claims no conformance**. Of the 13 Readiness 2.0 dimensions we claim relevance (not measured scores) to five: (4) Contextualization and Regional Impact; (5) Level of Integration of AI in Workflows; (7) Strategy Alignment; (8) Collaboration with AI; (10) AI & Policies.

| Y.3172 node | Borderline element | Readiness 2.0 dimension | Policy documents (examples, with chunk IDs) |
|---|---|---|---|
| SRC (source) | Staged synthetic events; 49 files hashed in [`data/sources.csv`](../data/sources.csv) (26 UAE, 9 Swiss, 14 global), re-verified 8 November 2026 | 4 | UAE Federal Law No. 2 of 2019 (Health Data Law), Art. 13 (`AE-HEALTH-ICT-LAW-2019:p8:c1`); TPA Art. 64 (`CH-HEALTH-TPA:p40:c1`) |
| C (collector) | `make verify-sources`, `make ingest`; absence searches logged in [`gaps/searches/`](../gaps/searches) | 10 | International Medical Device Regulators Forum (IMDRF) N14 incident-exchange participant list (`IMDRF-NCAR-N14-2025:p16:c1`) |
| PP (pre-processor) | 2,286 chunks with provenance; garbled Arabic detected and kept out of quoting | 4 | Federal Decree-Law 38/2024 official Arabic: registered, excluded (defective text layer) |
| M (model) | 12 institution agents and the AI liaison reviewer; `qwen3:8b`, temperature 0, stateless calls | 8 | Institution profiles in [`packs/ae/institutions/`](../packs/ae/institutions), [`packs/ch/institutions/`](../packs/ch/institutions), [`packs/global/institutions/`](../packs/global/institutions) |
| P (policy) | Code: action allow-lists, quote check, patient-data rule, three-YES routing, human-review flag | 10, 7 | FADP Art. 55 (`CH-DATA-FADP:p24:c1`); Personal Data Protection Law (PDPL) health-data exclusion (`AE-DATA-PDPL-2021-EN:p6:c2`) |
| D (distributor) | Synthetic action handlers; letters delivered or blocked in drill state only | 5 | [`packs/bridge/ae-ch.yaml`](../packs/bridge/ae-ch.yaml) (counterparts, reference answers) |
| SINK | Hash-chained log, decision trails, homework list, gap register | 8 | Decision trails for drills [A](decision-trail-governed-20261108-4.md), [B](decision-trail-ungoverned-20261108-3.md), [C](decision-trail-insufficient-20261108-3.md), [D](decision-trail-governed-scripted-20261108-3.md) |

## Requirements mapped to domain-specific policies

Each node's requirement is mapped to health-sector AI policy in the KB (exact, script-verified quotes; brackets give the text's type). A mapping shows that a text addresses the requirement, not that it applies to these synthetic facts.

| Node | Requirement in this use case | Domain-specific policy (type) and exact quote |
|---|---|---|
| SRC | An AI failure seen at the clinic must reach the responsible bodies in both countries | DHA AI in Healthcare policy (DHA policy): "Report to DHA-HRS all known or suspected incidents or deficiencies related to AI solutions used in their respective healthcare facility." (`AE-DHA-AI-HEALTH-2021:p12:c1`; DHA-HRS: DHA's Health Regulation Sector). Swiss Medical Devices Ordinance (MedDO) Art. 66: manufacturers report "any serious incidents involving the device in question that have occurred in Switzerland, as soon as they become aware of them" (`CH-HEALTH-MedDO:p28:c1`). Drills A and B test how a Dubai incident reaches Swissmedic. |
| C | Every source and decision is traceable to its origin | IMDRF good machine-learning practice, N88 (global, advisory): "design processes that can appropriately record and communicate decisions and rationale, as well as ensure traceability, reproducibility, data authenticity" (`IMDRF-AIML-N88-2025:p6:c2`) |
| PP | Retinal images are processed in Zurich, outside the UAE | Health Data Law Art. 13 (UAE law), quoted under Local policy mapping (`AE-HEALTH-ICT-LAW-2019:p8:c1`); its exceptions are in Resolution 51/2021, not obtained (CAND-004). |
| M | A model update is controlled, and real-world results are compared with validation | DHA AI policy: "Comply with all required certification of the AI software and its major upgraded versions from recognized international/local agencies." (`AE-DHA-AI-HEALTH-2021:p10:c1`) and "actual outcomes must be compared to those obtained in training and validation. Any significant discrepancies must call for further inspection." (`AE-DHA-AI-HEALTH-2021:p10:c1`). IMDRF N88 (advisory): "Clinical evaluation includes the use of datasets that are representative of the intended patient population" (`IMDRF-AIML-N88-2025:p7:c2`) |
| P | Humans keep oversight; failures can be traced and controlled | UAE Charter for the Development and Use of AI, 2024 (charter): "the irreplaceable value of human judgment and human oversight over AI" (`AE-AI-CHARTER-2024:p4:c1`). DHA AI policy: "AI solution developers must build systems whose failures can be traced, diagnosed, and controlled." (`AE-DHA-AI-HEALTH-2021:p7:c1`) |
| D | A failing tool can be stopped safely, and adverse events are passed on | DHA AI policy: "AI tool must be equipped with “Graceful Degradation” mechanisms by means of automatic alerts and gradual operation cessation abilities" (`AE-DHA-AI-HEALTH-2021:p10:c1`) and "Adverse events should be timely reported to relevant oversight bodies for appropriate investigation and action." (`AE-DHA-AI-HEALTH-2021:p11:c1`) |
| SINK | Results are audited; performance is judged for clinician and AI together | DHA AI policy: "Conduct regular audits of AI functionality by independent third party, and reporting to DHA-HRS as needed." (`AE-DHA-AI-HEALTH-2021:p13:c1`). IMDRF N88 (advisory): "including the performance of the human-AI team, rather than just the device in isolation." (`IMDRF-AIML-N88-2025:p7:c2`) |
| Strategy alignment | Both countries work to compatible aims | UAE AI Charter: "serves as a guiding framework to protect the rights of the UAE community in the development or use of AI solutions and technologies." (`AE-AI-CHARTER-2024:p2:c1`). **No Swiss AI strategy is in the KB**, so alignment could not be mapped. |

## Local policy mapping

Each liaison question is answered from registered texts, for example:

- **UAE, health data leaving the country:** "It is not permissible to store, process, generate or transform the health data and information outside State -which are related to the health services provided inside State- except in the case where a resolution is issued from the Health Authority in coordination with the Ministry." (`AE-HEALTH-ICT-LAW-2019:p8:c1`)
- **Switzerland, regulator-to-regulator data:** "The FDPIC may exchange information or personal data with foreign authorities that are responsible for data protection in order that they may fulfil their respective statutory duties in relation to data protection, provided the following requirements are satisfied: a. Reciprocity with regard to administrative assistance is guaranteed." (`CH-DATA-FADP:p24:c1`)

The PDPL excludes "e. Personal Health Data that has legislation regulating its protection and processing." (`AE-DATA-PDPL-2021-EN:p6:c2`), so the Health Data Law governs patient images and the PDPL covers clinic staff data. Only official English translations were searchable; extracted Arabic is garbled, so none was quoted or retyped. Resolution 51/2021 (the Art. 13 exceptions) is registered as unobtainable after documented attempts and was not searched for again.

## Error scenarios and results

Drill B releases staged events: a model update with fewer referrals, confirmed missed disease, a compromised vendor account, retraining on UAE images in Zurich, the vendor's "research" claim, letters to Swiss authorities, a suspend-or-continue dispute, an optional judge-injected insurer claim, and DHA's attempt to send patient images.

| Run | Decisions | Hash chain | Letters delivered / sent | Quotes verified | Audit-screen flags | Homework |
|---|---|---|---|---|---|---|
| A `governed-20261108-4` | 9 | verified | 0 / 3 | 10 of 13 | 1 | 5 |
| B `ungoverned-20261108-3` | 40 | verified | 0 / 5 | 24 of 30 | 8 | 8 |
| C `insufficient-20261108-3` | 7 | verified | 0 / 1 | 6 of 6 | 1 | 0 |
| D (scripted, not AI) `governed-scripted-20261108-3` | 11 | verified | 3 / 3 | 21 of 21 | 2 | 0 |

**Decisions:** institution-agent actions logged. **Quotes verified:** liaison-reviewer quotes that code found in the passages shown. **Audit-screen flags:** agent citations that the citation screen (`make audit-evidence`) marks as missing or needing review. **Homework:** `missing_evidence` items. All four runs also **replay with 0 differences**: re-running every code decision over the logged AI answers, without the model, gives the same outcomes. Logs and a step-by-step reproducibility guide are in the repository's [README](../README.md#reproducibility-guide).

What the runs show:

- **Patient data crossed only with both keys.** Code stopped the recall list (A step 5) and patient images (B step 14). In D the recall list crossed with verified legal-basis quotes and a matching recorded human approval (a drill fact).
- **The AI reviewer delivered no governed letter** (a result, not forced). It found the right provisions and said YES on legal basis each time, but answered UNCLEAR on transfer rules for a letter with no personal data (step 2: "The passages do not include the document you would need to determine transfer rules"), and joined text from two places at steps 5 and 8 (TPA Art. 64(1)'s opening with Art. 64(2); PDPL Art. 2(1)'s opening with item (c), skipping (a) and (b)), which code rejected. With reference answers (D) all three were delivered: the blocks come from the AI review, not from the law or code.
- **Joined and cut quotes rejected; copy slips accepted.** 6 of B's 30 quotes failed: TPA Art. 64's heading joined to paragraph 2; "The Office shall: 9." skipping items 1 to 8; a quote cut with "..."; a two-word fragment. A dropped space ("ProperProtection", B step 9) and a character slip (A step 5) were accepted, with the exact source text logged.
- **Delivered is not accepted.** In D the FDPIC's AI agent, on receiving the step 8 letter, recommended pausing under FADP Art. 16 (general foreign disclosure), not Art. 55, which the letter relied on.
- **No receiver, no letter.** Code blocked DHA's request at B step 13, which named no receiver, since the three questions cannot be asked.
- **Typed gaps where homework was expected.** In C the reviewer typed UNCLEAR answers `policy_gap` (legal basis, quoting the UAE Data Office's competences) and `implementation_gap` (transfer rules, quoting four real but unrelated FADP passages, such as Art. 15 on a representative's duties). Code checks that quotes are real, not that they apply.
- **Coverage and reproducibility.** Blocked branches ran in A, B and C; delivered branches (steps 3, 6, 9) only in D; no step failed. Re-running all four after one quote-check change gave byte-identical logs for A, C and D; B differed only in the two quotes the change accepts.

Details: [`run-review-2026-11-08-final-runs.md`](run-review-2026-11-08-final-runs.md).

## Policy and standards gap candidates derived from the mapping

All four candidates in [`gaps/candidate_register.yaml`](../gaps/candidate_register.yaml) pass the four-part rule (`make assess-candidates`, 8 November 2026): quotes verify; an absence search is recorded; a verified global comparison (European Union (EU), IMDRF) is quoted; no obtainable missing document could refute it. They are **candidates, not findings**: unreviewed, and "absent" means absent from this KB.

| ID | Type | Local evidence (verified quote) | Global comparison (verified quote) |
|---|---|---|---|
| CAND-003 | standards | Switzerland: "However, without resolving the institutional issues, Switzerland remains excluded from market surveillance with EU member states for medical devices." (`CH-EU-MRA-FACTSHEET-2025:p2:c2`). Neither country is an IMDRF National Competent Authority Report (NCAR) exchange participant (search [`SEARCH-NCAR-PARTICIPANTS-001`](../gaps/searches/SEARCH-NCAR-PARTICIPANTS-001.json)). | "Participation in the NCAR Exchange Program will be limited to the IMDRF Management Committee (MC) Regulators. A list of NCAR Participant Countries is provided in Annex1." (`IMDRF-NCAR-N14-2025:p9:c1`) |
| CAND-002 | policy | DHA's AI policy requires certification of "major upgraded versions" without defining them (`AE-DHA-AI-HEALTH-2021:p10:c1`; full quote under node M above) | "Changes to the approved device shall require approval from the notified body which issued the EU technical documentation assessment certificate where such changes could affect the safety and performance of the device" (`EU-MDR-2017-745:p202:c1`) |
| CAND-001 | implementation | The PDPL's health-data exclusion (`AE-DATA-PDPL-2021-EN:p6:c2`, quoted under Local policy mapping) leaves no UAE authority clearly competent to protect UAE health data held abroad. | The Organisation for Economic Co-operation and Development (OECD) 2007 privacy-enforcement Recommendation has 38 adherents, Switzerland among them and no non-members: "Spain Sweden Switzerland Türkiye United Kingdom United States Non-Members None" (`OECD-LEGAL-0352-ADHERENTS-2026:p8:c1`) |
| CAND-004 | policy | The Art. 13 exceptions are in a resolution the project could not obtain: "a. Cabinet Decision No. (51) of year 2021 on exemption for storage and transfer of health records and information must be abide to:" (`AE-DHA-HEALTH-DATA-PROTECTION-PP11-2022:p27:c1`) | By analogy only, EU national derogations are published: "The Commission shall keep the information publicly available." (`EU-MDR-2017-745:p30:c1`) |

The drills bear on, but do not prove, these candidates. Their two typed gap records (B: UAE Data Office transfer rules, `policy_gap`, quoting PDPL Art. 23; C: see results) need human review.

## References

- ITU AI for Good Sandbox Hackathon, UAE: [https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/](https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/)
- ITU-T Y.3172: [https://www.itu.int/rec/T-REC-Y.3172-201906-I/en](https://www.itu.int/rec/T-REC-Y.3172-201906-I/en)
- ITU AI Ready, Report 2.0: [https://www.itu.int/epublications/publication/ai-ready-analysis-towards-a-standardized-readiness-framework](https://www.itu.int/epublications/publication/ai-ready-analysis-towards-a-standardized-readiness-framework)
- Source register [`data/sources.csv`](../data/sources.csv); run review [`report/run-review-2026-11-08-final-runs.md`](run-review-2026-11-08-final-runs.md); decision trails [`decision-trail-governed-20261108-4.md`](decision-trail-governed-20261108-4.md), [`decision-trail-ungoverned-20261108-3.md`](decision-trail-ungoverned-20261108-3.md), [`decision-trail-insufficient-20261108-3.md`](decision-trail-insufficient-20261108-3.md), [`decision-trail-governed-scripted-20261108-3.md`](decision-trail-governed-scripted-20261108-3.md); candidate status [`report/candidate-status.json`](candidate-status.json).
