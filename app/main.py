"""FastAPI application factory.

Mounts static assets, Jinja2 templates, and all routers. On startup it ensures
storage directories exist and pre-indexes the seed paper (for the landing demo
widget) when the library is empty.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.rag.chunker import chunk_documents
from app.rag.loader import load_pdf
from app.rag.vectordb import add_documents, get_stats
from app.routers import chat, documents, pages, stats

_STATIC_DIR = Path("app/static")
_TEMPLATES_DIR = Path("app/templates")

_STATIC_DIR.mkdir(parents=True, exist_ok=True)
_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Local PDF RAG")
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

app.include_router(pages.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(stats.router)


@app.on_event("startup")
async def seed_demo_paper() -> None:
    """Pre-index the seed paper so the landing demo widget works out of the box.

    Skipped silently when no API key is configured (embeddings need a provider).
    """
    settings = get_settings()
    try:
        if get_stats()["documents"] > 0:
            return
        seed = Path(settings.seed_paper)
        if not seed.exists():
            return
        chunks = chunk_documents(load_pdf(seed))
        add_documents(chunks)
    except Exception as exc:  # noqa: BLE001 - never block startup on seeding
        print(f"[seed] skipped: {exc}")
