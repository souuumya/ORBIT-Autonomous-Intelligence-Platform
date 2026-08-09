from __future__ import annotations

from typing import Any
from app.agents.base import BaseAgent
from app.core.exceptions import NotFoundError
from app.db.repositories import MissionRepository, OutputRepository, TaskRepository
from app.schemas.events import EventType


class CreatorAgent(BaseAgent):
    async def run(self, mission_id: str, **kwargs: Any) -> dict[str, Any]:
        self.log_info("Starting deliverable creation for mission %s", mission_id)
        await self.emit_event(EventType.CREATOR_STARTED, {"mission_id": mission_id})

        mission_repo = MissionRepository(self.db)
        mission = mission_repo.get_by_id(mission_id)
        if not mission:
            raise NotFoundError(f"Mission {mission_id} not found")

        # Context from memory
        selected_strategy = {}
        research_brief = {}
        if self.memory_engine:
            selected_strategy = self.memory_engine.get_short_term_context(mission_id, "selected_strategy") or {}
            research_brief = self.memory_engine.get_short_term_context(mission_id, "research_brief") or {}

        task_repo = TaskRepository(self.db)
        tasks = task_repo.get_by_mission(mission_id)
        creation_task = next((t for t in tasks if t.task_type == "creation"), None)

        strategy_title = selected_strategy.get("title", "Standard Autonomous Execution")

        # Synthesize production-ready deliverable content
        deliverable_title = f"Autonomous Output: {mission.title}"
        summary = f"Comprehensive deliverable created for objective '{mission.objective}' using {strategy_title}."
        content_sections = [
            f"# Mission Deliverable: {mission.title}",
            f"**Objective**: {mission.objective}",
            f"**Execution Strategy**: {strategy_title}",
            "## Executive Summary",
            summary,
            "## Key Research Foundations",
        ]

        if research_brief.get("key_insights"):
            for insight in research_brief["key_insights"]:
                content_sections.append(f"- {insight}")
        else:
            content_sections.append("- Thorough domain alignment and standard compliance enforced.")

        content_sections.extend([
            "## Strategic Action Plan",
            "1. Deployment of modular backend capabilities.",
            "2. Validation of core workflow milestones and agent feedback loops.",
            "3. Autonomous delivery of verified platform outcomes.",
        ])

        full_content = "\n\n".join(content_sections)

        output_repo = OutputRepository(self.db)
        output = output_repo.create({
            "mission_id": mission_id,
            "task_id": creation_task.id if creation_task else None,
            "output_type": "primary_deliverable",
            "title": deliverable_title,
            "summary": summary,
            "content": full_content,
            "quality_score": 0.0,
            "status": "DRAFT",
        })

        if creation_task:
            task_repo.update(creation_task.id, {"status": "IN_PROGRESS"})

        if self.memory_engine:
            self.memory_engine.set_short_term_context(mission_id, "current_output_id", output.id)

        result = {
            "mission_id": mission_id,
            "output_id": output.id,
            "title": output.title,
            "summary": output.summary,
            "status": output.status,
        }

        await self.emit_event(EventType.OUTPUT_GENERATED, result)
        await self.emit_event(EventType.CREATOR_COMPLETED, result)
        self.log_info("Completed deliverable creation for mission %s (Output ID: %s)", mission_id, output.id)
        return result
