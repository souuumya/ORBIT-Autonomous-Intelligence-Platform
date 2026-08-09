import asyncio
import pytest

from app.schemas.mission import MissionInitializeRequest, MissionStatus
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine
from app.services.mission_state_manager import MissionStateManager


def test_agent_orchestrator_end_to_end(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="Full Autonomous Campaign",
        objective="Execute complete multi-agent pipeline and generate deliverable",
        created_by="lead_engineer",
    )))
    mission_id = res.mission_id

    orchestrator = AgentOrchestrator(
        db=db_session,
        event_bus=event_bus,
        state_manager=state_manager,
        memory_engine=memory_engine,
    )

    execution_res = asyncio.run(orchestrator.execute_mission(mission_id))

    assert execution_res.mission_id == mission_id
    assert execution_res.status == MissionStatus.COMPLETED.value
    assert execution_res.stage_results["Planning"]["milestones_count"] == 2
    assert execution_res.stage_results["Review"]["passed"] is True

    mission = state_manager.get_mission(mission_id)
    assert mission.status == MissionStatus.COMPLETED.value

    entries, total = state_manager.get_activity_feed(mission_id)
    assert total >= 5
