from __future__ import annotations

from typing import Any
from app.agents.base import BaseAgent
from app.core.exceptions import NotFoundError
from app.db.repositories import MissionRepository
from app.schemas.events import EventType


class ResearchAgent(BaseAgent):
    async def run(self, mission_id: str, **kwargs: Any) -> dict[str, Any]:
        self.log_info("Starting research for mission %s", mission_id)
        await self.emit_event(EventType.RESEARCH_STARTED, {"mission_id": mission_id})

        mission_repo = MissionRepository(self.db)
        mission = mission_repo.get_by_id(mission_id)
        if not mission:
            raise NotFoundError(f"Mission {mission_id} not found")

        # Query prior memories from MemoryEngine for cross-mission experience retrieval
        prior_memories = []
        if self.memory_engine:
            prior_memories = self.memory_engine.retrieve_relevant_memories(limit=10)

        retrieved_experience = [
            m.summary for m in prior_memories if m.mission_id and m.mission_id != mission_id
        ]

        key_insights = [
            f"Audience demand favors clear, structured outcomes for {mission.title}.",
            f"Prior attempts highlight the importance of high quality assurance and modular design.",
            f"Recommended focus: Ensure clarity, scalability, and robust execution.",
        ]

        if retrieved_experience:
            key_insights.append(
                f"Retrieved prior mission experience ({len(retrieved_experience)} record(s)): '{retrieved_experience[0]}'"
            )

        # Synthesize domain research and context brief based on objective
        research_brief = {
            "target_domain": mission.title,
            "objective_analysis": f"Focusing on: {mission.objective}",
            "key_insights": key_insights,
            "retrieved_prior_experience": retrieved_experience,
            "confidence_level": 0.95,
        }

        if self.memory_engine:
            self.memory_engine.set_short_term_context(mission_id, "research_brief", research_brief)

            if retrieved_experience:
                await self.memory_engine.store_long_term_memory(
                    summary=f"Retrieved prior experience from {len(retrieved_experience)} previous mission(s)",
                    insight=f"Applied prior lesson to '{mission.title}': {retrieved_experience[0]}",
                    memory_type="experience_retrieval",
                    confidence_score=0.95,
                    tags=["experience_retrieval", mission_id],
                    mission_id=mission_id,
                )

        result = {
            "mission_id": mission_id,
            "research_brief": research_brief,
            "insights_count": len(key_insights),
            "retrieved_prior_experience_count": len(retrieved_experience),
        }


        await self.emit_event(EventType.RESEARCH_COMPLETED, result)
        self.log_info("Completed research for mission %s", mission_id)
        return result
