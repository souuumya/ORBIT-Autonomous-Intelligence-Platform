import asyncio
import pytest

from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine


def test_memory_engine_short_and_long_term(db_session):
    event_bus = EventBus()
    memory_engine = MemoryEngine(db_session, event_bus)

    mission_id = "mission-mem-1"

    # Test short term context
    memory_engine.set_short_term_context(mission_id, "key1", "val1")
    assert memory_engine.get_short_term_context(mission_id, "key1") == "val1"
    assert memory_engine.get_all_short_term_context(mission_id) == {"key1": "val1"}

    memory_engine.clear_short_term_context(mission_id)
    assert memory_engine.get_short_term_context(mission_id, "key1") is None

    # Test long term memory persistence
    record = asyncio.run(memory_engine.store_long_term_memory(
        summary="Modular pattern success",
        insight="Modular agent design simplifies testability and isolation.",
        memory_type="lesson_learned",
        confidence_score=0.98,
        tags=["architecture", "testing"],
        mission_id=mission_id,
    ))

    assert record.id is not None
    assert record.summary == "Modular pattern success"

    retrieved = memory_engine.retrieve_relevant_memories(query_text="Modular")
    assert len(retrieved) >= 1
    assert retrieved[0].id == record.id
