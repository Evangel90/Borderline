.PHONY: fetch verify-sources ingest index drill verify-log replay report-figures ui itu-smoke

INTENT ?= retinopathy-ae-ch
RUN ?=
DRILL_ARGS ?=
PYTHON ?= $(CURDIR)/.venv/bin/python
ITU_SIM := vendor/ITUAIReadiness/simulation
PDF ?= $(CURDIR)/$(ITU_SIM)/server/knowledge/InputDocs/AI_Use_Cases/T-REC-Y.3172-201906-I!!PDF-E.pdf

define todo
	@echo "make $@: not implemented yet ($(1))"; exit 1
endef

fetch:
	$(call todo,M1)

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

replay:
	$(call todo,M2)

report-figures:
	$(call todo,M4)

ui:
	STREAMLIT_BROWSER_GATHER_USAGE_STATS=false $(PYTHON) -m streamlit run ui/app.py --server.headless true

# M0 check: ITU reference ingestion on one PDF, into a throwaway index.
# Needs `ollama serve` running and `ollama pull nomic-embed-text`.
itu-smoke:
	cd $(ITU_SIM) && AIREADY_CHROMADB_DIR=$(CURDIR)/index/itu-smoke \
		$(PYTHON) -m server.knowledge.ingest --reset --file "$(PDF)"
