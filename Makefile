.PHONY: fetch verify-sources ingest drill verify-log replay report-figures ui

INTENT ?= retinopathy-ae-ch
RUN ?=

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
