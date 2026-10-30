# Run review: `vector-retrieval-retry-20261030-1`

**Reviewed:** 30 October 2026  
**Scope:** first full drill using local multilingual Chroma retrieval. This is
an engineering and evidence-quality review, not legal advice or verification
of current law.

## Result

The seven default stages completed with 31 decisions from 12 agents. The
31-entry hash chain verifies with
`make verify-log RUN=vector-retrieval-retry-20261030-1`. All decisions record
retrieved chunk IDs. Every cited ID resolves to a chunk in the pack, appears
in that decision's retrieved set, and uses the matching page number. The
recorded event and payload views match the intent, and each selected action is
allowed by both the event view and the institution profile.

These checks establish traceability and simulation-boundary consistency. They
do not establish that a cited passage supports an agent's reasoning. This run
is not suitable as legal-accuracy evidence.

An initial attempt stopped before its first log entry because citation
validation rejected an empty citation list even when the model found no
supporting passage. Validation was corrected to match the prompt's instruction
to cite none when none supports the decision. The stopped attempt produced no
decision or gap record; this review covers the complete retry above.

## Findings requiring correction

| Severity | Run evidence | Finding |
| --- | --- | --- |
| High | Step 1 `screening_ai`, `report_model_update`: the rationale describes a user asking for a summary of supplied documents and AI ethics materials, rather than the model update in the drill. Its citations include a WHO footnote, an AI ethics opt-out passage, an ITU readiness passage, and a government-services execution passage. | The rationale is unrelated to the visible event, and the cited passages do not support the action. This is a model grounding failure despite valid citation IDs. |
| High | Step 4 `retina_swiss_ag`, `record_secondary_use_for_review`: cites `CH-DATA-FADP:p28:c1` (Art. 66, prosecution limitation) and `CH-HEALTH-MedDO:p35:c1` (Art. 87, Swissmedic access rights). | Neither excerpt supports the asserted cross-border processing and secondary-use review. The citations demonstrate a semantic retrieval and selection failure. |
| High | Step 2 `ede`, step 6 `ede`, and step 7 `ede`: manufacturer-evidence requests cite AI ethics, WHO guidance, or UAE PDPL transfer provisions. | These sources do not establish EDE's legal mandate or manufacturer-evidence powers. EDE's primary authorities remain unverified in the pack. |
| High | Step 2 `dha` and step 6/7 `dha`: patient follow-up, clinical review, and suspension assessment cite Dubai Law No. 26 of 2015 provisions concerning data registries/exchange and law enforcement. | These passages do not establish clinical follow-up duties or DHA suspension powers. DHA primary health policies and authority provisions remain outstanding. |
| High | Step 7 `uae_cyber` cites `AE-CYBER-LAW34:p6:c2`, a glossary passage defining encryption, for a security-evidence request. | The excerpt does not establish the cyber responder's mandate or the requested action. |
| Medium | Step 5 `retina_swiss_ag` cites an ITU AI-readiness passage for recording a research-purpose claim. Step 6 `swissmedic` cites a cybersecurity amendment alongside therapeutic-products material for a medical-device vigilance review. | The action may be a reasonable simulated review request, but these citations do not establish the stated legal basis. |
| Medium | Step 6 `mohap` and `ede` cite UAE PDPL transfer provisions for a simulated regulator-information request that explicitly excludes patient data and an EDE manufacturer-evidence request. | The retrieved transfer provisions do not establish either authority's power or the basis for this liaison route. The route remains a configured simulation rule, not a verified legal channel. |
| Medium | Step 3 and step 7 `ncsc` cite German Federal Gazette amendment chunks for an unresolved Swiss cyber-reporting scope assessment. | The agent correctly does not conclude that the vendor is covered. The German primary text and statutory-scope reasoning still need expert review; the citation alone does not prove the 24-hour deadline applies to this vendor. |
| Medium | The generated gap evidence assigns FADP Art. 16 relevance to `CH-DATA-FADP:p28:c1`, whose excerpt is Art. 66 on prosecution limitation. It also assigns MedDO Art. 66 relevance to `CH-HEALTH-MedDO:p28:c1`, whose excerpt is Art. 64 on traceability. | The gap register's configured relevance descriptions can overstate what its vector-selected chunks say. Treat this gap as a scenario coordination question only; its legal evidence needs correction and review. |

The stored gap artifact describes its retrieval as lexical. The run used the
new vector retrieval path, with term-based ranking afterward; that description
was stale. The orchestrator has been updated so future gap records describe
the current retrieval path and explicitly state that ranking does not verify
the relevance text.

## What the run does demonstrate

- The Chroma index returns source chunks within an agent's allowed
  jurisdictions and maps passage windows back to the exact chunk IDs.
- Retrieved IDs and cited IDs are retained in the audit log, and cited IDs
  resolve to their source chunks and provenance metadata.
- The NCSC action leaves reporting applicability unresolved rather than
  assuming that the Swiss vendor is in statutory scope.
- The step 6 liaison action records a simulated route only. No message or data
  leaves the local drill.
- EHS records a pause recommendation pending human approval; the simulated
  service is not paused by this run.

The citation-support problems mean the run validates index integration and
logging, not the correctness of legal retrieval or the six proposed domain
gaps. The gap remains one scenario-specific candidate, not a legal conclusion.

## Next work

1. Improve hybrid retrieval and query construction for event and institutional
   mandates; add checks that flag citations whose passage is unrelated to the
   stated action or legal concept.
2. Add primary sources for Cabinet Resolution No. 32 of 2020 and MoHAP
   Resolution No. 51 of 2021, plus primary EDE and DHA authorities, when the
   official files can be archived and verified.
3. Correct the gap evidence selectors and confirm the FADP/MedDO passages and
   German Swiss cyber-reporting provisions with a qualified reviewer.
4. Rerun the drill and review each citation before using it in the submission
   report. Keep the six brief themes marked as candidates until each has
   reviewed local and global evidence.
