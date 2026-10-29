"""Section/paragraph chunker preserving page citation metadata.

Splits page-level Documents (from the loader) into size-constrained chunks
while propagating ``source``, ``page`` and ``section`` onto every child chunk.
RecursiveCharacterTextSplitter preserves parent metadata by default; this
module wraps it to guarantee the citation-critical fields are present and to
add a per-chunk index for traceable ids.
"""
from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings

_SEPARATORS = ["\n\n", "\n", ". ", " "]


def build_splitter(
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> RecursiveCharacterTextSplitter:
    settings = get_settings()
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size if chunk_size is not None else settings.chunk_size,
        chunk_overlap=chunk_overlap if chunk_overlap is not None else settings.chunk_overlap,
        separators=_SEPARATORS,
    )


def chunk_documents(documents: list[Document]) -> list[Document]:
    """Chunk page-level Documents, preserving citation metadata on each chunk.

    Each returned chunk carries ``source``, ``page``, ``section`` (inherited
    from its parent page) plus a ``chunk_index`` scoped per source+page, used
    to build traceable vector-store ids.
    """
    splitter = build_splitter()
    chunks: list[Document] = []
    per_page_counter: dict[tuple[str, int], int] = {}

    for doc in documents:
        source = doc.metadata["source"]
        page = doc.metadata["page"]
        section = doc.metadata.get("section")

        for child in splitter.split_documents([doc]):
            key = (source, page)
            index = per_page_counter.get(key, 0)
            per_page_counter[key] = index + 1

            child.metadata = {
                "source": source,
                "page": page,
                "section": section,
                "chunk_index": index,
            }
            # Trim to a clean quote boundary; the splitter already breaks on
            # sentence/paragraph separators, so the content stays verbatim.
            child.page_content = child.page_content.strip()
            if child.page_content:
                chunks.append(child)

    return chunks
