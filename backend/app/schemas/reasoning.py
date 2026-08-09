from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class GoalAnalysis(BaseModel):
    objective: str
    target_outcomes: List[str] = Field(default_factory=list)
    feasibility_factors: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)


class StrategyCandidate(BaseModel):
    id: str
    title: str
    description: str
    trade_offs: List[str] = Field(default_factory=list)
    relevance_score: float = 1.0
    impact_score: float = 1.0
    risk_score: float = 0.1
    feasibility_score: float = 1.0
    score: float = 1.0


class RejectedStrategy(BaseModel):
    id: str
    title: str
    reason: str


class DecisionRecord(BaseModel):
    reason: str
    confidence: float
    alternatives: List[StrategyCandidate] = Field(default_factory=list)
    selected_strategy: StrategyCandidate
    rejected_strategies: List[RejectedStrategy] = Field(default_factory=list)
    reflection: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
