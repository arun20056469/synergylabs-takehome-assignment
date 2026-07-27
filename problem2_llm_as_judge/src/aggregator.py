from __future__ import annotations

import statistics


def aggregate(cases: list[dict]) -> dict:
    if not cases:
        return {}
    criteria = sorted(cases[0]["verdict_a"].criteria)
    a_scores = [item["verdict_a"].overall_score for item in cases]
    b_scores = [item["verdict_b"].overall_score for item in cases]
    winners = [item["pairwise"]["final_winner"] for item in cases]
    return {
        "cases": len(cases),
        "config_a": {"pass_rate": round(sum(item["verdict_a"].passed for item in cases) / len(cases), 4), "mean_overall": round(statistics.fmean(a_scores), 3),
                     "mean_criteria": {name: round(statistics.fmean(item["verdict_a"].criteria[name].score for item in cases), 3) for name in criteria}},
        "config_b": {"pass_rate": round(sum(item["verdict_b"].passed for item in cases) / len(cases), 4), "mean_overall": round(statistics.fmean(b_scores), 3),
                     "mean_criteria": {name: round(statistics.fmean(item["verdict_b"].criteria[name].score for item in cases), 3) for name in criteria}},
        "pairwise": {"a_wins": winners.count("A"), "b_wins": winners.count("B"), "ties": winners.count("Tie"),
                     "position_flip_rate": round(sum(item["pairwise"]["position_flip"] for item in cases) / len(cases), 4)},
        "declared_winner": "B" if winners.count("B") > winners.count("A") else "A" if winners.count("A") > winners.count("B") else "Tie",
    }
