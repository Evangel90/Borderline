# Run review: `retinopathy-agentic-classification-20261103-1`

**Run date:** 3 November 2026. **Model:** local `qwen3:8b`.

This is the first full run using the expanded agentic product dossier, the fictional EDE classification letter, and the fictional manufacturer corrective-action plan. It completed 32 decisions and two governance assessments. The hash chain verified successfully; final hash: `e4b37bf86f814b981301b23922b45760e528399443b4f6acb4752158414b63b6`.

## What the run demonstrates

The EDE agents received the classification as a scenario fact and selected `request_ede_manufacturer_evidence` at steps 2, 6, and 7. This shows the mock classification is visible in the intended way. The classification still did not establish Article 68 or Article 70 applicability by itself.

At step 7, the EDE rationale said Articles 68(7) and 70(2) allow an evidence request “if there is a safety concern” and concluded EDE “must request” evidence. That overstates the provisions: Article 68(7) is tied to qualifying reports under Article 68(3), while Article 70(2) is tied to the cases in Article 70(1). Those scenario predicates remain unverified. This manual finding is recorded as `CR-024` in `data/claim_review_seed.csv`.

The submitted manufacturer plan did not become a completed remediation. The EDE payload marked completion unverified, and the clinic still requested a manual-capacity and patient-follow-up review after a halt recommendation. No service halt, rollback, data transfer, or external regulatory communication occurred; tool effects remain simulated.

## Audit and limits

`make audit-evidence RUN=retinopathy-agentic-classification-20261103-1` found 16 decisions with no recorded citations and no additional lexical citation flags. Manual review added one unsupported legal-basis case (`CR-024`) that the lexical audit did not detect. This illustrates that a clean lexical audit does not establish exact legal support. The audit is not a legal-accuracy score, and the selected claim seed is not a general benchmark.

`make evaluate-claims` on the selected 24-case review set reports manual labels of 21 `UNSUPPORTED`, one `INSUFFICIENT_EVIDENCE`, and two `PARTIALLY_SUPPORTED`; triage outputs 19, four, and one respectively. The new CR-024 disagreement is classified as insufficient evidence by triage because it has no recorded citation, while manual review identifies the specific legal overstatement. This selected set is issue-focused and is not a general accuracy estimate.

The product letter and manufacturer plan are fabricated, canonical facts inside this simulation only. They are not real EDE or manufacturer records. Device risk class, detailed authorization-holder status, actual statutory report/case predicates, and whether the fictional corrective actions would be effective remain unresolved or untested.
