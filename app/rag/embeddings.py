"""Embedding model accessor.

OpenAI embeddings are used regardless of LLM provider (Anthropic exposes no
embeddings API). The function is wrapped in a *lazy* Embeddings implementation
so the OpenAI client is only constructed when text is actually embedded. This
lets stats/document-listing and page rendering work even before an API key is
configured; the missing-key error surfaces only on a real embed call.
"""
from __future__ import annotations

from functools import lru_cache

from langchain_core.embeddings import Embeddings

from app.config import get_embeddings


class LazyEmbeddings(Embeddings):
    """Defers building the concrete embedding model until first use."""

    def __init__(self) -> None:
        self._inner: Embeddings | None = None

    def _get(self) -> Embeddings:
        if self._inner is None:
            self._inner = get_embeddings()
        return self._inner

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._get().embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._get().embed_query(text)


@lru_cache
def get_embedding_function() -> Embeddings:
    """Cached lazy embedding model suitable for LangChain's Chroma wrapper."""
    return LazyEmbeddings()
