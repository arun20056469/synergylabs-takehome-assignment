# Problem 1 — Cost-Efficient RAG Application

This is a runnable FastAPI QA service over PDF, HTML, Markdown, and text files. It chooses **sqlite-vec**, an embedded SQLite vector extension: the process opens a local database only when the service runs, so its idle vector-storage cost is disk and backup rather than a permanently provisioned vector pod. The implementation uses a deterministic, normalized `hashing-tfidf-384` embedding by default so the sample project is reproducible offline. It writes the model name and 384 dimensions beside each embedding. This baseline can be swapped for an API or SentenceTransformers embedder without changing the store interface.

## Architecture

`PDF/HTML/MD -> extract + overlapping chunks -> SHA-256 IDs -> SQLite vectors + metadata -> top-k hybrid lexical/vector retrieval -> grounded answer with citations -> JSONL telemetry`

The stored metadata includes `source`, `file_type`, `category`, `chunk_index`, model name, and vector dimensions. `category`, `file_type`, and `source` are indexed filters. sqlite-vec narrows vector candidates; a transparent lexical re-ranker prevents a hash-embedding collision from beating direct lexical evidence. Re-ingestion uses the deterministic chunk hash as the SQLite primary key, so identical inputs add zero duplicate vectors.

## Setup and run

From the submission root:

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Ingest sample MD and HTML corpus; repeat to see idempotence.
python problem1_cost_efficient_rag\scripts\bootstrap_demo.py
python problem1_cost_efficient_rag\scripts\bootstrap_demo.py

# Generate retrieval, answer, latency, and cost artifacts.
python problem1_cost_efficient_rag\eval\run_evaluation.py

# Start API.
uvicorn problem1_cost_efficient_rag.src.api:app --reload --port 8000
```

On macOS/Linux replace the activation line with `source .venv/bin/activate` and path separators with `/`.

## API examples

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/ingest -ContentType 'application/json' -Body '{}'
Invoke-RestMethod -Method Post http://127.0.0.1:8000/query -ContentType 'application/json' -Body '{"query":"What encryption protects customer data at rest?", "top_k":3, "metadata_filter":{"category":"security"}}'
```

`POST /ingest` accepts `directory`, `chunk_size`, and `chunk_overlap`. Defaults are 450 characters and 60-character overlap (`RAG_CHUNK_SIZE`, `RAG_CHUNK_OVERLAP`). `POST /query` accepts `query`, `top_k`, and an optional metadata filter. When no chunk clears `RAG_MIN_SIMILARITY` (default `0.18`), it returns the exact no-context fallback instead of guessing.

Every query appends retrieval/generation timing, retrieved chunk count, and prompt/completion token usage to `logs/query_events.jsonl` (estimates for the offline extractor, provider usage when OpenAI is enabled). Set `RAG_GENERATION_PROVIDER=openai`, `RAG_GENERATION_MODEL`, and `OPENAI_API_KEY` in `.env` to use a grounded LLM prompt; `offline` remains the no-credential extractive baseline.

## Evaluation and results

`data/eval_dataset.json` contains 18 fixed questions with gold answers and deterministic SHA-256 gold chunk IDs (under the documented default chunking configuration). `eval/run_evaluation.py` computes Recall@3, Hit Rate@3, MRR, nDCG@3, context precision, exact-match containment, token F1, citation/lexical faithfulness, answer relevance, and p50/p95 retrieval latency. It writes:

- `results/eval_results.json` — all per-question and aggregate results.
- `results/cost_benchmark_table.md` — documented 100K, 1M, and 10M vector model.

The offline answer evaluator is intentionally deterministic: faithfulness checks that answers cite retrieved chunks and that answer terms are supported by the retrieved text. This avoids presenting an unrepeatable LLM score as evidence. The service also contains an optional OpenAI generation provider, with keys only in `.env`.

## Cost and trade-offs

The cost table includes a $25/month shared app VM plus disk and backup; it excludes embeddings and generation because those costs do not depend on vector-store choice. Managed prices are stated planning assumptions rather than vendor quotes. sqlite-vec is a good fit for small, lightly queried corpora and is deliberately transparent, but it becomes the weak point for large/high-QPS corpus search: it does not provide the distributed sharding, replicas, managed backup, or multi-region failover of a managed service. I would move to a managed service (or self-host Qdrant/pgvector) when sustained latency SLOs, concurrent writers, high availability, or 10M-scale query throughput matter more than the idle-cost savings.

For this demo, retrieval is the likely weak link at scale; generation is constrained to retrieved sentences and citations, prioritizing groundedness over fluent synthesis.
