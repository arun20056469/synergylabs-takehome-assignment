from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CriterionScore(BaseModel):
    score: int = Field(ge=1, le=5)
    rationale: str = Field(min_length=1)


class PointwiseVerdict(BaseModel):
    criteria: dict[str, CriterionScore]
    overall_score: float = Field(ge=1.0, le=5.0)
    overall_rationale: str = Field(min_length=1)
    passed: bool
    confidence: float = Field(ge=0.0, le=1.0)


class PairwiseVerdict(BaseModel):
    winner: Literal["A", "B", "Tie"]
    rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class JudgeCall(BaseModel):
    prompt: str
    raw_response: str
    prompt_tokens_estimate: int
    completion_tokens_estimate: int
    latency_ms: float
