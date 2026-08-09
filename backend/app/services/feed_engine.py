from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any, List, Optional, Dict, Tuple
from sqlalchemy.orm import Session

from app.db.repositories import ActivityFeedRepository
from app.schemas.events import EventEnvelope, EventType
from app.schemas.feed import FeedEntry, FeedResponse
from app.services.event_bus import EventBus

logger = logging.getLogger(__name__)


class FeedGenerationEngine:
    # Class-level cache dictionary: cache_key -> (expiration_timestamp, FeedResponse)
    _cache: Dict[str, Tuple[float, FeedResponse]] = {}
    _cache_ttl_seconds: float = 60.0
    _max_cache_entries: int = 1000

    def __init__(
        self,
        db: Session,
        event_bus: Optional[EventBus] = None,
        auto_subscribe: bool = False,
    ) -> None:
        self.db = db
        self.feed_repo = ActivityFeedRepository(db)
        self.event_bus = event_bus
        if auto_subscribe and event_bus:
            self.subscribe_to_event_bus(event_bus)

    def subscribe_to_event_bus(self, event_bus: Optional[EventBus] = None) -> None:
        eb = event_bus or self.event_bus
        if not eb:
            return
        for et in EventType:
            eb.subscribe(et, self.process_event)

    async def process_event(self, event: EventEnvelope) -> Optional[FeedEntry]:
        payload = event.payload or {}
        mission_id = payload.get("mission_id")
        if not mission_id or payload.get("_from_feed_engine"):
            return None

        current_stage = str(payload.get("current_stage") or payload.get("current_state") or event.event_type.value)
        agent_responsible = str(payload.get("agent_role") or payload.get("agent_responsible") or "System")
        progress_pct = float(payload.get("progress_percentage", 0.0))
        summary = str(payload.get("summary_of_work") or payload.get("message") or payload.get("reason") or f"Event {event.event_type.value} processed")
        decision = str(payload.get("decision_made") or payload.get("action") or f"Emitted {event.event_type.value}")
        confidence = float(payload.get("confidence", 1.0))
        reflection = payload.get("reflection")

        return await self.generate_entry(
            mission_id=mission_id,
            current_stage=current_stage,
            agent_responsible=agent_responsible,
            progress_percentage=progress_pct,
            summary_of_work=summary,
            decision_made=decision,
            confidence=confidence,
            reflection=reflection,
            event_type=event.event_type.value,
            extra_metadata={**payload, "_from_event": event.event_type.value},
            publish_event=False,
        )

    async def generate_entry(
        self,
        mission_id: str,
        current_stage: str,
        agent_responsible: str,
        progress_percentage: float,
        summary_of_work: str,
        decision_made: str,
        confidence: float = 1.0,
        reflection: Optional[str] = None,
        event_type: str = "STAGE_PROGRESS",
        user_id: Optional[str] = None,
        extra_metadata: Optional[dict[str, Any]] = None,
        publish_event: bool = True,
    ) -> FeedEntry:
        db_entry = self.feed_repo.add_feed_entry(
            mission_id=mission_id,
            current_stage=current_stage,
            agent_responsible=agent_responsible,
            progress_percentage=progress_percentage,
            summary_of_work=summary_of_work,
            decision_made=decision_made,
            confidence=confidence,
            reflection=reflection,
            event_type=event_type,
            user_id=user_id,
            extra_metadata=extra_metadata,
        )

        # Invalidate cache for this mission
        self.clear_cache(mission_id)

        entry = self._map_db_entry_to_feed_entry(db_entry)

        if publish_event and self.event_bus:
            await self.event_bus.publish(
                EventEnvelope(
                    event_type=EventType.MISSION_STATE_CHANGED,
                    payload={
                        "mission_id": mission_id,
                        "current_stage": current_stage,
                        "progress_percentage": progress_percentage,
                        "agent_responsible": agent_responsible,
                        "summary_of_work": summary_of_work,
                        "_from_feed_engine": True,
                    },
                )
            )

        logger.info(
            "FeedEngine generated entry for mission %s [%s - %.1f%%]: %s",
            mission_id,
            current_stage,
            progress_percentage,
            summary_of_work,
        )
        return entry

    async def get_mission_feed(
        self,
        mission_id: str,
        limit: int = 50,
        offset: int = 0,
        order_by_asc: bool = True,
        use_cache: bool = True,
    ) -> FeedResponse:
        cache_key = f"{mission_id}:{limit}:{offset}:{order_by_asc}"
        now = time.time()

        if use_cache and cache_key in self._cache:
            exp, cached_response = self._cache[cache_key]
            if now < exp:
                logger.debug("Cache HIT for mission feed query (%s)", cache_key)
                return cached_response

        entries, total = self.feed_repo.get_feed(
            mission_id=mission_id,
            limit=limit,
            offset=offset,
            order_by_asc=order_by_asc,
        )

        feed_entries = [self._map_db_entry_to_feed_entry(e) for e in entries]
        response = FeedResponse(
            mission_id=mission_id,
            entries=feed_entries,
            total_count=total,
        )

        if use_cache:
            self._evict_stale_cache_entries(now)
            self._cache[cache_key] = (now + self._cache_ttl_seconds, response)

        return response

    def _evict_stale_cache_entries(self, now: float) -> None:
        """Clean expired cache items and enforce max entry bounds."""
        expired = [k for k, (exp, _) in self._cache.items() if now >= exp]
        for k in expired:
            self._cache.pop(k, None)

        if len(self._cache) >= self._max_cache_entries:
            # Remove oldest 20% entries
            num_to_remove = max(1, int(self._max_cache_entries * 0.2))
            oldest_keys = list(self._cache.keys())[:num_to_remove]
            for k in oldest_keys:
                self._cache.pop(k, None)
            logger.debug("Evicted %d cache entries to enforce size bounds", len(oldest_keys))


    def clear_cache(self, mission_id: Optional[str] = None) -> None:
        if mission_id is None:
            self._cache.clear()
            logger.debug("Cleared entire FeedEngine cache")
        else:
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(f"{mission_id}:")]
            for k in keys_to_delete:
                self._cache.pop(k, None)
            logger.debug("Cleared FeedEngine cache for mission %s (%d keys removed)", mission_id, len(keys_to_delete))

    def _map_db_entry_to_feed_entry(self, db_entry: Any) -> FeedEntry:
        meta = db_entry.metadata_json or {}
        return FeedEntry(
            id=db_entry.id,
            mission_id=db_entry.mission_id,
            current_stage=meta.get("current_stage", "INITIALIZED"),
            timestamp=db_entry.created_at,
            agent_responsible=meta.get("agent_responsible", "System"),
            progress_percentage=float(meta.get("progress_percentage", 0.0)),
            summary_of_work=meta.get("summary_of_work", db_entry.message),
            decision_made=meta.get("decision_made", "State Transition"),
            confidence=float(meta.get("confidence", 1.0)),
            reflection=meta.get("reflection"),
            event_type=db_entry.event_type,
            message=db_entry.message,
            metadata=meta,
            created_at=db_entry.created_at,
        )
