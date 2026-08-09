import asyncio

from app.schemas.mission import (
    Mission,
    MissionEventType,
    MissionInitializeRequest,
    MissionPriority,
    MissionStatus,
)
from app.services.mission_engine import MissionEngine, MissionEngineDependencies


def test_initialize_mission_creates_event_and_sets_initialized_state():
    events = []

    def publisher(event):
        events.append(event)

    engine = MissionEngine(dependencies=MissionEngineDependencies(event_publisher=publisher))
    request = MissionInitializeRequest(
        title="Build a product brief",
        objective="Create a high-quality launch brief",
        description="Gather information and draft the brief",
        priority=MissionPriority.HIGH,
        created_by="tester",
    )

    response = asyncio.run(engine.initialize_mission(request))

    assert response.status == MissionStatus.INITIALIZED
    assert response.mission_id.startswith("mission-")
    assert len(events) == 2
    assert events[0].event_type == MissionEventType.MISSION_CREATED
    assert events[1].event_type == MissionEventType.MISSION_STATE_CHANGED


def test_retry_and_cancellation_state_changes():
    engine = MissionEngine()
    mission = Mission(
        id="mission-test",
        title="Research the market",
        objective="Understand the available opportunities",
        priority=MissionPriority.MEDIUM,
    )

    asyncio.run(engine.transition_state(mission, MissionStatus.RESEARCHING, "Starting research"))
    updated = asyncio.run(engine.retry_mission(mission, "Temporary issue"))
    assert updated.retries == 1
    assert updated.last_error == "Temporary issue"

    cancelled = asyncio.run(engine.cancel_mission(mission, "User cancelled"))
    assert cancelled.status == MissionStatus.CANCELLED
    assert cancelled.cancellation_requested is True


def test_execute_lifecycle_advances_through_states():
    engine = MissionEngine()
    mission = Mission(
        id="mission-lifecycle",
        title="Create a polished release",
        objective="Produce all launch materials",
        priority=MissionPriority.CRITICAL,
    )
    visited_states = []

    async def callback(current_mission, state):
        visited_states.append(state)

    asyncio.run(
        engine.execute_mission(
            mission,
            states=[MissionStatus.PLANNING, MissionStatus.RESEARCHING, MissionStatus.CREATING],
            callback=callback,
        )
    )

    assert [state for state in visited_states] == [
        MissionStatus.PLANNING,
        MissionStatus.RESEARCHING,
        MissionStatus.CREATING,
    ]
    assert mission.status == MissionStatus.CREATING
