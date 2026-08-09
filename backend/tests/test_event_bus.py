import asyncio
import pytest

from app.schemas.events import EventEnvelope, EventHistoryEntry, EventStatus, EventType
from app.services.event_bus import EventBus


def test_publish_and_dispatch_delivers_to_subscribers():
    bus = EventBus()
    handled = []

    async def handler(event: EventEnvelope) -> None:
        handled.append(event.payload["mission_id"])

    bus.subscribe(EventType.MISSION_CREATED, handler)

    event = EventEnvelope(event_type=EventType.MISSION_CREATED, payload={"mission_id": "mission-123"})
    asyncio.run(bus.publish(event))

    assert handled == ["mission-123"]
    history = bus.get_history()
    assert len(history) == 1
    assert history[0].status == EventStatus.DELIVERED


def test_retry_failed_delivery_and_dead_letter_queue():
    bus = EventBus(max_retries=2)
    attempts = []

    async def flaky_handler(event: EventEnvelope) -> None:
        attempts.append(event.payload["mission_id"])
        raise RuntimeError("handler failed")

    bus.subscribe(EventType.MISSION_FAILED, flaky_handler)

    event = EventEnvelope(event_type=EventType.MISSION_FAILED, payload={"mission_id": "mission-999"})
    asyncio.run(bus.publish(event))

    assert attempts.count("mission-999") == 2
    assert len(bus.get_dead_letter_queue()) == 1
    assert bus.get_dead_letter_queue()[0].status == EventStatus.DEAD_LETTER


def test_registry_and_history_are_available():
    bus = EventBus()

    async def handler(event: EventEnvelope) -> None:
        return None

    bus.subscribe(EventType.MISSION_STATE_CHANGED, handler)

    event = EventEnvelope(event_type=EventType.MISSION_STATE_CHANGED, payload={"state": "PLANNING"})
    asyncio.run(bus.publish(event))

    assert EventType.MISSION_STATE_CHANGED in bus.get_registered_event_types()
    assert len(bus.get_subscribers(EventType.MISSION_STATE_CHANGED)) == 1
    assert len(bus.get_history()) == 1


def test_unsubscribe_removes_handler():
    bus = EventBus()
    calls = []

    def sync_handler(event: EventEnvelope):
        calls.append("called")

    bus.subscribe(EventType.PLANNER_STARTED, sync_handler)
    assert len(bus.get_subscribers(EventType.PLANNER_STARTED)) == 1

    bus.unsubscribe(EventType.PLANNER_STARTED, sync_handler)
    assert len(bus.get_subscribers(EventType.PLANNER_STARTED)) == 0
