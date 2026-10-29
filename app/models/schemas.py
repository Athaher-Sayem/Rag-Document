"""Pydantic schemas for API request/response contracts."""
from __future__ import annotations

from pydantic import BaseModel


class Citation(BaseModel):
    source: str
    page: int
    quote: str


class AnswerWithCitations(BaseModel):
    answer: str
    citations: list[Citation]


class ChatRequest(BaseModel):
    session_id: str
    message: str
    source: str | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]


class DocMeta(BaseModel):
    source: str
    page_count: int
    page_range: str
    chunks: int


class Stats(BaseModel):
    documents: int
    total_chunks: int
    total_pages: int
    avg_chunks_per_doc: float
    last_ingested_at: float


class UploadResult(BaseModel):
    source: str
    chunks: int
    status: str
    detail: str | None = None


class HistoryTurn(BaseModel):
    role: str
    content: str
