from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    MISSION_CREATED = "MissionCreated"
    MISSION_STATE_CHANGED = "MissionStateChanged"
    PLANNER_STARTED = "PlannerStarted"
    PLANNER_COMPLETED = "PlannerCompleted"
    RESEARCH_STARTED = "ResearchStarted"
    RESEARCH_COMPLETED = "ResearchCompleted"
    DECISION_STARTED = "DecisionStarted"
    DECISION_COMPLETED = "DecisionCompleted"
    STRATEGY_SELECTED = "StrategySelected"
    CREATOR_STARTED = "CreatorStarted"
    CREATOR_COMPLETED = "CreatorCompleted"
    OUTPUT_GENERATED = "OutputGenerated"
    REVIEWER_STARTED = "ReviewerStarted"
    REVIEWER_COMPLETED = "ReviewerCompleted"
    REVIEW_PASSED = "ReviewPassed"
    REVIEW_FAILED = "ReviewFailed"
    ADAPTATION_TRIGGERED = "AdaptationTriggered"
    MEMORY_UPDATED = "MemoryUpdated"
    REFLECTION_COMPLETED = "ReflectionCompleted"
    MISSION_COMPLETED = "MissionCompleted"
    MISSION_FAILED = "MissionFailed"



class EventStatus(str, Enum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"


class EventEnvelope(BaseModel):
    event_type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EventHistoryEntry(BaseModel):
    event_id: str
    event: EventEnvelope
    status: EventStatus
    attempts: int = 0
    last_error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


EventHandler = Callable[[EventEnvelope], Any]
