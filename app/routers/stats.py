"""Stats route: live ChromaDB counts for the landing metrics band."""
from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import Stats
from app.rag.vectordb import get_stats

router = APIRouter(prefix="/api")


@router.get("/stats", response_model=Stats)
async def stats():
    return get_stats()
