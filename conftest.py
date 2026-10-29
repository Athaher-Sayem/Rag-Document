"""Shared pytest fixtures: synthetic PDFs and an isolated Chroma directory."""
from __future__ import annotations

import sys
from pathlib import Path

import pymupdf as fitz
import pytest

# Ensure the project root is importable regardless of invocation directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """A 3-page PDF with a large heading and topical body text per page."""
    path = tmp_path / "sample.pdf"
    pages = [
        ("Attention", "The attention mechanism computes weighted sums of value vectors. " * 10),
        ("Transformers", "Transformers stack attention layers with feedforward networks. " * 10),
        ("Scaling", "Scaling laws describe loss as a function of compute data and parameters. " * 10),
    ]
    doc = fitz.open()
    for heading, body in pages:
        page = doc.new_page()
        page.insert_text((72, 72), heading, fontsize=18)
        # insert_textbox wraps within the rectangle so all text stays on-page.
        page.insert_textbox(fitz.Rect(72, 110, 520, 720), body, fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture
def long_page_pdf(tmp_path: Path) -> Path:
    """A single page of long, wrapping text that must split with overlap."""
    path = tmp_path / "long.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "LongPage", fontsize=18)
    words = " ".join(f"word{i}" for i in range(240))
    page.insert_textbox(fitz.Rect(72, 110, 520, 720), words, fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture
def isolated_chroma(tmp_path: Path, monkeypatch):
    """Point the vector store at a temp dir and reset its cache for a clean slate."""
    from app.config import get_settings
    from app.rag.vectordb import get_vectorstore

    settings = get_settings()
    monkeypatch.setattr(settings, "chroma_dir", str(tmp_path / "chroma"))
    get_vectorstore.cache_clear()
    yield
    get_vectorstore.cache_clear()
