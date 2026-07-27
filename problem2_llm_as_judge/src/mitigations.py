from __future__ import annotations

from .judge import JudgeClient


def evaluate_pairwise_unbiased(client: JudgeClient, case: dict) -> dict:
    """Run A/B and B/A; disagreements are ties rather than an unmeasured position preference."""
    forward = client.judge_pair(case, case["output_a"], case["output_b"])
    reverse_raw = client.judge_pair(case, case["output_b"], case["output_a"])
    reverse_mapped = {"A": "B", "B": "A", "Tie": "Tie"}[reverse_raw.winner]
    consistent = forward.winner == reverse_mapped
    final = forward.winner if consistent else "Tie"
    return {"case_id": case["id"], "forward_winner": forward.winner, "reverse_winner_mapped": reverse_mapped,
            "position_consistent": consistent, "position_flip": not consistent, "final_winner": final,
            "rationale": forward.rationale if consistent else "Order-swap disagreement; conservatively declared Tie."}
