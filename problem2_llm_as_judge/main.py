from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from problem2_llm_as_judge.src.aggregator import aggregate
from problem2_llm_as_judge.src.judge import JudgeClient
from problem2_llm_as_judge.src.mitigations import evaluate_pairwise_unbiased
from problem2_llm_as_judge.src.validator import run_probes, test_retest, validate_gold


PROJECT = ROOT / "problem2_llm_as_judge"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else yaml.safe_load(path.read_text(encoding="utf-8"))


def run(all_checks: bool = True) -> dict:
    rubric = load(PROJECT / "config" / "rubric.yaml")
    config = load(PROJECT / "config" / "suite_config.yaml")
    cases = load(PROJECT / "data" / "test_suites" / "general_qa.json")
    client = JudgeClient(config["judge"], rubric, PROJECT / "logs" / "judge_audit.jsonl")
    evaluated = []
    for case in cases:
        verdict_a = client.judge_pointwise(case, case["output_a"])
        verdict_b = client.judge_pointwise(case, case["output_b"])
        evaluated.append({"id": case["id"], "verdict_a": verdict_a, "verdict_b": verdict_b,
                          "pairwise": evaluate_pairwise_unbiased(client, case)})
    report = {"configuration": {"judge_provider": client.provider, "judge_model": client.model,
                                "generator_a": config["generator_a"], "generator_b": config["generator_b"],
                                "mode": config["comparison"]["mode"]},
              "suite": aggregate(evaluated),
              "case_results": [{"id": item["id"], "verdict_a": item["verdict_a"].model_dump(), "verdict_b": item["verdict_b"].model_dump(),
                                "pairwise": item["pairwise"]} for item in evaluated]}
    if all_checks:
        report["validation"] = validate_gold(evaluated, load(PROJECT / "data" / "gold_labels" / "human_annotated.json"))
        report["test_retest"] = test_retest(client, cases, evaluated)
        report["adversarial_probes"] = run_probes(client, load(PROJECT / "data" / "test_suites" / "adversarial_probes.json"))
    report["audit"] = {"judge_calls": client.calls, "prompt_tokens_estimate": client.prompt_tokens, "completion_tokens_estimate": client.completion_tokens}
    output = PROJECT / "results" / "suite_report.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LLM-as-judge suite and validation.")
    parser.add_argument("--all", action="store_true", help="Run suite, validation, retest, and probes (default).")
    parser.add_argument("--suite-only", action="store_true", help="Run comparison only.")
    args = parser.parse_args()
    report = run(all_checks=not args.suite_only)
    print(json.dumps({"winner": report["suite"]["declared_winner"], "suite": report["suite"], "validation": report.get("validation")}, indent=2))
