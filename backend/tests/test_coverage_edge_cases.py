import asyncio
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.core.exceptions import AppException, NotFoundError
from app.db.repositories import (
    ActivityFeedRepository,
    MemoryRepository,
    MilestoneRepository,
    MissionRepository,
    OutputRepository,
    ReviewRepository,
    StrategyRepository,
    TaskRepository,
)
from app.schemas.mission import Mission, MissionInitializeRequest, MissionPriority, MissionStatus
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine
from app.services.mission_engine import MissionEngine, MissionEngineDependencies
from app.services.mission_state_manager import MissionStateManager
from app.api.v1.endpoints.agent import run_orchestrated_mission


def test_agent_orchestrator_revision_loop_and_failure_path(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Revision Mission",
        objective="Test orchestrator self-correction revision loop",
    )))
    mission_id = res.mission_id

    orchestrator = AgentOrchestrator(
        db=db_session,
        event_bus=event_bus,
        state_manager=state_manager,
        memory_engine=memory_engine,
    )

    # Patch reviewer.run to fail on first attempt, then pass on second
    attempt_count = 0
    original_reviewer_run = orchestrator.reviewer.run

    async def mock_reviewer_run(m_id, **kwargs):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count == 1:
            return {
                "mission_id": m_id,
                "passed": False,
                "score": 0.4,
                "recommendations": "Needs revision on depth",
            }
        return await original_reviewer_run(m_id, **kwargs)

    with patch.object(orchestrator.reviewer, "run", side_effect=mock_reviewer_run):
        result = asyncio.run(orchestrator.execute_mission(mission_id))
        assert result.status == MissionStatus.COMPLETED.value
        assert attempt_count == 2


def test_agent_orchestrator_max_revisions_exceeded(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Failing Revision Mission",
        objective="Test orchestrator failing after max revisions",
    )))
    mission_id = res.mission_id

    orchestrator = AgentOrchestrator(
        db=db_session,
        event_bus=event_bus,
        state_manager=state_manager,
        memory_engine=memory_engine,
    )

    async def mock_reviewer_always_fail(m_id, **kwargs):
        return {
            "mission_id": m_id,
            "passed": False,
            "score": 0.3,
            "recommendations": "Persistent failure",
        }

    with patch.object(orchestrator.reviewer, "run", side_effect=mock_reviewer_always_fail):
        result = asyncio.run(orchestrator.execute_mission(mission_id))
        assert result.status == MissionStatus.FAILED.value


    mission = state_manager.get_mission(mission_id)
    assert mission.status == MissionStatus.FAILED.value


def test_agent_orchestrator_unhandled_exception(db_session):
    orchestrator = AgentOrchestrator(db=db_session)
    with pytest.raises(NotFoundError):
        asyncio.run(orchestrator.execute_mission("nonexistent-id"))


def test_mission_engine_all_methods(db_session):
    events = []
    engine = MissionEngine(dependencies=MissionEngineDependencies(event_publisher=lambda e: events.append(e)))

    # Initialize
    res = asyncio.run(engine.initialize_mission(MissionInitializeRequest(
        title="Engine Comprehensive Test",
        objective="Test all MissionEngine transition methods",
    )))

    mission = Mission(
        id=res.mission_id,
        title="Engine Test",
        objective="Obj",
        priority=MissionPriority.MEDIUM,
    )

    # Transition
    asyncio.run(engine.transition_state(mission, MissionStatus.PLANNING, "Moving to planning", retry_count=1))
    assert mission.status == MissionStatus.PLANNING

    # Execute lifecycle
    asyncio.run(engine.execute_mission(mission, [MissionStatus.RESEARCHING, MissionStatus.CREATING]))
    assert mission.status == MissionStatus.CREATING

    # Complete mission
    asyncio.run(engine.complete_mission(mission, "Finished"))
    assert mission.status == MissionStatus.COMPLETED

    # Terminal state transition protection
    asyncio.run(engine.transition_state(mission, MissionStatus.RESEARCHING, "Should ignore"))
    assert mission.status == MissionStatus.COMPLETED

    # Terminal state execute_mission break
    asyncio.run(engine.execute_mission(mission, [MissionStatus.PLANNING]))
    assert mission.status == MissionStatus.COMPLETED

    # Test cancel, retry, fail on fresh mission
    m2 = Mission(id="m2", title="M2", objective="Obj2", priority=MissionPriority.HIGH)

    asyncio.run(engine.retry_mission(m2, "Retry 1"))
    assert m2.retries == 1

    # Retry exceeding max retries
    m2.retries = 3
    asyncio.run(engine.retry_mission(m2, "Max retries exceeded"))
    assert m2.status == MissionStatus.FAILED

    # Cancel & Fail on terminal states
    asyncio.run(engine.retry_mission(m2, "Should ignore because failed"))
    asyncio.run(engine.cancel_mission(m2, "Should ignore because failed"))

    # Fail mission
    m3 = Mission(id="m3", title="M3", objective="Obj3", priority=MissionPriority.CRITICAL)
    asyncio.run(engine.fail_mission(m3, "Direct failure reason"))
    assert m3.status == MissionStatus.FAILED

    # Cancel mission
    m4 = Mission(id="m4", title="M4", objective="Obj4", priority=MissionPriority.LOW)
    asyncio.run(engine.cancel_mission(m4, "User cancelled"))
    assert m4.status == MissionStatus.CANCELLED
    asyncio.run(engine.cancel_mission(m4, "Second cancel ignored"))


def test_mission_state_manager_edge_cases(db_session):
    state_mgr = MissionStateManager(db_session)

    # NotFound errors
    with pytest.raises(NotFoundError):
        asyncio.run(state_mgr.transition_state("bad-id", MissionStatus.PLANNING, "msg"))

    with pytest.raises(NotFoundError):
        asyncio.run(state_mgr.fail_mission("bad-id", "reason"))

    with pytest.raises(NotFoundError):
        asyncio.run(state_mgr.retry_mission("bad-id", "reason"))

    # Terminal state transition protection in state_manager
    res = asyncio.run(state_mgr.initialize_mission(MissionInitializeRequest(title="Term", objective="Obj")))
    m_id = res.mission_id

    asyncio.run(state_mgr.transition_state(m_id, MissionStatus.COMPLETED, "Completed"))
    # Second transition on completed mission should return early
    asyncio.run(state_mgr.transition_state(m_id, MissionStatus.PLANNING, "Should ignore"))

    mission = state_mgr.get_mission(m_id)
    assert mission.status == MissionStatus.COMPLETED.value


def test_repositories_coverage(db_session):
    m_repo = MissionRepository(db_session)
    t_repo = TaskRepository(db_session)
    ms_repo = MilestoneRepository(db_session)
    s_repo = StrategyRepository(db_session)
    o_repo = OutputRepository(db_session)
    r_repo = ReviewRepository(db_session)
    mem_repo = MemoryRepository(db_session)

    # MissionRepo list and update edge cases
    m1 = m_repo.create({"title": "M1", "objective": "Obj1", "status": "PLANNING"})
    m2 = m_repo.create({"title": "M2", "objective": "Obj2", "status": "COMPLETED"})

    missions, count = m_repo.list_missions(status="PLANNING")
    assert count == 1
    assert missions[0].id == m1.id

    assert m_repo.update("non-existent", {"title": "X"}) is None

    # TaskRepo edge cases
    t1 = t_repo.create_task({"mission_id": m1.id, "title": "T1"})
    assert t_repo.get_by_id(t1.id) is not None
    assert len(t_repo.get_by_mission(m1.id)) == 1
    assert t_repo.update("non-existent", {"title": "X"}) is None

    # MilestoneRepo
    ms1 = ms_repo.create({"mission_id": m1.id, "title": "MS1", "sequence_number": 1})
    assert len(ms_repo.get_by_mission(m1.id)) == 1

    # StrategyRepo
    strat = s_repo.create_strategy({"mission_id": m1.id, "name": "S1"})
    opt = s_repo.add_option({"strategy_id": strat.id, "title": "Opt1"})
    assert len(s_repo.get_by_mission(m1.id)) == 1

    # OutputRepo edge cases
    out = o_repo.create({"mission_id": m1.id, "title": "Out1"})
    assert len(o_repo.get_by_mission(m1.id)) == 1
    assert o_repo.update(out.id, {"title": "Out1 Updated"}).title == "Out1 Updated"
    assert o_repo.update("non-existent", {"title": "X"}) is None

    # ReviewRepo
    rev = r_repo.create({"mission_id": m1.id, "review_type": "qa", "passed": True})
    assert len(r_repo.get_by_mission(m1.id)) == 1

    # MemoryRepo search filter
    mem = mem_repo.store_memory(summary="Unique Summary", insight="Unique Insight", memory_type="insight")
    results = mem_repo.search_memories(query_text="Unique", memory_type="insight")
    assert len(results) >= 1


def test_run_orchestrated_mission_background_task(db_session):
    state_mgr = MissionStateManager(db_session)
    res = asyncio.run(state_mgr.initialize_mission(MissionInitializeRequest(title="Bg Mission", objective="Bg Obj")))
    asyncio.run(run_orchestrated_mission(res.mission_id))
    m = state_mgr.get_mission(res.mission_id)
    assert m.status == MissionStatus.COMPLETED.value


def test_api_readiness_failure(client):
    with patch("app.api.v1.endpoints.health.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("DB Connection Lost")
        mock_session_local.return_value = mock_db

        res = client.get("/api/v1/health/ready")
        assert res.status_code == 503
        assert "Database readiness check failed" in res.json()["detail"]


def test_custom_exception_handlers(client):
    from app.main import app
    from app.core.exceptions import AppException

    @app.get("/test-custom-app-exception")
    def raise_custom_app_exception():
        raise AppException("Custom App Level Exception")

    res = client.get("/test-custom-app-exception")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "APP_ERROR"
    assert res.json()["error"]["message"] == "Custom App Level Exception"

    @app.get("/test-unhandled-exception")
    def raise_unhandled_exception():
        raise RuntimeError("Something went wrong internally")

    # Pass raise_server_exceptions=False so test client doesn't re-raise unhandled server errors
    custom_client = TestClient(app, raise_server_exceptions=False)
    res_unhandled = custom_client.get("/test-unhandled-exception")
    assert res_unhandled.status_code == 500
    assert res_unhandled.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
