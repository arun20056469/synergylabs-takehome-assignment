from __future__ import annotations

import math


def recall_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    relevant = set(relevant_ids)
    return len(set(retrieved_ids[:k]) & relevant) / len(relevant) if relevant else 0.0


def hit_rate_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    return float(bool(set(retrieved_ids[:k]) & set(relevant_ids)))


def reciprocal_rank(retrieved_ids: list[str], relevant_ids: list[str]) -> float:
    relevant = set(relevant_ids)
    for index, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant:
            return 1.0 / index
    return 0.0


def ndcg_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    relevant = set(relevant_ids)
    dcg = sum((1.0 / math.log2(rank + 1)) for rank, item in enumerate(retrieved_ids[:k], start=1) if item in relevant)
    ideal_count = min(len(relevant), k)
    ideal_dcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_count + 1))
    return dcg / ideal_dcg if ideal_dcg else 0.0


def context_precision_at_k(retrieved_ids: list[str], relevant_ids: list[str], k: int) -> float:
    shown = retrieved_ids[:k]
    return len(set(shown) & set(relevant_ids)) / len(shown) if shown else 0.0
