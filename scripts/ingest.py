#!/usr/bin/env python3
"""
scripts/ingest.py - Ingest official PDFs into structured, citation-ready chunks.jsonl
Preserves document ID, title, jurisdiction, page number, and paragraph/clause indices.
"""

import csv
import json
import os
import re
import sys
from typing import List, Dict, Any
import pymupdf


def clean_text(text: str) -> str:
    """Normalize whitespace and strip unprintable characters."""
    # Replace multiple whitespace/newlines with a single space or normalized paragraph breaks
    lines = [line.strip() for line in text.splitlines()]
    # Reconnect hyphenated words broken across lines
    cleaned_lines = []
    for line in lines:
        if not line:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue
        if cleaned_lines and cleaned_lines[-1].endswith("-"):
            cleaned_lines[-1] = cleaned_lines[-1][:-1] + line
        else:
            cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def chunk_page_text(page_text: str, target_chunk_size: int = 1200, overlap: int = 200) -> List[str]:
    """
    Split page text into reasonable semantic chunks.
    Prioritizes article/section/paragraph boundaries if available.
    """
    cleaned = clean_text(page_text)
    if not cleaned:
        return []

    # If the page text is already within target length, keep it as one chunk
    if len(cleaned) <= target_chunk_size + 200:
        return [cleaned]

    # Split on double newline (paragraphs) first
    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        if current_len + para_len > target_chunk_size and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            # Keep the last paragraph for overlap if it's not huge
            if len(current_chunk[-1]) < overlap:
                current_chunk = [current_chunk[-1], para]
                current_len = len(current_chunk[0]) + para_len + 2
            else:
                current_chunk = [para]
                current_len = para_len
        else:
            current_chunk.append(para)
            current_len += para_len + 2

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def process_document(row: Dict[str, str]) -> List[Dict[str, Any]]:
    doc_id = row["doc_id"]
    title = row["title"]
    jurisdiction = row["jurisdiction"]
    file_path = row["file"]

    if not os.path.exists(file_path):
        print(f"⚠️  Skipping missing file: {file_path}")
        return []

    print(f"📄 Ingesting {doc_id} ({jurisdiction}): {os.path.basename(file_path)}")
    doc = pymupdf.open(file_path)
    total_pages = len(doc)
    doc_chunks = []

    for page_num in range(total_pages):
        page = doc[page_num]
        raw_text = page.get_text()
        page_chunks = chunk_page_text(raw_text)

        for chunk_idx, chunk_content in enumerate(page_chunks):
            chunk_id = f"{doc_id}:p{page_num + 1}:c{chunk_idx + 1}"
            doc_chunks.append({
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "title": title,
                "jurisdiction": jurisdiction,
                "page": page_num + 1,
                "total_pages": total_pages,
                "chunk_index": chunk_idx + 1,
                "text": chunk_content,
                "source_file": file_path
            })

    doc.close()
    return doc_chunks


def main():
    sources_csv = "data/sources.csv"
    if not os.path.exists(sources_csv):
        print(f"Error: {sources_csv} not found.")
        sys.exit(1)

    packs = {
        "AE": "packs/ae/chunks.jsonl",
        "CH": "packs/ch/chunks.jsonl",
        "GLOBAL": "packs/global/chunks.jsonl"
    }

    # Ensure directories exist
    for path in packs.values():
        os.makedirs(os.path.dirname(path), exist_ok=True)

    chunks_by_pack: Dict[str, List[Dict[str, Any]]] = {
        "AE": [],
        "CH": [],
        "GLOBAL": []
    }

    with open(sources_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            jurisdiction = row.get("jurisdiction", "").upper()
            if jurisdiction not in chunks_by_pack:
                continue
            chunks = process_document(row)
            chunks_by_pack[jurisdiction].extend(chunks)

    # Write out chunks.jsonl for each pack
    print("\n" + "=" * 50)
    for jur, output_file in packs.items():
        chunk_list = chunks_by_pack[jur]
        with open(output_file, mode="w", encoding="utf-8") as out_f:
            for c in chunk_list:
                out_f.write(json.dumps(c, ensure_ascii=False) + "\n")
        print(f"✅ Generated {output_file} with {len(chunk_list)} chunks.")

    print("=" * 50)
    print("Ingestion complete.")


if __name__ == "__main__":
    main()
