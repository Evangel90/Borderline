# Decision trail: governed-20261108-3

Unreviewed synthetic drill output; nothing here is a legal conclusion. Every AI decision was made by a model that sees only what its institution can see, and it may have missed things a person would consider.

## Institution decisions (each made by that institution's AI agent)

| Step | Institution | Decided by | Action chosen | Explanation | Evidence status |
|---|---|---|---|---|---|
| 1 | Swiss Agency for Therapeutic Products (Swissmedic) | AI agent (qwen3:8b) | `review_foreign_incident_report` | agent's own words | PARTIALLY_SUPPORTED |
| 2 | Emirates Drug Establishment (EDE) | AI agent (qwen3:8b) | `request_regulatory_evidence` | agent's own words | INSUFFICIENT_EVIDENCE |
| 4 | Neutral Policy and Legal Adviser | AI agent (qwen3:8b) | `request_gap_supporting_evidence` | agent's own words | PARTIALLY_SUPPORTED |
| 5 | Swiss Agency for Therapeutic Products (Swissmedic) | AI agent (qwen3:8b) | `share_patient_data_via_liaison` | agent's own words | PARTIALLY_SUPPORTED |
| 7 | Swiss Agency for Therapeutic Products (Swissmedic) | AI agent (qwen3:8b) | `review_foreign_incident_report` | agent's own words | PARTIALLY_SUPPORTED |
| 7 | Neutral Policy and Legal Adviser | AI agent (qwen3:8b) | `request_gap_supporting_evidence` | agent's own words | PARTIALLY_SUPPORTED |
| 8 | UAE Data Office | AI agent (qwen3:8b) | `request_regulatory_evidence` | agent's own words | PARTIALLY_SUPPORTED |
| 10 | Neutral Policy and Legal Adviser | AI agent (qwen3:8b) | `request_gap_supporting_evidence` | agent's own words | PARTIALLY_SUPPORTED |
| 11 | Neutral Policy and Legal Adviser | AI agent (qwen3:8b) | `request_gap_supporting_evidence` | agent's own words | PARTIALLY_SUPPORTED |

## Cross-border letters

### Step 2: Emirates Drug Establishment (EDE) → swissmedic (no patient data)

- Sending the letter: directed by the scenario (the only action offered to the ede AI agent at this step).
- Result: **BLOCK**, decided by code routing rule: at least one final answer is not YES.
- Quotes: 3 of 3 verified by code.

| Question | AI liaison reviewer proposed | Final | Final answer decided by | Needs human check |
|---|---|---|---|---|
| Is there a legal basis to share? | YES | YES | AI liaison reviewer (qwen3:8b) | yes |
| Is the transfer allowed under both sides' rules? | UNCLEAR | UNCLEAR (missing_evidence) | AI liaison reviewer (qwen3:8b) | no |
| Is the receiver the right counterpart? | YES | YES | AI liaison reviewer (qwen3:8b) | yes |

### Step 5: Swiss Agency for Therapeutic Products (Swissmedic) → ede (carries patient data)

- Sending the letter: directed by the scenario (the only action offered to the swissmedic AI agent at this step).
- Result: **BLOCK**, decided by code: patient-data rule (no verified legal-basis and transfer-rules quotes).
- Quotes: 4 of 5 verified by code.

| Question | AI liaison reviewer proposed | Final | Final answer decided by | Needs human check |
|---|---|---|---|---|
| Is there a legal basis to share? | YES | UNCLEAR (missing_evidence) | code: 1 quote(s) failed the verbatim check; answer set to UNCLEAR / missing_evidence. | no |
| Is the transfer allowed under both sides' rules? | UNCLEAR | UNCLEAR (missing_evidence) | AI liaison reviewer (qwen3:8b) | no |
| Is the receiver the right counterpart? | YES | YES | AI liaison reviewer (qwen3:8b) | yes |

- Code correction: Quote matched one continuous passage except for at most 2 character slips; code replaced it with the exact source text.

### Step 8: UAE Data Office → fodio (no patient data)

- Sending the letter: directed by the scenario (the only action offered to the uae_data_office AI agent at this step).
- Result: **BLOCK**, decided by code routing rule: at least one final answer is not YES.
- Quotes: 3 of 5 verified by code.

| Question | AI liaison reviewer proposed | Final | Final answer decided by | Needs human check |
|---|---|---|---|---|
| Is there a legal basis to share? | YES | UNCLEAR (missing_evidence) | code: 1 quote(s) failed the verbatim check; answer set to UNCLEAR / missing_evidence. | no |
| Is the transfer allowed under both sides' rules? | YES | UNCLEAR (missing_evidence) | code: 1 quote(s) failed the verbatim check; answer set to UNCLEAR / missing_evidence. | no |
| Is the receiver the right counterpart? | YES | YES | AI liaison reviewer (qwen3:8b) | yes |

