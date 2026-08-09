import asyncio
import pytest

from app.agents import DecisionAgent, PlannerAgent, ResearchAgent
from app.schemas.mission import MissionInitializeRequest
from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine
from app.services.mission_state_manager import MissionStateManager


def test_decision_agent_execution(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Decision Making",
        objective="Evaluate and pick best execution option",
    )))
    mission_id = res.mission_id

    planner = PlannerAgent(db_session, event_bus, memory_engine)
    researcher = ResearchAgent(db_session, event_bus, memory_engine)
    decision_maker = DecisionAgent(db_session, event_bus, memory_engine)

    asyncio.run(planner.run(mission_id))
    asyncio.run(researcher.run(mission_id))

    decision_res = asyncio.run(decision_maker.run(mission_id))

    assert decision_res["mission_id"] == mission_id
    assert decision_res["selected_option_id"] is not None
    assert decision_res["score"] > 0

    strategy_ctx = memory_engine.get_short_term_context(mission_id, "selected_strategy")
    assert strategy_ctx is not None
    assert strategy_ctx["option_id"] == decision_res["selected_option_id"]
