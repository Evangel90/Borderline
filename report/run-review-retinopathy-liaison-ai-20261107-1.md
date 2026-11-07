# Run review: retinopathy-liaison-ai-20261107-1

**Date:** 7 November 2026 · **Code:** `incident-drill` at `4a81067` · **Model:** local `qwen3:8b` via Ollama, 16,384-token context · **Status:** unreviewed drill output, not legal conclusions

The run directory (`runs/retinopathy-liaison-ai-20261107-1/`) is git-ignored and exists only on the machine that produced it. Final log hash `991654caadd1a57d398691a1024fe69437991569a641170b4f6421986f5df4c5`.

## Checks

| Check | Result |
|---|---|
| `make drill` | completed, exit 0, 29 decisions |
| `make verify-log` | hash chain verified |
| `make audit-evidence` | 6 decisions flagged (5 `no_citation`, 1 `citation_needs_review`); adjudicated below |
| Steps run | 1–6, 9, 11, 12. Skipped by condition: 7 and 8 (the UAE Data Office sent no letter), 10 (DHA's letter was blocked). Optional step 13 not run. |
| Evidence status | 17 `PARTIALLY_SUPPORTED`, 11 `INSUFFICIENT_EVIDENCE`, 1 `UNSUPPORTED` |
| Rationale | 22 model explanations, 7 rule-constrained rewrites |

## Liaison channel: AI reviewer decisions

Two letters were sent; both were blocked. Neither carried patient data, so the patient-data floor did not apply.

| Letter | Legal basis | Transfer rules | Counterpart | Quotes verified | Differs from YAML reference on |
|---|---|---|---|---|---|
| MoHAP → Swissmedic (step 6) | UNCLEAR, `policy_gap` | UNCLEAR, `policy_gap` | YES | 5 of 5 | transfer rules (YAML: YES) |
| DHA → Swissmedic (step 9) | YES | UNCLEAR, `missing_evidence` (one quote failed) | UNCLEAR, `missing_evidence` (proposed YES; quote failed) | 3 of 5 | all three |

- The code check worked as designed: two quotes that were not word for word in their chunks (`OECD-LEGAL-0352:p8:c1`, `CH-HEALTH-TPA:p41:c1`) turned their answers into UNCLEAR / `missing_evidence`.
- **Needs human review: DHA's legal-basis YES.** It rests on a verified quote from TPA Art. 63, "The federal and cantonal authorities responsible for enforcing this Act shall ensure mutual disclosure of the data …". Art. 63 is headed "Data disclosure between the enforcement authorities **in Switzerland**"; it is not a basis for disclosure to a foreign authority (that is Art. 64). The quote is exact, so the code accepted it. **The code verifies that a quote is exact, not that it supports the answer.** The letter was blocked anyway on the other two questions.
- The model often put its quotes in the `reason` field and reused one passage across questions.
- Result: one liaison gap candidate (`LIAISON-6-mohap`, `policy_gap`). DHA's letter produced two `missing_evidence` homework items and no candidate.

## Step 3 questions

| View | Passage shown | What the agent did |
|---|---|---|
| Step 5, policy adviser (research claim vs PP-13) | PP-13 4.7.5 (`p18:c2`) | Chose `request_gap_supporting_evidence`; the generic rewrite replaced its explanation and dropped citations. The research claim was not tested in the output. |
| Step 11, policy adviser (NCAR participants) | Annex 1 (`p16:c1`) and `p9:c2` | Said Switzerland and the UAE are not listed as NCAR participants, but cited `p9:c2` (confidentiality arrangements) instead of Annex 1 (`p16:c1`), and wrongly linked the NCAR point to why the liaison check failed. Needs review. |
| Step 12, DHA (research claim vs PP-13) | PP-13 4.7.5 | Chose the new `assess_secondary_use_claim` and cited PP-13 4.7.5: the vendor's claim "lacks required ethics approval, patient consent records, and de-identification logs". Overstates the policy as "mandated" and does not say whom it binds (the clinics, not the vendor). |
| Step 12, policy adviser | PP-13 4.7.5, NCAR `p9:c2`, `p16:c1` | Chose `request_gap_supporting_evidence`; rewritten, no citations. |

## Adjudication of flagged decisions

| Entry | Flag | Adjudication |
|---|---|---|
| `log-2-screening_ai` | no citation | Acceptable: action rests on visible audit facts. |
| `log-3-retina_swiss_ag` | no citation | Acceptable: preservation rests on visible incident facts. |
| `log-3-ncsc` | no citation | Needs a citation: names the Information Security Act reporting duty without citing it (hedged as "to determine if"). |
| `log-11-dha` | no citation | Overstates: "DHA's mandate includes coordinating patient follow-up" comes from the institution profile, not a source; "without … consent" is not a visible fact (the view says only that data lineage is unknown). |
| `log-12-screening_ai` | citation needs review | Unsupported: WHO guideline p. 94 is about product liability, not pausing a screening service. The citation should be dropped. |
| `log-12-ncsc` | no citation | Same as `log-3-ncsc`: names the ISA without citing it; hedged. |

## What to fix before relying on these numbers

1. The liaison quote check needs a relevance guard, or human review of every YES, because an exact but irrelevant quote can pass (DHA, TPA Art. 63).
2. The policy adviser's substantive answers at steps 5 and 12 are replaced by the generic `request_gap_supporting_evidence` rewrite, so the step-3 questions mostly do not reach the output for the adviser.
3. The UAE Data Office chose `assess_regulatory_competence` instead of writing to the FDPIC, so the Data Office → FDPIC letter (and steps 7–8) did not occur in this run.
