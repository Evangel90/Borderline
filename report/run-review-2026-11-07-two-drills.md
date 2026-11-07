# Run review: main drill and companion drill, 7 November 2026

**Model:** local `qwen3:8b` via Ollama, 16,384-token context · **Status:** unreviewed drill output, not legal conclusions. Run folders are git-ignored and exist only on the machine that produced them.

| Run | Drill | Decisions | Hash chain | Audit flags |
|---|---|---|---|---|
| `retinopathy-main-20261107-2` (with optional step 13) | `retinopathy-ae-ch` | 37 | verified | 8 |
| `retinopathy-coop-20261107-1` | `retinopathy-ae-ch-cooperation` | 7 | verified | 3 |

## Step coverage (`make step-coverage`, written to `report/step-coverage.json`)

- **Main drill:** steps 1–6, 8, 9, 11, 12 and 13 ran. Steps 7 and 10 were skipped because both letters were blocked. Unlike the first run, the Data Office now sends its letter at step 6, so step 8 runs.
- **Companion drill:** steps 1, 2, 4, 5, 7 and 8 ran. Steps 3 and 6 were skipped because both letters were blocked.
- **No unconditional step was missed in either run.**
- **Not yet covered in any run:** the three "delivered" branches (Data Office → FDPIC, DHA → Swissmedic, EDE → Swissmedic).

## Liaison decisions

All five letters were blocked; none carried patient data.

| Letter | Legal basis | Transfer rules | Counterpart | Quotes verified |
|---|---|---|---|---|
| Main: MoHAP → Swissmedic | UNCLEAR, `policy_gap` | UNCLEAR, `policy_gap` | YES (flagged for human review) | 5/5 |
| Main: Data Office → FDPIC | UNCLEAR, `missing_evidence` | UNCLEAR, `missing_evidence` | YES (flagged) | 9/9 |
| Main: DHA → Swissmedic | YES (flagged; rests on TPA Art. 63, a Swiss-domestic rule) | UNCLEAR (quote failed) | UNCLEAR (quote failed) | 3/5 |
| Companion: Data Office → FDPIC (staff data) | UNCLEAR, `missing_evidence` (reviewer's own answer) | UNCLEAR, `missing_evidence` | YES (flagged) | 7/8 |
| Companion: EDE → Swissmedic (vigilance) | proposed **YES** → UNCLEAR (quote failed) | UNCLEAR | proposed **YES** → UNCLEAR (quote failed) | 3/6 |

**Why EDE's letter was blocked: a citation slip, not a legal finding.** The reviewer quoted the right provision, the opening of TPA Art. 64: "The federal authorities responsible for the enforcement of this Act may disclose information which is not publicly accessible …". But it gave chunk ID `CH-HEALTH-TPA:p41:c1`. That sentence is on page 40 (`p40:c1`), and Art. 64 continues onto page 41. The code checks the quote against the cited passage, so it rejected it as designed.

**Why the companion Data Office letter was blocked: the reviewer's own call.** It answered UNCLEAR on legal basis even though FADP Art. 55 was shown and verified, probably because the reciprocity assurance is only a drill fact.

## Fixes from the first review, as seen in these runs

- **Human-review flag:** every YES now carries it. DHA's Art. 63 YES is flagged.
- **Policy adviser's own cited answers now reach the log:** main steps 8, 12 and 13, and companion steps 4 and 8.
  - Step 5 (main) and step 7 (companion) were still rewritten, because those answers had no citation that survived screening.
  - Several kept answers lean on the OECD Recommendation. They need a human check for relevance.
