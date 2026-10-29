"""Application settings and model factories.

Reads configuration from environment variables (or a local .env file) via
pydantic-settings. Centralizes RAG parameters and exposes factories that
return the configured LLM and embedding model regardless of provider choice.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM provider
    llm_provider: str = "openai"  # openai | anthropic
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # Embeddings
    embedding_model: str = "text-embedding-3-small"

    # Chunking
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Retrieval
    retriever_k: int = 6
    fetch_k: int = 20
    mmr_lambda: float = 0.5

    # Memory
    memory_window: int = 10

    # Seed demo paper (pre-indexed for the landing demo widget)
    seed_paper: str = "./data/seed/sample.pdf"

    # Paths
    data_dir: str = "./data"
    chroma_dir: str = "./data/chroma"
    upload_dir: str = "./data/uploads"

    @property
    def chroma_path(self) -> Path:
        return self._ensure(Path(self.chroma_dir))

    @property
    def upload_path(self) -> Path:
        return self._ensure(Path(self.upload_dir))

    @staticmethod
    def _ensure(path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_llm():
    """Return the configured chat model (OpenAI or Anthropic)."""
    settings = get_settings()
    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key,
            temperature=0.2,
        )
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        temperature=0.2,
        streaming=True,
    )


def get_embeddings():
    """Return the embedding model.

    OpenAI embeddings are used regardless of LLM provider because Anthropic
    does not expose an embeddings API.
    """
    settings = get_settings()
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )
