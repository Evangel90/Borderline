# AI for Good Sandbox Hackathon — Borderline

**Team:** [confirm team name] · **Solution:** Borderline · **Team leader:** [add] · **Members:** [add]
**Contact:** [add] · **GitHub:** https://github.com/Evangel90/Borderline
**Status:** submission draft for the 10 November 2026 deadline; integrated run complete, but five-page rendered layout, team/contact fields and final citation review remain outstanding.

## Introduction

Borderline is a policy-grounded, multi-agent deployment-review and incident-drill prototype for diagnostic AI. The UAE–Switzerland diabetic-retinopathy use case asks whether a fictional Dubai clinic can responsibly adopt a Swiss-vendor cloud screening service before it is connected to patient care. Borderline gives simulated clinic, vendor, public-authority and policy-adviser roles different facts and authorized actions; it retrieves provenance-bearing policy evidence, records their proposed actions and exposes unresolved safety, data-governance and coordination questions. It does not control a clinical system, make patient decisions or issue legal opinions.

The fictional screening system is agentic because it can use approved workflow tools: it checks image quality, records a result, prepares or routes referrals for positive/uncertain cases, and can close a negative task. A clinician remains responsible for diagnosis and treatment. The drill asks what evidence, controls and human review are required before deployment, then tests those arrangements when a later model/workflow update is associated with missed referable disease.

## Use case and requirements

The primary scenario begins before deployment. RetinaVision-DX is a fictional Swiss-vendor service for diabetic-retinopathy screening. A Dubai clinic captures retinal images, encrypts and transmits them to the vendor's assumed compute environment in Switzerland, and receives image-quality status, a screening result and referral recommendation in return. The clinic does not host the model weights. The scenario requires the actors to establish the vendor's retention periods for images, results, telemetry and support logs; vendor and subprocessor access; and the route for any onward transfer before approving deployment. These are fictional scenario facts and questions, not claims about a real vendor or UAE deployment.

An optional post-deployment stress test introduces a v2.4 update, 47 synthetic missed referable cases on Cam-7, suspected stolen vendor credentials, possible secondary use of UAE-origin images for retraining, a regulator evidence request and a safety-versus-access decision. Information is released progressively and agent views are role-specific. This tests whether the pre-deployment records and coordination plan are sufficient when the facts become adverse.

The product dossier includes a fabricated EDE classification letter establishing medical-equipment/SaMD classification **only inside the drill**, and a fictional manufacturer corrective-action plan marked submitted but not completed. Real-world product classification, marketing authorization, device risk class, legal marketing-rights holder, clinic licensing, actual report/case predicates, remediation results and patient follow-up remain unknown. No model should infer those facts. The purpose is to test the simulated system's response, not to represent an actual manufacturer or EDE decision.

Use-case requirements are to: (1) retrieve relevant, traceable UAE, Swiss and global sources; (2) release events progressively with incomplete and unevenly distributed facts; (3) represent different institutional roles and permitted actions; (4) preserve uncertainty and require human approval for consequential simulated decisions; (5) identify evidence and governance gaps; and (6) expose a reproducible decision trace. The current prototype partially meets these requirements. Actions only alter synthetic state; the human-approval form is local and unauthenticated.

## Mapping to ITU-T Y.3172 and AI Readiness Framework 2.0

Y.3172 is an architectural reference for ML in future networks. Borderline adapts its pipeline vocabulary to a healthcare governance simulation; it is **not a telecom implementation and does not claim formal Y.3172 conformance**. Y.3172 describes pipeline components including SRC, C, PP, M, P, D and SINK, plus management/orchestration and sandbox functions ([ITU-T Y.3172](https://www.itu.int/rec/T-REC-Y.3172-201906-I/en)).

| Pipeline concept | Borderline component and scenario requirement | Local policy / source connection |
| --- | --- | --- |
| ML Intent | `intents/retinopathy-ae-ch.yaml` defines actors, staged events, agent views, actions and expected checks. | Scenario maps requirements to registered UAE/Swiss roles and applicable-source checks. |
| SRC | Synthetic clinical events and registered source documents; no patient images or live telemetry. | UAE Federal Decree-Law No. 38/2024; DHA AI and referral policies; Swiss MedDO, FADP and cyber-reporting materials. |
| C | Source ingestion and hybrid lexical/vector retrieval in the local knowledge index. | `data/sources.csv` preserves issuer, source status, language, URL/path, hash and scope notes. |
| PP | PDF extraction/OCR, chunking, language and provenance metadata. | Arabic materials are included; Arabic text controls where the official portal says so. Translation/OCR needs human review for consequential interpretation. |
| M | Configured AI agent proposes one role-authorized action and a concise rationale. | WHO health-AI guidance and relevant local policy excerpts are retrieval aids; they are not automatically binding. |
| P | Institution action allow-lists, evidence triage, cross-border gate and human-approval state. | UAE/Swiss legal predicates and source scope are checked separately; current gates are partial/configured and not a complete legal engine. |
| D / SINK | Orchestrator dispatches the action to a synthetic handler and records its result/state change. | No real regulator message, clinical order, referral, model rollback or data transfer occurs. |
| MLFO / Sandbox | Orchestrator releases events and runs agents in an isolated local drill. | Local synthetic sandbox only; no hosted or distributed ITU Sandbox deployment is evidenced. |

The ITU AI Readiness Framework 2.0 uses six factors and 13 dimensions. Borderline reports qualitative relevance, not national readiness scores ([ITU AI Readiness Report 2.0](https://www.itu.int/epublications/publication/ai-ready-analysis-towards-a-standardized-readiness-framework)). The ITU reference ingestion path was smoke-run on Y.3172: 50 source chunks and 19 framework definitions entered a separate local index. The production drill still uses Borderline's own local hybrid index; no ITU-hosted deployment is available in the evidence. The policy pack may be considered for publication in the ITU AI for Good Lab only as a future hackathon outcome.

| Readiness dimension | Borderline mapping and current limit |
| --- | --- |
| 1 Data/model Marketplace | Policy knowledge base only; no data/model marketplace or patient dataset. |
| 2 Generated Content Marketplace | No generated-content ecosystem; rationales are logged outputs only. |
| 3 Cross-domain correlation analysis | Health, vendor, cyber and data actors interact; no correlation analytics are implemented. |
| 4 Contextualization and Regional Impact | Dubai/UAE use case with Swiss vendor and country packs; no local stakeholder impact study. |
| 5 AI Integration in Workflows | Referral and clinic workflow modeled; no hospital-system integration. |
| 6 Human Interface | Streamlit viewer/review form; accessibility, Arabic UI and usability not evaluated. |
| 7 Strategy Alignment | UAE/Swiss materials are in the knowledge base; no outcome/KPI alignment assessment. |
| 8 Collaboration with AI | Simulated human review/approval; unauthenticated and not measured. |
| 9 Impacts of Humans in AI Integration | Safety/access tradeoff modeled with synthetic facts; no measured patient or workforce impact. |
| 10 AI & Policies | Core focus; source mapping exists but legal applicability and gap claims need review. |
| 11 AI for Inclusion | No subgroup, gender, disability or language-access evaluation. |
| 12 Granular Priorities | Retinopathy/Dubai priority is explicit; no fine-tuning or evolving local-priority mechanism. |
| 13 Digital Infrastructure | Cameras/cloud are assumptions; compute, connectivity, device distribution and energy are not measured. |

The six factors map as follows: **Data**—provenance-tracked policy sources, but no open clinical data or data-quality assessment; **Research**—simulated roles, but no expert validation collaboration; **Deployment Support**—local prototype, without clinic or hosted-sandbox deployment; **Standards**—traceability and conceptual Y.3172 mapping, without conformance review; **Open source and Code**—public repository and pinned ITU reference submodule, with no integrated shared KB contribution; **Sandbox Environments**—synthetic isolated scenarios, not ITU-hosted. Full traceability and limitations are in [`docs/HACKATHON_CRITERIA_AUDIT.md`](../docs/HACKATHON_CRITERIA_AUDIT.md).

## Local policy mapping and knowledge base

The knowledge base registers 31 source records and a linked OCR derivative; all 32 tracked source/extraction artifacts pass `make verify-sources`. The current AE, CH and global packs contain 1,859 chunks. UAE materials include the medical-products law in Arabic and official English translation, EDE establishment/pharmacovigilance materials, the DHA AI-health, referral and sentinel-event policies, the health-ICT law, data protection and cybersecurity sources. Swiss materials include the Medical Devices Ordinance, Therapeutic Products Act, Human Research Act, FADP/DPO and cybersecurity reporting sources. WHO guidance, ITU-T Y.3172, ITU AI Readiness 2.0, the UN AI governance report and G7 code provide global context. Provenance and limits are recorded in [`data/sources.csv`](../data/sources.csv). This is a scenario-focused local knowledge base, not a complete or already-published cross-national collection; its contribution scope and claim discipline are recorded in the [use-case and knowledge-base note](USE_CASE_AND_KB_CONTRIBUTION.md).

The source register does not mean all relevant law is complete or applicable. UAE ICT health implementing/exemption documents are not yet archived in the local pack; the DPO Annex 1 snapshot needs currency review; Swiss cyber reporting depends on entity scope; and Arabic OCR/translation lacks human Arabic review. Article 68(7) and 70(2) in the EDE pathway remain conditional on separate statutory facts. The latest drill cites the English translation at `AE-FEDERAL-DECREE-LAW-38-2024-EN:p54:c2` and `:p56:c2`; the Arabic original controls. The EDE evidence request is a simulated fact-finding step, not an asserted legal duty.

## Evaluation scenario and preliminary results

The evaluated revised primary run is `retinopathy-evidence-packet-20261105-1`, using local `qwen3:8b`: 22 decisions, one `READY_FOR_HUMAN_REVIEW` deployment assessment, a verified hash chain, and no automated citation-screening findings. The scenario first records six missing vendor records, then supplies six fictional exhibits. The assessment concludes that the clinic can move to accountable human review while activation remains pending workflow fit and transfer safeguards. This is a synthetic operational result, not a legal or product-quality conclusion. The earlier `retinopathy-final-itu-criteria-20261103-4` incident run predates the revised scenario. The current ten-question retrieval seed reaches the exact passage in top six for 9/10 questions; it is curated, not a general accuracy measure.

The run audit found 14 decisions without citations and two DHA citations flagged for review (`log-2-dha`, `log-6-dha`). Both are screened `UNSUPPORTED`: the cited referral policy gives scope and continuity-of-care context, but does not establish an AI-specific incident duty or that the clinics are DHA-licensed. The rollback decision is recorded as a proposal pending human approval, with rollback availability and safety unverified and no irrelevant WHO citation. See the [run review](run-review-retinopathy-final-itu-criteria-20261103-4.md). The concise logged rationale, source references, actions, tool outcomes and hash chain provide a structured decision trace; private model chain-of-thought is not requested or stored. The report still needs a rendered page-count check and passage-level review of policy-gap comparisons.

## Policy and standards gaps identified from mapping

The current evidence supports **questions for validation**, not conclusions that UAE, Swiss or international law has a gap:

1. **Post-update diagnostic safety controls:** the synthetic incident exposes missing release/change records, Cam-7 validation, rollback verification, clinician-review thresholds and completed follow-up evidence. WHO guidance calls for safety/quality controls in practice and continuous assessment of AI applications (`WHO-GUIDELINES-AI-HEALTH:p13:c1`, `:p14:c1`; advisory, not binding law). Local policy applicability and the responsible authority for each control need confirmation.
2. **Incident-related health-data reuse and exchange:** controller roles, identifiability, purpose/legal basis, transfer route and minimum necessary evidence remain unknown. UAE (`AE-DATA-PDPL-2021`, `AE-HEALTH-ICT-LAW-2019`) and Swiss (`CH-DATA-FADP`, `CH-DATA-DPO`) privacy sources plus WHO's discussion of secondary health-data use and consent (`WHO-GUIDELINES-AI-HEALTH:p103:c1`, `:p160:c1`; advisory) are relevant, but no lawful-basis or transfer conclusion is made. A protocol specifying decision owners, required records and privacy/security review is a candidate operational response.
3. **Safety versus access:** 47 synthetic missed cases create a safety concern while stopping screening may delay access. Manual screening capacity, patient follow-up and rollback safety are unverified. The drill supports a human review question, not a specific suspension decision or legal power.

The final submission must attach passage-level local and global citations to each gap comparison, label binding law separately from advisory guidance, and preserve each unresolved fact. Do not report the old six candidate themes as established findings. The integrated drill is complete; next render and edit this report to no more than five pages, complete the passage-level review and fill in team/contact fields. Demo video is optional for initial submission and required if shortlisted.

## References

- ITU AI for Good Lab Hackathon: UAE requirements, evaluation criteria, report template and FAQ: https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/
- ITU-T Y.3172, *Architectural framework for machine learning in future networks including IMT-2020*: https://www.itu.int/rec/T-REC-Y.3172-201906-I/en
- ITU, *AI Ready — Analysis Towards a Standardized Readiness Framework, Report 2.0*: https://www.itu.int/epublications/publication/ai-ready-analysis-towards-a-standardized-readiness-framework
- Source manifest: [`data/sources.csv`](../data/sources.csv). Run review: [`final integrated run`](run-review-retinopathy-final-itu-criteria-20261103-4.md); earlier EDE review: [`EDE citation review`](run-review-retinopathy-ede-citations-20261103-4.md); criteria audit: [`criteria audit`](../docs/HACKATHON_CRITERIA_AUDIT.md).
