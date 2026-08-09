import asyncio
import pytest

from app.schemas.mission import MissionInitializeRequest
from app.schemas.reflection import MissionReflectionReport
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine
from app.services.mission_state_manager import MissionStateManager
from app.services.reflection_engine import ReflectionEngine


def test_reflection_engine_7_questions_and_metrics(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    engine = ReflectionEngine(db_session, memory_engine, event_bus)

    mission_id = "mission-reflection-spec-1"
    stage_results = {
        "Planning": {"milestones_count": 2},
        "Researching": {"research_brief": {"confidence_level": 0.95}},
        "Decision": {"selected_title": "Strategy A: Comprehensive Synthesis", "confidence": 0.96},
        "Creation": {"title": "Deliverable Asset"},
        "Review": {"passed": True, "score": 0.92, "recommendations": "Minor polishing"},
    }
    review_result = stage_results["Review"]

    report = asyncio.run(engine.analyze_and_reflect(
        mission_id=mission_id,
        stage_results=stage_results,
        review_result=review_result,
        revision_count=1,
    ))

    assert isinstance(report, MissionReflectionReport)
    assert report.mission_id == mission_id

    # 1. What worked well?
    assert len(report.what_worked_well) >= 2
    # 2. What failed?
    assert len(report.what_failed) >= 1
    # 3. Why?
    assert len(report.why_failed) >= 1
    # 4. Which strategy performed best?
    assert "Strategy A" in report.best_performing_strategy
    # 5. Which strategy should never be used again?
    assert len(report.deprecated_strategies) >= 1
    # 6. What should be remembered?
    assert len(report.key_takeaways) >= 2
    # 7. How confident was the decision?
    assert 0.0 <= report.decision_confidence <= 1.0

    # Outputs
    assert len(report.lessons_learned) >= 2
    assert len(report.improvement_suggestions) >= 2
    assert 0.0 <= report.performance_score <= 1.0

    # Verify retrieval from Memory Engine
    retrieved = engine.get_mission_reflection(mission_id)
    assert retrieved is not None
    assert retrieved.mission_id == mission_id
    assert retrieved.performance_score == report.performance_score


def test_api_reflection_endpoint(client, db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="API Reflection Test",
        objective="Verify GET /api/v1/agent/reflection endpoint",
    )))
    mission_id = res.mission_id

    orchestrator = AgentOrchestrator(
        db=db_session,
        event_bus=event_bus,
        state_manager=state_manager,
        memory_engine=memory_engine,
    )
    asyncio.run(orchestrator.execute_mission(mission_id))

    response = client.get(f"/api/v1/agent/reflection?mission_id={mission_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["mission_id"] == mission_id
    assert "what_worked_well" in data
    assert "what_failed" in data
    assert "why_failed" in data
    assert "best_performing_strategy" in data
    assert "deprecated_strategies" in data
    assert "key_takeaways" in data
    assert "decision_confidence" in data
    assert "lessons_learned" in data
    assert "improvement_suggestions" in data
    assert "performance_score" in data


def test_api_reflection_not_found(client):
    response = client.get("/api/v1/agent/reflection?mission_id=nonexistent-mission")
    assert response.status_code == 404
