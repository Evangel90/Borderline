.PHONY: ui step-coverage decision-trail verify-sources ingest index drill verify-log audit-evidence assess-candidates evaluate-claims evaluate-retrieval replay itu-smoke knowledge-base verify-knowledge-base

INTENT ?= retinopathy-ae-ch
RUN ?=
DRILL_ARGS ?=
PYTHON ?= $(CURDIR)/.venv/bin/python
ITU_SIM := vendor/ITUAIReadiness/simulation
PDF ?= $(CURDIR)/$(ITU_SIM)/server/knowledge/InputDocs/AI_Use_Cases/T-REC-Y.3172-201906-I!!PDF-E.pdf

verify-sources:
	$(PYTHON) scripts/verify_sources.py

ingest:
	$(PYTHON) scripts/ingest.py
	$(PYTHON) scripts/build_index.py

index:
	$(PYTHON) scripts/build_index.py

drill:
	$(PYTHON) scripts/run_drill.py --intent $(INTENT) $(if $(RUN),--run-id $(RUN),) $(DRILL_ARGS)

verify-log:
	@if [ -z "$(RUN)" ]; then echo "Error: specify RUN=<run_id>"; exit 1; fi
	$(PYTHON) scripts/verify_log.py --run $(RUN)

audit-evidence:
	@if [ -z "$(RUN)" ]; then echo "Error: specify RUN=<run_id>"; exit 1; fi
	$(PYTHON) scripts/audit_evidence.py --run $(RUN)

assess-candidates:
	$(PYTHON) scripts/assess_candidates.py

decision-trail:
	@if [ -z "$(RUN)" ]; then echo "Error: specify RUN=<run_id>"; exit 1; fi
	$(PYTHON) scripts/decision_trail.py --run $(RUN)

# Usage: make step-coverage RUNS="retinopathy-governed=<run> retinopathy-ae-ch=<run> retinopathy-insufficient-evidence=<run>"
step-coverage:
	$(PYTHON) scripts/step_coverage.py $(RUNS)

evaluate-claims:
	$(PYTHON) scripts/evaluate_claim_seed.py

evaluate-retrieval:
	$(PYTHON) scripts/evaluate_retrieval.py

# Code replay: re-runs every code decision over the logged AI answers; no model is called.
# Usage: make replay RUN=<run_id> [REPLAY_ARGS="--log edited.jsonl"]
replay:
	@if [ -z "$(RUN)" ]; then echo "Error: specify RUN=<run_id>"; exit 1; fi
	$(PYTHON) scripts/replay.py --run $(RUN) $(REPLAY_ARGS)

# Judge dashboard at http://localhost:8501 (reads saved files only; no model needed).
ui:
	STREAMLIT_BROWSER_GATHER_USAGE_STATS=false $(PYTHON) -m streamlit run ui/app.py --server.headless true --server.address localhost

# Optional local check: ITU reference ingestion on one PDF, into a throwaway index.
# Needs a local clone of https://github.com/CrashingGuru/ITUAIReadiness in vendor/ (not in this repository).
# Needs `ollama serve` running and `ollama pull nomic-embed-text`.
itu-smoke:
	cd $(ITU_SIM) && AIREADY_CHROMADB_DIR=$(CURDIR)/index/itu-smoke \
		$(PYTHON) -m server.knowledge.ingest --reset --file "$(PDF)"

# Build the knowledge base in the ITU layout: copy the registered files the drills search into
# knowledge-base/InputDocs/ (hash-checked), build knowledge-base/chromadb/ with the unmodified ITU
# ingestion functions, and regenerate knowledge-base/InputDocs/Inputs.md. Same prerequisites as itu-smoke.
knowledge-base:
	$(PYTHON) scripts/build_knowledge_base.py --ingest

# Check the copies in knowledge-base/InputDocs/ against data/sources.csv (no model needed).
verify-knowledge-base:
	$(PYTHON) scripts/build_knowledge_base.py --check
