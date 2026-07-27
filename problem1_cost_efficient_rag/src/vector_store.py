from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Iterable

from .ingestion import Chunk


class HashingEmbedder:
    """Deterministic 384-dim sparse hashing embedding for an offline reproducible demo."""

    def __init__(self, dimensions: int = 384, model_name: str = "hashing-tfidf-384") -> None:
        self.dimensions = dimensions
        self.model_name = model_name

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-z0-9]{2,}", text.lower())
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            number = int.from_bytes(digest, "big")
            idx = number % self.dimensions
            sign = 1.0 if (number >> 9) & 1 else -1.0
            vector[idx] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


class SQLiteVectorStore:
    """SQLite disk store: no always-on service, deterministic upserts, metadata indexes."""

    def __init__(self, path: Path, embedder: HashingEmbedder) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path, self.embedder = path, embedder
        self._sqlite_vec = None
        self.using_sqlite_vec = False
        try:
            import sqlite_vec
            self._sqlite_vec = sqlite_vec
        except ImportError:
            pass
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        if self._sqlite_vec is not None:
            try:
                connection.enable_load_extension(True)
                self._sqlite_vec.load(connection)
                connection.enable_load_extension(False)
            except sqlite3.Error:
                # Keep the implementation usable in restricted environments, but surface the fallback in health/README.
                self._sqlite_vec = None
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                  id TEXT PRIMARY KEY,
                  source TEXT NOT NULL,
                  file_type TEXT NOT NULL,
                  category TEXT NOT NULL,
                  chunk_index INTEGER NOT NULL,
                  text TEXT NOT NULL,
                  embedding TEXT NOT NULL,
                  embedding_model TEXT NOT NULL,
                  embedding_dimensions INTEGER NOT NULL,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_chunks_category ON chunks(category);
                CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source);
                """
            )
            if self._sqlite_vec is not None:
                try:
                    connection.execute(f"CREATE VIRTUAL TABLE IF NOT EXISTS chunk_vectors USING vec0(embedding float[{self.embedder.dimensions}])")
                    indexed_rowids = {int(row[0]) for row in connection.execute("SELECT rowid FROM chunk_vectors")}
                    for row in connection.execute("SELECT rowid, embedding FROM chunks"):
                        if int(row["rowid"]) not in indexed_rowids:
                            connection.execute("INSERT INTO chunk_vectors(rowid, embedding) VALUES (?, ?)",
                                               (int(row["rowid"]), self._sqlite_vec.serialize_float32(json.loads(row["embedding"]))))
                    self.using_sqlite_vec = True
                except sqlite3.Error:
                    self.using_sqlite_vec = False
            connection.commit()

    def upsert(self, chunks: Iterable[Chunk]) -> tuple[int, int]:
        inserted = skipped = 0
        with closing(self._connect()) as connection:
            for chunk in chunks:
                embedding = self.embedder.embed(chunk.text)
                vector = json.dumps(embedding, separators=(",", ":"))
                cursor = connection.execute(
                    """
                    INSERT INTO chunks (id, source, file_type, category, chunk_index, text, embedding, embedding_model, embedding_dimensions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO NOTHING
                    """,
                    (chunk.chunk_id, chunk.source, chunk.file_type, chunk.category, chunk.chunk_index,
                     chunk.text, vector, self.embedder.model_name, self.embedder.dimensions),
                )
                if cursor.rowcount:
                    if self.using_sqlite_vec and self._sqlite_vec is not None:
                        rowid = connection.execute("SELECT rowid FROM chunks WHERE id = ?", (chunk.chunk_id,)).fetchone()[0]
                        connection.execute("INSERT INTO chunk_vectors(rowid, embedding) VALUES (?, ?)",
                                           (rowid, self._sqlite_vec.serialize_float32(embedding)))
                    inserted += 1
                else:
                    skipped += 1
            connection.commit()
        return inserted, skipped

    def search(self, query: str, top_k: int = 3, metadata_filter: dict[str, str] | None = None) -> list[dict[str, Any]]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        metadata_filter = metadata_filter or {}
        allowed = {"category", "file_type", "source"}
        bad = set(metadata_filter) - allowed
        if bad:
            raise ValueError(f"Unsupported metadata filter(s): {sorted(bad)}")
        clauses, params = [], []
        for key, value in metadata_filter.items():
            clauses.append(f"{key} = ?")
            params.append(value)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        query_vector = self.embedder.embed(query)
        query_terms = self._meaningful_terms(query)
        with closing(self._connect()) as connection:
            rows = connection.execute("SELECT rowid AS sqlite_rowid, * FROM chunks" + where, params).fetchall()
            if self.using_sqlite_vec and self._sqlite_vec is not None:
                try:
                    candidates = {int(row["rowid"]) for row in connection.execute(
                        "SELECT rowid FROM chunk_vectors WHERE embedding MATCH ? AND k = ?",
                        (self._sqlite_vec.serialize_float32(query_vector), max(50, top_k * 10)),
                    )}
                    filtered_rows = [row for row in rows if int(row["sqlite_rowid"]) in candidates]
                    if filtered_rows:
                        rows = filtered_rows
                except sqlite3.Error:
                    self.using_sqlite_vec = False
        results = []
        for row in rows:
            vector_similarity = sum(a * b for a, b in zip(query_vector, json.loads(row["embedding"])))
            document_terms = self._meaningful_terms(row["text"])
            lexical_similarity = len(query_terms & document_terms) / len(query_terms) if query_terms else 0.0
            # Hybrid lexical/vector score is transparent and prevents a hash collision from outranking direct evidence.
            similarity = 0.30 * vector_similarity + 0.70 * lexical_similarity
            record = dict(row)
            record.pop("embedding", None)
            record.pop("sqlite_rowid", None)
            record["score"] = round(similarity, 6)
            record["vector_score"] = round(vector_similarity, 6)
            record["lexical_score"] = round(lexical_similarity, 6)
            results.append(record)
        return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]

    @staticmethod
    def _meaningful_terms(text: str) -> set[str]:
        stop_words = {"a", "an", "the", "and", "are", "as", "at", "be", "by", "do", "does", "for", "from", "how", "in", "is", "of", "on", "or", "that", "this", "to", "what", "when", "which", "who", "with"}
        terms = set()
        for token in re.findall(r"[a-z0-9]{2,}", text.lower()):
            if token in stop_words:
                continue
            if token.endswith("tion") and len(token) > 6:
                token = token[:-3] + "t"  # encryption -> encrypt
            elif token.endswith("ed") and len(token) > 4:
                token = token[:-2]
            elif token.endswith("s") and len(token) > 4:
                token = token[:-1]
            terms.add(token)
        return terms

    def chunks_for_source(self, source: str) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection:
            return [dict(row) for row in connection.execute("SELECT * FROM chunks WHERE source = ? ORDER BY chunk_index", (source,))]

    def count(self) -> int:
        with closing(self._connect()) as connection:
            return int(connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])
