# Synthetic product dossier: RetinaVision-DX v2.4

**Status:** canonical fictional evidence for the simulation. Agents should treat the EDE classification letter and manufacturer corrective-action plan below as established scenario documents. They are invented for this drill and are not real-world records, regulatory decisions, or proof of actual product status.

## Product concept for the hackathon

RetinaVision-DX is a fictional, cloud-connected, agentic diabetic-retinopathy screening system deployed by fictional Swiss vendor RetinaSwiss AG to fictional Dubai clinics. Version 2.4 is a software update. The product analyzes retinal fundus images captured with a clinic camera and returns image-quality status, a diabetic-retinopathy risk category, confidence, and a recommended next step.

It is agentic because it can use approved workflow tools, not just generate text. In the assumed deployment, it can:

1. Retrieve the screening order and relevant patient identifiers from the clinic system.
2. Check image quality and request a repeat capture when an image is inadequate.
3. Analyze the image and create a result in the clinic system.
4. For a positive or uncertain result, prepare or place a referral in the clinic queue and send an approved patient notification.
5. For a negative result, close the screening task and send a “no referral indicated” message without routine clinician review.
6. Send technical telemetry to the Swiss vendor for service monitoring. Whether image-level or patient-identifiable data was included in the incident-related transfer is deliberately unresolved.

The system does not prescribe, diagnose other eye diseases, or perform treatment. In the assumed workflow, a clinician remains responsible for clinical diagnosis and treatment, but negative cases are not routinely reviewed before the patient is told no referral is indicated. That automation boundary makes the safety incident and human-oversight questions concrete.

## Incident facts assumed for this scenario

- Version 2.4 was deployed to Dubai clinics using Cam-7 retinal cameras.
- A later spot audit confirmed 47 missed referable diabetic-retinopathy cases associated with this camera/model combination. Some patients received a no-referral message; patient follow-up is not yet known.
- The vendor says v2.4 included a model update and workflow-agent changes. The exact change record, validation evidence, release approval, rollback readiness, and affected date range are unavailable.
- Stolen vendor credentials were reportedly used during an update operation. Attribution, access scope, and whether the actor changed model weights, workflow rules, or both are unconfirmed.
- The vendor says it retrained the model for research using images associated with a safety incident. The lawful basis, data fields, consent/notice, transfer path, access log, and actual training use are unverified.
- Serious patient harm has not been confirmed. The product's UAE classification, marketing authorization, legal marketing-rights holder, clinic licenses, and the status of any Article 68(3) report or Article 70(1) condition remain unknown.

## Fictional EDE classification letter (scenario fact)

For purposes of the drill, assume this fictional letter was issued by EDE after reviewing the fictional product dossier:

> **EDE product classification letter — SIMULATION ONLY**  
> Applicant: RetinaSwiss AG, Switzerland; UAE representative: Gulf Vision Medical Trading LLC (fictional).  
> Product: RetinaVision-DX, software version 2.4, including the image-analysis model and referral-workflow agent.  
> Intended purpose: analysis of retinal fundus images to screen for diabetic retinopathy and support referral decisions.  
> Scenario determination: regulated medical equipment / software as a medical device under Federal Decree-Law No. 38 of 2024. UAE marketing authorization is required before commercial supply or clinical deployment.  
> Device risk class: not determined by this preliminary classification letter; it must be established through the applicable authorization process.  
> UAE marketing authorization: none is recorded in the fictional case file.  
> This letter is a fabricated exhibit for the Borderline drill. It has no real EDE reference number, signatory, legal effect, or evidentiary value outside the simulation.

Within the scenario, agents may treat the classification and lack of recorded marketing authorization as established facts. They must not invent a risk class, authorization certificate, or official report/case determination. The legal conditions for applying Articles 68(7) and 70(2) remain a separate question.

## Fictional manufacturer corrective-action plan (scenario fact)

Assume RetinaSwiss AG submitted this plan after the confirmed false-negative signal. This is the manufacturer's plan, not proof that the actions succeeded:

1. **Containment:** stop further v2.4 rollout immediately; disable automated “negative / no referral” closure for Cam-7; route all Cam-7 results to a licensed clinician until a new release is approved.
2. **Patient safety:** provide the affected clinics a list of 47 potentially missed cases using the minimum identifiers required; clinics verify identity, arrange clinician review, and document contact and referral outcomes. Completion is not yet confirmed.
3. **Rollback:** prepare rollback to v2.3, but do not reactivate it until compatibility, security integrity, and clinical performance checks are completed. The rollback has not yet been approved or executed.
4. **Investigation:** preserve v2.4 model weights, workflow configuration, update package, signing keys, access logs, telemetry, and audit records; suspend vendor credentials implicated in the suspected compromise; compare model and agent changes against the approved release record.
5. **Validation:** reproduce the Cam-7 failure, test a representative locked dataset, assess false-negative rates by image quality and relevant patient subgroups, and obtain independent clinical review before any re-release.
6. **Data handling:** freeze secondary training on incident-associated images; preserve access and transfer logs; identify whether images or identifiers left UAE systems; do not delete relevant evidence during the investigation.
7. **Governance:** no model or workflow-agent update may resume in Dubai until the vendor provides the investigation package, the clinics and relevant authorities complete review, and an accountable human approves the release under the scenario's assumed governance process.

Plan status in the drill: **submitted; implementation and completion unverified**.

## Scenario status fields

| Field | Scenario value |
| --- | --- |
| Product concept and intended use | Established fictional scenario fact, as described above |
| UAE medical-product classification | Established within the drill by the fictional EDE letter: regulated medical equipment / SaMD |
| UAE marketing authorization | None recorded in the fictional case file; required under the assumed letter |
| Device risk class and marketing-rights holder authorization details | Unknown / not established by the classification letter |
| Manufacturer corrective-action plan | Submitted as a fictional artifact; execution and outcomes unverified |
| Application of Articles 68(7) and 70(2) to incident | Assess separately; statutory report/case predicates are not automatically established by classification |

The point of the drill is to test what follows from a known simulated classification, what further facts are needed for statutory incident pathways, and how agents distinguish a submitted plan from completed remediation.

## Remaining fictional vendor evidence requested by the drill

The classification letter and corrective-action plan are scenario exhibits. Other requested records may remain outstanding: detailed product labeling and intended-use statement; system architecture and data-flow diagram; software bill of materials and model/version identifiers; complete v2.4 change and approval records; Cam-7 validation and subgroup performance results; risk-management file; post-market complaint and incident records; update signing/access logs; rollback verification; UAE marketing authorization application or certificate; legal entity holding marketing rights; data-processing and cross-border transfer records; and evidence of whether incident-associated images were accessed or used for training.

## Scope note

This dossier is deliberately synthetic. The completed November 2026 run predates these exhibits. A new run is required to evaluate this expanded scenario. Keep the simulation-only labels attached whenever the classification letter or manufacturer plan is shown outside the drill.
