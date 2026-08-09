from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class MissionStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    PLANNING = "PLANNING"
    RESEARCHING = "RESEARCHING"
    CREATING = "CREATING"
    REVIEWING = "REVIEWING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class MissionPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MissionInitializeRequest(BaseModel):
    title: str = Field(..., alias="mission_title")
    objective: str = Field(..., alias="mission_objective")
    description: str = Field(default="", alias="mission_description")
    priority: MissionPriority | str = MissionPriority.MEDIUM
    context: dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = Field(default=None, alias="user_id")

    model_config = {
        "populate_by_name": True,
    }

    @field_validator("title", "objective")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Value must not be empty")
        return value.strip()


    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, value: Any) -> MissionPriority:
        if isinstance(value, MissionPriority):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            try:
                return MissionPriority(normalized)
            except ValueError as exc:
                raise ValueError("priority must be one of: low, medium, high, critical") from exc
        raise ValueError("priority must be one of: low, medium, high, critical")


class Mission(BaseModel):
    id: str
    title: str
    objective: str
    description: str = ""
    priority: MissionPriority
    context: dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = None
    status: MissionStatus = MissionStatus.INITIALIZED
    retries: int = 0
    max_retries: int = 3
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_error: Optional[str] = None
    cancellation_requested: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class MissionEventType(str, Enum):
    MISSION_CREATED = "MissionCreated"
    MISSION_STATE_CHANGED = "MissionStateChanged"
    MISSION_RETRY_REQUESTED = "MissionRetryRequested"
    MISSION_CANCELLED = "MissionCancelled"
    MISSION_FAILED = "MissionFailed"
    MISSION_COMPLETED = "MissionCompleted"


class MissionEvent(BaseModel):
    event_type: MissionEventType
    mission_id: str
    state: MissionStatus
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MissionInitializeResponse(BaseModel):
    mission_id: str
    status: MissionStatus
    created_at: datetime
    message: str
