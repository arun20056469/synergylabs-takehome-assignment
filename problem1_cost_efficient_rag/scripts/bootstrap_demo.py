from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from problem1_cost_efficient_rag.src.api import ingest
from problem1_cost_efficient_rag.src.api import IngestRequest


if __name__ == "__main__":
    print(ingest(IngestRequest()))
