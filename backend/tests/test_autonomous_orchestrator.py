import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from app.schemas.mission import MissionInitializeRequest, MissionStatus
from app.schemas.orchestrator import AgentState, StageConfig, WorkflowConfig
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine
from app.services.mission_state_manager import MissionStateManager


def test_autonomous_orchestrator_default_pipeline(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Autonomous Orchestrator Test",
        objective="Run full stage-by-stage pipeline",
    )))
    mission_id = res.mission_id

    orchestrator = AgentOrchestrator(
        db=db_session,
        event_bus=event_bus,
        state_manager=state_manager,
        memory_engine=memory_engine,
    )

    result = asyncio.run(orchestrator.execute_mission(mission_id))

    assert result.mission_id == mission_id
    assert result.status == MissionStatus.COMPLETED.value
    assert result.progress_percentage == 100.0
    assert len(result.stage_results) == 5

    # Check agent statuses
    statuses = orchestrator.get_agent_statuses()
    assert len(statuses) == 5
    for role, summary in statuses.items():
        assert summary.status == AgentState.COMPLETED

    mission = state_manager.get_mission(mission_id)
    assert mission.status == MissionStatus.COMPLETED.value


def test_autonomous_orchestrator_stage_timeout_and_rollback(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Timeout Mission",
        objective="Test stage timeout and rollback",
    )))
    mission_id = res.mission_id

    # Configure short stage timeout
    custom_workflow = WorkflowConfig(stages=[
        StageConfig(stage_name="Planning", agent_role="PlannerAgent", timeout_seconds=0.01, max_retries=1, backoff_seconds=0.01)
    ])

    orchestrator = AgentOrchestrator(
        db=db_session,
        event_bus=event_bus,
        state_manager=state_manager,
        memory_engine=memory_engine,
        workflow_config=custom_workflow,
    )

    # Patch planner.run to sleep longer than timeout
    async def slow_planner_run(m_id, **kwargs):
        await asyncio.sleep(0.5)
        return {}

    with patch.object(orchestrator.planner, "run", side_effect=slow_planner_run):
        result = asyncio.run(orchestrator.execute_mission(mission_id))
        assert result.status == MissionStatus.FAILED.value
        assert "timed out" in result.error

    statuses = orchestrator.get_agent_statuses()
    assert statuses["PlannerAgent"].status == AgentState.ROLLED_BACK


def test_autonomous_orchestrator_stage_retry_recovery(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Retry Recovery Mission",
        objective="Test stage retry recovery",
    )))
    mission_id = res.mission_id

    custom_workflow = WorkflowConfig(stages=[
        StageConfig(stage_name="Planning", agent_role="PlannerAgent", timeout_seconds=5.0, max_retries=2, backoff_seconds=0.01)
    ])

    orchestrator = AgentOrchestrator(
        db=db_session,
        event_bus=event_bus,
        state_manager=state_manager,
        memory_engine=memory_engine,
        workflow_config=custom_workflow,
    )

    attempts = 0
    original_planner_run = orchestrator.planner.run

    async def flaky_planner_run(m_id, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("Transient network issue")
        return await original_planner_run(m_id, **kwargs)

    with patch.object(orchestrator.planner, "run", side_effect=flaky_planner_run):
        result = asyncio.run(orchestrator.execute_mission(mission_id))
        assert result.status == MissionStatus.COMPLETED.value
        assert attempts == 2

    statuses = orchestrator.get_agent_statuses()
    assert statuses["PlannerAgent"].status == AgentState.COMPLETED


def test_autonomous_orchestrator_global_timeout(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Global Timeout Mission",
        objective="Test global mission execution timeout",
    )))
    mission_id = res.mission_id

    custom_workflow = WorkflowConfig(
        global_timeout_seconds=0.05,
        stages=[StageConfig(stage_name="Planning", agent_role="PlannerAgent", timeout_seconds=10.0)],
    )

    orchestrator = AgentOrchestrator(
        db=db_session,
        event_bus=event_bus,
        state_manager=state_manager,
        memory_engine=memory_engine,
        workflow_config=custom_workflow,
    )

    async def slow_planner(m_id, **kwargs):
        await asyncio.sleep(0.5)

    with patch.object(orchestrator.planner, "run", side_effect=slow_planner):
        result = asyncio.run(orchestrator.execute_mission(mission_id))
        assert result.status == MissionStatus.FAILED.value
        assert "timed out" in result.error.lower()
