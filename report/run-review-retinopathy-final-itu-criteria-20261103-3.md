# Run review: `retinopathy-final-itu-criteria-20261103-3`

**Run date:** 3 November 2026. **Model:** local `qwen3:8b`.

The full eight-stage drill completed with 32 decisions and two governance assessments. Final hash: `597812d818f09fd0277ce14dab0ace4afa7b271e0a2185267fb48ee8eef3794d`. `make verify-log` passed. A static comparison found no action outside the actor's event-authorized actions. No real clinic, regulator, vendor API, patient record, model or data transfer was affected.

## Evidence and decisions

- EDE steps 2, 6 and 7 each cite the English translation passages `AE-FEDERAL-DECREE-LAW-38-2024-EN:p54:c2` and `:p56:c2`. The controlled rationale states the Article 68(7)/70(2) predicates remain unverified, treats the evidence request as simulated fact-finding, and caps confidence at 0.5. Each is `PARTIALLY_SUPPORTED` under the lexical screen; this is not legal validation. The linked source metadata says the Arabic original controls.
- The run records two assessments: `OBJECTIVE_CONFLICT` (safety versus screening access) and `EVIDENCE_DEFICIENCY` (cross-border data/evidence coordination). Both are `INSUFFICIENT_EVIDENCE` and should be presented as unresolved questions, not established legal or policy gaps.
- The audit found 14 decisions without citations and two citations flagged for review. The uncited entries are `log-1-screening_ai`, `log-1-retina_swiss_ag`, `log-2-screening_ai`, `log-3-retina_swiss_ag`, `log-3-uae_cyber`, `log-4-retina_swiss_ag`, `log-5-retina_swiss_ag`, `log-6-dha`, `log-7-screening_ai`, `log-7-dubai_clinic_operator`, `log-7-uae_cyber`, `log-7-ncsc`, `log-7-policy_adviser`, and `log-8-dubai_clinic_operator`. Some are operational choices based on visible scenario facts; source-based, legal or policy claims among them still need review.
- `log-2-dha` cites `AE-DHA-REFERRAL-2022:p1:c2`, but its rationale overstates what the passage says and assumes an unverified DHA facility license. The decision is marked `UNSUPPORTED`.
- `log-7-retina_swiss_ag` cites `WHO-GUIDELINES-AI-HEALTH:p31:c1`, a passage about early COVID-19 screening/checker applications and their evaluation. It does not support a model-rollback mandate. The decision is marked `UNSUPPORTED`.

The audit is a lexical/metadata screen. Its `UNSUPPORTED` and `PARTIALLY_SUPPORTED` labels require manual passage review; neither label is a legal opinion. The prospective citation code change now keeps exact chunk IDs named in a rationale visible for review. It does not establish that those sources support the rationale.

## ITU criteria evidence

The run exercises the staged, role-specific scenario and synthetic action sandbox. Source integrity also passed separately: `make verify-sources` verifies all 32 tracked source/extraction artifacts. The ten-question retrieval evaluation on the current index reached the exact passage in the top six for 9/10 cases and in the top three for 8/10; this curated seed does not measure legal accuracy. `make itu-smoke` successfully ingested the Y.3172 PDF with the pinned ITU reference package (50 chunks plus 19 framework definitions) into a separate local throwaway index. The active Borderline KB remains local; no ITU-hosted/distributed deployment was demonstrated.

This run is suitable as a transparent prototype demonstration, with its unsupported citations and unresolved assessments shown as limitations. It is not evidence of clinical accuracy, country readiness, legal compliance or full Y.3172 conformance.
