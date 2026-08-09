import asyncio
import pytest

from app.agents import CreatorAgent, DecisionAgent, PlannerAgent, ResearchAgent, ReviewerAgent
from app.schemas.mission import MissionInitializeRequest
from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine
from app.services.mission_state_manager import MissionStateManager


def test_reviewer_agent_pass_and_fail(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Quality Review Mission",
        objective="Verify review pipeline scoring",
    )))
    mission_id = res.mission_id

    planner = PlannerAgent(db_session, event_bus, memory_engine)
    researcher = ResearchAgent(db_session, event_bus, memory_engine)
    decision_maker = DecisionAgent(db_session, event_bus, memory_engine)
    creator = CreatorAgent(db_session, event_bus, memory_engine)
    reviewer = ReviewerAgent(db_session, event_bus, memory_engine)

    asyncio.run(planner.run(mission_id))
    asyncio.run(researcher.run(mission_id))
    asyncio.run(decision_maker.run(mission_id))
    asyncio.run(creator.run(mission_id))

    # Standard review pass
    review_res = asyncio.run(reviewer.run(mission_id))
    assert review_res["passed"] is True
    assert review_res["score"] >= 0.8

    # Forced failure review test
    review_fail_res = asyncio.run(reviewer.run(mission_id, force_fail=True))
    assert review_fail_res["passed"] is False
    assert review_fail_res["score"] < 0.5
