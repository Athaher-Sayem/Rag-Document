"""MMR retriever with optional per-source scoping.

Maximum Marginal Relevance keeps retrieved chunks diverse across pages, which
improves multi-claim answers. An optional ``source`` filter restricts results
to a single uploaded document.
"""
from __future__ import annotations

from langchain_core.documents import Document

from app.config import get_settings
from app.rag.vectordb import get_vectorstore


def build_search_kwargs(source: str | None, k: int | None) -> dict:
    settings = get_settings()
    kwargs: dict = {
        "k": k or settings.retriever_k,
        "fetch_k": settings.fetch_k,
        "lambda_mult": settings.mmr_lambda,
    }
    if source:
        kwargs["filter"] = {"source": source}
    return kwargs


def retrieve(query: str, source: str | None = None, k: int | None = None) -> list[Document]:
    """Return the top-k MMR chunks for ``query``, optionally scoped to ``source``."""
    retriever = get_vectorstore().as_retriever(
        search_type="mmr",
        search_kwargs=build_search_kwargs(source, k),
    )
    return retriever.invoke(query)
