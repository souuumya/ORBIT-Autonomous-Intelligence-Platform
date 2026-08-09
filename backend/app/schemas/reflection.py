from __future__ import annotations

from datetime import UTC, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class MissionReflectionReport(BaseModel):
    mission_id: str
    what_worked_well: List[str] = Field(default_factory=list, description="Positive aspects of execution and high-scoring stages")
    what_failed: List[str] = Field(default_factory=list, description="Failures, revision triggers, or quality bottlenecks")
    why_failed: List[str] = Field(default_factory=list, description="Root cause rationale for identified failures or revisions")
    best_performing_strategy: str = Field(..., description="Top strategy selected and validated")
    deprecated_strategies: List[str] = Field(default_factory=list, description="Strategies that underperformed or should never be used again")
    key_takeaways: List[str] = Field(default_factory=list, description="Critical insights that should be remembered for future missions")
    decision_confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence level of decision made")
    lessons_learned: List[str] = Field(default_factory=list, description="Synthesized operational lessons learned")
    improvement_suggestions: List[str] = Field(default_factory=list, description="Actionable suggestions for future pipeline iterations")
    performance_score: float = Field(1.0, ge=0.0, le=1.0, description="Composite overall mission performance score")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
