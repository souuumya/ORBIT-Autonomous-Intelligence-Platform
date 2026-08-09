from __future__ import annotations

from typing import Any
from app.agents.base import BaseAgent
from app.core.exceptions import NotFoundError
from app.db.repositories import MilestoneRepository, MissionRepository, StrategyRepository, TaskRepository
from app.schemas.events import EventType


class PlannerAgent(BaseAgent):
    async def run(self, mission_id: str, **kwargs: Any) -> dict[str, Any]:
        self.log_info("Starting planning for mission %s", mission_id)
        await self.emit_event(EventType.PLANNER_STARTED, {"mission_id": mission_id})

        mission_repo = MissionRepository(self.db)
        mission = mission_repo.get_by_id(mission_id)
        if not mission:
            raise NotFoundError(f"Mission {mission_id} not found")

        # 1. Retrieve prior insights from memory if available
        prior_insights = []
        if self.memory_engine:
            prior_insights = self.memory_engine.retrieve_relevant_memories(
                query_text=mission.title,
                limit=3,
            )

        # 2. Decompose mission into structured milestones
        milestone_repo = MilestoneRepository(self.db)
        m1 = milestone_repo.create({
            "mission_id": mission_id,
            "title": "Phase 1: Research & Strategy Formulation",
            "description": f"Gather domain evidence and define options for '{mission.title}'",
            "sequence_number": 1,
            "status": "IN_PROGRESS",
        })

        m2 = milestone_repo.create({
            "mission_id": mission_id,
            "title": "Phase 2: Deliverable Generation & Quality Assurance",
            "description": f"Execute chosen strategy and perform quality review for '{mission.title}'",
            "sequence_number": 2,
            "status": "PENDING",
        })

        # 3. Create discrete tasks
        task_repo = TaskRepository(self.db)
        task_research = task_repo.create_task({
            "mission_id": mission_id,
            "milestone_id": m1.id,
            "title": f"Investigate audience and domain context for '{mission.title}'",
            "description": f"Gather research data relevant to: {mission.objective}",
            "task_type": "research",
            "status": "PENDING",
            "priority": mission.priority,
            "assigned_agent_role": "ResearchAgent",
        })

        task_create = task_repo.create_task({
            "mission_id": mission_id,
            "milestone_id": m2.id,
            "title": f"Produce core deliverable for '{mission.title}'",
            "description": f"Generate primary output artifact according to selected strategy",
            "task_type": "creation",
            "status": "PENDING",
            "priority": mission.priority,
            "assigned_agent_role": "CreatorAgent",
        })

        # 4. Generate candidate strategy options
        strategy_repo = StrategyRepository(self.db)
        strategy = strategy_repo.create_strategy({
            "mission_id": mission_id,
            "name": f"Execution Strategy Set for {mission.title}",
            "description": "Candidate strategies evaluated by DecisionAgent",
            "rationale": "Generated based on objective requirements and historical memory patterns",
            "status": "PROPOSED",
        })

        opt_agile = strategy_repo.add_option({
            "strategy_id": strategy.id,
            "task_id": task_create.id,
            "title": "Strategy A: Fast Agile Execution",
            "description": "Focus on high-speed synthesis and rapid prototyping of outputs.",
            "rationale": "High efficiency and immediate turn-around time.",
            "score": 0.85,
            "status": "CANDIDATE",
        })

        opt_comprehensive = strategy_repo.add_option({
            "strategy_id": strategy.id,
            "task_id": task_create.id,
            "title": "Strategy B: Deep Comprehensive Execution",
            "description": "Focus on extensive multi-angle contextual analysis and exhaustive elaboration.",
            "rationale": "Maximum depth and high quality assurance.",
            "score": 0.92,
            "status": "CANDIDATE",
        })

        # Save to short term memory context
        if self.memory_engine:
            self.memory_engine.set_short_term_context(mission_id, "milestones", [m1.id, m2.id])
            self.memory_engine.set_short_term_context(mission_id, "tasks", [task_research.id, task_create.id])
            self.memory_engine.set_short_term_context(mission_id, "strategy_id", strategy.id)
            self.memory_engine.set_short_term_context(mission_id, "strategy_options", [opt_agile.id, opt_comprehensive.id])

        result = {
            "mission_id": mission_id,
            "milestones_count": 2,
            "tasks_count": 2,
            "strategy_id": strategy.id,
            "strategy_options": [opt_agile.title, opt_comprehensive.title],
            "prior_insights_found": len(prior_insights),
        }

        await self.emit_event(EventType.PLANNER_COMPLETED, result)
        self.log_info("Completed planning for mission %s", mission_id)
        return result
