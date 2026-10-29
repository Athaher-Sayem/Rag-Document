"""Page routes: landing, chat, and document library UIs."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.rag.vectordb import list_documents

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    # Starlette >=0.29 signature: TemplateResponse(request, name, context).
    return templates.TemplateResponse(request, "landing.html", {})


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse(
        request, "chat.html", {"documents": list_documents()}
    )


@router.get("/documents", response_class=HTMLResponse)
async def documents_page(request: Request):
    return templates.TemplateResponse(
        request, "documents.html", {"documents": list_documents()}
    )
