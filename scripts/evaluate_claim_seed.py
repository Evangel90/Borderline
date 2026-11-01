#!/usr/bin/env python3
"""Compare lexical triage with the manually reviewed claim seed."""

import csv
import json
from collections import Counter
from pathlib import Path

from engine.evidence import triage_citations
from engine.models import Chunk


def main() -> None:
    chunks = {}
    for pack in ("ae", "ch", "global"):
        for line in (Path("packs") / pack / "chunks.jsonl").read_text(encoding="utf-8").splitlines():
            item = Chunk.model_validate_json(line)
            chunks[item.chunk_id] = item
    decisions = {}
    rows = list(csv.DictReader(Path("data/claim_review_seed.csv").open(encoding="utf-8")))
    results = []
    for row in rows:
        run_id = row["run_id"]
        if run_id not in decisions:
            decisions[run_id] = {
                entry["entry_id"]: entry
                for entry in (json.loads(line) for line in (Path("runs") / run_id / "log.jsonl").open(encoding="utf-8"))
            }
        decision = decisions[run_id][row["entry_id"]]
        cited = row["recorded_citation_ids"].split("|") if row["recorded_citation_ids"] else []
        status, weak = triage_citations(
            row["claim_focus"], decision["action_taken"].replace("_", " "),
            cited, chunks, decision["jurisdiction"], decision["action_taken"],
            decision["actor_id"], decision.get("visible_payload"),
        )
        results.append({
            "case_id": row["case_id"], "manual": row["assessment"],
            "triage": status, "weak_citation_ids": weak,
        })
    print(json.dumps({
        "cases": len(results),
        "manual_counts": dict(Counter(item["manual"] for item in results)),
        "triage_counts": dict(Counter(item["triage"] for item in results)),
        "results": results,
        "limitation": "This seed is small and selected for known issues; counts are not general accuracy estimates.",
    }, indent=2))


if __name__ == "__main__":
    main()
