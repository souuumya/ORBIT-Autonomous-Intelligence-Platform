from __future__ import annotations

import logging
from typing import Any, List, Optional
from sqlalchemy.orm import Session

from app.db.repositories import MemoryRepository
from app.schemas.events import EventEnvelope, EventType
from app.services.event_bus import EventBus

logger = logging.getLogger(__name__)


class MemoryEngine:
    def __init__(
        self,
        db: Session,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.db = db
        self.memory_repo = MemoryRepository(db)
        self.event_bus = event_bus
        self._short_term_memory: dict[str, dict[str, Any]] = {}

    def set_short_term_context(self, mission_id: str, key: str, value: Any) -> None:
        if mission_id not in self._short_term_memory:
            self._short_term_memory[mission_id] = {}
        self._short_term_memory[mission_id][key] = value

    def get_short_term_context(self, mission_id: str, key: str) -> Optional[Any]:
        return self._short_term_memory.get(mission_id, {}).get(key)

    def get_all_short_term_context(self, mission_id: str) -> dict[str, Any]:
        return dict(self._short_term_memory.get(mission_id, {}))

    def clear_short_term_context(self, mission_id: str) -> None:
        self._short_term_memory.pop(mission_id, None)

    async def store_long_term_memory(
        self,
        summary: str,
        insight: str,
        memory_type: str = "insight",
        confidence_score: float = 1.0,
        tags: Optional[List[str]] = None,
        mission_id: Optional[str] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> Any:
        record = self.memory_repo.store_memory(
            summary=summary,
            insight=insight,
            memory_type=memory_type,
            confidence_score=confidence_score,
            tags=tags,
            mission_id=mission_id,
            user_id=user_id,
            organization_id=organization_id,
        )

        if self.event_bus:
            await self.event_bus.publish(
                EventEnvelope(
                    event_type=EventType.MEMORY_UPDATED,
                    payload={
                        "memory_id": record.id,
                        "memory_type": record.memory_type,
                        "summary": record.summary,
                        "mission_id": mission_id,
                    },
                )
            )

        logger.info("Stored long-term memory record %s for mission %s", record.id, mission_id)
        return record

    def retrieve_relevant_memories(
        self,
        query_text: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Any]:
        return self.memory_repo.search_memories(query_text=query_text, memory_type=memory_type, limit=limit)
