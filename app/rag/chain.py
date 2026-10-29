"""LCEL RAG chain: condense -> retrieve -> answer, with streaming + citations.

The answer is streamed token-by-token over SSE. Citations are derived from the
retrieved chunks themselves (each carries source, page, and verbatim text), so
every citation's quote is guaranteed to be an exact span from the indexed PDF.
"""
from __future__ import annotations

import json
from typing import AsyncIterator

from langchain_core.documents import Document

from app.config import get_llm
from app.memory.store import add_turn, get_history
from app.models.schemas import AnswerWithCitations, Citation
from app.rag.prompts import ANSWER_PROMPT, CONDENSE_PROMPT, format_context
from app.rag.retriever import retrieve


def _condense_question(history: list, question: str) -> str:
    """Rewrite a follow-up into a standalone query using chat history."""
    if not history:
        return question
    chain = CONDENSE_PROMPT | get_llm()
    result = chain.invoke({"history": history, "question": question})
    text = getattr(result, "content", result)
    return text.strip() if isinstance(text, str) else str(text).strip()


def _to_citations(chunks: list[Document]) -> list[Citation]:
    """Dedupe retrieved chunks by (source, page); use chunk text as the quote."""
    seen: dict[tuple[str, int], Citation] = {}
    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        page = int(chunk.metadata.get("page", 0) or 0)
        key = (source, page)
        if key in seen:
            continue
        seen[key] = Citation(source=source, page=page, quote=chunk.page_content.strip())
    return list(seen.values())


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


def answer(session_id: str, message: str, source: str | None = None) -> AnswerWithCitations:
    """Synchronous (non-streaming) answer with structured citations."""
    history = get_history(session_id)
    standalone = _condense_question(history, message)
    chunks = retrieve(standalone, source=source)
    context = format_context(chunks)
    chain = ANSWER_PROMPT | get_llm()
    result = chain.invoke(
        {"context": context, "history": history, "question": message}
    )
    full_answer = getattr(result, "content", str(result))
    if not isinstance(full_answer, str):
        full_answer = str(full_answer)
    add_turn(session_id, message, full_answer)
    return AnswerWithCitations(answer=full_answer, citations=_to_citations(chunks))


async def answer_stream(
    session_id: str, message: str, source: str | None = None
) -> AsyncIterator[str]:
    """Stream an answer over SSE: token events, then a citations event, then done."""
    history = get_history(session_id)
    standalone = _condense_question(history, message)
    chunks = retrieve(standalone, source=source)
    context = format_context(chunks)

    chain = ANSWER_PROMPT | get_llm()
    parts: list[str] = []
    async for event in chain.astream(
        {"context": context, "history": history, "question": message}
    ):
        token = getattr(event, "content", "")
        if not token:
            continue
        parts.append(token)
        yield _sse({"type": "token", "text": token})

    full_answer = "".join(parts)
    add_turn(session_id, message, full_answer)

    citations = _to_citations(chunks)
    yield _sse({"type": "citations", "citations": [c.model_dump() for c in citations]})
    yield _sse({"type": "done"})
