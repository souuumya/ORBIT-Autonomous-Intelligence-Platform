import asyncio
import time
import pytest
from unittest.mock import patch

from app.schemas.events import EventType
from app.schemas.mission import MissionInitializeRequest, MissionStatus
from app.schemas.orchestrator import StageConfig, WorkflowConfig
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.event_bus import EventBus
from app.services.feed_engine import FeedGenerationEngine
from app.services.memory_engine import MemoryEngine
from app.services.mission_state_manager import MissionStateManager


def test_phase1_complete_mission_lifecycle_and_summary(db_session):
    """Test full Phase 1 autonomous mission execution and summary contents."""
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)
    feed_engine = FeedGenerationEngine(db_session, event_bus, auto_subscribe=True)

    recorded_events = []
    for et in EventType:
        event_bus.subscribe(et, lambda e: recorded_events.append(e.event_type))

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Phase 1 Autonomous Launch",
        objective="Run end-to-end multi-agent execution pipeline without user prompts",
    )))
    mission_id = res.mission_id

    orchestrator = AgentOrchestrator(
        db=db_session,
        event_bus=event_bus,
        state_manager=state_manager,
        memory_engine=memory_engine,
        feed_engine=feed_engine,
    )

    result = asyncio.run(orchestrator.execute_mission(mission_id))

    # 1. Mission Status & Progress
    assert result.mission_id == mission_id
    assert result.status == MissionStatus.COMPLETED.value
    assert result.progress_percentage == 100.0

    # 2. Event Ordering Verification
    event_names = [e.value for e in recorded_events]
    assert "MissionCreated" in event_names
    assert "MissionStateChanged" in event_names
    assert "PlannerStarted" in event_names
    assert "PlannerCompleted" in event_names
    assert "ResearchStarted" in event_names
    assert "ResearchCompleted" in event_names
    assert "DecisionStarted" in event_names
    assert "DecisionCompleted" in event_names
    assert "CreatorStarted" in event_names
    assert "CreatorCompleted" in event_names
    assert "ReviewerStarted" in event_names
    assert "ReviewerCompleted" in event_names
    assert "ReflectionCompleted" in event_names
    assert "MemoryUpdated" in event_names
    assert "MissionCompleted" in event_names

    # Assert sequence ordering for key milestones
    planner_idx = event_names.index("PlannerStarted")
    research_idx = event_names.index("ResearchStarted")
    decision_idx = event_names.index("DecisionStarted")
    creator_idx = event_names.index("CreatorStarted")
    reviewer_idx = event_names.index("ReviewerStarted")
    reflection_idx = event_names.index("ReflectionCompleted")
    completed_idx = event_names.index("MissionCompleted")

    assert planner_idx < research_idx < decision_idx < creator_idx < reviewer_idx < reflection_idx < completed_idx

    # 3. Completed Mission Summary Verification (Requirement 13 - All 11 elements)
    summary = state_manager.get_completed_mission_summary(mission_id)

    assert summary["mission_id"] == mission_id
    assert summary["original_objective"] == "Run end-to-end multi-agent execution pipeline without user prompts"
    assert summary["execution_status"] == MissionStatus.COMPLETED.value
    assert len(summary["milestones"]) >= 2
    assert len(summary["decisions"]) >= 1
    assert len(summary["rejected_alternatives"]) >= 1
    assert summary["created_output"] is not None
    assert summary["created_output"]["quality_score"] > 0
    assert summary["review_result"] is not None
    assert summary["review_result"]["passed"] is True
    assert summary["reflection"] is not None
    assert len(summary["lessons_learned"]) >= 1
    assert len(summary["timeline_events"]) >= 5


def test_phase1_agent_failure_and_rollback(db_session):
    """Test unrecoverable agent failure leads to graceful termination and rollback."""
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Unrecoverable Failure Mission",
        objective="Fail during Creator stage to verify graceful rollback",
    )))
    mission_id = res.mission_id

    orchestrator = AgentOrchestrator(
        db=db_session,
        event_bus=event_bus,
        state_manager=state_manager,
        memory_engine=memory_engine,
    )

    async def broken_creator(m_id, **kwargs):
        raise ValueError("Fatal rendering synthesis error")

    with patch.object(orchestrator.creator, "run", side_effect=broken_creator):
        result = asyncio.run(orchestrator.execute_mission(mission_id))

    assert result.status == MissionStatus.FAILED.value
    assert "Fatal rendering synthesis error" in result.error

    mission = state_manager.get_mission(mission_id)
    assert mission.status == MissionStatus.FAILED.value
    assert "Rollback triggered" in mission.last_error


def test_phase1_retry_recovery_handling(db_session):
    """Test retry handling recovers from transient agent exceptions."""
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Transient Flake Mission",
        objective="Recover from single-attempt network drop during Researching",
    )))
    mission_id = res.mission_id

    custom_workflow = WorkflowConfig(stages=[
        StageConfig(stage_name="Researching", agent_role="ResearchAgent", timeout_seconds=5.0, max_retries=2, backoff_seconds=0.01)
    ])

    orchestrator = AgentOrchestrator(
        db=db_session,
        event_bus=event_bus,
        state_manager=state_manager,
        memory_engine=memory_engine,
        workflow_config=custom_workflow,
    )

    attempts = 0
    original_research_run = orchestrator.researcher.run

    async def flaky_research_run(m_id, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("Transient connection refused")
        return await original_research_run(m_id, **kwargs)

    with patch.object(orchestrator.researcher, "run", side_effect=flaky_research_run):
        result = asyncio.run(orchestrator.execute_mission(mission_id))

    assert result.status == MissionStatus.COMPLETED.value
    assert attempts == 2


def test_phase1_async_api_initialization_flow(client, db_session):
    """Test POST /api/v1/agent/init triggers background mission execution autonomously."""
    payload = {
        "mission_title": "End-to-End Autonomous Pipeline",
        "mission_objective": "Validate background execution from initialization to completion",
        "mission_description": "Automatic execution trigger test",
        "priority": "high",
        "user_id": "test-user-1",
    }

    init_res = client.post("/api/v1/agent/init", json=payload)
    assert init_res.status_code == 200
    res_data = init_res.json()

    mission_id = res_data["mission_id"]
    assert res_data["status"] == "INITIALIZED"

    # Poll feed until completed (with timeout limit)
    start_time = time.time()
    completed = False

    while time.time() - start_time < 10.0:
        feed_res = client.get(f"/api/v1/agent/feed?mission_id={mission_id}")
        assert feed_res.status_code == 200
        feed_data = feed_res.json()

        stages = [e["current_stage"] for e in feed_data["entries"]]
        if "COMPLETED" in stages:
            completed = True
            break
        time.sleep(0.2)

    assert completed is True

    # Verify reflection endpoint
    ref_res = client.get(f"/api/v1/agent/reflection?mission_id={mission_id}")
    assert ref_res.status_code == 200
    ref_data = ref_res.json()
    assert ref_data["mission_id"] == mission_id
    assert ref_data["performance_score"] > 0
