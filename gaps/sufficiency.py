"""
gaps/sufficiency.py - Evidence-sufficiency rule for gap candidates.

A candidate becomes SUPPORTED_CANDIDATE only when all four conditions hold:

1. every quote verifies word for word against its chunk (engine/quotes.py);
2. every listed search record exists in gaps/searches/ and none of its absent terms was found;
3. at least one verified quote from a GLOBAL source is marked as a comparator;
4. no known-missing document that is still obtainable could refute it.

Known-missing documents come in three kinds. "Unobtainable after documented attempts" does not
block (it needs at least one documented attempt; without one it counts as obtainable). Each such
document should have its own accessibility candidate, unless the register records a reason in
`accessibility_candidate_exempt_reason`. "Obtainable but not fetched" blocks.
"Question answered by a registered source" does not block, but only when every answering quote
verifies; otherwise it counts as obtainable.

This only sets candidate status. It is not used by the drill, so missing documents never stop a
drill from running. Nothing here is a legal conclusion; every result is marked unreviewed.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Iterable

import yaml

from engine.models import Chunk
from engine.quotes import verify_quote

SUPPORTED = "SUPPORTED_CANDIDATE"
OPEN = "OPEN_CANDIDATE"
UNOBTAINABLE = "unobtainable_after_documented_attempts"
OBTAINABLE = "obtainable_not_fetched"
# The document itself was not fetched, but the specific question it could settle is answered
# by quotes from a registered source. Counts only if every answering quote verifies.
ANSWERED = "question_answered_by_registered_source"
MISSING_KINDS = {UNOBTAINABLE, OBTAINABLE, ANSWERED}
QUOTE_ROLES = {"host", "partner", "global_comparator", "context"}


@dataclass
class Assessment:
    candidate_id: str
    title: str
    status: str
    category: str = ""
    reason_from_drill: str = ""
    recommendation: str = ""
    unmet: list[dict[str, str]] = field(default_factory=list)  # {"condition", "detail"}
    notes: list[str] = field(default_factory=list)
    quotes: list[dict[str, Any]] = field(default_factory=list)
    searches: list[dict[str, Any]] = field(default_factory=list)
    blocking_documents: list[str] = field(default_factory=list)
    unobtainable_documents: list[str] = field(default_factory=list)
    answered_documents: list[str] = field(default_factory=list)
    reviewed_by_legal_professional: bool = False

    def fail(self, condition: str, detail: str) -> None:
        self.unmet.append({"condition": condition, "detail": detail})

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "title": self.title,
            "category": self.category,
            "reason_from_drill": self.reason_from_drill,
            "recommendation": self.recommendation,
            "status": self.status,
            "unmet_conditions": self.unmet,
            "notes": self.notes,
            "quotes": self.quotes,
            "searches": self.searches,
            "blocking_documents": self.blocking_documents,
            "unobtainable_documents": self.unobtainable_documents,
            "answered_documents": self.answered_documents,
            "reviewed_by_legal_professional": self.reviewed_by_legal_professional,
            "is_legal_conclusion": False,
        }


def load_chunks(paths: Iterable[str] = ("packs/ae/chunks.jsonl", "packs/ch/chunks.jsonl",
                                        "packs/global/chunks.jsonl")) -> dict[str, Chunk]:
    chunks: dict[str, Chunk] = {}
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    chunk = Chunk(**json.loads(line))
                    chunks[chunk.chunk_id] = chunk
    return chunks


def load_search(search_dir: str, search_id: str) -> dict[str, Any] | None:
    path = os.path.join(search_dir, f"{search_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def answering_quotes(document: dict[str, Any], chunks: dict[str, Chunk]) -> list[dict[str, Any]]:
    return [
        verify_quote(item["chunk_id"], item["quote"], item.get("translation", ""), chunks)
        for item in document.get("answered_by", [])
    ]


def missing_document_kind(document: dict[str, Any], chunks: dict[str, Chunk]) -> tuple[str, str]:
    """Return the effective kind and a note when the declared kind is not honoured."""
    kind = document.get("kind")
    doc_id = document.get("id")
    if kind not in MISSING_KINDS:
        return OBTAINABLE, f"{doc_id}: unknown kind '{kind}', treated as obtainable."
    if kind == UNOBTAINABLE and not document.get("attempts"):
        return OBTAINABLE, f"{doc_id}: marked unobtainable without a documented attempt, treated as obtainable."
    if kind == ANSWERED:
        quotes = answering_quotes(document, chunks)
        if not quotes:
            return OBTAINABLE, f"{doc_id}: marked answered without any answering quote, treated as obtainable."
        failed = [q for q in quotes if not q["verified"]]
        if failed:
            return OBTAINABLE, (
                f"{doc_id}: answering quote failed verification ("
                + "; ".join(f"{q['chunk_id']}: {q['failure']}" for q in failed)
                + "), treated as obtainable."
            )
    return kind, ""


def assess_candidate(candidate: dict[str, Any], missing: dict[str, dict[str, Any]],
                     chunks: dict[str, Chunk], search_dir: str) -> Assessment:
    result = Assessment(candidate["id"], candidate.get("title", ""), OPEN,
                        category=candidate.get("category", ""),
                        reason_from_drill=" ".join(candidate.get("reason_from_drill", "").split()),
                        recommendation=" ".join(candidate.get("recommendation", "").split()))

    # 1. Every quote verifies.
    for item in candidate.get("quotes", []):
        record = verify_quote(item["chunk_id"], item["quote"], item.get("translation", ""), chunks)
        role = item.get("role", "")
        record["role"] = role
        if role not in QUOTE_ROLES:
            record["verified"] = False
            record["failure"] = f"Unknown quote role '{role}'."
        if item.get("note"):
            record["note"] = item["note"]
        result.quotes.append(record)
    if not result.quotes:
        result.fail("quotes_verify", "No quotes recorded.")
    failed = [q for q in result.quotes if not q["verified"]]
    if failed:
        result.fail(
            "quotes_verify",
            f"{len(failed)} quote(s) failed verification: "
            + "; ".join(f"{q['chunk_id']}: {q['failure']}" for q in failed)
        )

    # 2. A search record exists and its absent terms really were not found.
    searches = candidate.get("searches", [])
    if not searches:
        result.fail("search_record", "No search record listed.")
    for search in searches:
        record = load_search(search_dir, search["search_id"])
        check = {"search_id": search["search_id"], "exists": record is not None, "problems": []}
        if record is None:
            check["problems"].append("Search record file not found in gaps/searches/.")
        else:
            not_found = set(record.get("not_found", []))
            for term in search.get("absent_terms", []):
                if term not in not_found:
                    found = record.get("found", {}).get(term)
                    check["problems"].append(
                        f"'{term}' was found ({', '.join(found)})." if found
                        else f"'{term}' was not part of this search."
                    )
        result.searches.append(check)
        if check["problems"]:
            result.fail("search_record", f"{search['search_id']}: " + " ".join(check["problems"]))

    # 3. A verified global comparator is quoted.
    if not any(q["verified"] and q["role"] == "global_comparator" and q.get("jurisdiction") == "GLOBAL"
               for q in result.quotes):
        result.fail("global_comparator", "No verified quote from a GLOBAL source is marked as a comparator.")

    # 4. No obtainable known-missing document could refute it.
    for doc_id in candidate.get("could_be_refuted_by", []):
        document = missing.get(doc_id)
        if document is None:
            result.blocking_documents.append(doc_id)
            result.fail("no_obtainable_refuter",
                        f"Refuting document '{doc_id}' is not in the missing-documents list; treated as obtainable.")
            continue
        kind, note = missing_document_kind(document, chunks)
        if note:
            result.notes.append(note)
        if kind == ANSWERED:
            result.answered_documents.append(doc_id)
            result.notes.append(
                f"{doc_id} was not fetched; the question it could settle is answered by verified quotes from "
                + ", ".join(item["chunk_id"] for item in document["answered_by"])
                + (f". Limits: {document['limits']}" if document.get("limits") else ".")
            )
        elif kind == UNOBTAINABLE:
            result.unobtainable_documents.append(doc_id)
            status = document.get("status_note") or "is not publicly accessible to the project after documented attempts"
            result.notes.append(f"{doc_id} {status}; it does not block this candidate but could still refute it.")
        else:
            result.blocking_documents.append(doc_id)
            result.fail("no_obtainable_refuter", f"Obtainable document not yet fetched could refute this: {doc_id}.")

    for text in candidate.get("refuting_evidence_to_look_for", []):
        result.notes.append(f"Not known to exist, so not blocking: {text}")

    result.status = SUPPORTED if not result.unmet else OPEN
    return result


def assess_register(register: dict[str, Any], chunks: dict[str, Chunk],
                    search_dir: str = "gaps/searches") -> dict[str, Any]:
    missing = {doc["id"]: doc for doc in register.get("missing_documents", [])}
    assessments = [assess_candidate(c, missing, chunks, search_dir) for c in register.get("candidates", [])]

    # Every unobtainable document needs its own accessibility candidate.
    covered = {c.get("accessibility_of") for c in register.get("candidates", [])}
    register_notes = []
    for doc_id, document in missing.items():
        kind, note = missing_document_kind(document, chunks)
        if note:
            register_notes.append(note)
        exempt = (document.get("accessibility_candidate_exempt_reason") or "").strip()
        if kind == UNOBTAINABLE and doc_id not in covered and not exempt:
            register_notes.append(f"{doc_id} is unobtainable but has no accessibility candidate.")

    return {
        "rule": [
            "every quote verifies word for word against its chunk",
            "a search record exists in gaps/searches/ and its absent terms were not found",
            "a verified GLOBAL comparator is quoted",
            "no obtainable known-missing document could refute it",
        ],
        "disclaimer": (
            "Candidates, not findings. Nothing here is a legal conclusion and nothing has been reviewed "
            "by anyone with legal standing. Verification confirms exact text only, not that a quote "
            "supports the hypothesis. Absence means absence from this knowledge base."
        ),
        "missing_documents": [
            {"id": doc_id, "title": doc.get("title", ""),
             "declared_kind": doc.get("kind"), "effective_kind": missing_document_kind(doc, chunks)[0],
             **({"answered_by": answering_quotes(doc, chunks)} if doc.get("answered_by") else {})}
            for doc_id, doc in missing.items()
        ],
        "register_problems": register_notes,
        "candidates": [a.to_dict() for a in assessments],
    }


def load_register(path: str = "gaps/candidate_register.yaml") -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)
