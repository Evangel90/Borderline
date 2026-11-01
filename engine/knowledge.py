"""Persistent Chroma vector index for provenance-bearing policy chunks."""

from __future__ import annotations

import hashlib
import json
import os
import re
import math
from collections import Counter
from typing import Iterable

import chromadb
from fastembed import TextEmbedding

from engine.models import Chunk


DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "policy_chunks_v1"
WINDOW_CHARS = 420
WINDOW_OVERLAP = 80
SEARCH_STOPWORDS = {"what", "which", "where", "does", "about", "from", "with",
                    "the", "and", "for", "into", "that", "this", "say", "under"}


class KnowledgeIndex:
    """Index chunks locally and return them with metadata/provenance intact."""

    def __init__(
        self,
        chunks: Iterable[Chunk],
        path: str | None = None,
        model_name: str | None = None,
    ) -> None:
        self.chunks = {chunk.chunk_id: chunk for chunk in chunks}
        self.path = path or os.getenv("BORDERLINE_VECTOR_PATH", "index/chroma")
        self.model_name = model_name or os.getenv("BORDERLINE_EMBEDDING_MODEL", DEFAULT_MODEL)
        self.embedder = TextEmbedding(model_name=self.model_name)
        self.client = chromadb.PersistentClient(path=self.path)
        self.collection = self._collection_for_model()
        self._sync()

    def _collection_for_model(self):
        existing_names = {
            item if isinstance(item, str) else item.name
            for item in self.client.list_collections()
        }
        if COLLECTION_NAME in existing_names:
            collection = self.client.get_collection(
                COLLECTION_NAME, embedding_function=None
            )
            metadata = collection.metadata or {}
            if metadata.get("embedding_model") != self.model_name:
                self.client.delete_collection(COLLECTION_NAME)
        return self.client.get_or_create_collection(
            COLLECTION_NAME,
            embedding_function=None,
            metadata={"hnsw:space": "cosine", "embedding_model": self.model_name},
        )

    @staticmethod
    def _content_hash(chunk: Chunk) -> str:
        content = json.dumps(
            {
                "doc_id": chunk.doc_id,
                "jurisdiction": chunk.jurisdiction,
                "title": chunk.title,
                "text": chunk.text,
                "source_file": chunk.source_file,
                "source_url": chunk.source_url,
                "source_issuer": chunk.source_issuer,
                "source_sha256": chunk.source_sha256,
                "source_retrieved": chunk.source_retrieved,
                "source_language": chunk.source_language,
                "source_official_language": chunk.source_official_language,
                "source_binding": chunk.source_binding,
                "source_in_force_from": chunk.source_in_force_from,
                "source_notes": chunk.source_notes,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _sync(self) -> None:
        current = self.collection.get(include=["metadatas"])
        stored = dict(zip(current["ids"], current["metadatas"] or []))
        vectors = {
            f"{chunk.chunk_id}::w{window_index}": (chunk, text, window_index)
            for chunk in self.chunks.values()
            for window_index, text in enumerate(self._windows(chunk.text), 1)
        }
        expected_ids = set(vectors)
        stale_ids = sorted(set(stored) - expected_ids)
        if stale_ids:
            self.collection.delete(ids=stale_ids)

        changed = [
            (vector_id, chunk, text, window_index)
            for vector_id, (chunk, text, window_index) in vectors.items()
            if stored.get(vector_id, {}).get("content_sha256") != self._content_hash(chunk)
        ]
        for start in range(0, len(changed), 64):
            batch = changed[start : start + 64]
            embeddings = list(self.embedder.embed([text for _, _, text, _ in batch]))
            self.collection.upsert(
                ids=[vector_id for vector_id, _, _, _ in batch],
                embeddings=[vector.tolist() for vector in embeddings],
                documents=[text for _, _, text, _ in batch],
                metadatas=[
                    {
                        "chunk_id": chunk.chunk_id,
                        "window_index": window_index,
                        "doc_id": chunk.doc_id,
                        "jurisdiction": chunk.jurisdiction,
                        "title": chunk.title,
                        "page": chunk.page,
                        "source_file": chunk.source_file,
                        "source_url": chunk.source_url,
                        "source_issuer": chunk.source_issuer,
                        "source_sha256": chunk.source_sha256,
                        "source_retrieved": chunk.source_retrieved,
                        "source_language": chunk.source_language,
                        "source_official_language": chunk.source_official_language,
                        "source_binding": chunk.source_binding,
                        "source_in_force_from": chunk.source_in_force_from,
                        "source_notes": chunk.source_notes,
                        "content_sha256": self._content_hash(chunk),
                    }
                    for _, chunk, _, window_index in batch
                ],
            )

    @staticmethod
    def _windows(text: str) -> list[str]:
        """Split long chunks into overlapping passages below the embedder's token limit."""
        if len(text) <= WINDOW_CHARS:
            return [text]
        windows = []
        start = 0
        while start < len(text):
            end = min(start + WINDOW_CHARS, len(text))
            if end < len(text):
                boundary = text.rfind(" ", start, end)
                if boundary > start + WINDOW_CHARS // 2:
                    end = boundary
            windows.append(text[start:end].strip())
            if end == len(text):
                break
            start = max(start + 1, end - WINDOW_OVERLAP)
        return windows

    def search(
        self,
        query: str,
        jurisdictions: list[str],
        top_k: int = 4,
        doc_id: str | None = None,
    ) -> list[Chunk]:
        if not query.strip() or not jurisdictions or top_k <= 0:
            return []

        where: dict = {"jurisdiction": {"$in": jurisdictions}}
        if doc_id:
            where = {"$and": [where, {"doc_id": doc_id}]}
        query_vector = next(self.embedder.query_embed([query])).tolist()
        count = self.collection.count()
        if not count:
            return []
        result = self.collection.query(
            query_embeddings=[query_vector],
            n_results=min(max(top_k * 8, top_k), count),
            where=where,
            include=["metadatas"],
        )
        vector_rank = []
        seen = set()
        for metadata in result["metadatas"][0]:
            chunk_id = metadata.get("chunk_id")
            if (chunk_id in self.chunks and chunk_id not in seen
                    and self.chunks[chunk_id].jurisdiction in jurisdictions
                    and (not doc_id or self.chunks[chunk_id].doc_id == doc_id)):
                seen.add(chunk_id)
                vector_rank.append(chunk_id)

        # Rare matching terms help exact article and definition questions that
        # semantic embeddings can place below the vector candidate cutoff.
        allowed = [
            chunk for chunk in self.chunks.values()
            if chunk.jurisdiction in jurisdictions and (not doc_id or chunk.doc_id == doc_id)
        ]
        terms = lambda value: {
            word for word in re.findall(r"[a-z]{3,}|[0-9]{2,}", value.lower())
            if word not in SEARCH_STOPWORDS
        }
        query_terms = terms(query)
        documents = {chunk.chunk_id: terms(f"{chunk.title} {chunk.text}") for chunk in allowed}
        frequencies = Counter(term for words in documents.values() for term in words)
        lexical_rank = sorted(
            allowed,
            key=lambda chunk: (
                -sum(
                    math.log1p((len(allowed) + 1) / (frequencies[term] + 1))
                    for term in query_terms & documents[chunk.chunk_id]
                ),
                chunk.chunk_id,
            ),
        )
        lexical_ids = [
            chunk.chunk_id for chunk in lexical_rank
            if query_terms & documents[chunk.chunk_id]
        ][:max(top_k * 8, top_k)]
        ranks = {}
        for candidates, weight in ((vector_rank, 1.0), (lexical_ids, 1.5)):
            for rank, chunk_id in enumerate(candidates, 1):
                ranks[chunk_id] = ranks.get(chunk_id, 0) + weight / (20 + rank)
        ordered = sorted(ranks, key=lambda chunk_id: (-ranks[chunk_id], chunk_id))
        return [self.chunks[chunk_id] for chunk_id in ordered[:top_k]]

