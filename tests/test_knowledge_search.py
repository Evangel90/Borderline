from engine.knowledge import KnowledgeIndex
from engine.models import Chunk


def chunk(chunk_id, jurisdiction, text):
    return Chunk(
        chunk_id=chunk_id, doc_id=chunk_id, title="Synthetic source",
        jurisdiction=jurisdiction, page=1, total_pages=1, chunk_index=1,
        text=text, source_file="synthetic",
    )


class Embedder:
    def query_embed(self, _queries):
        yield type("Vector", (), {"tolist": lambda self: [0.1, 0.2]})()


class Collection:
    def count(self):
        return 2

    def query(self, **_kwargs):
        return {"metadatas": [[{"chunk_id": "ch"}, {"chunk_id": "ae"}]]}


def test_hybrid_search_keeps_jurisdiction_and_document_filters():
    index = object.__new__(KnowledgeIndex)
    index.chunks = {
        "ch": chunk("ch", "CH", "A clinical incident is reviewed."),
        "ae": chunk("ae", "AE", "Encryption and digital evidence are defined."),
    }
    index.embedder = Embedder()
    index.collection = Collection()
    assert [item.chunk_id for item in index.search("encryption digital evidence", ["AE"])] == ["ae"]
    assert index.search("encryption digital evidence", ["AE"], doc_id="ch") == []
