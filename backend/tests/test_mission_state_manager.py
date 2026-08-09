import pytest
import asyncio

from app.schemas.mission import MissionInitializeRequest, MissionPriority, MissionStatus
from app.services.event_bus import EventBus
from app.services.mission_state_manager import MissionStateManager
from app.core.exceptions import ValidationError, NotFoundError


def test_initialize_mission(db_session):
    event_bus = EventBus()
    state_manager = MissionStateManager(db_session, event_bus)

    req = MissionInitializeRequest(
        title="Test Mission",
        objective="Verify state manager initialization",
        priority=MissionPriority.HIGH,
        created_by="user_123",
    )

    res = asyncio.run(state_manager.initialize_mission(req))
    assert res.mission_id is not None
    assert res.status == MissionStatus.INITIALIZED

    mission = state_manager.get_mission(res.mission_id)
    assert mission is not None
    assert mission.title == "Test Mission"
    assert mission.priority == "high"


def test_state_transitions_and_feed(db_session):
    event_bus = EventBus()
    state_manager = MissionStateManager(db_session, event_bus)

    req = MissionInitializeRequest(
        title="Transition Mission",
        objective="Test transition flow",
    )
    res = asyncio.run(state_manager.initialize_mission(req))
    mission_id = res.mission_id

    asyncio.run(state_manager.transition_state(mission_id, MissionStatus.PLANNING, "Entered planning phase"))
    mission = state_manager.get_mission(mission_id)
    assert mission.status == MissionStatus.PLANNING.value

    entries, total = state_manager.get_activity_feed(mission_id)
    assert total >= 2
    assert entries[0].message == "Entered planning phase"


def test_retry_and_failure(db_session):
    state_manager = MissionStateManager(db_session)

    req = MissionInitializeRequest(
        title="Retry Mission",
        objective="Test retry limits",
    )
    res = asyncio.run(state_manager.initialize_mission(req))
    mission_id = res.mission_id

    # Try retries up to max limit
    can_retry_1 = asyncio.run(state_manager.retry_mission(mission_id, "Error 1"))
    assert can_retry_1 is True

    can_retry_2 = asyncio.run(state_manager.retry_mission(mission_id, "Error 2"))
    assert can_retry_2 is True

    can_retry_3 = asyncio.run(state_manager.retry_mission(mission_id, "Error 3"))
    assert can_retry_3 is True

    # 4th retry should exceed limit and fail mission
    can_retry_4 = asyncio.run(state_manager.retry_mission(mission_id, "Error 4"))
    assert can_retry_4 is False

    mission = state_manager.get_mission(mission_id)
    assert mission.status == MissionStatus.FAILED.value


from pydantic import ValidationError as PydanticValidationError


def test_invalid_initialization(db_session):
    state_manager = MissionStateManager(db_session)
    with pytest.raises((ValidationError, PydanticValidationError)):
        asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(title="", objective="Valid")))

