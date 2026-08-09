from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class ReplayStep(BaseModel):
    id: str
    mission_id: str
    step_number: int
    timestamp: datetime
    agent: str
    action_type: str
    reason: str
    confidence: float = 1.0
    duration_ms: float = 0.0
    output_summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class MissionReplayTimeline(BaseModel):
    mission_id: str
    total_steps: int
    steps: List[ReplayStep]
