"""Conservative, lexical citation triage; never a legal support determination."""

import re

from engine.models import Chunk


STOPWORDS = {
    "about", "action", "after", "against", "agent", "allow", "also", "because",
    "before", "could", "decision", "evidence", "from", "have", "into", "must",
    "need", "only", "other", "review", "should", "their", "there", "these",
    "this", "those", "under", "with", "would", "where", "which", "while",
    "request", "record", "assess", "information", "incident", "policy",
}

LEGAL_CLAIM = re.compile(
    r"\b(?:law|legal(?:ly)?|statut(?:e|ory)|regulat(?:ion|ory)|mandat(?:e|ed)|"
    r"obligat(?:ion|ed)|authorit(?:y|ies)|must report|required to report)\b",
    re.IGNORECASE,
)
NON_BINDING = {"guidance", "guidelines", "national_strategy", "framework_report",
               "international_report", "international_code", "international_standard"}
META_RESPONSE = re.compile(
    r"\b(?:the user (?:has provided|is asking|may be looking)|"
    r"seeking a structured summary|documents and chunks|"
    r"your (?:question|request) asks)\b",
    re.IGNORECASE,
)


def off_topic_rationale(rationale: str) -> bool:
    """Catch clear document-assistant replies inside an institutional drill."""
    return bool(META_RESPONSE.search(rationale))


def content_terms(value: str) -> set[str]:
    return {
        word for word in re.findall(r"[a-z]{5,}", value.lower())
        if word not in STOPWORDS
    }


def triage_citations(
    rationale: str, action_description: str, cited_ids: list[str], chunks: dict[str, Chunk],
    actor_jurisdiction: str | None = None,
) -> tuple[str, list[str]]:
    """Return warning status and IDs with no overlap or clear scope mismatch.

    Overlap can only indicate possible relevance. It cannot establish mandate,
    applicability, legal force, or support for an exact assertion.
    """
    if not cited_ids:
        return "INSUFFICIENT_EVIDENCE", []
    claim_terms = content_terms(f"{rationale} {action_description}")
    asserts_legal_basis = bool(LEGAL_CLAIM.search(rationale))
    weak = [
        chunk_id for chunk_id in cited_ids
        if chunk_id not in chunks
        or not claim_terms.intersection(content_terms(chunks[chunk_id].text))
        or (asserts_legal_basis and chunks[chunk_id].source_binding in NON_BINDING)
        or (asserts_legal_basis and actor_jurisdiction is not None
            and chunks[chunk_id].jurisdiction != actor_jurisdiction)
    ]
    return ("UNSUPPORTED" if weak else "PARTIALLY_SUPPORTED"), weak
