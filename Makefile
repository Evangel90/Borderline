.PHONY: fetch verify-sources ingest drill verify-log replay report-figures ui itu-smoke

INTENT ?= retinopathy-ae-ch
RUN ?=
PYTHON ?= $(CURDIR)/.venv/bin/python
ITU_SIM := vendor/ITUAIReadiness/simulation
PDF ?= $(CURDIR)/$(ITU_SIM)/server/knowledge/InputDocs/AI_Use_Cases/T-REC-Y.3172-201906-I!!PDF-E.pdf

define todo
	@echo "make $@: not implemented yet ($(1))"; exit 1
endef

fetch:
	$(call todo,M1)

verify-sources:
	$(call todo,M1)

ingest:
	$(call todo,M1)

drill:
	$(call todo,M2)

verify-log:
	$(call todo,M2)

replay:
	$(call todo,M2)

report-figures:
	$(call todo,M4)

ui:
	$(call todo,M2)

# M0 check: ITU reference ingestion on one PDF, into a throwaway index.
# Needs `ollama serve` running and `ollama pull nomic-embed-text`.
itu-smoke:
	cd $(ITU_SIM) && AIREADY_CHROMADB_DIR=$(CURDIR)/index/itu-smoke \
		$(PYTHON) -m server.knowledge.ingest --reset --file "$(PDF)"
