from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class AgentState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    ROLLED_BACK = "ROLLED_BACK"


class StageConfig(BaseModel):
    stage_name: str
    agent_role: str
    timeout_seconds: float = 30.0
    max_retries: int = 2
    backoff_seconds: float = 0.1


class WorkflowConfig(BaseModel):
    global_timeout_seconds: float = 180.0
    stages: List[StageConfig] = Field(default_factory=lambda: [
        StageConfig(stage_name="Planning", agent_role="PlannerAgent", timeout_seconds=30.0, max_retries=2),
        StageConfig(stage_name="Researching", agent_role="ResearchAgent", timeout_seconds=30.0, max_retries=2),
        StageConfig(stage_name="Decision", agent_role="DecisionAgent", timeout_seconds=30.0, max_retries=2),
        StageConfig(stage_name="Creation", agent_role="CreatorAgent", timeout_seconds=30.0, max_retries=2),
        StageConfig(stage_name="Review", agent_role="ReviewerAgent", timeout_seconds=30.0, max_retries=2),
    ])


class AgentStatusSummary(BaseModel):
    agent_role: str
    status: AgentState = AgentState.IDLE
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: Optional[str] = None


class OrchestratorExecutionResult(BaseModel):
    mission_id: str
    status: str
    progress_percentage: float = 0.0
    agent_statuses: dict[str, AgentStatusSummary] = Field(default_factory=dict)
    stage_results: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
