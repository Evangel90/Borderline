# Borderline

A prototype for cross-border AI incident drills, built for the
[ITU AI for Good Lab Hackathon: United Arab Emirates](https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/).
The current drill is wired to UAE (AE) and Switzerland (CH); adding a new
country pack does not yet configure a new drill automatically.

Each participating role is represented by an agent. The LLM selects among
role-authorized actions, which the sandbox records in synthetic drill state;
agents cite retrieved policy chunks when relevant evidence is available. A separate border gate can veto data
transfers or route regulator notifications. Decisions and tool outcomes are
written to a hash-chained audit log.

The demo drill pairs the UAE (host) with Switzerland in healthcare: a Swiss
vendor's AI diabetic retinopathy screening tool fails in UAE clinics after a
model update.

> All scenario data is synthetic. Agent roles are simulated and never represent
> any authority's official position.

## Status

The eight-stage timeline gives participating agents role-specific event views;
an optional judge-injected escalation can be enabled for a run. The OpenRouter
free-model router chooses the agents' actions. Policy retrieval remains
deterministic keyword search; there is no vector database. The checked-in
scenario actions only change synthetic drill state. No real clinical,
regulatory, or data-transfer system is connected. If the configured model is
unavailable, the drill stops; there is no scripted decision fallback. The
Streamlit viewer displays each agent's visible facts, decisions, tool outcomes,
evidence, and audit-chain status. `make replay` and `make report-figures` are
not implemented yet.

The expanded timeline has passed static validation but is not yet verified
end to end. A first remote attempt stopped during step 4 on an invalid evidence
ID. A second attempt logged 25 decisions through step 6 and part of step 7,
then stopped when OpenRouter's 50-request daily free limit was exhausted. Its
partial hash chain verifies, but no gap record was produced. Some citations in
the partial run also need human relevance review before being treated as
support for legal claims.

## Layout

```
packs/ae/, packs/ch/      country packs: documents/, institutions/*.yaml, chunks.jsonl
packs/bridge/ae-ch.yaml   what links the two countries (adequacy, treaties)
packs/global/             global benchmarks, neutral adviser, ITU standards
intents/                  staged drill specs (the Y.3172 "ML intent")
engine/                   LLM agents, action sandbox, orchestrator, gates
audit/                    hash-chained log and verifier
gaps/                     gap register
data/raw/, data/sources.csv   source files and provenance register
runs/<run_id>/            log.jsonl, gaps.jsonl
ui/                       Streamlit timeline
report/, video/           submission material
```

## Setup and demo

```sh
git clone --recurse-submodules https://github.com/Evangel90/Borderline.git
cd Borderline
python3.11 -m venv .venv
.venv/bin/pip install -e .
export OPENROUTER_API_KEY=your-key
make verify-sources
make drill INTENT=retinopathy-ae-ch RUN=demo-2026-10-30
make verify-log RUN=demo-2026-10-30
```

Create an API key from [OpenRouter](https://openrouter.ai/settings/keys) and
export it as `OPENROUTER_API_KEY`. The default model `openrouter/free` routes
requests among available free models that support structured outputs. Free
models have rate limits and availability can change; the selected model can
vary between agent decisions. The drill sends its
prompts, synthetic events, and retrieved policy excerpts to OpenRouter; do not
include real patient or confidential data. Set `BORDERLINE_LLM_MODEL` to a
specific model ID if needed, or `BORDERLINE_LLM_PROVIDER=ollama` to use local
Ollama instead (`BORDERLINE_OLLAMA_URL` and `BORDERLINE_LLM_TIMEOUT` configure
the local service and timeout).

The `RUN` value must be new each time; existing run IDs are immutable and the
engine refuses to append to them. The supplied policy chunks are checked in;
agent prompts and retrieved excerpts are sent to OpenRouter when a drill runs.
Use `DRILL_ARGS=--include-optional-events` with `make drill` to include the
judge-injected reserve event.
`vendor/ITUAIReadiness` contains the [ITU reference
code](https://github.com/CrashingGuru/ITUAIReadiness) (MIT), pinned as a git
submodule; `make itu-smoke` is optional and requires that project's dependencies
and a locally running Ollama embedding model.

To review saved drill runs in the Streamlit timeline, install the optional UI
dependency and start the viewer:

```sh
.venv/bin/pip install -e '.[ui]'
make ui
```

## Commands

Run from the repo root.

| Command | What it does |
| --- | --- |
| `make fetch` | Not implemented yet |
| `make verify-sources` | Re-hash sources and flag any change |
| `make ingest` | Rebuild citation-ready text chunks from registered PDFs (no vector index) |
| `make drill INTENT=retinopathy-ae-ch` | Run the LLM-driven drill; requires a configured model provider and API key for OpenRouter |
| `make verify-log RUN=<run_id>` | Check the hash chain; name the first broken entry |
| `make replay RUN=<run_id>` | Not implemented yet |
| `make report-figures RUN=<run_id>` | Not implemented yet |
| `make ui` | Start the Streamlit run viewer (install `.[ui]` first) |

## Scope and limitations

This is a synthetic policy-drill prototype, not a clinical tool or legal
opinion. The LLM chooses from actions declared in each institution profile;
Python validates the chosen action and runs a corresponding sandbox tool. The
border gate has veto authority over transfers and external notifications. These
tools only update in-memory drill state and the local audit log. The model's
short rationale is logged; private chain-of-thought is neither requested nor
stored. The hash chain is tamper-evident but not digitally signed or externally
anchored. The gap analysis is scenario-specific and keyword-retrieved, not an
autonomous legal conclusion. Review citations and actions against current
authoritative sources before real-world use.

## License

[MIT](LICENSE)
