# Folio — Chat with Your Textbook/Research Paper

A citation-grade RAG app for PDFs. Ingest academic papers, textbooks, or
technical manuals and ask complex questions across them. Answers are grounded
strictly in retrieved context and cite the **source file, page number, and a
verbatim quote** for every claim. Conversations keep memory of prior turns.

## Stack

- **Backend:** FastAPI
- **RAG:** LangChain (LCEL), ChromaDB, PyMuPDF
- **LLM:** OpenAI (default) or Anthropic — configurable
- **Embeddings:** OpenAI `text-embedding-3-small`
- **Frontend:** Jinja2 templates + vanilla JS (SSE streaming), sage/forest/emerald design system

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt

copy .env.example .env            # then set OPENAI_API_KEY (and provider)
python run.py                     # http://127.0.0.1:8000
```

On first launch the seed paper in `data/seed/sample.pdf` is indexed so the
landing demo works immediately. Upload your own PDFs from `/documents`.

## Surfaces

| Route | What it is |
|---|---|
| `/` | Analytics-style landing page (animated citation trace, live metrics, demo) |
| `/chat` | Full chat app — streaming answers, citations rail, source scoping |
| `/documents` | Library — drag-drop upload, indexed-doc table, remove with undo |

## How it works

1. **Ingest** — `PyMuPDF` extracts per-page text and detects headings. Chunks
   carry `source`, `page`, `section`, and `chunk_index`.
2. **Retrieve** — chunks are embedded into ChromaDB; MMR retrieval returns
   diverse chunks, optionally scoped to one document.
3. **Cite** — a condense step rewrites follow-ups using chat history, the model
   answers only from context with inline `[file, p.N]` markers, and citations
   are derived from the retrieved chunks (so quotes are exact spans).

## Configuration

See `.env.example`. Key values:

- `LLM_PROVIDER` — `openai` or `anthropic`
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`
- `LLM_MODEL` — e.g. `gpt-4o-mini` or `claude-3-5-sonnet`
- `CHUNK_SIZE`, `CHUNK_OVERLAP`, `RETRIEVER_K`, `FETCH_K`, `MMR_LAMBDA`, `MEMORY_WINDOW`

## Tests

```bash
pytest
```

Chunker, citation-derivation, and stats tests run without any API key.
Retrieval tests require `OPENAI_API_KEY` (they exercise real embeddings) and
skip automatically when it is absent.

## Notes

- Fonts (Space Grotesk, DM Sans) are **self-hosted** in `app/static/fonts/` so
  no third-party font CDN is contacted on this local tool.
- Conversation memory is in-process. For multi-worker deployments, swap
  `app/memory/store.py` for a Redis/Postgres-backed message history.
- Stretch goals (not in baseline): cross-encoder re-ranking and an embedded
  PDF page viewer that jumps a citation to its highlighted page.
"# Rag-Document" 
