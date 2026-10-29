# User Taste Preferences
- Works on Windows (project paths under `C:\Django\`, home at `C:\Users\Asus`). Confidence: 0.9
- Prefers LangChain over LlamaIndex for RAG pipelines, even when LlamaIndex is recommended for the use case. Confidence: 0.6
- Prefers hosted LLM APIs (OpenAI/Anthropic) over local models (Ollama) for quality and simplicity over privacy/offline use. Confidence: 0.6
- Prefers PyMuPDF (`fitz`) for PDF parsing with page-aware extraction. Confidence: 0.5
- Prefers server-rendered templates (Jinja2 + HTMX) over separate SPA frontends (React) for simpler projects — values monolithic, single-stack deployments. Confidence: 0.6
- Prefers detailed, verifiable citations (page number + source filename + verbatim quote) in RAG answer outputs. Confidence: 0.5
- Values structured output (Pydantic schemas via `with_structured_output`) over free-text parsing for reliable data extraction from LLMs. Confidence: 0.5
- Prefers restrained, "analytics-style" UI design: generous whitespace, subtle hairline borders, restrained shadows, responsive layouts, and explicitly avoids emoji-heavy cards and excessive gradients. Confidence: 0.65
