from __future__ import annotations

import re

from problem1_cost_efficient_rag.src.rag_pipeline import FALLBACK_ANSWER


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def exact_match(answer: str, gold: str) -> float:
    return float(" ".join(_tokens(gold)) in " ".join(_tokens(answer)))


def token_f1(answer: str, gold: str) -> float:
    answer = re.sub(r"\[Doc:[^\]]+\]", "", answer)
    answer_tokens, gold_tokens = _tokens(answer), _tokens(gold)
    if not answer_tokens or not gold_tokens:
        return 0.0
    overlap = sum(min(answer_tokens.count(token), gold_tokens.count(token)) for token in set(answer_tokens))
    precision, recall = overlap / len(answer_tokens), overlap / len(gold_tokens)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def groundedness(answer: str, retrieved_chunks: list[dict]) -> float:
    """Citation- and lexical-support-based faithfulness check, reproducible without an LLM."""
    if answer == FALLBACK_ANSWER:
        return 1.0
    if not retrieved_chunks or "[Doc:" not in answer:
        return 0.0
    answer_terms = set(_tokens(re.sub(r"\[Doc:[^\]]+\]", "", answer)))
    context_terms = set(_tokens(" ".join(chunk["text"] for chunk in retrieved_chunks)))
    return round(len(answer_terms & context_terms) / max(1, len(answer_terms)), 4)


def answer_relevance(answer: str, question: str) -> float:
    if answer == FALLBACK_ANSWER:
        return 0.0
    question_terms, answer_terms = set(_tokens(question)), set(_tokens(answer))
    return round(len(question_terms & answer_terms) / max(1, len(question_terms)), 4)
