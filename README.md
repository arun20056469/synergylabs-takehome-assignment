# SynergyLabs Applied AI / ML Engineering Take-Home

This submission contains two independently runnable projects:

1. `problem1_cost_efficient_rag` — a disk-backed, low-cost RAG service with ingestion, metadata filtering, evaluation, query telemetry, and a reproducible cost model.
2. `problem2_llm_as_judge` — a structured LLM-as-judge evaluation pipeline with pairwise order swapping, audit logs, adversarial probes, validation, and A/B reporting.

Each project has its own README, sample inputs, tests, and generated result artifacts. Both default to a deterministic offline provider so the included demonstrations run without credentials; optional OpenAI use is enabled only through `.env` settings.

## Quick start (Windows PowerShell)

```powershell
cd "synergylabs_takehome"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python problem1_cost_efficient_rag\scripts\bootstrap_demo.py
python problem1_cost_efficient_rag\eval\run_evaluation.py
python problem2_llm_as_judge\main.py --all
```

For the HTTP service, use:

```powershell
uvicorn problem1_cost_efficient_rag.src.api:app --reload --port 8000
```

Detailed commands, environment variables, limitations, and evaluation discussion are in each project README.
