"""Stats and document listing aggregation (no ChromaDB/embeddings required)."""
from __future__ import annotations

from app.rag import vectordb


def test_get_stats_aggregates_counts(monkeypatch):
    metas = [
        {"source": "a.pdf", "page": 1, "indexed_at": 100.0},
        {"source": "a.pdf", "page": 2, "indexed_at": 100.0},
        {"source": "b.pdf", "page": 1, "indexed_at": 200.0},
    ]
    ids = ["id1", "id2", "id3"]
    monkeypatch.setattr(vectordb, "_all_records", lambda: (metas, ids))

    stats = vectordb.get_stats()
    assert stats["documents"] == 2
    assert stats["total_chunks"] == 3
    assert stats["total_pages"] == 2  # distinct pages {1, 2}
    assert stats["avg_chunks_per_doc"] == 1.5
    assert stats["last_ingested_at"] == 200.0


def test_get_stats_empty(monkeypatch):
    monkeypatch.setattr(vectordb, "_all_records", lambda: ([], []))
    stats = vectordb.get_stats()
    assert stats["documents"] == 0
    assert stats["total_chunks"] == 0
    assert stats["avg_chunks_per_doc"] == 0


def test_list_documents_page_range(monkeypatch):
    metas = [
        {"source": "a.pdf", "page": 1},
        {"source": "a.pdf", "page": 2},
        {"source": "a.pdf", "page": 3},
    ]
    monkeypatch.setattr(vectordb, "_all_records", lambda: (metas, ["x", "y", "z"]))

    docs = vectordb.list_documents()
    assert len(docs) == 1
    entry = docs[0]
    assert entry["source"] == "a.pdf"
    assert entry["page_count"] == 3
    assert entry["chunks"] == 3
    assert entry["page_range"] == "1–3"
