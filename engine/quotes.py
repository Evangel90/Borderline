"""
engine/quotes.py - Exact-quote verification shared by the liaison channel and the gap rules.

A quote counts only if it appears word for word in the chunk it cites. Only runs of
whitespace are normalised. Arabic quotes must match an Arabic chunk, carry an English
translation shown with a fixed "unofficial translation" label, and are rejected when the
extracted Arabic shows known PDF extraction errors (decision 3 in the handoff).
"""

from __future__ import annotations

import re
from typing import Any

from engine.models import Chunk

TRANSLATION_LABEL = "unofficial translation by the project, not an official text"
MIN_QUOTE_WORDS = 6

ARABIC = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
# Some UAE PDFs extract badly. Text showing these signs is not the official wording, so it
# is never accepted as a verbatim quote (decision 3); a human must check the PDF instead.
GARBLED_ARABIC_SIGNS = (
    # Broken lam-alef ligatures: "اإلمارات" for "الإمارات", "املتعلق" for "المتعلق".
    re.compile(r"(?<![\u0600-\u06FF])[وبلفك]?ا(?:إل|أل|آل|ال|مل)"),
    # Arabic presentation forms (glyph codes, not letters), as in "ﻟﺴﻨﺔ".
    re.compile(r"[\uFB50-\uFDFF\uFE70-\uFEFF]"),
    # Syriac, Arabic Supplement / Extended-A, Latin Extended-B and IPA letters inside Arabic text.
    re.compile(r"[\u0700-\u077F\u08A0-\u08FF\u0180-\u02FF]"),
    # Letters reversed within words (visual order): no Arabic word starts with ة or ى,
    # as in "ةدحتملا" for "المتحدة".
    re.compile(r"(?<![\u0600-\u06FF])[ةى]"),
)


def garbled_arabic(text: str) -> bool:
    return any(sign.search(text) for sign in GARBLED_ARABIC_SIGNS)


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def verify_quote(chunk_id: str, quote: str, translation: str,
                 shown: dict[str, Chunk]) -> dict[str, Any]:
    """Check one quote against the chunk it cites. Never raises; returns the check record."""
    record: dict[str, Any] = {
        "chunk_id": chunk_id,
        "quote": quote,
        "verified": False,
        "failure": "",
    }
    if translation.strip():
        record["translation"] = translation
        record["translation_label"] = TRANSLATION_LABEL
    chunk = shown.get(chunk_id)
    needle = normalize_whitespace(quote)
    is_arabic = bool(ARABIC.search(needle))
    if chunk is None:
        record["failure"] = "Chunk ID was not among the passages available to this check (shown to the reviewer, or in the knowledge base)."
        return record
    record.update(doc_id=chunk.doc_id, jurisdiction=chunk.jurisdiction,
                  language=chunk.source_language)
    if not needle:
        record["failure"] = "Quote is empty."
    elif len(needle.split()) < MIN_QUOTE_WORDS:
        record["failure"] = f"Quote is shorter than {MIN_QUOTE_WORDS} words."
    elif chunk.source_language == "ar" and not is_arabic:
        record["failure"] = "Chunk is Arabic; quote the Arabic original, not a translation."
    elif is_arabic and chunk.source_language != "ar":
        record["failure"] = "Arabic quote cited against a non-Arabic chunk."
    elif needle not in normalize_whitespace(chunk.text):
        record["failure"] = "Quote does not appear verbatim in the cited chunk."
    elif is_arabic and not translation.strip():
        record["failure"] = "Arabic quote has no English translation."
    elif is_arabic and garbled_arabic(needle):
        record["failure"] = (
            "Matched Arabic text shows known PDF extraction errors (broken ligatures or glyph codes); "
            "it is not the official wording and needs a human check."
        )
    else:
        record["verified"] = True
    return record
