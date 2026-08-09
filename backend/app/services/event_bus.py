from __future__ import annotations

import asyncio
import logging
import threading
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Awaitable, Callable, Optional

from app.schemas.events import EventEnvelope, EventHandler, EventHistoryEntry, EventStatus, EventType
from app.utils.retry import async_retry_with_backoff

logger = logging.getLogger(__name__)


@dataclass
class EventBusDependencies:
    logger: Optional[logging.Logger] = None


@dataclass
class EventBus:
    """Async Event Bus providing publish/subscribe messaging, event history logging, subscriber retries,
    and Dead Letter Queue (DLQ) support.
    """
    max_retries: int = 3
    dependencies: EventBusDependencies = field(default_factory=EventBusDependencies)
    _subscribers: dict[EventType, list[EventHandler]] = field(default_factory=lambda: defaultdict(list), init=False)
    _history: list[EventHistoryEntry] = field(default_factory=list, init=False)
    _dead_letter_queue: list[EventHistoryEntry] = field(default_factory=list, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    _sync_lock: threading.RLock = field(default_factory=threading.RLock, init=False)

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Register a subscriber handler for a specific EventType."""
        with self._sync_lock:
            self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unregister a subscriber handler for a specific EventType."""
        with self._sync_lock:
            self._subscribers[event_type] = [subscriber for subscriber in self._subscribers.get(event_type, []) if subscriber != handler]

    def get_registered_event_types(self) -> list[EventType]:
        """Get list of EventTypes currently having active subscribers."""
        with self._sync_lock:
            return list(self._subscribers.keys())

    def get_subscribers(self, event_type: EventType) -> list[EventHandler]:
        """Get list of active subscriber handlers for an EventType."""
        with self._sync_lock:
            return list(self._subscribers.get(event_type, []))

    def get_history(self) -> list[EventHistoryEntry]:
        """Retrieve copy of all recorded event history entries."""
        with self._sync_lock:
            return list(self._history)

    def get_dead_letter_queue(self) -> list[EventHistoryEntry]:
        """Retrieve copy of Dead Letter Queue (DLQ) entries."""
        with self._sync_lock:
            return list(self._dead_letter_queue)

    async def publish(self, event: EventEnvelope) -> EventHistoryEntry:
        """Publish an EventEnvelope asynchronously to all registered subscribers."""
        history_entry = EventHistoryEntry(
            event_id=str(uuid.uuid4()),
            event=event,
            status=EventStatus.PENDING,
            attempts=0,
        )

        with self._sync_lock:
            self._history.append(history_entry)

        await self._dispatch_event(history_entry)
        return history_entry

    async def _dispatch_event(self, entry: EventHistoryEntry) -> None:
        async with self._lock:
            subscribers = list(self.get_subscribers(entry.event.event_type))
            if not subscribers:
                entry.status = EventStatus.DELIVERED
                entry.updated_at = datetime.now(UTC)
                return

            for subscriber in subscribers:
                def on_retry(exc: Exception, attempt: int) -> None:
                    entry.attempts = attempt
                    entry.last_error = str(exc)
                    entry.status = EventStatus.FAILED
                    entry.updated_at = datetime.now(UTC)
                    logger.warning("Event delivery attempt %d failed for %s: %s", attempt, entry.event_id, exc)

                async def invoke_subscriber():
                    res = subscriber(entry.event)
                    if isinstance(res, Awaitable):
                        await res

                try:
                    await async_retry_with_backoff(
                        func=invoke_subscriber,
                        max_retries=self.max_retries - 1 if self.max_retries > 0 else 0,
                        initial_backoff=0.01,
                        backoff_factor=1.5,
                        jitter=False,
                        on_retry_callback=on_retry,
                    )
                    entry.attempts += 1
                    entry.status = EventStatus.DELIVERED
                    entry.updated_at = datetime.now(UTC)
                except Exception as exc:
                    entry.attempts = self.max_retries
                    entry.last_error = str(exc)
                    entry.status = EventStatus.DEAD_LETTER
                    entry.updated_at = datetime.now(UTC)
                    self._dead_letter_queue.append(entry)
                    logger.warning("Event %s delivered to dead-letter queue: %s", entry.event_id, exc)
                    break

            if entry.status in {EventStatus.PENDING, EventStatus.FAILED}:
                entry.status = EventStatus.DELIVERED
                entry.updated_at = datetime.now(UTC)
