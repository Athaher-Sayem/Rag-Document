"""Citation derivation and context formatting (no LLM required)."""
from __future__ import annotations

from langchain_core.documents import Document

from app.rag.chain import _to_citations
from app.rag.prompts import format_context


def _doc(text: str, source: str, page: int) -> Document:
    return Document(page_content=text, metadata={"source": source, "page": page})


def test_citations_dedupe_by_source_and_page():
    chunks = [
        _doc("alpha text", "a.pdf", 1),
        _doc("beta text", "a.pdf", 1),  # same page -> deduped
        _doc("gamma text", "b.pdf", 2),
    ]
    citations = _to_citations(chunks)
    assert len(citations) == 2
    assert {(c.source, c.page) for c in citations} == {("a.pdf", 1), ("b.pdf", 2)}


def test_citation_quote_is_verbatim_chunk_text():
    citations = _to_citations([_doc("the exact span", "a.pdf", 3)])
    assert citations[0].quote == "the exact span"


def test_format_context_tags_each_chunk():
    chunks = [_doc("hello world", "x.pdf", 5)]
    context = format_context(chunks)
    assert "[CTX 1 | x.pdf | p.5]" in context
    assert "hello world" in context


def test_format_context_numbers_multiple_chunks():
    chunks = [_doc("one", "a.pdf", 1), _doc("two", "b.pdf", 2)]
    context = format_context(chunks)
    assert "[CTX 1 | a.pdf | p.1]" in context
    assert "[CTX 2 | b.pdf | p.2]" in context
