from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from inspect import isawaitable
from typing import Any, Awaitable, Callable, Optional

from app.core.exceptions import ValidationError
from app.schemas.mission import (
    Mission,
    MissionEvent,
    MissionEventType,
    MissionInitializeRequest,
    MissionInitializeResponse,
    MissionStatus,
)


logger = logging.getLogger(__name__)


@dataclass
class MissionEngineDependencies:
    event_publisher: Optional[Callable[[MissionEvent], None]] = None


@dataclass
class MissionEngine:
    dependencies: MissionEngineDependencies = field(default_factory=MissionEngineDependencies)

    async def initialize_mission(self, request: MissionInitializeRequest) -> MissionInitializeResponse:
        self._validate_request(request)

        mission_id = self._generate_mission_id()
        mission = Mission(
            id=mission_id,
            title=request.title,
            objective=request.objective,
            description=request.description,
            priority=request.priority,
            context=request.context,
            created_by=request.created_by,
            metadata={"initial_request": request.model_dump()},
        )

        self._transition_state(mission, MissionStatus.INITIALIZED, "Mission initialized")
        self._emit_event(
            mission,
            MissionEventType.MISSION_CREATED,
            MissionStatus.INITIALIZED,
            "Mission created successfully",
        )
        self._emit_event(
            mission,
            MissionEventType.MISSION_STATE_CHANGED,
            MissionStatus.INITIALIZED,
            "Mission entered initialized state",
        )

        return MissionInitializeResponse(
            mission_id=mission.id,
            status=mission.status,
            created_at=mission.created_at,
            message="Mission initialized successfully",
        )

    async def transition_state(
        self,
        mission: Mission,
        new_state: MissionStatus,
        message: str,
        *,
        retry_count: int | None = None,
    ) -> Mission:
        if mission.status in {MissionStatus.COMPLETED, MissionStatus.CANCELLED, MissionStatus.FAILED}:
            return mission

        self._transition_state(mission, new_state, message, retry_count=retry_count)
        self._emit_event(
            mission,
            MissionEventType.MISSION_STATE_CHANGED,
            new_state,
            message,
        )
        return mission

    async def execute_mission(
        self,
        mission: Mission,
        states: list[MissionStatus],
        *,
        callback: Optional[Callable[[Mission, MissionStatus], Awaitable[None] | None]] = None,
    ) -> Mission:
        if not states:
            return mission

        for state in states:
            if mission.status in {MissionStatus.CANCELLED, MissionStatus.FAILED, MissionStatus.COMPLETED}:
                break

            await self.transition_state(mission, state, f"Advancing mission to {state.value}")
            if callback is not None:
                result = callback(mission, state)
                if isawaitable(result):
                    await result
            await asyncio.sleep(0)

        return mission

    async def cancel_mission(self, mission: Mission, reason: str) -> Mission:
        if mission.status in {MissionStatus.COMPLETED, MissionStatus.CANCELLED, MissionStatus.FAILED}:
            return mission

        mission.cancellation_requested = True
        mission.status = MissionStatus.CANCELLED
        mission.updated_at = datetime.now(UTC)
        mission.last_error = reason
        self._emit_event(
            mission,
            MissionEventType.MISSION_CANCELLED,
            MissionStatus.CANCELLED,
            reason,
        )
        logger.info("Mission %s cancelled: %s", mission.id, reason)
        return mission

    async def retry_mission(self, mission: Mission, reason: str) -> Mission:
        if mission.retries >= mission.max_retries:
            mission.status = MissionStatus.FAILED
            mission.last_error = reason
            mission.updated_at = datetime.now(UTC)
            self._emit_event(
                mission,
                MissionEventType.MISSION_FAILED,
                MissionStatus.FAILED,
                reason,
            )
            logger.warning("Mission %s exceeded max retries: %s", mission.id, reason)
            return mission

        mission.retries += 1
        mission.last_error = reason
        mission.updated_at = datetime.now(UTC)
        self._emit_event(
            mission,
            MissionEventType.MISSION_RETRY_REQUESTED,
            mission.status,
            f"Retry requested for mission due to: {reason}",
        )
        logger.info("Mission %s retry requested (%s/%s): %s", mission.id, mission.retries, mission.max_retries, reason)
        return mission

    async def fail_mission(self, mission: Mission, reason: str) -> Mission:
        mission.status = MissionStatus.FAILED
        mission.updated_at = datetime.now(UTC)
        mission.last_error = reason
        self._emit_event(
            mission,
            MissionEventType.MISSION_FAILED,
            MissionStatus.FAILED,
            reason,
        )
        logger.error("Mission %s failed: %s", mission.id, reason)
        return mission

    async def complete_mission(self, mission: Mission, message: str) -> Mission:
        mission.status = MissionStatus.COMPLETED
        mission.updated_at = datetime.now(UTC)
        self._emit_event(
            mission,
            MissionEventType.MISSION_COMPLETED,
            MissionStatus.COMPLETED,
            message,
        )
        logger.info("Mission %s completed: %s", mission.id, message)
        return mission

    def _validate_request(self, request: MissionInitializeRequest) -> None:
        if request.title is None or not request.title.strip():
            raise ValidationError("Mission title is required")
        if request.objective is None or not request.objective.strip():
            raise ValidationError("Mission objective is required")

    def _generate_mission_id(self) -> str:
        return f"mission-{uuid.uuid4().hex}"

    def _transition_state(
        self,
        mission: Mission,
        new_state: MissionStatus,
        message: str,
        *,
        retry_count: int | None = None,
    ) -> None:
        previous_state = mission.status
        mission.status = new_state
        mission.updated_at = datetime.now(UTC)
        if retry_count is not None:
            mission.retries = retry_count

        logger.info(
            "Mission %s state transition: %s -> %s | %s",
            mission.id,
            previous_state,
            new_state,
            message,
        )

    def _emit_event(
        self,
        mission: Mission,
        event_type: MissionEventType,
        state: MissionStatus,
        message: str,
        *,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        event = MissionEvent(
            event_type=event_type,
            mission_id=mission.id,
            state=state,
            message=message,
            metadata=metadata or {},
        )

        if self.dependencies.event_publisher is not None:
            self.dependencies.event_publisher(event)

        logger.info("Mission %s emitted event %s: %s", mission.id, event_type.value, message)
