from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import settings
from .ingestion import iter_documents, make_chunks
from .rag_pipeline import RAGPipeline
from .vector_store import HashingEmbedder, SQLiteVectorStore


app = FastAPI(title="Cost-Efficient RAG", version="1.0.0")
store = SQLiteVectorStore(settings.store_path, HashingEmbedder(settings.embedding_dimensions, settings.embedding_model))
pipeline = RAGPipeline(store, settings)


class IngestRequest(BaseModel):
    directory: str | None = Field(default=None, description="Local folder; defaults to bundled sample corpus")
    chunk_size: int | None = Field(default=None, gt=0)
    chunk_overlap: int | None = Field(default=None, ge=0)


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=settings.top_k, ge=1, le=20)
    metadata_filter: dict[Literal["category", "file_type", "source"], str] | None = None


@app.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "vector_backend": "sqlite-vec" if store.using_sqlite_vec else "sqlite-json-fallback", "stored_chunks": store.count(), "embedding_model": settings.embedding_model,
            "embedding_dimensions": settings.embedding_dimensions}


@app.post("/ingest")
def ingest(request: IngestRequest) -> dict[str, object]:
    directory = Path(request.directory).resolve() if request.directory else settings.raw_documents_dir
    if not directory.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory: {directory}")
    chunk_size = request.chunk_size or settings.chunk_size
    overlap = request.chunk_overlap if request.chunk_overlap is not None else settings.chunk_overlap
    if overlap >= chunk_size:
        raise HTTPException(status_code=400, detail="chunk_overlap must be less than chunk_size")
    inserted = skipped = documents = 0
    for file in iter_documents(directory):
        source = file.relative_to(settings.project_root).as_posix() if file.is_relative_to(settings.project_root) else str(file)
        new, existing = store.upsert(make_chunks(file, source, chunk_size, overlap))
        inserted += new
        skipped += existing
        documents += 1
    return {"documents": documents, "inserted_chunks": inserted, "skipped_existing_chunks": skipped,
            "stored_chunks": store.count(), "chunk_size": chunk_size, "chunk_overlap": overlap}


@app.post("/query")
def query(request: QueryRequest) -> dict[str, object]:
    try:
        return pipeline.query(request.query, request.top_k, request.metadata_filter)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
