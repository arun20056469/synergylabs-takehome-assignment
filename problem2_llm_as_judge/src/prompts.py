from __future__ import annotations

import json


def pointwise_prompt(case: dict, candidate: str, rubric: dict) -> str:
    anchors = "\n".join(f"Score {item['score']}: {item['example']} ({item['rationale']})" for item in rubric["scale_anchors"])
    criteria = "\n".join(f"- {name}: {details['description']}" for name, details in rubric["criteria"].items())
    return f"""You are an impartial, reference-based LLM judge. Return ONLY JSON.

Bias controls:
1. Judge factual support criterion by criterion before assigning the overall score.
2. Do not reward unsupported length; penalize irrelevant padding in tone/completeness.
3. Polished, confident, or sycophantic wording cannot compensate for factual errors.
4. Use the full 1-5 scale and calibrate against the anchors.

Score anchors:
{anchors}

Rubric:
{criteria}

Input: {case['input']}
System prompt: {case.get('system_prompt', '')}
Reference answer: {case.get('expected_output', '')}
Candidate answer: {candidate}

JSON schema: {{"criteria": {{"criterion": {{"score": 1, "rationale": "evidence"}}}}, "overall_score": 1.0, "overall_rationale": "summary", "passed": false, "confidence": 0.0}}"""


def pairwise_prompt(case: dict, answer_a: str, answer_b: str, rubric: dict) -> str:
    return f"""You are an impartial pairwise evaluator. Compare answers only against the input and reference, not their position or writing style. Unsupported verbosity and confidently stated errors are penalties. Return ONLY JSON with winner A, B, or Tie, rationale, and confidence.

Input: {case['input']}
Reference answer: {case.get('expected_output', '')}
Answer A: {answer_a}
Answer B: {answer_b}
Rubric criteria: {json.dumps(rubric['criteria'])}
JSON schema: {{"winner":"A|B|Tie", "rationale":"evidence", "confidence":0.0}}"""
