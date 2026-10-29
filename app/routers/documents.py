"""Document management routes: upload, list, delete."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.config import get_settings
from app.models.schemas import DocMeta, UploadResult
from app.rag.chunker import chunk_documents
from app.rag.loader import load_pdf
from app.rag.vectordb import add_documents, delete_by_source, list_documents

router = APIRouter(prefix="/api")


@router.post("/upload", response_model=list[UploadResult])
async def upload(files: list[UploadFile] = File(...)):
    settings = get_settings()
    upload_dir: Path = settings.upload_path
    results: list[UploadResult] = []

    for file in files:
        name = Path(file.filename or "").name
        if not name.lower().endswith(".pdf"):
            results.append(
                UploadResult(source=name, chunks=0, status="error", detail="not a PDF")
            )
            continue

        target = upload_dir / name
        with open(target, "wb") as out:
            out.write(await file.read())

        # Re-uploading replaces: drop any prior chunks for this source first.
        delete_by_source(name)
        chunks = chunk_documents(load_pdf(target))
        added = add_documents(chunks)
        results.append(UploadResult(source=name, chunks=added, status="ok"))

    return results


@router.get("/documents", response_model=list[DocMeta])
async def list_docs():
    return list_documents()


@router.delete("/documents/{source}")
async def delete_doc(source: str):
    delete_by_source(source)
    path = get_settings().upload_path / source
    if path.exists():
        path.unlink()
    return {"status": "deleted", "source": source}
