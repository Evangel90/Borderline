# Machine-assisted Arabic passage review: EDE powers

**Prepared:** 3 November 2026. **Status:** provisional reading aid; not a certified translation or legal opinion.

You do not need to read Arabic to use this packet. It identifies the relevant pages and explains what the available machine-readable text appears to say. For this review I compared the embedded Arabic text in the user-provided original PDF with the official UAE legislation portal's English translation, then checked the relevant provision structure and conditions. No human Arabic review has occurred.

## Documents and page references

The primary source is Federal Decree-Law No. 38 of 2024, Arabic original, registered as `AE-FEDERAL-DECREE-LAW-38-2024-AR`. The searchable PDF is at `data/raw/ae/AE_Federal_Decree_Law_38_2024_Medical_Products_AR.pdf`; its SHA-256 is recorded in `data/sources.csv`. The paired official English translation is `AE-FEDERAL-DECREE-LAW-38-2024-EN` and is a reading aid. The portal identifies Arabic as the official language for interpretation.

Check the printed Arabic page numbers 53–55 (the PDF viewer page number may differ because of front matter): Article 68(7) is on printed page 54; Article 70(1)–(2) begins on printed page 55. In the English translation these are printed pages 54 and 56, respectively. The Arabic file has embedded selectable text rather than requiring OCR, but extraction shows broken word ordering and spacing in places. A selectable text layer is not proof that extraction is accurate.

## What the text appears to say

| Provision | Machine-assisted reading | Conditions and limits visible in the text |
| --- | --- | --- |
| Article 68(7) | EDE investigates reports it receives about the cases in Article 68(3), checks their validity and accuracy in consultation and coordination with the relevant pharmaceutical or health establishments or biobanks, and may inspect, take samples, and request relevant information and documents. | The investigation power is tied to received reports about the Article 68(3) cases. Article 68(3) lists specified adverse events and product or research cases. It does not read as an unrestricted evidence-request power for any incident. |
| Article 70(1)–(2) | EDE may suspend circulation when needed to confirm information indicating a lack of product quality, safety, or effectiveness. Clause 2 describes investigation and confirmation of the cases in Clause 1, including consultation with relevant establishments, inspections, samples, and requests for relevant information and documents. | The investigation/request language is tied to the Article 70(1) cases. Those include specified product-quality, safety, effectiveness, authorization, and compliance conditions. Withdrawal is subject to the specified conditions and timing in Clause 1. |

This is a comparison of the available Arabic text and the portal's English translation. It suggests the English version preserves the broad structure of both provisions. It does not validate every Arabic word, resolve legal nuance, or establish that this scenario meets either provision's conditions.

## Why direct Arabic model reading has limits here

The 2024 Arabic PDF is selectable, but extraction output visible in the indexed chunks contains reordered fragments and unusual character sequences. This can disrupt clauses, negation, cross-references, and numbers. A language model can read Arabic directly, but if the supplied text is corrupted it may confidently interpret the corrupted sequence. The official English translation provides a useful independent comparison, but it is still a translation and does not remove uncertainty in the extracted Arabic.

The separate 2023 EDE-establishment PDF is scanned and was processed with Arabic OCR. That document has a higher text-recognition risk than the selectable 2024 law. Its Article 8 retrieval should be treated as a locator only until the OCR text is checked against the page image.

## What this means for the drill

The sources support a conditional proposition: EDE may investigate and request relevant evidence when the facts fall within the specified report or product-safety provisions. The drill leaves the product's UAE classification and marketing authorization, the Article 68(3) report status, and the Article 70(1) case conditions unverified. Therefore this review does not establish that either statutory pathway applies to the fictional incident. The current operational conclusion remains “applicability unresolved.”

The four weak EDE/clinic citations in the 2 November run are still correctly assessed as unsupported: their recorded passages did not support the specific claims made. This comparison does not retroactively make those citations adequate.

## If no Arabic reviewer is available

Use this as a provisional research aid. Preserve the Arabic PDF and its hash, cite the precise article and printed page, note that the English rendering is the portal translation, and state which factual conditions are unknown. Do not describe the Arabic wording as human-verified or the case-specific legal conclusion as settled. If a consequential decision must be made before specialist review is available, present the uncertainty to the responsible decision-maker and seek qualified UAE legal advice through an available official or professional channel.

Sources: [UAE legislation portal, Federal Decree-Law No. 38 of 2024 (Arabic)](https://uaelegislation.gov.ae/ar/legislations/2751); [official English translation](https://uaelegislation.gov.ae/en/legislations/2751/download).
