from __future__ import annotations

import math
import statistics

from .judge import JudgeClient


def quadratic_weighted_kappa(human: list[int], judge: list[int]) -> float:
    labels = sorted(set(human) | set(judge))
    if len(labels) < 2:
        return 1.0
    index = {label: i for i, label in enumerate(labels)}
    matrix = [[0.0 for _ in labels] for _ in labels]
    for a, b in zip(human, judge):
        matrix[index[a]][index[b]] += 1
    total = len(human)
    row = [sum(line) for line in matrix]
    col = [sum(matrix[i][j] for i in range(len(labels))) for j in range(len(labels))]
    observed = expected = 0.0
    denominator = max(1, (len(labels) - 1) ** 2)
    for i in range(len(labels)):
        for j in range(len(labels)):
            weight = ((i - j) ** 2) / denominator
            observed += weight * matrix[i][j] / total
            expected += weight * (row[i] * col[j]) / (total * total)
    return round(1 - observed / expected, 4) if expected else 1.0


def validate_gold(cases: list[dict], labels: list[dict]) -> dict:
    label_by_id = {row["id"]: row for row in labels}
    human, judge, winner_match = [], [], []
    for case in cases:
        gold = label_by_id[case["id"]]
        human.extend([gold["human_score_a"], gold["human_score_b"]])
        judge.extend([round(case["verdict_a"].overall_score), round(case["verdict_b"].overall_score)])
        winner_match.append(case["pairwise"]["final_winner"] == gold["human_winner"])
    return {"score_exact_agreement": round(sum(a == b for a, b in zip(human, judge)) / len(human), 4),
            "quadratic_weighted_cohens_kappa": quadratic_weighted_kappa(human, judge),
            "pairwise_winner_agreement": round(sum(winner_match) / len(winner_match), 4), "observations": len(human)}


def test_retest(client: JudgeClient, cases: list[dict], first_results: list[dict]) -> dict:
    repeat = []
    for case in cases:
        verdict_a = client.judge_pointwise(case, case["output_a"])
        verdict_b = client.judge_pointwise(case, case["output_b"])
        repeat.append((verdict_a, verdict_b))
    unchanged = 0
    total = len(cases) * 2
    for original, again in zip(first_results, repeat):
        unchanged += int(round(original["verdict_a"].overall_score, 3) == round(again[0].overall_score, 3))
        unchanged += int(round(original["verdict_b"].overall_score, 3) == round(again[1].overall_score, 3))
    return {"repeated_judgments": total, "same_score_rate": round(unchanged / total, 4),
            "note": "Offline provider is deterministic; use a non-zero-temperature external judge to measure production stochasticity."}


def run_probes(client: JudgeClient, probes: list[dict]) -> dict:
    rows = []
    for probe in probes:
        case = {"id": probe["id"], "input": probe["input"], "expected_output": probe["expected_output"], "system_prompt": "Be concise and factual."}
        verdict = client.judge_pointwise(case, probe["model_output"])
        correct = verdict.passed == probe["expected_pass"]
        if "max_overall_score" in probe:
            correct = correct and verdict.overall_score <= probe["max_overall_score"]
        rows.append({"id": probe["id"], "expected_pass": probe["expected_pass"], "judge_passed": verdict.passed,
                     "overall_score": verdict.overall_score, "expected_behavior_observed": correct})
    return {"probe_accuracy": round(sum(row["expected_behavior_observed"] for row in rows) / len(rows), 4), "probes": rows}
