"""Citation-aware prompt templates and context formatting.

The answer prompt forces the model to ground every claim in the retrieved
context and tag it inline with ``[filename, p.N]``. The condense prompt
rewrites a follow-up question into a standalone query using chat history so
memory-backed turns retrieve correctly.
"""
from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

CONDENSE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Given a conversation and a follow-up question, rewrite the "
            "follow-up into a standalone question that can be understood "
            "without the prior context. Reply with the question only.",
        ),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)

ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a precise research assistant that answers strictly from "
            "the provided context, which is extracted from academic papers and "
            "textbooks.\n\n"
            "Rules:\n"
            "1. Answer only using the context below. If the context does not "
            "contain the answer, say you do not know.\n"
            "2. After every claim, cite the source inline as "
            "[filename, p.N] using the page number from the context tag.\n"
            "3. Do not invent page numbers or sources.\n"
            "4. Keep the answer focused and readable.\n\n"
            "Context (each block tagged [CTX i | filename | p.N]):\n{context}",
        ),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)


def format_context(chunks: list[Document]) -> str:
    """Render chunks as tagged context blocks the model can cite precisely."""
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        source = chunk.metadata.get("source", "unknown")
        page = chunk.metadata.get("page", "?")
        lines.append(f"[CTX {i} | {source} | p.{page}]\n{chunk.page_content}")
    return "\n\n".join(lines)
