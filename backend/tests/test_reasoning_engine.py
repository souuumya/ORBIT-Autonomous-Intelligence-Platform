import asyncio
import pytest

from app.agents import DecisionAgent, PlannerAgent, ResearchAgent
from app.schemas.mission import MissionInitializeRequest
from app.schemas.reasoning import DecisionRecord, GoalAnalysis
from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine
from app.services.mission_state_manager import MissionStateManager
from app.services.reasoning_engine import ReasoningEngine


def test_goal_analysis_and_strategy_generation(db_session):
    engine = ReasoningEngine(db_session)
    analysis = engine.analyze_goal("Build autonomous reasoning engine", {"priority": "high"})

    assert isinstance(analysis, GoalAnalysis)
    assert analysis.objective == "Build autonomous reasoning engine"
    assert len(analysis.target_outcomes) >= 3
    assert len(analysis.feasibility_factors) >= 3

    candidates = engine.generate_candidate_strategies("AI Reasoning", analysis.objective, analysis)
    assert len(candidates) >= 2
    assert candidates[0].score > 0
    assert candidates[0].relevance_score > 0

    confidence = engine.calculate_confidence(candidates)
    assert 0.0 <= confidence <= 1.0


def test_make_decision_structure(db_session):
    event_bus = EventBus()
    engine = ReasoningEngine(db_session, event_bus)

    mission_id = "mission-reasoning-1"
    decision = asyncio.run(engine.make_decision(
        mission_id=mission_id,
        title="Reasoning Engine Mission",
        objective="Verify decision payload requirements",
    ))

    assert isinstance(decision, DecisionRecord)
    assert decision.reason is not None and len(decision.reason) > 0
    assert 0.0 <= decision.confidence <= 1.0
    assert len(decision.alternatives) >= 2
    assert decision.selected_strategy is not None
    assert len(decision.rejected_strategies) >= 1

    # Verify decision payload keys match required contract
    payload = decision.model_dump()
    assert "reason" in payload
    assert "confidence" in payload
    assert "alternatives" in payload
    assert "selected_strategy" in payload
    assert "rejected_strategies" in payload
    assert "reflection" in payload


def test_reflection_and_replay(db_session):
    event_bus = EventBus()
    engine = ReasoningEngine(db_session, event_bus)

    mission_id = "mission-replay-100"
    decision = asyncio.run(engine.make_decision(
        mission_id=mission_id,
        title="Replay Test",
        objective="Test decision persistence and replay",
    ))

    # Initial decision before reflection has reflection as None
    assert decision.reflection is None

    # Generate reflection
    reflected = asyncio.run(engine.generate_reflection(
        mission_id=mission_id,
        decision_record=decision,
        execution_outcome={"status": "success"},
        review_result={"passed": True, "score": 0.96},
    ))

    assert reflected.reflection is not None
    assert "Post-execution reflection" in reflected.reflection
    assert "0.96" in reflected.reflection

    # Replay decision from database
    replayed = engine.replay_decision(mission_id)
    assert replayed is not None
    assert replayed.selected_strategy.title == decision.selected_strategy.title
    assert replayed.reflection == reflected.reflection


def test_decision_agent_integration(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Reasoning Integration",
        objective="Test DecisionAgent integration with ReasoningEngine",
    )))
    mission_id = res.mission_id

    planner = PlannerAgent(db_session, event_bus, memory_engine)
    researcher = ResearchAgent(db_session, event_bus, memory_engine)
    decision_agent = DecisionAgent(db_session, event_bus, memory_engine)

    asyncio.run(planner.run(mission_id))
    asyncio.run(researcher.run(mission_id))

    decision_res = asyncio.run(decision_agent.run(mission_id))

    assert "reason" in decision_res
    assert "confidence" in decision_res
    assert "alternatives" in decision_res
    assert "selected_strategy" in decision_res
    assert "rejected_strategies" in decision_res
    assert decision_res["confidence"] > 0
