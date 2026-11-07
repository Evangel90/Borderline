# Gap candidates: health-data authority, AI change control, incident-report exchange

**Date:** 7 November 2026 · **Status:** candidates, not findings · **Search records:** `gaps/searches/`

> **Update, step 2 (7 November 2026, later).** Candidate status is now set by code, not by hand: `make assess-candidates` applies the evidence-sufficiency rule to `gaps/candidate_register.yaml` and writes `report/candidate-status.json`. Under that rule CAND-001, CAND-002 and CAND-003 are `OPEN_CANDIDATE`: each waits on one obtainable document that could refute it (OECD adherents list; a clean Arabic text of Federal Decree-Law 38/2024; the Swiss–EU mutual recognition agreement). CAND-004, Resolution 51 "not publicly accessible to the project after documented attempts", is `SUPPORTED_CANDIDATE` (unreviewed). The assessments in the table below are the earlier hand-made ones; the JSON file is authoritative.

Nothing in this file is a legal conclusion. Nobody with legal standing has reviewed it. Each candidate states what the registered sources say, quoted exactly with the chunk ID, what we searched for and did not find, and what evidence is still missing. "Not found" means not found in this knowledge base. It does not mean the law is silent.

| Candidate | Type | Assessment | Strongest evidence | Main open question |
|---|---|---|---|---|
| CAND-003 Incident-report exchange | coordination / standards | `SUPPORTED_CANDIDATE` | IMDRF participant list names neither country | Any bilateral UAE–Swiss vigilance arrangement outside this knowledge base |
| CAND-002 AI change control | standards | `PARTLY_SUPPORTED` (UAE side) | DHA's undefined "major upgraded versions" vs. EU/Swiss prior-approval rule and the EU's worked example of a significant algorithm change | EDE rules in Arabic sources not fully searched |
| CAND-001 Health-data authority abroad | coordination / policy | `INSUFFICIENT_EVIDENCE` | PDPL excludes health data; Swiss FADP needs a data-protection counterpart | Data Office may act through agreements; Resolution 51 not obtained |

## CAND-003: Neither country is in the international device-incident exchange

**Type:** coordination / standards · **Assessment:** `SUPPORTED_CANDIDATE`

**Hypothesis.** An international channel exists for medical-device regulators to exchange incident reports under confidentiality arrangements, but neither Swissmedic nor any UAE regulator participates. In the drill, a Swiss-made device harming UAE patients has no established regulator-to-regulator incident channel.

| Source | Quote | Chunk |
|---|---|---|
| IMDRF N14 (2025), 4.2 | "Participation in the NCAR Exchange Program will be limited to the IMDRF Management Committee (MC) Regulators. A list of NCAR Participant Countries is provided in Annex1." | `IMDRF-NCAR-N14-2025:p9:c1` |
| IMDRF N14 (2025), 4.2 | "IMDRF MC Regulators who intend to participate in the NCAR Exchange Program will need where possible to have confidentiality arrangements in place with other participating NCAs and the NCAR Secretariat." | `IMDRF-NCAR-N14-2025:p9:c2` |
| IMDRF N14 (2025), Annex 1 | "Annex 1– IMDRF NCAR Participant Countries" (27 entries; neither Switzerland nor the United Arab Emirates is listed) | `IMDRF-NCAR-N14-2025:p16:c1` |
| Bridge pack, incident notification rule | No UAE–Switzerland vigilance or incident-notification exchange instrument is registered. | `packs/bridge/ae-ch.yaml` |

**Refuting evidence to look for:** a bilateral UAE–Swiss memorandum on device vigilance; Swissmedic access to NCAR reports through the European Commission (listed in Annex 1) under the Swiss–EU mutual recognition agreement; IMDRF membership changes after March 2025.

## CAND-002: The UAE rule for approving AI software upgrades is undefined

**Type:** standards · **Assessment:** `PARTLY_SUPPORTED` (UAE side)

**Revised hypothesis.** Switzerland, through the EU MDR annexes it applies, requires prior approval of device changes that could affect safety or performance. The registered UAE sources require certification of "major upgraded versions" of AI software without defining "major" or naming the certifying body. International practice (IMDRF, FDA) adds AI-specific controls for retraining. The candidate gap is on the UAE side; the Swiss side has a general rule that would reach the drill's retraining, so a Swiss gap is not claimed.

| Source | Quote | Chunk |
|---|---|---|
| DHA AI in Healthcare Policy, 4.6.10 | "Comply with all required certification of the AI software and its major upgraded versions from recognized international/local agencies." | `AE-DHA-AI-HEALTH-2021:p10:c1` |
| Swiss MedDO, Art. 23 | "The conformity assessment procedure is governed by Articles 52 and 54 and by Annexes IX–XI to EU-MDR" | `CH-HEALTH-MedDO:p13:c1` |
| EU MDR, Annex IX 4.10 | "Changes to the approved device shall require approval from the notified body which issued the EU technical documentation assessment certificate where such changes could affect the safety and performance of the device or the conditions prescribed for use of the device." | `EU-MDR-2017-745:p202:c1` |
| EU MDCG 2020-3 Rev.1 (2023), examples of significant software changes | "change of an algorithm which impact the operating principles or impact the control of the device and may alter the diagnosis or therapy delivered" | `EU-MDCG-2020-3-REV1:p13:c2` |
| IMDRF N88 (2025), principle 10 | "when models are retrained after deployment, there are appropriate controls in place to manage risks of overfitting, unintended bias, or degradation of the model (for example, dataset drift) that may impact the safety and performance of the model." | `IMDRF-AIML-N88-2025:p8:c2` |
| US FDA PCCP guidance (nonbinding comparator) | "1) a detailed description of the specific, planned device modifications, which is referred to as the “Description of Modifications”; 2) the associated methodology to develop, validate, and implement those modifications in a manner that ensures the continued safety and effectiveness of the device across the intended use populations, which is referred to as the “Modification Protocol”; and 3) the assessment of the benefits and risks of the planned modifications and risk mitigations, which is referred to as the “Impact Assessment.”" | `US-FDA-PCCP-AI-2025:p7:c2` |

**About the EU guidance.** MDCG 2020-3 is nonbinding and applies only to legacy devices still on old MDD/AIMDD certificates; devices certified under the MDR follow Annex IX 4.10 above. It is cited here as a worked example of what a defined "significant algorithm change" looks like. A retraining that may alter the diagnosis, as in the drill, would fall on the significant side.

**Search records:** `SEARCH-AI-CHANGE-CONTROL-001` (UAE and Swiss) and `SEARCH-AI-CHANGE-CONTROL-002` (adds EU, IMDRF, FDA). "Predetermined change control", "change control plan" and "modification protocol" appear only in the FDA guidance. "Machine learning" does not appear in the EU MDR.

**Refuting evidence to look for:** EDE requirements for software changes in Federal Decree-Law No. 38 of 2024 or its implementing rules (the English search found only drug-oriented re-approval grounds; Arabic sources were not covered); any UAE AI-device guidance outside this knowledge base.

## CAND-001: No clearly competent UAE counterpart for protecting UAE health data abroad

**Type:** coordination / policy · **Assessment:** `INSUFFICIENT_EVIDENCE`

**Hypothesis.** When UAE patients' health data is held and reused abroad, the registered sources do not clearly name a UAE authority that is both competent for that data and set up to ask the foreign data-protection authority for help.

| Source | Quote | Chunk |
|---|---|---|
| UAE PDPL, Art. 2(2) | "Provisions of this Decree by Law shall not apply to the following: … e. Personal Health Data that has legislation regulating its protection and processing." | `AE-DATA-PDPL-2021-EN:p6:c2` |
| UAE Health Data Law, Art. 13 | "It is not permissible to store, process, generate or transform the health data and information outside State -which are related to the health services provided inside State- except in the case where a resolution is issued from the Health Authority in coordination with the Ministry." | `AE-HEALTH-ICT-LAW-2019:p8:c1` |
| DHA health data policy PP-11, 4.15.1 | "Protected health information should not be transferred to a country or territory outside the UAE; except for transfer of PHI within the category of UAE ICT Health Law exemptions" | `AE-DHA-HEALTH-DATA-PROTECTION-PP11-2022:p27:c1` |
| DHA health data policy PP-11, 4.19.3 | "must inform the UAE Information Office and DHA the contact details of the appointed DPO." | `AE-DHA-HEALTH-DATA-PROTECTION-PP11-2022:p35:c1` |
| DHA health information sharing policy PP-13 (2024), 4.20.1 | "Protected health information should not be transferred to a country or territory outside the UAE; except for transfer of PHI within the category of Cabinet Decision No. (51) of year 2021" | `AE-DHA-HEALTH-INFO-SHARING-PP13-2024:p30:c2` |
| DHA PP-13 (2024), 4.7.5 secondary use without consent | "For the purposes of scientific and clinical research, provided that the ethics and rules of scientific research are followed as per ICH_GCP principles and guidelines. Non-identifiable If Identifiable data needed, then Patient consent required" | `AE-DHA-HEALTH-INFO-SHARING-PP13-2024:p18:c2` |
| UAE Data Office law, Art. 3(9) | "Propose joining or signing the international conventions and agreements and propose the partnership agreements with the gulf, regional and international states, organisations, and bodies with regards to the activities and competencies of the Office" | `AE-DATA-OFFICE-LAW-44-2021:p2:c2` |
| Swiss FADP, Art. 55(1) | "The FDPIC may exchange information or personal data with foreign authorities that are responsible for data protection in order that they may fulfil their respective statutory duties in relation to data protection, provided the following requirements are satisfied: a. Reciprocity with regard to administrative assistance is guaranteed." | `CH-DATA-FADP:p24:c1` |
| OECD Recommendation (2007), para. 19 (global comparator) | "Member countries should designate a national contact point for co-operation and mutual assistance under this Recommendation" | `OECD-LEGAL-0352:p9:c1` |

**What changed with the new evidence.** DHA's policy gives Dubai a working rule for health data leaving the UAE (exemptions plus DHA approval). It also has facilities report their data-protection officer to a federal office as well as DHA. The English text says "UAE Information Office"; the Arabic version says "Emirates Data Office". So the Data Office has some role in health data in Dubai. And the Data Office law lets it propose international agreements. The candidate therefore narrows: the authorities exist, but no registered instrument connects either of them to the Swiss FDPIC with the reciprocity FADP Art. 55 requires.

**The vendor's "research" claim, tested against DHA's 2024 policy.** PP-13 allows research use of health data without consent only for non-identifiable data and only if ICH-GCP ethics and rules are followed; identifiable data needs patient consent. In the drill the vendor has no ethics approval, no consent records and no de-identification log. On the drill's facts, the claim does not meet DHA's stated conditions. Calling it product development instead would not help: on the rendered PDF page (p. 18) the condition cell "Non-identifiable / If Identifiable data needed, then Patient consent required" is one merged cell spanning both the research row and the row "For development and innovation activities or health registries". Text extraction attached it to the research row only. One limit remains: PP-13 binds healthcare entities under DHA jurisdiction (the Dubai clinics), not the Swiss vendor directly.

**Search record:** `SEARCH-HEALTH-DATA-AUTHORITY-001` (20 UAE documents, including both DHA data policies and the Data Office law): "foreign authorit" and "reciproc" not found.

**Resolution No. 51 of 2021 could not be obtained (7 November 2026).** It exists: MoHAP's archived document viewer is titled "قرار وزاري رقم ( 51 ) لسنة 2021م بشأن الحالات التي يجوز فيها تخزين أو نقل البيانات والمعلومات الصحية إلى خارج الدولة" (*unofficial translation by the project, not an official text: "Ministerial Resolution No. (51) of 2021 on the cases in which health data and information may be stored or transferred outside the State"*; 4 pages), but the archive kept no readable page images. MoHAP's sites refuse connections from outside the region. The link in DHA's policy (4.15.1) points to a gazette issue containing the federal narcotics law, not Resolution 51. Its content is known here only from law-firm summaries, which are not quotable evidence. That a regulator's own policy links to the wrong legal instrument is itself an implementation weakness worth noting.

**Refuting evidence to look for:** the text of Ministerial Resolution No. 51 of 2021 (law-firm summaries say it has about ten exceptions, including research with health-authority approval; if that holds, the vendor's unapproved "research" retraining would still fall outside it); any Data Office cooperation agreement or OECD contact-point designation (the UAE is not an OECD member, so adherence must be checked); PDPL Executive Regulations (reportedly not yet issued as of mid-2026; not verified against the Official Gazette).
