#!/usr/bin/env python3
"""Screen a recorded run for citation traceability and obvious relevance risks."""

import argparse
import json
import re
from pathlib import Path

from audit.hasher import HashChainedLogger
from engine.evidence import off_topic_rationale, triage_citations
from engine.models import Chunk


def audit_run(run_id: str) -> dict:
    log_path = Path("runs") / run_id / "log.jsonl"
    valid, message, _ = HashChainedLogger.verify_log(str(log_path))
    if not valid:
        raise ValueError(f"Cannot audit invalid log: {message}")
    chunks = {}
    for pack in ("ae", "ch", "global"):
        path = Path("packs") / pack / "chunks.jsonl"
        for line in path.read_text(encoding="utf-8").splitlines():
            chunk = Chunk.model_validate_json(line)
            chunks[chunk.chunk_id] = chunk

    findings = []
    decisions = 0
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        decisions += 1
        cited_ids = []
        for citation in entry.get("cited_clauses", []):
            match = re.search(r"; ([^;()]+)\)$", citation)
            if not match:
                findings.append({"entry_id": entry["entry_id"], "issue": "unparseable_citation", "citation": citation})
                continue
            cited_ids.append(match.group(1))
        for chunk_id in cited_ids:
            if chunk_id not in entry.get("retrieved_chunk_ids", []):
                findings.append({"entry_id": entry["entry_id"], "issue": "citation_not_retrieved", "chunk_id": chunk_id})
            if chunk_id not in chunks:
                findings.append({"entry_id": entry["entry_id"], "issue": "unknown_chunk", "chunk_id": chunk_id})
        rationale = entry.get("justification", "")
        status, weak = triage_citations(
            rationale, entry.get("action_taken", "").replace("_", " "),
            cited_ids, chunks, entry.get("jurisdiction"), entry.get("action_taken"),
        )
        if off_topic_rationale(rationale):
            findings.append({"entry_id": entry["entry_id"], "issue": "off_topic_rationale"})
        if weak:
            findings.append({"entry_id": entry["entry_id"], "issue": "citation_needs_review", "chunk_ids": weak})
        if status == "INSUFFICIENT_EVIDENCE":
            findings.append({"entry_id": entry["entry_id"], "issue": "no_citation"})
    return {
        "run_id": run_id,
        "hash_chain_verified": True,
        "decisions": decisions,
        "screening_findings": findings,
        "limitation": "Lexical and metadata screening only; exact support, mandate, and legal applicability require human review.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    print(json.dumps(audit_run(args.run), indent=2))


if __name__ == "__main__":
    main()
