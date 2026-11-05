# Borderline use case and knowledge-base contribution

## Use case

**Borderline supports a fictional UAE clinic's pre-deployment review of a Swiss-vendor diabetic-retinopathy screening service.** It is a policy-grounded multi-agent sandbox: it does not screen patients, diagnose disease, approve a real deployment, or issue legal advice.

The clinic is considering `RetinaVision-DX`, a fictional cloud-connected service supplied by the fictional Swiss company RetinaSwiss AG. In the scenario, the clinic captures retinal fundus images in Dubai. Its encrypted workstation sends the images to the vendor's stated Swiss processing environment; the vendor's model runs there and returns an image-quality result, screening category, and recommended referral outcome to the clinic. The clinic does not receive the model weights. Retention, support access, telemetry, subprocessors, and any later reuse of images are explicit facts to be established and reviewed before deployment.

This is a credible shape for a vendor service, but the named vendor, UAE deployment, locations, data-flow terms, and events are fictional scenario facts. They do not assert that a real Swiss supplier serves UAE clinics.

## What Borderline demonstrates

The drill releases facts progressively to a clinic operator, vendor, UAE health/data/cyber roles, Swiss counterparts, and a policy adviser. Each agent has a role-specific view and may take only declared synthetic actions. Borderline retrieves provenance-bearing UAE, Swiss, and global policy passages and records the decision, cited passages, tool outcome, uncertainty, and hash link.

The intended reviewer-facing output is a pre-deployment evidence checklist:

- which data categories would leave the clinic and where each is processed;
- what the vendor must clarify about model version, validation, access, retention, subprocessors, and incident handling;
- which actor should review a question under the scenario's institutional map;
- which policy passages are relevant and which decisive facts remain unknown;
- whether a proposed policy or coordination gap is supported, only a candidate, an operational deficiency, or insufficiently evidenced.

## Staged real-world pressures

The primary decision is whether the clinic has enough evidence to proceed with the fictional remote service. An optional post-deployment stress test introduces a vendor model/workflow update, a safety signal, suspected credential misuse, and a question about secondary use of UAE-origin images. This tests how agents behave when information is incomplete and unevenly distributed; it does not claim the events occurred outside the simulation.

## Knowledge-base contribution

The checked-in knowledge base contains selected UAE, Swiss, and global public sources with source URLs, issuer, jurisdiction, language, file hash, status, and passage-level provenance. It is a reproducible, scenario-focused example of the kind of country knowledge needed for policy-grounded agents.

It is **not** currently hosted by the ITU AI for Good Lab, distributed across countries, complete for the scenario, or a validated statement of law. Any publication of an open knowledge-base contribution in the ITU AI for Good Lab would be an outcome of the hackathon, subject to its process and review.

## Claim discipline

A source not appearing in the local pack does not establish that no applicable policy exists. Borderline records an `INSUFFICIENT_EVIDENCE` outcome when the actor, facility, data, legal predicate, authority, or passage-level support is unresolved. A policy-gap conclusion requires reviewed local evidence, a specific global comparator, and an explanation of why the applicable framework does not resolve the scenario question.
