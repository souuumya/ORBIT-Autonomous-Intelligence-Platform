import asyncio
import pytest

from app.agents import ResearchAgent
from app.schemas.mission import MissionInitializeRequest
from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine
from app.services.mission_state_manager import MissionStateManager


def test_research_agent_execution(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Market Analysis",
        objective="Analyze competitive landscape",
    )))
    mission_id = res.mission_id

    researcher = ResearchAgent(db_session, event_bus, memory_engine)
    res_data = asyncio.run(researcher.run(mission_id))

    assert res_data["mission_id"] == mission_id
    assert res_data["insights_count"] > 0

    brief = memory_engine.get_short_term_context(mission_id, "research_brief")
    assert brief is not None
    assert brief["target_domain"] == "Market Analysis"
