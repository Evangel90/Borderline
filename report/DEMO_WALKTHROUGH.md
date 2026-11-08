# Borderline demo walkthrough (final runs, 8 November 2026)

## One-sentence story

When a Swiss-made screening AI fails in Dubai, Borderline rehearses which cross-border letters may legally go out, which AI agent decided what, and where the rules run out. Code checks every quote and stops patient data unless a verified legal basis is quoted and a recorded human approval matches the disclosure.

Abbreviations, spelled out once: Emirates Drug Establishment (EDE); Swiss Agency for Therapeutic Products (Swissmedic); Federal Data Protection and Information Commissioner (FDPIC); Dubai Health Authority (DHA); Ministry of Health and Prevention (MoHAP); Therapeutic Products Act (TPA); Federal Act on Data Protection (FADP); Personal Data Protection Law (PDPL).

## Before you start

The demo uses the four final runs, all made on the same code (`b229477`), not live model calls. The runs exist only on the machine that produced them (`runs/` is git-ignored). Their decision trails are committed in `report/`.

| Drill | Run ID | Decision trail |
|---|---|---|
| A, governed | `governed-20261108-4` | `report/decision-trail-governed-20261108-4.md` |
| B, ungoverned (with optional step 13) | `ungoverned-20261108-3` | `report/decision-trail-ungoverned-20261108-3.md` |
| C, insufficient evidence | `insufficient-20261108-3` | `report/decision-trail-insufficient-20261108-3.md` |
| D, scripted control for A (not an AI decision) | `governed-scripted-20261108-3` | `report/decision-trail-governed-scripted-20261108-3.md` |

## Sequence (about six minutes)

1. **Set the scene (0:00–0:40).** RetinaVision-DX is a fictional Swiss diabetic-retinopathy screening service used at fictional Dubai clinics. An update misses referable disease in 47 synthetic patients, the update came from a compromised vendor account, and UAE images in Zurich were reused for retraining. Say "fictional" and "synthetic"; the laws are real.

2. **Who decides (0:40–1:30).** Open `report/decision-trail-ungoverned-20261108-3.md`. Show the first table: 12 institutions, each an AI agent (`qwen3:8b`, run locally) choosing from its own allowed actions. Then show a letter table and its three columns:
   - "AI liaison reviewer proposed";
   - "Final";
   - "Final answer decided by", which names either the reviewer or a code rule.

3. **Patient data stopped at the border (1:30–2:15).** Still in Drill B, go to step 14. DHA tries to send patient images to Swissmedic. The reviewer answered UNCLEAR on legal basis and transfer rules, and code's patient-data rule blocked the letter. Then show step 13: DHA's request named no receiver, so code blocked it without asking the three questions.

4. **Code catches joined quotes (2:15–3:00).** Drill B step 9: the reviewer proposed YES on transfer rules and counterpart, but its quotes joined TPA Art. 64's heading to paragraph 2, so code set those answers to UNCLEAR and the letter was blocked. Also show the accepted copy slip: the reviewer wrote "ProperProtection", code accepted it as one slip and logged the exact source text, "Proper Protection".

5. **The governed drill, and its control (3:00–4:15).** Open `report/decision-trail-governed-20261108-4.md` (Drill A). The three letters were written to real provisions (TPA Art. 64, FADP Art. 55), with the senders' assurances as labelled synthetic exhibits. The reviewer said YES on legal basis each time, but misread the transfer question at step 2 and joined quotes at steps 5 and 8, so all three were blocked. We did not loosen any check. Then open `report/decision-trail-governed-scripted-20261108-3.md` (Drill D): the same letters, with the hand-written reference answers in place of the AI reviewer, were all delivered, and the recall list crossed only because a recorded human approval matched it. Say plainly that Drill D's answers are not AI decisions, and show step 9, where the receiving FDPIC agent still recommended pausing.

6. **When evidence is missing (4:15–5:00).** Open `report/decision-trail-insufficient-20261108-3.md` (Drill C). The letter without a reciprocity assurance was blocked. Say that this drill did not go as expected: the reviewer typed its UNCLEAR answers as `policy_gap` and `implementation_gap` instead of sending them to homework, quoting real FADP passages that do not concern transfer. Code checks that quotes are real, not that they apply; a person must review that record. Resolution 51/2021 is registered as missing and is not hunted for.

7. **Proof and candidates (5:00–6:00).** Run:

   ```sh
   make verify-log RUN=ungoverned-20261108-3
   make replay RUN=governed-20261108-4
   make assess-candidates
   ```

   The hash chain verifies, and the replay re-runs every code decision with 0 differences. The candidate assessment shows four `SUPPORTED_CANDIDATE`s (candidates, unreviewed, not legal conclusions). Close on CAND-003: neither country is in the International Medical Device Regulators Forum (IMDRF) incident-report exchange.

## Optional user interface (UI) route

`make ui` starts the Streamlit viewer. It was built for the earlier pre-deployment run and **has not been checked against the final runs**. Use the decision-trail files unless the viewer has been checked first.

## Presenter checklist

- Say "candidate", never "finding" or "violation". Nothing here is a legal conclusion.
- Name the decider every time: institution AI agent, AI liaison reviewer, or code.
- Say plainly that the AI liaison reviewer delivered no governed letter, that Drill D's deliveries used scripted answers, and that Drill C did not go as expected.
- Expand each abbreviation the first time you say it.
