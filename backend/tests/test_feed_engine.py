import asyncio
import pytest

from app.schemas.feed import FeedEntry, FeedResponse
from app.schemas.mission import MissionInitializeRequest
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.event_bus import EventBus
from app.services.feed_engine import FeedGenerationEngine
from app.services.memory_engine import MemoryEngine
from app.services.mission_state_manager import MissionStateManager


def test_feed_generation_engine_all_9_fields(db_session):
    event_bus = EventBus()
    feed_engine = FeedGenerationEngine(db_session, event_bus)

    mission_id = "mission-feed-spec-1"
    entry = asyncio.run(feed_engine.generate_entry(
        mission_id=mission_id,
        current_stage="Researching",
        agent_responsible="ResearchAgent",
        progress_percentage=20.0,
        summary_of_work="Gathered domain evidence and competitor context brief.",
        decision_made="Compiled 3 key insights with high confidence.",
        confidence=0.95,
        reflection="Audience demand and compliance factors validated.",
    ))

    assert isinstance(entry, FeedEntry)
    assert entry.mission_id == mission_id
    assert entry.current_stage == "Researching"
    assert entry.timestamp is not None
    assert entry.agent_responsible == "ResearchAgent"
    assert entry.progress_percentage == 20.0
    assert entry.summary_of_work == "Gathered domain evidence and competitor context brief."
    assert entry.decision_made == "Compiled 3 key insights with high confidence."
    assert entry.confidence == 0.95
    assert entry.reflection == "Audience demand and compliance factors validated."

    # Retrieve feed and verify 9 fields
    feed_res = asyncio.run(feed_engine.get_mission_feed(mission_id))
    assert isinstance(feed_res, FeedResponse)
    assert feed_res.total_count == 1
    retrieved = feed_res.entries[0]

    assert retrieved.current_stage == "Researching"
    assert retrieved.agent_responsible == "ResearchAgent"
    assert retrieved.progress_percentage == 20.0
    assert retrieved.summary_of_work == "Gathered domain evidence and competitor context brief."
    assert retrieved.decision_made == "Compiled 3 key insights with high confidence."
    assert retrieved.confidence == 0.95
    assert retrieved.reflection == "Audience demand and compliance factors validated."


def test_feed_pagination_ordering_and_filtering(db_session):
    feed_engine = FeedGenerationEngine(db_session)
    m1 = "mission-filter-1"
    m2 = "mission-filter-2"

    for i in range(5):
        asyncio.run(feed_engine.generate_entry(
            mission_id=m1,
            current_stage=f"Stage-{i}",
            agent_responsible="TestAgent",
            progress_percentage=float(i * 20),
            summary_of_work=f"Work summary step {i}",
            decision_made=f"Decision {i}",
            confidence=0.9,
        ))

    asyncio.run(feed_engine.generate_entry(
        mission_id=m2,
        current_stage="Stage-M2",
        agent_responsible="TestAgent",
        progress_percentage=10.0,
        summary_of_work="M2 work",
        decision_made="M2 decision",
    ))

    # Test filtering by mission m1
    feed_m1 = asyncio.run(feed_engine.get_mission_feed(m1, limit=50, offset=0, use_cache=False))
    assert feed_m1.total_count == 5
    assert all(e.mission_id == m1 for e in feed_m1.entries)

    # Test chronological ascending order
    for i in range(len(feed_m1.entries) - 1):
        assert feed_m1.entries[i].timestamp <= feed_m1.entries[i + 1].timestamp
        assert feed_m1.entries[i].progress_percentage <= feed_m1.entries[i + 1].progress_percentage

    # Test pagination (limit 2, offset 1)
    page_feed = asyncio.run(feed_engine.get_mission_feed(m1, limit=2, offset=1, use_cache=False))
    assert len(page_feed.entries) == 2
    assert page_feed.total_count == 5
    assert page_feed.entries[0].progress_percentage == 20.0
    assert page_feed.entries[1].progress_percentage == 40.0


def test_feed_caching_and_invalidation(db_session):
    feed_engine = FeedGenerationEngine(db_session)
    mission_id = "mission-cache-test"

    asyncio.run(feed_engine.generate_entry(
        mission_id=mission_id,
        current_stage="Planning",
        agent_responsible="PlannerAgent",
        progress_percentage=10.0,
        summary_of_work="Initial plan",
        decision_made="Plan approved",
    ))

    # Initial query populates cache
    res1 = asyncio.run(feed_engine.get_mission_feed(mission_id, use_cache=True))
    assert res1.total_count == 1

    # Verify cache key exists
    cache_key = f"{mission_id}:50:0:True"
    assert cache_key in FeedGenerationEngine._cache

    # Generating new entry invalidates mission cache
    asyncio.run(feed_engine.generate_entry(
        mission_id=mission_id,
        current_stage="Researching",
        agent_responsible="ResearchAgent",
        progress_percentage=30.0,
        summary_of_work="Research complete",
        decision_made="Insights compiled",
    ))

    assert cache_key not in FeedGenerationEngine._cache

    # Subsequent query returns updated feed
    res2 = asyncio.run(feed_engine.get_mission_feed(mission_id, use_cache=True))
    assert res2.total_count == 2


def test_api_feed_endpoint(client, db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)
    state_manager = MissionStateManager(db_session, event_bus)

    res = asyncio.run(state_manager.initialize_mission(MissionInitializeRequest(
        title="API Feed Integration",
        objective="Verify GET /api/v1/agent/feed endpoint output format",
    )))
    mission_id = res.mission_id

    orchestrator = AgentOrchestrator(
        db=db_session,
        event_bus=event_bus,
        state_manager=state_manager,
        memory_engine=memory_engine,
    )
    asyncio.run(orchestrator.execute_mission(mission_id))

    response = client.get(f"/api/v1/agent/feed?mission_id={mission_id}&limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()

    assert data["mission_id"] == mission_id
    assert data["total_count"] >= 5
    assert len(data["entries"]) >= 5

    first_entry = data["entries"][0]
    assert "mission_id" in first_entry
    assert "current_stage" in first_entry
    assert "timestamp" in first_entry
    assert "agent_responsible" in first_entry
    assert "progress_percentage" in first_entry
    assert "summary_of_work" in first_entry
    assert "decision_made" in first_entry
    assert "confidence" in first_entry
    assert "reflection" in first_entry
