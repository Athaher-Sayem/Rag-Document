"""Chat routes: streaming answer endpoint and history lookup."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.memory.store import get_history_dicts
from app.models.schemas import ChatRequest, HistoryTurn
from app.rag.chain import answer_stream

router = APIRouter(prefix="/api")


@router.post("/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(
        answer_stream(request.session_id, request.message, request.source),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history/{session_id}", response_model=list[HistoryTurn])
async def history(session_id: str):
    return get_history_dicts(session_id)
