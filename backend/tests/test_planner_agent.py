import asyncio
import pytest

from app.agents import PlannerAgent
from app.schemas.mission import MissionInitializeRequest
from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine
from app.services.mission_state_manager import MissionStateManager


def test_planner_agent_execution(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Plan Launch Strategy",
        objective="Create milestones for product launch",
    )))
    mission_id = res.mission_id

    planner = PlannerAgent(db_session, event_bus, memory_engine)
    plan_result = asyncio.run(planner.run(mission_id))

    assert plan_result["mission_id"] == mission_id
    assert plan_result["milestones_count"] == 2
    assert plan_result["tasks_count"] == 2
    assert len(plan_result["strategy_options"]) == 2

    # Check memory context
    milestone_ids = memory_engine.get_short_term_context(mission_id, "milestones")
    assert milestone_ids is not None
    assert len(milestone_ids) == 2
