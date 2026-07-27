from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from problem1_cost_efficient_rag.eval.evaluate_retrieval import ndcg_at_k, recall_at_k, reciprocal_rank
from problem1_cost_efficient_rag.src.ingestion import split_text
from problem1_cost_efficient_rag.src.vector_store import HashingEmbedder, SQLiteVectorStore


class RAGCoreTests(unittest.TestCase):
    def test_chunk_overlap_validation(self) -> None:
        with self.assertRaises(ValueError):
            split_text("test", 10, 10)

    def test_idempotent_upsert_and_filter(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            store = SQLiteVectorStore(Path(folder) / "db.sqlite3", HashingEmbedder())
            from problem1_cost_efficient_rag.src.ingestion import Chunk
            chunk = Chunk("one", "sample.md", "md", "product", 0, "Starter plan includes fifteen users.")
            self.assertEqual(store.upsert([chunk]), (1, 0))
            self.assertEqual(store.upsert([chunk]), (0, 1))
            self.assertEqual(len(store.search("users", metadata_filter={"category": "product"})), 1)

    def test_ir_metrics(self) -> None:
        self.assertEqual(recall_at_k(["a", "b"], ["b"], 2), 1.0)
        self.assertEqual(reciprocal_rank(["a", "b"], ["b"]), 0.5)
        self.assertAlmostEqual(ndcg_at_k(["a", "b"], ["b"], 2), 1 / 1.5849625, places=5)


if __name__ == "__main__":
    unittest.main()
