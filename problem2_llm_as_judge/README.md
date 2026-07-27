# Problem 2 — LLM-as-Judge Evaluation Pipeline

This runnable, reference-based pipeline evaluates two output configurations using a clear six-criterion rubric and an auditable structured verdict. It is intentionally designed as a regression-quality tool rather than a bare “give it a score” prompt.

## Judging design

The primary mode is **reference-based pairwise A-vs-B**, with pointwise verdicts recorded for each candidate. Reference-based judging fits this factual/support-oriented suite because a gold answer makes correctness and omissions inspectable; pairwise comparison is useful for declaring whether a new prompt/model wins. Each verdict includes `correctness`, `faithfulness`, `completeness`, `instruction_following`, `tone`, and `safety`, each with evidence rationale, plus an overall weighted score, pass state, and confidence.

## Run

From the submission root after installing `requirements.txt`:

```powershell
python problem2_llm_as_judge\main.py --all
python -m unittest problem2_llm_as_judge.tests.test_pipeline
```

The run reads JSON test suites and YAML configuration/rubric, appends every prompt and raw judge response to `logs/judge_audit.jsonl`, and writes `results/suite_report.json`. `JUDGE_PROVIDER=offline` is the reproducible default. Set `JUDGE_PROVIDER=openai`, `JUDGE_MODEL`, and `OPENAI_API_KEY` in `.env` to use an OpenAI judge; the generator labels remain independently configurable in `config/suite_config.yaml` and `GENERATOR_A_MODEL`/`GENERATOR_B_MODEL` environment variables.

## Bias controls implemented and measured

| Risk | Code mitigation | Reported evidence |
|---|---|---|
| Position bias | Every pair is judged as A/B and B/A. The reverse result is remapped to original labels; disagreement becomes a conservative Tie. | `pairwise.position_flip_rate` and per-case `position_flip`. |
| Verbosity bias | Rubric and prompt penalize unsupported padding. | `probe-padded-correct` cannot receive a high unpenalized score; terse-correct and verbose-wrong probes are reported. |
| Self-enhancement | Generator A/B families are configured separately from the judge family. | Configuration is saved in the report; select an external judge from a different family in production. |
| Sycophancy/style | Per-criterion reference grounding is required; polished confidently-wrong probes are included. | `probe-confidently-wrong` expected behavior. |
| Score clustering | 5/3/1 calibration anchors are injected into every judge prompt. | Per-criterion means and overall score distributions are retained per case. |

## Validation and release use

`--all` performs three validations: human/gold agreement (exact score agreement and quadratic weighted Cohen’s kappa), test-retest score consistency, and the adversarial probe suite. The bundled offline result demonstrates pipeline behavior, not real-world LLM reliability—it is deterministic and should not be used to gate a release by itself. Before release gating, run a diverse human-labelled suite with the actual external judge, require an acceptable kappa/flip rate, retain human review for safety/high-impact failures, and inspect audit records for regressions.

The report declares a winner only after position-swap mitigation. In the supplied suite, prompt/configuration B is expected to win because it has correct, concise answers while A contains omissions, style violations, and factual errors.
