from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional
from sqlalchemy.orm import Session

from app.schemas.events import EventEnvelope, EventType
from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract Base Class for all autonomous platform agents.
    
    Provides standardized database access, event bus publishing, short/long-term memory integration,
    logging methods, and unified telemetry execution wrappers.
    """

    def __init__(
        self,
        db: Session,
        event_bus: Optional[EventBus] = None,
        memory_engine: Optional[MemoryEngine] = None,
    ) -> None:
        self.db = db
        self.event_bus = event_bus
        self.memory_engine = memory_engine
        self.agent_role = self.__class__.__name__

    @abstractmethod
    async def run(self, mission_id: str, **kwargs: Any) -> dict[str, Any]:
        """Execute agent responsibility for the given mission."""
        pass

    async def execute_with_telemetry(
        self,
        mission_id: str,
        action_func: Callable[[], Any],
        start_event_type: Optional[EventType] = None,
        complete_event_type: Optional[EventType] = None,
    ) -> dict[str, Any]:
        """Wrap agent execution with standardized timing, logging, and event emissions.

        Args:
            mission_id: The active mission identifier.
            action_func: Async or sync callable containing agent business logic.
            start_event_type: EventType emitted before execution.
            complete_event_type: EventType emitted upon successful execution.

        Returns:
            Dictionary payload produced by action_func.
        """
        self.log_info("Starting execution for mission %s", mission_id)
        if start_event_type:
            await self.emit_event(start_event_type, {"mission_id": mission_id})

        t_start = time.perf_counter()
        try:
            res = action_func()
            if hasattr(res, "__await__"):
                result = await res
            else:
                result = res

            duration_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
            self.log_info("Completed execution for mission %s in %.2fms", mission_id, duration_ms)

            if complete_event_type:
                await self.emit_event(complete_event_type, {**result, "duration_ms": duration_ms})

            return result

        except Exception as exc:
            duration_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
            self.log_error("Execution failed for mission %s after %.2fms: %s", mission_id, duration_ms, exc)
            raise exc

    async def emit_event(
        self,
        event_type: EventType,
        payload: dict[str, Any],
    ) -> None:
        """Publish an EventEnvelope to the EventBus if configured."""
        if self.event_bus:
            envelope = EventEnvelope(
                event_type=event_type,
                payload={**payload, "agent_role": self.agent_role},
            )
            await self.event_bus.publish(envelope)

    def log_info(self, msg: str, *args: Any) -> None:
        """Log informational message prefixed by agent role."""
        logger.info(f"[{self.agent_role}] " + msg, *args)

    def log_error(self, msg: str, *args: Any) -> None:
        """Log error message prefixed by agent role."""
        logger.error(f"[{self.agent_role}] " + msg, *args)
