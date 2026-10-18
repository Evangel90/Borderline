# Borderline

A country-agnostic engine for cross-border AI incident drills, built for the
[ITU AI for Good Lab Hackathon: United Arab Emirates](https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/).

Each country's laws and institutions load as plug-in packs. The engine generates
one agent per institution, releases an incident step by step, controls what may
cross the border through a liaison channel, logs every decision with its cited
clause, and outputs domain-level policy gaps paired with global examples.

The demo drill pairs the UAE (host) with Switzerland in healthcare: a Swiss
vendor's AI diabetic retinopathy screening tool fails in UAE clinics after a
model update.

> All scenario data is synthetic. Agent roles are simulated and never represent
> any authority's official position.

## Status

M0 (setup). The layout exists; nothing runs yet.

## Layout

```
packs/ae/, packs/ch/      country packs: documents/, institutions/*.yaml, chunks.jsonl
packs/bridge/ae-ch.yaml   what links the two countries (adequacy, treaties)
packs/global/             global benchmarks and ITU standards (chunks.jsonl)
domains/health/           incident template
intents/                  drill specs (the Y.3172 "ML intent")
engine/                   orchestrator, agents, liaison channel, policy node, gates
audit/                    hash-chained log and verifier
gaps/                     gap register
data/raw/, data/sources.csv   source files and provenance register
runs/<run_id>/            log.jsonl, gaps.jsonl
ui/                       Streamlit timeline
report/, video/           submission material
```

## Commands

Run from the repo root. Targets are stubs until their milestone lands.

| Command | What it does |
| --- | --- |
| `make fetch` | Download sources, hash them, update `data/sources.csv` |
| `make verify-sources` | Re-hash sources and flag any change |
| `make ingest` | Build chunks and the vector index |
| `make drill INTENT=retinopathy-ae-ch` | Run the full drill offline, write `runs/<run_id>/` |
| `make verify-log RUN=<run_id>` | Check the hash chain; name the first broken entry |
| `make replay RUN=<run_id>` | Re-run and diff decisions against the saved log |
| `make report-figures RUN=<run_id>` | Compute every number the report quotes |
| `make ui` | Start the Streamlit timeline |

## Scope and limitations

To be written before submission.

## License

[MIT](LICENSE)
