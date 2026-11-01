#!/usr/bin/env python3
"""Measure exact reviewed passage retrieval on a small question seed."""

import csv
import json
from pathlib import Path

from engine.knowledge import KnowledgeIndex
from engine.models import Chunk


def main() -> None:
    chunks = [
        Chunk.model_validate_json(line)
        for pack in ("ae", "ch", "global")
        for line in (Path("packs") / pack / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    index = KnowledgeIndex(chunks)
    cases = list(csv.DictReader(Path("data/retrieval_benchmark_seed.csv").open(encoding="utf-8")))
    results = []
    for case in cases:
        hits = index.search(case["question"], case["jurisdictions"].split("|"), top_k=6)
        ids = [chunk.chunk_id for chunk in hits]
        gold = set(case["gold_chunk_ids"].split("|"))
        rank = next((rank for rank, chunk_id in enumerate(ids, 1) if chunk_id in gold), None)
        results.append({"case_id": case["case_id"], "rank": rank, "retrieved_ids": ids})
    print(json.dumps({
        "cases": len(results),
        "hit_at_6": sum(item["rank"] is not None for item in results),
        "hit_at_3": sum(item["rank"] is not None and item["rank"] <= 3 for item in results),
        "results": results,
        "limitation": "Curated ten-question seed; exact chunk hit measures retrieval only, not claim support or legal applicability.",
    }, indent=2))


if __name__ == "__main__":
    main()
