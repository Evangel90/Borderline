#!/usr/bin/env python3
"""
Record an absence search: what was searched for, in which registered documents, and what was found.

A gap claimed "by absence" is only as good as the search behind it. This script makes that search
repeatable: it scans the ingested chunk packs for exact phrases and writes a JSON record naming
every document searched, every phrase, and every matching chunk ID. It searches the English
extraction only; documents held only in Arabic are listed separately so the record states that
they were not covered.

Usage (add --doc DOC_ID, repeatable, to limit the search to named documents):
  python scripts/search_absence.py --id AI-CHANGE-CONTROL --packs ae ch \
      --term "predetermined change control" --term "software update" --out gaps/searches/x.json
"""

import argparse
import csv
import json
import re
import sys
from datetime import date

ARABIC_RE = re.compile(r"[؀-ۿ]")


def load_sources(csv_path: str) -> dict[str, dict[str, str]]:
    with open(csv_path, encoding="utf-8") as handle:
        return {row["doc_id"]: row for row in csv.DictReader(handle)}


def search(packs: list[str], terms: list[str], docs: list[str] | None = None) -> dict:
    documents: dict[str, dict[str, int]] = {}
    hits: dict[str, list[str]] = {term: [] for term in terms}
    for pack in packs:
        with open(f"packs/{pack}/chunks.jsonl", encoding="utf-8") as handle:
            for line in handle:
                chunk = json.loads(line)
                if docs and chunk["doc_id"] not in docs:
                    continue
                text = " ".join(chunk["text"].split())
                stats = documents.setdefault(chunk["doc_id"], {"chunks": 0, "arabic_chunks": 0})
                stats["chunks"] += 1
                if ARABIC_RE.search(text) and len(ARABIC_RE.findall(text)) > len(text) / 4:
                    stats["arabic_chunks"] += 1
                lowered = text.lower()
                for term in terms:
                    if term.lower() in lowered:
                        hits[term].append(chunk["chunk_id"])
    return {"documents": documents, "hits": hits}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--id", required=True, help="Search record ID")
    parser.add_argument("--question", required=True, help="What the search tries to establish")
    parser.add_argument("--packs", nargs="+", required=True, choices=["ae", "ch", "global"])
    parser.add_argument("--term", action="append", required=True, help="Exact phrase (case-insensitive)")
    parser.add_argument("--doc", action="append", help="Limit the search to this doc_id (repeatable)")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    sources = load_sources("data/sources.csv")
    result = search(args.packs, args.term, args.doc)
    if args.doc and set(args.doc) - set(result["documents"]):
        missing = ", ".join(sorted(set(args.doc) - set(result["documents"])))
        print(f"No chunks for: {missing}", file=sys.stderr)
        return 1
    excluded = sorted(
        doc_id for doc_id, row in sources.items()
        if row["jurisdiction"].lower() in args.packs
        and (row.get("retrieval_excluded") or "").strip().lower() in {"1", "true", "yes"}
        and (not args.doc or doc_id in args.doc)
    )
    mostly_arabic = sorted(
        doc_id for doc_id, stats in result["documents"].items()
        if stats["arabic_chunks"] > stats["chunks"] / 2
    )
    record = {
        "search_id": args.id,
        "date": date.today().isoformat(),
        "question": args.question,
        "searched_for": args.term,
        "searched_in": [
            {"doc_id": doc_id, "title": sources.get(doc_id, {}).get("title", ""),
             "binding": sources.get(doc_id, {}).get("binding", ""), "chunks": stats["chunks"]}
            for doc_id, stats in sorted(result["documents"].items())
        ],
        "found": {term: ids for term, ids in result["hits"].items()},
        "not_found": [term for term, ids in result["hits"].items() if not ids],
        "coverage_limits": {
            "excluded_from_retrieval": excluded,
            "mostly_arabic_not_covered_by_english_terms": mostly_arabic,
            "method": "Exact case-insensitive phrase match over ingested English text; no synonyms, no semantic search."
                      + (f" Limited to: {', '.join(args.doc)}." if args.doc else ""),
            "meaning": "Absence here means absence from this knowledge base, not from the jurisdiction's law.",
        },
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"Searched {len(record['searched_in'])} documents for {len(args.term)} phrases; "
          f"{len(record['not_found'])} phrases not found. Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
