"""ChromaDB vector store with traceable, per-source deletable ids.

A single persistent collection ``"library"`` holds every chunk across all
documents. Chunk ids encode ``source::page::index`` so a whole document can be
removed reliably. Metadata includes an ``indexed_at`` timestamp so stats can
report the most recent ingestion.
"""
from __future__ import annotations

import time
from functools import lru_cache
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import get_settings
from app.rag.embeddings import get_embedding_function

_COLLECTION = "library"


def _chunk_id(meta: dict[str, Any]) -> str:
    return f"{meta['source']}::p{meta['page']}::{meta['chunk_index']}"


@lru_cache
def get_vectorstore() -> Chroma:
    settings = get_settings()
    return Chroma(
        collection_name=_COLLECTION,
        embedding_function=get_embedding_function(),
        persist_directory=str(settings.chroma_path),
    )


def add_documents(chunks: list[Document]) -> int:
    """Index chunks, assigning traceable ids and an ingestion timestamp.

    Returns the number of chunks added.
    """
    if not chunks:
        return 0
    now = time.time()
    for chunk in chunks:
        chunk.metadata["indexed_at"] = now
    ids = [_chunk_id(c.metadata) for c in chunks]
    get_vectorstore().add_documents(chunks, ids=ids)
    return len(chunks)


def delete_by_source(source: str) -> None:
    """Remove every chunk belonging to ``source`` from the collection."""
    get_vectorstore()._collection.delete(where={"source": source})


def _all_records() -> tuple[list[dict[str, Any]], list[str]]:
    result = get_vectorstore()._collection.get(include=["metadatas"])
    return result.get("metadatas", []) or [], result.get("ids", []) or []


def list_documents() -> list[dict[str, Any]]:
    """Aggregate indexed chunks by source: page range + chunk count."""
    metas, _ = _all_records()
    by_source: dict[str, dict[str, Any]] = {}
    for meta in metas:
        source = meta.get("source")
        if not source:
            continue
        entry = by_source.setdefault(
            source, {"source": source, "pages": set(), "chunks": 0}
        )
        entry["chunks"] += 1
        page = meta.get("page")
        if isinstance(page, int):
            entry["pages"].add(page)

    docs: list[dict[str, Any]] = []
    for source, entry in sorted(by_source.items()):
        pages = sorted(entry["pages"])
        docs.append(
            {
                "source": source,
                "page_count": len(pages),
                "page_range": f"{pages[0]}–{pages[-1]}" if pages else "—",
                "chunks": entry["chunks"],
            }
        )
    return docs


def get_stats() -> dict[str, Any]:
    """Live counts for the landing metrics band and stats endpoint."""
    metas, ids = _all_records()
    sources = {m.get("source") for m in metas if m.get("source")}
    pages = {m.get("page") for m in metas if isinstance(m.get("page"), int)}
    last_at = max((m.get("indexed_at", 0) for m in metas), default=0.0)
    doc_count = len(sources)
    chunk_count = len(ids)
    avg = round(chunk_count / doc_count, 1) if doc_count else 0
    return {
        "documents": doc_count,
        "total_chunks": chunk_count,
        "total_pages": len(pages),
        "avg_chunks_per_doc": avg,
        "last_ingested_at": last_at,
    }
