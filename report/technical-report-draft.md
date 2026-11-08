# AI for Good Sandbox Hackathon: United Arab Emirates — Borderline

**Team:** Borderline · **Team leader:** Oladipo Evangel · **Members:** Oladipo Evangel, Professor James Agajo
**Contact:** [oladipoevangel90@gmail.com](mailto:oladipoevangel90@gmail.com), +2348135001380 · **GitHub:** [github.com/Evangel90/Borderline](https://github.com/Evangel90/Borderline/tree/incident-drill) (branch `incident-drill`)
**Status:** submission draft, 8 November 2026. All results come from four runs on 8 November 2026, all on the same code (commit `b229477`) and model: A `governed-20261108-4`, B `ungoverned-20261108-3`, C `insufficient-20261108-3`, and D `governed-scripted-20261108-3`, a scripted control whose liaison answers are **not AI decisions**. Nothing in this report is a legal conclusion; no person with legal standing has reviewed it. Policy gaps are called **candidates**.

## Introduction

When a medical AI product made in one country fails in another, the regulators, data-protection authorities and cyber agencies of both countries must exchange information quickly. Each of them works under different laws, and none sees the whole picture. Borderline is a multi-agent drill engine that rehearses this cross-border response before a real incident happens. It records three things: which institution AI agent decided what, which letters may legally cross the border, and where the rules run out.

The use case is a fictional diabetic-retinopathy screening service, RetinaVision-DX. It is made by a fictional Swiss vendor and used at fictional Dubai clinics. A model update misses referable disease in 47 synthetic patients. The update was pushed from a compromised vendor account, and UAE patients' retinal images held in Zurich were reused for retraining. The jurisdictions are the United Arab Emirates (UAE) and Switzerland (CH). All scenario facts are synthetic; all policy sources are real, public and registered with their file hashes.

## What role does AI play?

Three kinds of decision-maker take part, and every log entry records which one decided: **institution AI agents**, an **AI liaison reviewer**, and **code**. People make the final decision on anything the drill flags; nothing it produces is a legal conclusion.

**Local language models.**

- Every AI decision is made by `qwen3:8b`, an open-weight model with 8 billion parameters, run on the team's laptop through Ollama. No application programming interface (API) key is needed, and no prompt, passage or synthetic patient fact leaves the machine.
- Temperature is 0, so the model always picks its most likely next word: the same inputs give the same log. The context window is 16,384 tokens, and code refuses to send a prompt that would not fit rather than let it be cut silently.
- Search uses a small multilingual embedding model (`paraphrase-multilingual-MiniLM-L12-v2`, through fastembed), also local, combined with keyword matching.
- The model plays two roles:
  1. **Institution AI agents**, one per institution, 12 in all. **UAE:** the Dubai Health Authority (DHA), the Ministry of Health and Prevention (MoHAP), the Emirates Drug Establishment (EDE), the UAE Data Office, UAE cyber incident coordination, the screening service and the clinic operator. **Switzerland:** the Swiss Agency for Therapeutic Products (Swissmedic), the Federal Data Protection and Information Commissioner (FDPIC), the National Cyber Security Centre (NCSC) and the vendor. **Neutral:** a policy adviser. Each call is stateless: the agent chooses one action and explains it with citations.
  2. **An AI liaison reviewer**, a separate call that is not the sender. For every cross-border letter it answers three questions (is there a legal basis to share; is the transfer allowed under both sides' rules; is the receiver the right counterpart) with YES, NO or UNCLEAR, each backed by exact quotes.
- One setting swaps the model. The 8-billion-parameter model is a limitation: it joins quotes and misreads questions (see the results).

**Context provided by the knowledge base (KB).**

- 49 registered source and extraction files (26 UAE, 9 Swiss, 14 global), each hashed in [`data/sources.csv`](../data/sources.csv), split into 2,286 passages. Each passage keeps its document, page, language and binding status, and an ID such as `CH-HEALTH-TPA:p40:c1`.
- An agent sees only its institution's view of the event, its mandate and allowed actions, and passages retrieved from its own country's texts plus global guidance; the neutral adviser sees both countries. It may cite only passages it was shown.
- The reviewer sees passages searched separately for each country, plus the provision the letter says it relies on and any drill exhibits (synthetic documents labelled as such).
- What the KB cannot provide is recorded, not guessed. Garbled Arabic text is kept out of quoting; Resolution 51/2021 is registered as unobtainable; a missing document becomes homework. Retrieval finds the exact passage in the top six results for 8 of 10 test questions.

**Policy guidelines to be applied.** Policy is applied at three levels:

1. **Institution mandates:** each agent may choose only actions listed in its institution's profile. For example, DHA's include opening a clinical incident review and requesting a patient follow-up review. The profiles are simulations, not official positions.
2. **Cross-border law, through the three liaison questions:** legal basis (for example, Swiss Therapeutic Products Act Art. 64, Federal Act on Data Protection Art. 55); both sides' transfer rules (UAE Federal Law No. 2 of 2019 Art. 13; Federal Act on Data Protection Art. 16); counterpart (the pairs configured in [`packs/bridge/ae-ch.yaml`](../packs/bridge/ae-ch.yaml)).
3. **Drill rules enforced by code, not AI:**
   - every quote must appear word for word in a passage that was shown, allowing at most two character slips (a wrong, missing or extra character, including a space), with the exact source text logged; a fabricated, joined or uncited quote turns the answer into UNCLEAR;
   - a real quote with the wrong chunk ID is moved to the right passage only if its text occurs in exactly one shown passage;
   - a legal-basis YES must rest on national law, never on global guidance or a drill exhibit;
   - patient data crosses only with two keys: verified national-law quotes behind YES on legal basis and transfer rules, and a recorded human approval whose scope matches the letter;
   - a letter naming no receiver is blocked, and a letter is delivered only on three YES answers, each flagged for human review;
   - an agent's explanation that makes a legal claim without a citation is sent back once; if it still fails, code substitutes fixed wording or a review action, and the log says so.

   Every UNCLEAR or NO is typed `policy_gap`, `implementation_gap`, `conflict` or `missing_evidence`. Only the first three can become gap candidates; `missing_evidence` goes to a homework list.

## Use-case requirements

- It is **critical** that every claim carries an exact quote with its chunk ID, verified by code, and that no output is presented as a legal conclusion.
- It is **critical** that patient data never crosses the border without a verified legal-basis quote, a verified transfer-rules quote and a recorded human approval for that disclosure.
- It is **critical** that each institution acts only on what it can see and only within its mandate, and that the log shows who decided what.
- It is **expected** that missing documents are recorded as homework, not treated as proof that a rule is absent, and that each gap candidate is paired with a verified global comparison.
- It is **of added value** that the engine is country-agnostic: country packs, a bridge pack and a drill intent are plain YAML (a readable configuration format) and can be swapped.

## Demo scenarios: three AI drills and one scripted control

| Drill | What it tests | Steps | Expected | Actual (8 November 2026) |
|---|---|---|---|---|
| A, governed (`retinopathy-governed`) | Three letters written to the conditions of a real provision, with the senders' assurances as labelled synthetic exhibits: EDE → Swissmedic vigilance request (Therapeutic Products Act (TPA) Art. 64(1)); Swissmedic → EDE recall list of 47 patients (TPA Art. 64(2)(c)), with a recorded human approval; UAE Data Office → FDPIC on staff data (Federal Act on Data Protection (FADP) Art. 55) | 11 | 3 delivered | **0 delivered**: the reviewer said YES on legal basis each time, but misread one question and joined quotes from two places, which code rejected |
| B, ungoverned (`retinopathy-ae-ch`, with optional step 13) | Progressive incident with 12 institutions; DHA tries to send patient images to Switzerland | 16 | letters blocked with typed gaps; images stopped | 4 of 4 blocked; a fifth letter, naming no receiver, blocked by code; images stopped; 1 typed gap (`policy_gap`); 8 homework items |
| C, insufficient evidence (`retinopathy-insufficient-evidence`) | Questions whose deciding document is missing | 8 | homework, not candidates | **not as expected**: 1 letter blocked, but its UNCLEAR answers were typed `policy_gap` and `implementation_gap`, so a typed gap record was created and no homework |
| D, scripted control for A (`retinopathy-governed`, `--reviewer scripted`) | Why D exists: same letters as Drill A, but the project's hand-written reference answers stand in for the AI liaison reviewer, to test whether Drill A's blocks come from the AI review or from the law and the code. Institution agents are still AI; code still checks every quote and the human approval | 11 | 3 delivered if the law and code allow it | 3 delivered; not an AI result |

## Mapping to ITU-T Y.3172 and the AI Readiness Framework 2.0

Y.3172 is the International Telecommunication Union (ITU) architecture for machine learning (ML) in future networks. Borderline borrows its pipeline vocabulary for a health-governance drill. It is **not a telecom implementation and claims no conformance**. Of the 13 Readiness 2.0 dimensions, we claim relevance to five: (4) Contextualization and Regional Impact; (5) Level of Integration of AI in Workflows; (7) Strategy Alignment; (8) Collaboration with AI; (10) AI & Policies. We do not claim measured readiness scores.

| Y.3172 node | Borderline element | Readiness 2.0 dimension | Policy documents (examples, with chunk IDs) |
|---|---|---|---|
| SRC (source) | Synthetic incident events released step by step; 49 registered source and extraction files, hashed in [`data/sources.csv`](../data/sources.csv) (26 UAE, 9 Swiss, 14 global), all re-verified on 8 November 2026 | 4 | UAE Federal Law No. 2 of 2019 (Health Data Law), Art. 13 (`AE-HEALTH-ICT-LAW-2019:p8:c1`); Swiss TPA Art. 64 (`CH-HEALTH-TPA:p40:c1`) |
| C (collector) | `make verify-sources`, `make ingest`; absence searches recorded in [`gaps/searches/`](../gaps/searches) (what was searched for, where, what was found) | 10 | International Medical Device Regulators Forum (IMDRF) N14 incident-exchange participant list (`IMDRF-NCAR-N14-2025:p16:c1`) |
| PP (pre-processor) | 2,286 chunks with provenance; garbled Arabic text is detected and kept out of quoting | 4 | Federal Decree-Law 38/2024 official Arabic, registered but excluded because its text layer is defective |
| M (model) | 12 institution agents and the AI liaison reviewer, `qwen3:8b`, temperature 0, one stateless call each | 8 | Institution profiles in [`packs/ae/institutions/`](../packs/ae/institutions), [`packs/ch/institutions/`](../packs/ch/institutions), [`packs/global/institutions/`](../packs/global/institutions) |
| P (policy) | Code: action allow-lists, quote verification, patient-data rule, three-YES routing, human-review flag on every YES | 10, 7 | FADP Art. 55 (`CH-DATA-FADP:p24:c1`); Personal Data Protection Law (PDPL) health-data exclusion (`AE-DATA-PDPL-2021-EN:p6:c2`) |
| D (distributor) | Synthetic action handlers; a letter is delivered, blocked or routed in drill state only | 5 | [`packs/bridge/ae-ch.yaml`](../packs/bridge/ae-ch.yaml) (counterparts and reference answers) |
| SINK | Hash-chained log (`log.jsonl`), decision trail, homework list, gap register, Streamlit viewer | 8 | [`decision-trail-governed-20261108-4.md`](decision-trail-governed-20261108-4.md), [`decision-trail-ungoverned-20261108-3.md`](decision-trail-ungoverned-20261108-3.md), [`decision-trail-insufficient-20261108-3.md`](decision-trail-insufficient-20261108-3.md), [`decision-trail-governed-scripted-20261108-3.md`](decision-trail-governed-scripted-20261108-3.md) |

## Requirements mapped to domain-specific policies

For each node, the use-case requirement is mapped to health-sector AI policy in the knowledge base. Every quote is exact and verified by script against its chunk. "Type" separates law, health-authority policy and charters from advisory global guidance. A mapping shows that a text speaks to the requirement, not that it legally applies to these synthetic facts.

| Node | Requirement in this use case | Domain-specific policy (type) and exact quote |
|---|---|---|
| SRC | An AI failure seen at the clinic must reach the responsible bodies in both countries | DHA AI in Healthcare policy (DHA policy): "Report to DHA-HRS all known or suspected incidents or deficiencies related to AI solutions used in their respective healthcare facility." (`AE-DHA-AI-HEALTH-2021:p12:c1`; DHA-HRS is DHA's Health Regulation Sector). Swiss Medical Devices Ordinance (MedDO) Art. 66 (Swiss ordinance): manufacturers report "any serious incidents involving the device in question that have occurred in Switzerland, as soon as they become aware of them" (`CH-HEALTH-MedDO:p28:c1`). The Dubai incident did not occur in Switzerland; how it reaches Swissmedic is the question Drills A and B test. |
| C | Every source and decision is traceable to its origin | International Medical Device Regulators Forum (IMDRF) good machine-learning practice, N88 (global guidance, advisory): "design processes that can appropriately record and communicate decisions and rationale, as well as ensure traceability, reproducibility, data authenticity" (`IMDRF-AIML-N88-2025:p6:c2`) |
| PP | Retinal images are processed in Zurich, outside the UAE | Federal Law No. 2 of 2019, Art. 13 (UAE law): "It is not permissible to store, process, generate or transform the health data and information outside State" (`AE-HEALTH-ICT-LAW-2019:p8:c1`). The exceptions are in Resolution 51/2021, which the project could not obtain (CAND-004). |
| M | A model update must be controlled, and real-world results compared with validation | DHA AI policy (DHA policy): "Comply with all required certification of the AI software and its major upgraded versions from recognized international/local agencies." (`AE-DHA-AI-HEALTH-2021:p10:c1`) and "actual outcomes must be compared to those obtained in training and validation. Any significant discrepancies must call for further inspection." (`AE-DHA-AI-HEALTH-2021:p10:c1`). IMDRF N88 (advisory): "Clinical evaluation includes the use of datasets that are representative of the intended patient population" (`IMDRF-AIML-N88-2025:p7:c2`) |
| P | Humans keep oversight; failures can be traced and controlled | UAE Charter for the Development and Use of AI, 2024 (UAE charter): "the irreplaceable value of human judgment and human oversight over AI" (`AE-AI-CHARTER-2024:p4:c1`). DHA AI policy: "AI solution developers must build systems whose failures can be traced, diagnosed, and controlled." (`AE-DHA-AI-HEALTH-2021:p7:c1`) |
| D | A failing tool can be stopped safely, and adverse events are passed on | DHA AI policy: "AI tool must be equipped with “Graceful Degradation” mechanisms by means of automatic alerts and gradual operation cessation abilities" (`AE-DHA-AI-HEALTH-2021:p10:c1`) and "Adverse events should be timely reported to relevant oversight bodies for appropriate investigation and action." (`AE-DHA-AI-HEALTH-2021:p11:c1`) |
| SINK | Results are audited, and performance is judged for clinician and AI together | DHA AI policy: "Conduct regular audits of AI functionality by independent third party, and reporting to DHA-HRS as needed." (`AE-DHA-AI-HEALTH-2021:p13:c1`). IMDRF N88 (advisory): "including the performance of the human-AI team, rather than just the device in isolation." (`IMDRF-AIML-N88-2025:p7:c2`) |
| Strategy alignment | Both countries' institutions work to compatible aims | UAE AI Charter: "serves as a guiding framework to protect the rights of the UAE community in the development or use of AI solutions and technologies." (`AE-AI-CHARTER-2024:p2:c1`). **No Swiss AI strategy is registered in the knowledge base**, so cross-border strategy alignment could not be mapped. |

## Local policy mapping

Each liaison question is answered from the registered texts. Two examples:

- **The UAE rule on health data leaving the country:** "It is not permissible to store, process, generate or transform the health data and information outside State -which are related to the health services provided inside State- except in the case where a resolution is issued from the Health Authority in coordination with the Ministry." (`AE-HEALTH-ICT-LAW-2019:p8:c1`)
- **The Swiss route for regulator-to-regulator data:** "The FDPIC may exchange information or personal data with foreign authorities that are responsible for data protection in order that they may fulfil their respective statutory duties in relation to data protection, provided the following requirements are satisfied: a. Reciprocity with regard to administrative assistance is guaranteed." (`CH-DATA-FADP:p24:c1`)

**Keeping both UAE laws.** The PDPL does not apply to "e. Personal Health Data that has legislation regulating its protection and processing." (`AE-DATA-PDPL-2021-EN:p6:c2`). So the Health Data Law governs patient images, while the PDPL still covers clinic staff data.

**Arabic sources.** Where the Arabic original controls, only the official English translation was searchable. No Arabic quote was used in these runs, because the extracted Arabic text is garbled and we do not retype it.

**Resolution 51 of 2021.** This resolution sets the Art. 13 exceptions. It is registered as not obtainable after documented attempts and was not searched for again.

## Error scenarios and results

Drill B releases events in stages: model update and fewer referrals; missed disease confirmed on one camera; compromised vendor account; retraining on UAE images in Zurich; the vendor's "research" claim; UAE authorities learn of the reuse; letters to Swiss authorities; the suspend-or-continue dispute; an optional judge-injected insurer claim; and DHA's attempt to send patient images.

| Run | Decisions | Hash chain | Letters delivered / sent | Quotes verified | Audit-screen flags | Homework |
|---|---|---|---|---|---|---|
| A `governed-20261108-4` | 9 | verified | 0 / 3 | 10 of 13 | 1 | 5 |
| B `ungoverned-20261108-3` | 40 | verified | 0 / 5 | 24 of 30 | 8 | 8 |
| C `insufficient-20261108-3` | 7 | verified | 0 / 1 | 6 of 6 | 1 | 0 |
| D, scripted control (not an AI decision) `governed-scripted-20261108-3` | 11 | verified | 3 / 3 | 21 of 21 | 2 | 0 |

What the runs show:

- **Patient data crossed only with both keys.** The recall list (Drill A step 5) and the patient images (Drill B step 14) were stopped by code's patient-data rule. In Drill D the recall list crossed, because its legal-basis quotes verified and a recorded human approval (a drill fact) matched the letter exactly.
- **The AI reviewer did not deliver the governed letters.** This is a result, not a forced outcome. It found the right provisions and said YES on legal basis for all three letters, but at step 2 it answered UNCLEAR on transfer rules for a letter carrying no personal data ("The passages do not include the document you would need to determine transfer rules"). At steps 5 and 8 its legal-basis quotes joined text from two places: the opening of TPA Art. 64(1) with Art. 64(2), and the opening of Personal Data Protection Law (PDPL) Art. 2(1) with item (c), skipping (a) and (b). Code rejected both. In Drill D, with the reference answers standing in, all three letters were delivered. So the blocks come from the AI review, not from missing law or code.
- **Code rejected joined and cut quotes, and accepted copy slips.** 6 of Drill B's 30 quotes failed: TPA Art. 64's heading joined to its paragraph 2; "The Office shall: 9." skipping items 1 to 8; a quote shortened with "..."; a two-word fragment. Code accepted quotes with small copy slips and logged the exact source text: a dropped space ("ProperProtection" for "Proper Protection", Drill B step 9) and a character slip (Drill A step 5).
- **Delivered is not accepted.** In Drill D the FDPIC's AI agent received the step 8 letter and recommended pausing, citing the general foreign-disclosure rule (FADP Art. 16) rather than Art. 55, which the letter relied on. Whether that is right needs a person.
- **A letter with no receiver is blocked.** At Drill B step 13 DHA's AI agent sent a request that named no receiver. Code blocked it, because the three questions cannot be asked; nothing crossed.
- **Typed gaps where homework was expected.** In Drill C the reviewer typed its UNCLEAR answers `policy_gap` (legal basis, quoting the UAE Data Office's competences) and `implementation_gap` (transfer rules), quoting four real FADP passages that do not concern transfer, such as Art. 15 on a representative's duties. Code checks that quotes are real, not that they apply, so the typed record stands and needs human review.
- **Coverage and reproducibility.** Every blocked branch ran in Drills A, B and C; the delivered branches (steps 3, 6, 9) ran only in Drill D. No step failed. Running all four drills again after one change to the quote check gave byte-identical logs for A, C and D; B differed only in two quotes that the change now accepts.

Full details are in [`report/run-review-2026-11-08-final-runs.md`](run-review-2026-11-08-final-runs.md).

## Policy and standards gap candidates derived from the mapping

All four candidates in [`gaps/candidate_register.yaml`](../gaps/candidate_register.yaml) meet the project's four-part rule (`make assess-candidates`, 8 November 2026):

1. every quote verifies;
2. a recorded absence search exists;
3. a verified global comparison is quoted (here from European Union (EU) and IMDRF texts);
4. no obtainable missing document could refute the candidate.

They are **candidates, not findings**. They are unreviewed, and "absent" means absent from this knowledge base.

| ID | Type | Local evidence (verified quote) | Global comparison (verified quote) |
|---|---|---|---|
| CAND-003 | standards | Switzerland: "However, without resolving the institutional issues, Switzerland remains excluded from market surveillance with EU member states for medical devices." (`CH-EU-MRA-FACTSHEET-2025:p2:c2`). Neither country appears in the participant list of the IMDRF National Competent Authority Report (NCAR) exchange (search [`SEARCH-NCAR-PARTICIPANTS-001`](../gaps/searches/SEARCH-NCAR-PARTICIPANTS-001.json)). | "Participation in the NCAR Exchange Program will be limited to the IMDRF Management Committee (MC) Regulators. A list of NCAR Participant Countries is provided in Annex1." (`IMDRF-NCAR-N14-2025:p9:c1`) |
| CAND-002 | policy | DHA's AI policy requires certification of "major upgraded versions" without defining them: "Comply with all required certification of the AI software and its major upgraded versions from recognized international/local agencies." (`AE-DHA-AI-HEALTH-2021:p10:c1`) | "Changes to the approved device shall require approval from the notified body which issued the EU technical documentation assessment certificate where such changes could affect the safety and performance of the device or the conditions prescribed for use of the device." (`EU-MDR-2017-745:p202:c1`) |
| CAND-001 | implementation | The PDPL excludes "e. Personal Health Data that has legislation regulating its protection and processing." (`AE-DATA-PDPL-2021-EN:p6:c2`), so no single UAE authority is clearly competent to protect UAE health data held abroad. | The Organisation for Economic Co-operation and Development (OECD) 2007 privacy-enforcement Recommendation lists 38 adherents, including Switzerland and no non-members: "Spain Sweden Switzerland Türkiye United Kingdom United States Non-Members None" (`OECD-LEGAL-0352-ADHERENTS-2026:p8:c1`) |
| CAND-004 | policy | The exceptions to Art. 13 are in a resolution the project could not obtain: "a. Cabinet Decision No. (51) of year 2021 on exemption for storage and transfer of health records and information must be abide to:" (`AE-DHA-HEALTH-DATA-PROTECTION-PP11-2022:p27:c1`) | By analogy only, EU national derogations are published: "The Commission shall keep the information publicly available." (`EU-MDR-2017-745:p30:c1`) |

The drills bear on these candidates without proving them. Two typed gap records came from the liaison channel: in Drill B, the UAE Data Office's transfer rules (`policy_gap`, quoting PDPL Art. 23); in Drill C, legal basis (`policy_gap`) and transfer rules (`implementation_gap`) for a request with no reciprocity assurance, whose transfer quotes do not concern transfer. Both need human review before they add support.

## Scope and limitations

- Synthetic scenario; open-weight local model; no clinical, regulatory or data-transfer system is connected.
- Each drill was run once on the final code. Running all four drills again after one change to the quote check gave byte-identical logs for A, C and D; B differed only in two quotes that the change now accepts. Results from an 8-billion-parameter model vary between prompts, and the reviewer sometimes joins quotes or picks the wrong provision.
- Code verifies that quotes are real, not that they apply. Free-text reasons are not verified.
- Arabic originals could not be quoted. Resolution 51/2021 is missing.
- The knowledge base is local, not hosted by ITU. Retrieval finds the exact passage in the top six for 8 of 10 test questions (7 of 10 in the top three); this measures retrieval only.
- `make replay` is a code replay: it re-runs every code decision over the logged answers, without calling the model. All four runs replay with 0 differences (11 letters, 70 quotes). It cannot show that the model would answer the same way again.
- Drill D shows that the route works when the answers are right. It says nothing about whether an AI can do the review, and it is not counted in any AI result.

## References

- ITU AI for Good Sandbox Hackathon, UAE: [https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/](https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/)
- ITU-T Y.3172: [https://www.itu.int/rec/T-REC-Y.3172-201906-I/en](https://www.itu.int/rec/T-REC-Y.3172-201906-I/en)
- ITU AI Ready, Report 2.0: [https://www.itu.int/epublications/publication/ai-ready-analysis-towards-a-standardized-readiness-framework](https://www.itu.int/epublications/publication/ai-ready-analysis-towards-a-standardized-readiness-framework)
- A criterion-by-criterion evidence map is in [`docs/HACKATHON_CRITERIA_AUDIT.md`](../docs/HACKATHON_CRITERIA_AUDIT.md).
- Source register [`data/sources.csv`](../data/sources.csv); run review [`report/run-review-2026-11-08-final-runs.md`](run-review-2026-11-08-final-runs.md); decision trails [`decision-trail-governed-20261108-4.md`](decision-trail-governed-20261108-4.md), [`decision-trail-ungoverned-20261108-3.md`](decision-trail-ungoverned-20261108-3.md), [`decision-trail-insufficient-20261108-3.md`](decision-trail-insufficient-20261108-3.md), [`decision-trail-governed-scripted-20261108-3.md`](decision-trail-governed-scripted-20261108-3.md); candidate status [`report/candidate-status.json`](candidate-status.json).
