import asyncio
import pytest

from app.schemas.mission import MissionInitializeRequest
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine
from app.services.mission_state_manager import MissionStateManager
from app.services.replay_engine import DecisionReplayService


def test_decision_replay_end_to_end_timeline(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)
    replay_service = DecisionReplayService(db_session)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Replay Timeline Mission",
        objective="Verify complete decision replay step generation",
        created_by="tester",
    )))
    mission_id = res.mission_id

    orchestrator = AgentOrchestrator(
        db=db_session,
        event_bus=event_bus,
        state_manager=state_manager,
        memory_engine=memory_engine,
        replay_service=replay_service,
    )

    asyncio.run(orchestrator.execute_mission(mission_id))

    timeline = replay_service.get_timeline(mission_id)

    assert timeline.mission_id == mission_id
    assert timeline.total_steps >= 9
    steps = timeline.steps

    # Check chronological ordering
    for i in range(len(steps) - 1):
        assert steps[i].step_number < steps[i + 1].step_number
        assert steps[i].timestamp <= steps[i + 1].timestamp

    # Check action types sequence present
    action_types = [s.action_type for s in steps]
    assert "MISSION_STARTED" in action_types
    assert "PLANNER" in action_types
    assert "RESEARCH" in action_types
    assert "DECISION" in action_types
    assert "REJECTED_STRATEGY" in action_types
    assert "SELECTED_STRATEGY" in action_types
    assert "CREATOR" in action_types
    assert "REVIEWER" in action_types
    assert "MEMORY_UPDATE" in action_types
    assert "MISSION_COMPLETE" in action_types

    # Check required fields present on every step
    for step in steps:
        assert step.timestamp is not None
        assert step.agent is not None and len(step.agent) > 0
        assert step.reason is not None and len(step.reason) > 0
        assert 0.0 <= step.confidence <= 1.0
        assert step.duration_ms >= 0.0
        assert step.output_summary is not None


def test_api_agent_replay_endpoint(client, db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="API Replay Test",
        objective="Verify GET /api/v1/agent/replay endpoint",
    )))
    mission_id = res.mission_id

    orchestrator = AgentOrchestrator(
        db=db_session,
        event_bus=event_bus,
        state_manager=state_manager,
        memory_engine=memory_engine,
    )
    asyncio.run(orchestrator.execute_mission(mission_id))

    response = client.get(f"/api/v1/agent/replay?mission_id={mission_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["mission_id"] == mission_id
    assert data["total_steps"] >= 9
    assert len(data["steps"]) == data["total_steps"]

    first_step = data["steps"][0]
    assert first_step["action_type"] == "MISSION_STARTED"
    assert "timestamp" in first_step
    assert "agent" in first_step
    assert "reason" in first_step
    assert "confidence" in first_step
    assert "duration_ms" in first_step
    assert "output_summary" in first_step


def test_api_replay_not_found(client):
    response = client.get("/api/v1/agent/replay?mission_id=nonexistent-mission")
    assert response.status_code == 404
