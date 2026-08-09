from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class FeedEntry(BaseModel):
    id: str
    mission_id: str
    current_stage: str = Field(..., description="Current operational stage of mission")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    agent_responsible: str = Field(..., description="Agent role managing the stage")
    progress_percentage: float = Field(0.0, ge=0.0, le=100.0)
    summary_of_work: str = Field(..., description="Concise summary of work performed")
    decision_made: str = Field(..., description="Decision or outcome of stage")
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    reflection: Optional[str] = Field(None, description="Post-execution reasoning reflection when available")
    
    # System compatibility fields
    event_type: str = "STAGE_PROGRESS"
    message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FeedResponse(BaseModel):
    mission_id: str
    entries: List[FeedEntry]
    total_count: int
