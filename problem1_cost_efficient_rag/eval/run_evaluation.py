from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from problem1_cost_efficient_rag.eval.cost_analysis import build_rows, markdown_table
from problem1_cost_efficient_rag.eval.evaluate_answer import answer_relevance, exact_match, groundedness, token_f1
from problem1_cost_efficient_rag.eval.evaluate_retrieval import context_precision_at_k, hit_rate_at_k, ndcg_at_k, recall_at_k, reciprocal_rank
from problem1_cost_efficient_rag.src.api import IngestRequest, ingest, pipeline, store


def mean(values: list[float]) -> float:
    return round(statistics.fmean(values), 4) if values else 0.0


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((len(ordered) - 1) * p))
    return round(ordered[index], 3) if ordered else 0.0


def main() -> None:
    first_ingest = ingest(IngestRequest())
    second_ingest = ingest(IngestRequest())
    dataset = json.loads((ROOT / "problem1_cost_efficient_rag" / "data" / "eval_dataset.json").read_text(encoding="utf-8"))
    k = 3
    rows, recall, hit, mrr, ndcg, precision = [], [], [], [], [], []
    em, f1, faithful, relevance, latencies = [], [], [], [], []
    for case in dataset:
        result = pipeline.query(case["question"], top_k=k)
        relevant_ids = case["relevant_chunk_ids"]
        retrieved_ids = [item["chunk_id"] for item in result["citations"]]
        recall.append(recall_at_k(retrieved_ids, relevant_ids, k))
        hit.append(hit_rate_at_k(retrieved_ids, relevant_ids, k))
        mrr.append(reciprocal_rank(retrieved_ids, relevant_ids))
        ndcg.append(ndcg_at_k(retrieved_ids, relevant_ids, k))
        precision.append(context_precision_at_k(retrieved_ids, relevant_ids, k))
        em.append(exact_match(result["answer"], case["ground_truth_answer"]))
        f1.append(token_f1(result["answer"], case["ground_truth_answer"]))
        faithful.append(groundedness(result["answer"], result["retrieved_chunks"]))
        relevance.append(answer_relevance(result["answer"], case["question"]))
        latencies.append(result["telemetry"]["retrieval_latency_ms"])
        rows.append({"id": case["id"], "retrieved_ids": retrieved_ids, "relevant_chunk_ids": relevant_ids,
                     "answer": result["answer"], "answer_exact_match": em[-1], "answer_f1": f1[-1],
                     "faithfulness": faithful[-1], "answer_relevance": relevance[-1],
                     "retrieval_latency_ms": latencies[-1]})
    results = {
        "run_configuration": {"top_k": k, "vector_backend": "sqlite-vec" if store.using_sqlite_vec else "sqlite-json-fallback", "embedding_model": store.embedder.model_name, "embedding_dimensions": store.embedder.dimensions,
                              "dataset_questions": len(dataset), "stored_chunks": store.count()},
        "ingestion_idempotence": {"first_run": first_ingest, "second_run": second_ingest},
        "retrieval_metrics": {"recall_at_3": mean(recall), "hit_rate_at_3": mean(hit), "mrr": mean(mrr),
                              "ndcg_at_3": mean(ndcg), "context_precision_at_3": mean(precision)},
        "answer_metrics": {"exact_match_contains_gold": mean(em), "token_f1": mean(f1), "faithfulness_citation_lexical": mean(faithful),
                           "answer_relevance_lexical": mean(relevance)},
        "latency_ms": {"retrieval_p50": percentile(latencies, 0.5), "retrieval_p95": percentile(latencies, 0.95)},
        "per_question": rows,
    }
    results_dir = ROOT / "problem1_cost_efficient_rag" / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "eval_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    assumptions = """# Cost comparison assumptions\n\n- 384-dimensional float32 vectors (1,536 bytes) plus 512 bytes average metadata/index allowance per vector.\n- 50,000 queries/month; the embedded price includes a $25 shared application VM, $0.08/GB-month disk, and $0.023/GB-month backup.\n- Managed prices are deliberately illustrative planning assumptions for an always-on managed vector service, not a vendor quote; pricing, replicas, throughput and region can change the outcome.\n- Embedding/generation API spend is excluded because it is comparable across stores.\n\n"""
    (results_dir / "cost_benchmark_table.md").write_text(assumptions + markdown_table(build_rows()) + "\n", encoding="utf-8")
    print(json.dumps({"retrieval": results["retrieval_metrics"], "answers": results["answer_metrics"], "latency": results["latency_ms"]}, indent=2))


if __name__ == "__main__":
    main()
