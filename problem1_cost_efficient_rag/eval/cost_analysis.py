from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CostRow:
    vectors: int
    estimated_storage_gb: float
    embedded_monthly_usd: float
    managed_monthly_usd: float
    savings_percent: float


def estimate(vector_count: int, dimensions: int = 384) -> CostRow:
    # float32 vector + 512 B average metadata/index allowance; 2 replica backups excluded.
    storage_gb = vector_count * (dimensions * 4 + 512) / (1024 ** 3)
    # Shared app VM ($25/mo) + gp3-like disk ($0.08/GB/mo) + one backup ($0.023/GB/mo).
    embedded = 25.0 + storage_gb * 0.103
    # Conservative illustrative managed-serverless/pod allocation, including always-on base capacity.
    managed = 70.0 if vector_count <= 100_000 else 280.0 if vector_count <= 1_000_000 else 1_200.0
    return CostRow(vector_count, round(storage_gb, 2), round(embedded, 2), managed, round((1 - embedded / managed) * 100, 1))


def build_rows() -> list[dict]:
    return [asdict(estimate(count)) for count in (100_000, 1_000_000, 10_000_000)]


def markdown_table(rows: list[dict]) -> str:
    lines = [
        "| Vectors | Estimated disk | Embedded SQLite deployment | Illustrative managed DB | Savings |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(f"| {row['vectors']:,} | {row['estimated_storage_gb']:.2f} GB | ${row['embedded_monthly_usd']:.2f}/mo | ${row['managed_monthly_usd']:.2f}/mo | {row['savings_percent']:.1f}% |")
    return "\n".join(lines)
