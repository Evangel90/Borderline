"""Guard: the chunk packs must match data/sources.csv.

If a register line is edited without re-running `make ingest`, chunks carry stale provenance
(this happened once with the DHA PP-13 notes). These tests fail until ingest is re-run.
"""

import csv
import json
import os

import pytest

FIELD_MAP = {  # chunk field -> register column, as written by scripts/ingest.py
    "title": "title",
    "jurisdiction": "jurisdiction",
    "source_file": "file",
    "source_url": "source_url",
    "source_issuer": "issuer",
    "source_sha256": "sha256",
    "source_retrieved": "retrieved",
    "source_language": "language",
    "source_official_language": "official_language",
    "source_binding": "binding",
    "source_in_force_from": "in_force_from",
    "source_notes": "notes",
}


def excluded(row):
    return (row.get("retrieval_excluded") or "").strip().lower() in {"1", "true", "yes"}


@pytest.fixture(scope="module")
def register():
    with open("data/sources.csv", encoding="utf-8") as source:
        return {row["doc_id"]: row for row in csv.DictReader(source)}


@pytest.fixture(scope="module")
def chunks():
    items = []
    for pack in ("ae", "ch", "global"):
        with open(f"packs/{pack}/chunks.jsonl", encoding="utf-8") as source:
            items.extend(json.loads(line) for line in source if line.strip())
    return items


def test_every_chunk_carries_its_current_register_provenance(register, chunks):
    stale = sorted({
        f"{chunk['doc_id']}.{field}"
        for chunk in chunks
        for field, column in FIELD_MAP.items()
        if chunk["doc_id"] in register and chunk[field] != (register[chunk["doc_id"]].get(column) or "")
    })
    assert stale == [], "Packs are out of date; run `make ingest`. Stale: " + ", ".join(stale[:10])


def test_no_chunk_comes_from_an_unregistered_or_excluded_document(register, chunks):
    unknown = sorted({c["doc_id"] for c in chunks if c["doc_id"] not in register})
    leaked = sorted({c["doc_id"] for c in chunks if c["doc_id"] in register and excluded(register[c["doc_id"]])})
    assert unknown == [] and leaked == []


def test_every_retrievable_registered_file_has_chunks(register, chunks):
    present = {c["doc_id"] for c in chunks}
    missing = sorted(
        doc_id for doc_id, row in register.items()
        if row.get("file") and os.path.exists(row["file"]) and not excluded(row) and doc_id not in present
    )
    assert missing == [], "Registered files with no chunks; run `make ingest`: " + ", ".join(missing)
