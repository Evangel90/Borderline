# Borderline demo walkthrough (8 November 2026 runs)

## One-sentence story

When a Swiss-made screening AI fails in Dubai, Borderline rehearses which cross-border letters may legally go out, which AI agent decided what, and where the rules run out. Code checks every quote and stops patient data unless a verified legal basis is quoted.

Abbreviations, spelled out once: Emirates Drug Establishment (EDE); Swiss Agency for Therapeutic Products (Swissmedic); Federal Data Protection and Information Commissioner (FDPIC); Dubai Health Authority (DHA); Ministry of Health and Prevention (MoHAP); Therapeutic Products Act (TPA); Federal Act on Data Protection (FADP); Personal Data Protection Law (PDPL).

## Before you start

The demo uses saved runs, not live model calls. The three runs below exist only on the machine that produced them (`runs/` is git-ignored). Their decision trails are committed in `report/`.

| Drill | Run ID | Decision trail |
|---|---|---|
| A, governed | `governed-20261108-1` | `report/decision-trail-governed-20261108-1.md` |
| B, ungoverned (with optional step 13) | `ungoverned-20261108-1` | `report/decision-trail-ungoverned-20261108-1.md` |
| C, insufficient evidence | `insufficient-20261108-1` | `report/decision-trail-insufficient-20261108-1.md` |
| D, scripted control for A (not an AI decision) | `governed-scripted-20261108-1` | `report/decision-trail-governed-scripted-20261108-1.md` |

## Sequence (about six minutes)

1. **Set the scene (0:00–0:40).** RetinaVision-DX is a fictional Swiss diabetic-retinopathy screening service used at fictional Dubai clinics. An update misses referable disease in 47 synthetic patients, the update came from a compromised vendor account, and UAE images in Zurich were reused for retraining. Say "fictional" and "synthetic"; the laws are real.

2. **Who decides (0:40–1:30).** Open `report/decision-trail-ungoverned-20261108-1.md`. Show the first table: 12 institutions, each an AI agent (`qwen3:8b`, run locally) choosing from its own allowed actions. Then show a letter table and its three columns:
   - "AI liaison reviewer proposed";
   - "Final";
   - "Final answer decided by", which names either the reviewer or a code rule.

3. **Patient data stopped at the border (1:30–2:30).** Still in Drill B, go to step 14. DHA tries to send patient images to Swissmedic. The reviewer said YES on legal basis, citing a PDPL company-transfer rule, and UNCLEAR on transfer rules. Code's patient-data rule blocked the letter. Point out the honest part: the YES was flagged for human review because the quote is real, but the PDPL excludes health data covered by its own law (`AE-DATA-PDPL-2021-EN:p6:c2`). Code checks that a quote is real; a person checks that it applies.

4. **Code catches an invented quote (2:30–3:15).** Drill B step 9: the reviewer said YES three times, but its transfer-rules "quote" joined a page header to FADP Art. 55 and skipped Art. 54. Code found it was not in the source and set the answer to UNCLEAR, so the letter was blocked.

5. **The governed drill, and why it did not deliver (3:15–4:15).** Open `report/decision-trail-governed-20261108-1.md`. The three letters were written to the conditions of real provisions (TPA Art. 64, FADP Art. 55), but all three were blocked. In each case the reviewer answered UNCLEAR on legal basis, and code did not overrule it. Present this as a finding: the assurances existed only as data fields, not as quotable documents, and the project's own reference table also says UNCLEAR. We did not loosen any check to make the letters pass. Then open `report/decision-trail-governed-scripted-20261108-1.md` (Drill D): the same letters, with the hand-written reference answers in place of the AI liaison reviewer, were all delivered, so the blocks come from the AI review. Say plainly that Drill D's answers are not AI decisions, and show step 9, where the receiving FDPIC agent still recommended pausing.

6. **Homework, not accusations (4:15–5:00).** Open `report/decision-trail-insufficient-20261108-1.md` (Drill C). The letter without a reciprocity assurance was blocked, and the open questions went to the homework list (`liaison_homework.jsonl`, 2 items), not to gap candidates. Resolution 51/2021 is registered as missing and is not hunted for.

7. **Proof and candidates (5:00–6:00).** Run:

   ```sh
   make verify-log RUN=ungoverned-20261108-1
   make step-coverage RUNS="retinopathy-governed=governed-20261108-1 retinopathy-ae-ch=ungoverned-20261108-1 retinopathy-insufficient-evidence=insufficient-20261108-1"
   make assess-candidates
   ```

   The hash chain verifies. Step coverage shows every blocked branch covered and no delivered branch reached. The candidate assessment shows four `SUPPORTED_CANDIDATE`s (candidates, unreviewed, not legal conclusions). Close on CAND-003: neither country is in the International Medical Device Regulators Forum (IMDRF) incident-report exchange.

## Optional user interface (UI) route

`make ui` starts the Streamlit viewer. It was built for the earlier pre-deployment run and **has not been checked against the 8 November runs**. Use the decision-trail files unless the viewer has been checked first.

## Presenter checklist

- Say "candidate", never "finding" or "violation". Nothing here is a legal conclusion.
- Name the decider every time: institution AI agent, AI liaison reviewer, or code.
- Say plainly that no governed letter was delivered in these runs, and that one request at Drill B step 13 bypassed the liaison check (a known defect).
- Expand each abbreviation the first time you say it.
