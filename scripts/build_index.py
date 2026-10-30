#!/usr/bin/env python3
"""Build or update the local Chroma index from ingested policy chunks."""

import json
from pathlib import Path

from engine.knowledge import KnowledgeIndex
from engine.models import Chunk


def main() -> None:
    chunks = []
    for pack in ("ae", "ch", "global"):
        path = Path(f"packs/{pack}/chunks.jsonl")
        if not path.exists():
            raise SystemExit(f"Missing {path}; run make ingest first.")
        with path.open(encoding="utf-8") as source:
            chunks.extend(Chunk.model_validate(json.loads(line)) for line in source if line.strip())

    index = KnowledgeIndex(chunks)
    print(
        f"Indexed {len(index.chunks)} chunks as {index.collection.count()} "
        f"passages in {index.path} with {index.model_name}."
    )


if __name__ == "__main__":
    main()
