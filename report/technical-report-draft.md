# Borderline: Cross-Border AI Incident Drill Engine

**ITU AI for Good Lab Hackathon: United Arab Emirates**  
**Technical report — working draft, 30 October 2026**  
**Team:** [add team members]  
**Repository:** [Borderline on GitHub](https://github.com/Evangel90/Borderline)

> Draft status: the expanded scenario has been attempted twice. The first
> remote run (`borderline-eight-stage-20261030-1`) stopped during step 4 after
> nine decisions on an invalid citation. The second run
> (`borderline-eight-stage-20261030-2`) logged 25 decisions through step 6 and part of step 7, then stopped
> when OpenRouter's 50-request daily free limit was exhausted. Its partial hash
> chain verifies, but there is no completed gap record. The scenario still
> needs a complete run, citation relevance review, legal-source review, and
> the six-gap analysis.

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

| Y.3172-related concept | Borderline prototype | Current limit |
| --- | --- | --- |
| ML intent | YAML drill intent defines the use case, stages, participants, and private agent views. | The engine is currently wired to AE–CH files and identifiers. |
| ML collector / preprocessing | Registered source PDFs are extracted and split into citation-bearing chunks. | Retrieval is deterministic keyword search; ingestion is not yet an integrated distributed vector knowledge base hosted in the ITU Sandbox. |
| Policy node | AE–CH bridge YAML contains transfer and regulator-route rules. | Rules are static and do not yet execute and record each of the three policy checks separately. |
| ML function orchestrator | Python releases timeline stages and invokes declared participants. | Timing is a staged label, not a simulated clock; no dynamic event scheduler or judge UI exists. |
| Model / agents | OpenRouter's free-model router produces structured agent proposals. | The model can vary across decisions; no LoRA fine-tune or event-tagging model is implemented. |
| Sandbox | Action handlers update synthetic state and return tool outcomes. | No external systems are integrated; human approval is represented in the scenario but not enforced as a live approval workflow. |
| Audit | JSONL decisions are hash-chained and independently verifiable. | The log records concise rationales and citations, not private chain-of-thought; full retrieval and liaison message traces still need completion. |

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

The collection is incomplete for the proposed scenario. The UAE ICT Health
Law and its 2021 exemptions, primary materials supporting EDE's role, and
relevant DHA materials still need to be registered and ingested. The Swiss
cyber reporting duty and its applicability to this vendor also require primary
source verification. The DPO Annex 1 text in the repository is noted as a
checked-in 2023 version and must be checked for currency. Agent profiles
marked `source_review_required` are placeholders for simulation until this
work is done. The project does not issue legal advice or determine how these
rules apply to a real incident.

## 7. Evaluation scenario and prototype evidence

The current intent contains eight staged events and an optional reserve
escalation. Static checks confirmed that the intent parses, all declared
participants have profiles, each participant has an explicit view, and all
declared actions have sandbox handlers. The first OpenRouter attempt stopped
in step 4 after nine decisions because the FDPIC agent returned a citation ID
outside its retrieved evidence. A second attempt recorded 25 decisions through
step 6 and part of step 7 before the daily free-model quota was exhausted. Its
partial log's hash chain verifies, but no policy-gap record was produced and
the run is not a completed evaluation. At least one rationale cited a source
that does not support the asserted device-regulatory basis; citation presence
alone is not counted as evidence quality.

An earlier four-step prototype run, `or-free-20261030-5`, completed with 11
agent decisions and a verified hash chain. That run validates the earlier
action-selection, gate, and logging path; it does not evaluate the new staged
scenario or its private-view behavior. The next evaluation should rerun all
seven default stages, verify the chain, and review each decision for action
authorization, information visibility, evidence relevance, and gate outcome.

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
and evidence from the completed drill before it is reported as a finding.

## Submission checklist

- [ ] Complete legal-source verification and update the source register/chunks.
- [ ] Run the expanded scenario and verify the audit chain.
- [ ] Review agent visibility, action permissions, citations, and gate outcomes.
- [ ] Develop and evidence the six domain-level gap comparisons.
- [ ] Confirm team details and final report layout against the official template.
- [ ] Add report references and stay within the five-page maximum.
- [ ] Optional: record a demo video of no more than seven minutes; shortlisted
      teams will need one.
