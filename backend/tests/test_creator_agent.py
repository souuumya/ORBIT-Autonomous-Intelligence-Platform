import asyncio
import pytest

from app.agents import CreatorAgent, DecisionAgent, PlannerAgent, ResearchAgent
from app.schemas.mission import MissionInitializeRequest
from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine
from app.services.mission_state_manager import MissionStateManager


def test_creator_agent_execution(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Deliverable Generation",
        objective="Produce primary marketing brief deliverable",
    )))
    mission_id = res.mission_id

    planner = PlannerAgent(db_session, event_bus, memory_engine)
    researcher = ResearchAgent(db_session, event_bus, memory_engine)
    decision_maker = DecisionAgent(db_session, event_bus, memory_engine)
    creator = CreatorAgent(db_session, event_bus, memory_engine)

    asyncio.run(planner.run(mission_id))
    asyncio.run(researcher.run(mission_id))
    asyncio.run(decision_maker.run(mission_id))

    creator_res = asyncio.run(creator.run(mission_id))

    assert creator_res["mission_id"] == mission_id
    assert creator_res["output_id"] is not None
    assert creator_res["status"] == "DRAFT"
    assert "Deliverable Generation" in creator_res["title"]
