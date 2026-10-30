# Borderline: Cross-Border AI Incident Drill Engine

**ITU AI for Good Lab Hackathon: United Arab Emirates**  
**Technical report — working draft, 30 October 2026**  
**Team:** [add team members]  
**Repository:** [Borderline on GitHub](https://github.com/Evangel90/Borderline)

> Draft status: a full eight-stage run using local `qwen3:8b`
> (`local-qwen3-human-gate-20261030-1`) completed with 31 decisions and a
> generated gap register. Its hash chain verifies. EHS recorded a pause
> recommendation pending human approval; the simulated service was not paused,
> and no approval has yet been recorded. This is a prototype evaluation, not a
> legal validation: citations and the generated gap evidence need human review,
> and the country source collection and six-gap analysis remain incomplete.

## 1. Overall introduction

Borderline is a prototype for running cross-border AI incident drills. It
represents institutions and other participating roles as agents. For each
event, an agent receives a role-specific view, retrieves policy excerpts,
selects one action allowed by its profile, and gives a short rationale. A
Python sandbox records the simulated action; a configured bridge gate can
block or route selected data and regulator-channel actions. Decisions, the
agent's visible event facts, citations, tool outcomes, and state changes are
written to a hash-chained log.

The current demonstration is wired to the United Arab Emirates and
Switzerland. It uses synthetic facts and simulated actions only. It does not
connect to clinics, regulators, vendors, or patient systems. The engine is not
yet country-plug-in complete: loading a new country pack alone does not make
that country's agents and bridge rules run automatically.

## 2. Use case

The drill concerns a Swiss vendor's diabetic-retinopathy screening model,
deployed in synthetic Dubai clinics. Dubai Health Authority is the selected
emirate-level health authority for this version. A model update is followed by
an audit that finds missed referable disease. Later events introduce suspected
stolen vendor credentials, use of UAE-origin retinal images held in
Switzerland for model retraining, a research-purpose claim, a regulator
information request, and a decision about suspension versus continued
screening. A reserve event alleges that patient images appeared in an insurer's
pricing model.

All people, patient counts, incidents, and events in the drill are synthetic.
The eight events are staged from T+0 to T+24 hours, with the judge-injected
event disabled by default. Each participating agent receives an explicit
event view. Facts are recorded in the decision log so reviewers can inspect
what each agent saw.

## 3. Use-case requirements

The prototype is intended to demonstrate: progressive incident events;
institution-specific roles and action permissions; role-specific information
access; evidence retrieval from country and global policy chunks; a cross-border
policy gate; simulated actions; and reviewable run records. The current
implementation meets these requirements partially. In particular, the gate
uses configured rules rather than a complete three-part legal-basis,
transfer-rules, and counterpart assessment. The new eight-stage timeline has
not yet been run end to end against the remote model.

## 4. Mapping to ITU-T Y.3172

This is an architectural mapping, not a claim of full Y.3172 conformance.

| Y.3172-related concept       | Borderline prototype                                                                                                                                               | Current limit                                                                                                                                    |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| ML intent                    | YAML drill intent defines the use case, stages, participants, and private agent views.                                                                             | The engine is currently wired to AE–CH files and identifiers.                                                                                   |
| ML collector / preprocessing | Registered source PDFs are extracted into provenance-bearing chunks; the current code indexes them in local persistent Chroma using multilingual embeddings. | The index is local and not an integrated distributed knowledge base hosted in the ITU Sandbox; retrieval quality still needs scenario evaluation. |
| Policy node                  | AE–CH bridge YAML contains transfer and regulator-route rules.                                                                                                    | Rules are static and do not yet execute and record each of the three policy checks separately.                                                   |
| ML function orchestrator     | Python releases timeline stages and invokes declared participants.                                                                                                 | Timing is a staged label, not a simulated clock; no dynamic event scheduler or judge UI exists.                                                  |
| Model / agents               | Local Ollama `qwen3:8b` produced structured agent proposals for the completed evaluation run.                                                                    | No LoRA fine-tune or event-tagging model is implemented; model output still needs evidence and legal review.                                     |
| Sandbox                      | Action handlers update synthetic state and return tool outcomes. A clinic-pause recommendation now waits for a separate human decision in the Streamlit review UI. | Human approval is local and unauthenticated; it changes only displayed synthetic state and does not control a real system.                       |
| Audit                        | JSONL decisions are hash-chained and independently verifiable; current decisions record retrieved chunk IDs as well as citations.                               | The log records concise rationales, not private chain-of-thought; embedding queries, match scores, and liaison message traces are not recorded. |

## 5. Mapping to the ITU AI Readiness Framework 2.0

Borderline addresses contextualization through UAE and Swiss source packs and
role profiles; cross-domain analysis through health, data protection, device
safety, and cyber roles; open-source management through a public code
repository; and human interaction through review-oriented simulated actions.
These are design aims with partial implementation. The free-model router is a
remote service and does not guarantee one pinned model across decisions. The
prototype has no fine-tuning workflow, enforced human-approval step, measured
energy profile, or formal social-inclusion evaluation. These areas require
implementation or evidence before claiming completion.

## 6. Local policy mapping

The source register and chunks currently include UAE AI strategy and charter
materials, AI ethics guidance, the Personal Data Protection Law, Dubai data
exchange law, and federal cybercrime legislation. Swiss materials include the
Federal Act on Data Protection and its Ordinance, Medical Devices Ordinance,
Therapeutic Products Act, and Human Research Act. WHO health-AI guidance and
ITU materials are included in the global pack. Provenance is recorded in
[`data/sources.csv`](../data/sources.csv); source hashes can be checked with
`make verify-sources`.

The collection is incomplete for the proposed scenario. Federal Law No. 2 of
2019 on ICT in Health is now registered and ingested; its English PDF was
obtained from ISAHD, a platform managed by the Dubai Health Authority, and
checked against the official UAE Legislation portal. The portal states that
the Arabic text prevails. The executive regulation ([Cabinet Resolution No. 32
of 2020](https://uaelegislation.gov.ae/en/legislations/1444), official UAE
Legislation record and download) and the 2021 exemption resolution ([MoHAP
Ministerial Resolution No. 51](https://mohap.gov.ae/en/w/ministerial-decree-no.-51-of-the-year-2021-regarding-cases-in-which-health-data-and-information-may-be-stored-or-transferred-outside-the-country),
official MoHAP record; its official attachment is
[here](https://uaephl.mohap.gov.ae/admin/Attachment/Download?id=8e6c0280-78fc-4b4f-bdb4-2637c2909b38&response=download))
have been located and their contents reviewed, but the PDF downloads remain
unavailable from this environment (UAE Legislation returns HTTP 403 and the
MoHAP attachment host times out). They are therefore not yet in the source
register or chunks. Archive and hash the official PDFs before treating these
rules as evidence in a drill. Primary materials supporting EDE's role and
relevant DHA materials remain outstanding. The Swiss Information Security
Act reporting amendment, Cybersecurity Ordinance, and official BACS fact sheet
are now registered and ingested. NCSC guidance limits mandatory reporting to
entities in the statutory scope; the drill must not assume the Swiss vendor is
covered without an applicability determination. The updated run's step-3
rationale still has a citation mismatch for its Art. 74b reference, as recorded
in [`run-review-local-qwen3-cyber-scope-20261030-1.md`](run-review-local-qwen3-cyber-scope-20261030-1.md).
The DPO Annex 1 text in the repository is noted as a checked-in 2023 version
and must be checked for currency. Agent profiles marked
`source_review_required` are placeholders for simulation until this work is
done. The project does not issue legal advice or determine how these rules
apply to a real incident.

## 7. Evaluation scenario and prototype evidence

The current intent contains eight staged events and an optional reserve
escalation. Static checks confirmed that the intent parses, all declared
participants have profiles, each participant has an explicit view, and all
declared actions have sandbox handlers. The expanded run
`local-qwen3-human-gate-20261030-1` completed all seven default stages with 31 decisions
from 12 agents; the optional reserve escalation was not enabled. The run
generated a policy-gap record and its 31-entry hash chain verifies. The log
contains 23 decisions with citations. The step-6 gate result was visible to
six agents, while two actions were recorded on the simulated liaison route; no
external message or data was sent. Review found all 31 actions allowed by
their event views and institution profiles, and all logged payloads matched
the assigned private views. Citation membership did not guarantee support:
the NCSC's cyber-reporting assessment cited Swiss medical-device provisions,
and EDE cited a UAE data-protection preamble for a device-evidence request.
The earlier run `local-qwen3-20261030-1` recorded the AI as paused without
approval. In the latest run, EHS recorded a recommendation only, leaving the
simulated service unpaused pending a separate local human decision. That
approval is not yet recorded.
That earlier run's engineering review is in
[`run-review-local-qwen3-20261030-1.md`](run-review-local-qwen3-20261030-1.md).
A later run, `local-qwen3-cyber-scope-20261030-1`, completed with 31 decisions
and a verified hash chain after the Swiss cyber sources and NCSC scope
instructions were added. Its step-3 rationale correctly leaves the vendor's
mandatory reporting status unestablished, but cites a chunk that does not
support its Art. 74b reference. The step-7 NCSC decision also treats scope as
unresolved. See
[`run-review-local-qwen3-cyber-scope-20261030-1.md`](run-review-local-qwen3-cyber-scope-20261030-1.md).
The newest run improves this one issue but is not submission-ready evidence
for legal accuracy, human oversight, or a complete liaison policy check.
The subsequent run `local-qwen3-uae-law-scope-20261030-1` completed with 31
decisions and a verified hash chain after the ICT Health Law was ingested.
The Data Office cited Article 13 in step 7 but not at the earlier step-6
review, and the missing exemption resolution prevents a complete assessment.
Its review is in
[`run-review-local-qwen3-uae-law-scope-20261030-1.md`](run-review-local-qwen3-uae-law-scope-20261030-1.md).

An earlier four-step prototype run, `or-free-20261030-5`, completed with 11
agent decisions and a verified hash chain. That run validates the earlier
action-selection, gate, and logging path; it does not evaluate the expanded
scenario or its private-view behavior. The two incomplete OpenRouter attempts
are retained as historical records.

The persistent Chroma index and multilingual embedding retrieval were added
after the saved 30 October evaluation runs. Those historical runs used the
previous lexical retrieval implementation and do not contain retrieved-chunk
IDs. Run and review the expanded drill again against the current index before
using it as submission evidence.

## 8. Candidate policy and standards gaps

The repository currently records one scenario-specific gap concerning
cross-border evidence sharing and vigilance coordination. The six items below
are **candidate themes from the project brief**, not yet six findings supported
by a completed mapping and run:

1. Unclear lead authority when a foreign AI vendor's update harms patients.
   Global comparison candidate: GDPR lead supervisory authority and IMDRF
   regulator information exchange.
2. Unclear classification of health-data retraining as research, treatment,
   or a new purpose. Global comparison candidate: EU AI Act data-governance
   duties.
3. Model updates may reach patients without a fresh review. Global comparison
   candidate: US FDA predetermined change-control plans for AI devices; verify
   current status before use.
4. No clear fast legal route for cross-border regulator sharing of health
   evidence. Global comparison candidate: Council of Europe Convention 108+
   cooperation; verify each country's status and applicability.
5. Unclear duty to inform patients when an AI screening tool errs in care.
   Global comparison candidate: EU AI Act deployer information duty.
6. Authority may be split across emirate, federal, free-zone, and cantonal
   structures. Global comparison candidate: EU NIS2 single-point-of-contact
   model.

Each candidate needs a sourced local-policy mapping, a checked global example,
and evidence from a reviewed run using the current vector retrieval before it
is reported as a finding.

## Submission checklist

- [ ] Complete legal-source verification and update the source register/chunks.
- [X] Run the expanded scenario with local `qwen3:8b` and verify the audit chain.
- [X] Review agent visibility, action permissions, citations, and gate outcomes; findings recorded in the run review.
- [ ] Develop and evidence the six domain-level gap comparisons.
- [ ] Confirm team details and final report layout against the official template.
- [ ] Add report references and stay within the five-page maximum.
- [ ] Optional: record a demo video of no more than seven minutes; shortlisted
  teams will need one.
