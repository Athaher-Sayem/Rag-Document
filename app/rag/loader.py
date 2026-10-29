"""Page-aware PDF loader using PyMuPDF (fitz).

Emits one LangChain Document per page carrying metadata required for exact
citations: source filename, 1-indexed page number, and the current section
heading (detected via font-size heuristics). The per-page text becomes the
verbatim quote source for citations after chunking.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pymupdf as fitz  # PyMuPDF
from langchain_core.documents import Document


def _median_font_size(page: fitz.Page) -> float | None:
    """Median font size of all text spans on the page (heading baseline)."""
    sizes: list[float] = []
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if text:
                    sizes.append(span.get("size", 0))
    if not sizes:
        return None
    sizes.sort()
    return sizes[len(sizes) // 2]


def _headings_on_page(page: fitz.Page, baseline: float | None) -> list[str]:
    """Detect heading spans: markedly larger or bold text relative to baseline."""
    if baseline is None:
        return []
    threshold = baseline * 1.15
    headings: list[str] = []
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue
                size = span.get("size", 0)
                flags = span.get("flags", 0)
                bold = bool(flags & 2 ** 4)  # fitz.TEXT_FONT_BOLD
                if size >= threshold or (bold and size >= baseline):
                    if text.lower() not in {"references", "bibliography"} or size >= threshold:
                        headings.append(text)
    return headings


def load_pdf(path: str | Path) -> list[Document]:
    """Load a PDF into per-page Documents with citation metadata.

    Args:
        path: filesystem path to the PDF.

    Returns:
        One Document per non-empty page with metadata
        ``{"source": filename, "page": 1-indexed, "section": heading_or_None}``.
    """
    path = Path(path)
    source = path.name
    docs: list[Document] = []
    current_section: str | None = None

    with fitz.open(path) as doc:
        for page_number, page in enumerate(doc, start=1):
            baseline = _median_font_size(page)
            for heading in _headings_on_page(page, baseline):
                current_section = heading

            text = page.get_text("text").strip()
            if not text:
                continue

            docs.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": source,
                        "page": page_number,
                        "section": current_section,
                    },
                )
            )
    return docs


def iter_pdfs(paths: list[str | Path]) -> Iterator[Document]:
    """Load many PDFs, flattening their per-page Documents into one stream."""
    for path in paths:
        yield from load_pdf(path)
