# Borderline demo walkthrough

## One-sentence story

Borderline helps a fictional UAE clinic decide whether it has enough accountable, traceable evidence to move a Swiss cloud diagnostic-AI service from proposal to human deployment review—without mistaking vendor paperwork for approval.

## Demonstration sequence (about six minutes)

1. **Set the boundary (0:00–0:40).**
   Introduce RetinaVision-DX as a fictional diabetic-retinopathy screening service. Retinal images are captured in Dubai; an encrypted package, pseudonymous screening ID and camera metadata are sent to assumed vendor compute in Zurich; an image-quality result, risk/referral recommendation return to the clinic. No real patient data, vendor, deployment, approval or legal conclusion is represented.

2. **Show the decision, not a generic chatbot (0:40–1:20).**
   Open [`intents/retinopathy-ae-ch.yaml`](../intents/retinopathy-ae-ch.yaml). Point out that the primary sequence is pre-deployment and that agents have distinct roles and allowed actions. The question is whether the clinic can begin accountable review, not whether the model can diagnose a patient.

3. **Reveal the missing-evidence moment (1:20–2:15).**
   Show the data-flow and retention questions, then the six vendor records requested: validation, camera subgroup performance, release approval, rollback, software components and subprocessors. Explain that a missing record becomes a traceable operational evidence deficiency rather than an invented legal violation.

4. **Reveal the fictional packet (2:15–3:10).**
   Open [`synthetic-product-dossier-retinavision-dx.md`](synthetic-product-dossier-retinavision-dx.md). Show the six exhibits and their simulation-only labels. The important distinction: receipt of an exhibit changes the workflow state, but it is not proof the exhibit is adequate and it does not approve activation.

5. **Show the bounded outcome (3:10–4:10).**
   Open [`gaps.jsonl`](../runs/retinopathy-evidence-packet-20261105-1/gaps.jsonl). The assessment is `READY_FOR_HUMAN_REVIEW` and `PRE_DEPLOYMENT_EVIDENCE_RECEIVED`. Read the remaining requirements: accountable human review, clinic authorization/workflow fit, and cross-border transfer basis and safeguards. This is Borderline's unique output: a documented hand-off from supplied vendor evidence to a named human governance decision.

6. **Prove the trace (4:10–5:00).**
   In the repository, run:

   ```sh
   make verify-log RUN=retinopathy-evidence-packet-20261105-1
   make audit-evidence RUN=retinopathy-evidence-packet-20261105-1
   ```

   Show that the hash chain verifies and the automated evidence screen returns no findings for this primary run. Explain the limit: this screen checks the structured run record; it does not replace human legal, clinical or vendor due diligence.

7. **Close with contribution and limit (5:00–6:00).**
   Show [`data/sources.csv`](../data/sources.csv) and the [use-case/knowledge-base note](USE_CASE_AND_KB_CONTRIBUTION.md). Borderline contributes a scenario-focused, provenance-tracked UAE–Switzerland policy knowledge base and reproducible agent workflow. It is not a national readiness score, legal engine, clinical decision-support system or already-published ITU knowledge base. The optional incident stress scenario is future/supporting evidence until its citations have been remediated and reviewed.

## Optional UI route

Start the local viewer with `make ui`, select `retinopathy-evidence-packet-20261105-1`, then show the timeline, final deployment assessment and audit status. A saved run is preferable to a live model call: the demonstration should be reproducible and should not expose patient or confidential data.

## Presenter checklist

- Say “fictional” when naming the vendor, service, clinics, data flow or exhibits.
- Say “human review pending,” never “approved” or “compliant.”
- Separate automated audit results from human interpretation of policy and evidence.
- Do not use the older incident drill as proof of a clean result.
