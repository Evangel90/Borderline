# Decision trail: governed-scripted-20261108-1

Unreviewed synthetic drill output; nothing here is a legal conclusion. Every AI decision was made by a model that sees only what its institution can see, and it may have missed things a person would consider.

## Institution decisions (each made by that institution's AI agent)

| Step | Institution | Decided by | Action chosen | Explanation | Evidence status |
|---|---|---|---|---|---|
| 1 | Swiss Agency for Therapeutic Products (Swissmedic) | AI agent (qwen3:8b) | `review_foreign_incident_report` | agent's own words | PARTIALLY_SUPPORTED |
| 2 | Emirates Drug Establishment (EDE) | AI agent (qwen3:8b) | `request_regulatory_evidence` | agent's own words | INSUFFICIENT_EVIDENCE |
| 3 | Swiss Agency for Therapeutic Products (Swissmedic) | AI agent (qwen3:8b) | `review_foreign_incident_report` | agent's own words | PARTIALLY_SUPPORTED |
| 3 | RetinaSwiss AG | AI agent (qwen3:8b) | `initiate_model_rollback` | explanation replaced by fixed wording (code rule) | INSUFFICIENT_EVIDENCE |
| 5 | Swiss Agency for Therapeutic Products (Swissmedic) | AI agent (qwen3:8b) | `share_patient_data_via_liaison` | agent's own words | PARTIALLY_SUPPORTED |
| 6 | Emirates Drug Establishment (EDE) | AI agent (qwen3:8b) | `assess_ede_device_safety_action` | agent's own words | PARTIALLY_SUPPORTED |
| 6 | Dubai Health Authority (DHA) | AI agent (qwen3:8b) | `request_patient_follow_up_review` | explanation replaced by fixed wording (code rule) | UNSUPPORTED |
| 8 | UAE Data Office | AI agent (qwen3:8b) | `request_regulatory_evidence` | agent's own words | PARTIALLY_SUPPORTED |
| 9 | Federal Data Protection and Information Commissioner (FDPIC / EDÖB) | AI agent (qwen3:8b) | `recommend_pause_disclosure` | agent's own words | PARTIALLY_SUPPORTED |
| 9 | RetinaSwiss AG | AI agent (qwen3:8b) | `preserve_vendor_security_evidence` | agent's own words | PARTIALLY_SUPPORTED |
| 11 | Neutral Policy and Legal Adviser | AI agent (qwen3:8b) | `prepare_policy_gap_review` | agent's own words | PARTIALLY_SUPPORTED |

## Cross-border letters

### Step 2: Emirates Drug Establishment (EDE) → swissmedic (no patient data)

- Sending the letter: directed by the scenario (the only action offered to the ede AI agent at this step).
- Result: **ROUTE**, decided by code routing rule: all three final answers YES.
- Quotes: 7 of 7 verified by code.

| Question | Scripted reviewer (not AI) proposed | Final | Final answer decided by | Needs human check |
|---|---|---|---|---|
| Is there a legal basis to share? | YES | YES | scripted reviewer: scripted reference answers (not an AI decision) | yes |
| Is the transfer allowed under both sides' rules? | YES | YES | scripted reviewer: scripted reference answers (not an AI decision) | yes |
| Is the receiver the right counterpart? | YES | YES | scripted reviewer: scripted reference answers (not an AI decision) | yes |

### Step 5: Swiss Agency for Therapeutic Products (Swissmedic) → ede (carries patient data)

- Sending the letter: directed by the scenario (the only action offered to the swissmedic AI agent at this step).
- Result: **ROUTE**, decided by code routing rule: all three final answers YES, and human approval APPROVAL-SWISSMEDIC-RECALL-001 (Swissmedic legal officer (role; drill fact)) matches this letter.
- Quotes: 7 of 7 verified by code.

| Question | Scripted reviewer (not AI) proposed | Final | Final answer decided by | Needs human check |
|---|---|---|---|---|
| Is there a legal basis to share? | YES | YES | scripted reviewer: scripted reference answers (not an AI decision) | yes |
| Is the transfer allowed under both sides' rules? | YES | YES | scripted reviewer: scripted reference answers (not an AI decision) | yes |
| Is the receiver the right counterpart? | YES | YES | scripted reviewer: scripted reference answers (not an AI decision) | yes |

### Step 8: UAE Data Office → fodio (no patient data)

- Sending the letter: directed by the scenario (the only action offered to the uae_data_office AI agent at this step).
- Result: **ROUTE**, decided by code routing rule: all three final answers YES.
- Quotes: 7 of 7 verified by code.

| Question | Scripted reviewer (not AI) proposed | Final | Final answer decided by | Needs human check |
|---|---|---|---|---|
| Is there a legal basis to share? | YES | YES | scripted reviewer: scripted reference answers (not an AI decision) | yes |
| Is the transfer allowed under both sides' rules? | YES | YES | scripted reviewer: scripted reference answers (not an AI decision) | yes |
| Is the receiver the right counterpart? | YES | YES | scripted reviewer: scripted reference answers (not an AI decision) | yes |

