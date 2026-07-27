from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_ROOT = PROJECT_ROOT.parent
load_dotenv(SUBMISSION_ROOT / ".env")


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


@dataclass(frozen=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    store_path: Path = Path(os.getenv("RAG_STORE_PATH", str(PROJECT_ROOT / "data" / "vector_store" / "rag.sqlite3")))
    raw_documents_dir: Path = Path(os.getenv("RAG_DOCUMENTS_DIR", str(PROJECT_ROOT / "data" / "raw_documents")))
    log_path: Path = Path(os.getenv("RAG_LOG_PATH", str(PROJECT_ROOT / "logs" / "query_events.jsonl")))
    chunk_size: int = _env_int("RAG_CHUNK_SIZE", 450)
    chunk_overlap: int = _env_int("RAG_CHUNK_OVERLAP", 60)
    top_k: int = _env_int("RAG_TOP_K", 3)
    min_similarity: float = _env_float("RAG_MIN_SIMILARITY", 0.15)
    embedding_model: str = os.getenv("RAG_EMBEDDING_MODEL", "hashing-tfidf-384")
    embedding_dimensions: int = _env_int("RAG_EMBEDDING_DIMENSIONS", 384)
    generation_provider: str = os.getenv("RAG_GENERATION_PROVIDER", "offline").lower()
    generation_model: str = os.getenv("RAG_GENERATION_MODEL", "gpt-4o-mini")


settings = Settings()
