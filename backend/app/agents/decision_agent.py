from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.core.exceptions import NotFoundError
from app.db.repositories import MissionRepository, StrategyRepository
from app.schemas.events import EventType
from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine
from app.services.reasoning_engine import ReasoningEngine


class DecisionAgent(BaseAgent):
    """Decision Agent responsible for goal analysis, multi-candidate strategy evaluation,
    confidence calculation, and strategy selection.
    """

    def __init__(
        self,
        db: Session,
        event_bus: Optional[EventBus] = None,
        memory_engine: Optional[MemoryEngine] = None,
        reasoning_engine: Optional[ReasoningEngine] = None,
    ) -> None:
        super().__init__(db, event_bus, memory_engine)
        self.reasoning_engine = reasoning_engine or ReasoningEngine(db, event_bus)

    async def run(self, mission_id: str, **kwargs: Any) -> dict[str, Any]:
        """Evaluate mission options and pick optimal strategy using AI Reasoning Engine."""
        self.log_info("Starting strategy evaluation and reasoning for mission %s", mission_id)
        await self.emit_event(EventType.DECISION_STARTED, {"mission_id": mission_id})

        mission_repo = MissionRepository(self.db)
        mission = mission_repo.get_by_id(mission_id)
        if not mission:
            raise NotFoundError(f"Mission {mission_id} not found")

        # Fetch research brief if available in memory
        research_brief = {}
        if self.memory_engine:
            research_brief = self.memory_engine.get_short_term_context(mission_id, "research_brief") or {}

        # Run ReasoningEngine
        decision_record = await self.reasoning_engine.make_decision(
            mission_id=mission_id,
            title=mission.title,
            objective=mission.objective,
            context=mission.context_json,
            research_brief=research_brief,
        )

        # Sync database records with ReasoningEngine output
        strategy_repo = StrategyRepository(self.db)
        strategies = strategy_repo.get_by_mission(mission_id)
        if not strategies:
            strat = strategy_repo.create_strategy({
                "mission_id": mission_id,
                "name": f"Execution Strategy for {mission.title}",
                "description": decision_record.reason,
                "rationale": decision_record.reason,
                "status": "APPROVED",
            })
            strategy_repo.add_option({
                "strategy_id": strat.id,
                "title": decision_record.selected_strategy.title,
                "description": decision_record.selected_strategy.description,
                "rationale": decision_record.reason,
                "score": decision_record.selected_strategy.score,
                "status": "SELECTED",
            })
        else:
            active_strategy = strategies[0]
            active_strategy.status = "APPROVED"
            active_strategy.rationale = decision_record.reason
            active_strategy.selected_at = datetime.now(UTC)
            selected_title = decision_record.selected_strategy.title.lower()
            for opt in getattr(active_strategy, "options", []):
                if opt.title.lower() in selected_title or selected_title in opt.title.lower():
                    opt.status = "SELECTED"
                else:
                    opt.status = "REJECTED"
            self.db.commit()

        if self.memory_engine:
            self.memory_engine.set_short_term_context(mission_id, "reasoning_decision", decision_record.model_dump())
            self.memory_engine.set_short_term_context(mission_id, "selected_strategy", {
                "id": decision_record.selected_strategy.id,
                "option_id": decision_record.selected_strategy.id,
                "title": decision_record.selected_strategy.title,
                "score": decision_record.selected_strategy.score,
            })

        result = {
            "mission_id": mission_id,
            "reason": decision_record.reason,
            "confidence": decision_record.confidence,
            "alternatives": [c.model_dump() for c in decision_record.alternatives],
            "selected_strategy": decision_record.selected_strategy.model_dump(),
            "rejected_strategies": [r.model_dump() for r in decision_record.rejected_strategies],
            "selected_option_id": decision_record.selected_strategy.id,
            "selected_title": decision_record.selected_strategy.title,
            "score": decision_record.selected_strategy.score,
        }

        await self.emit_event(EventType.STRATEGY_SELECTED, result)
        await self.emit_event(EventType.DECISION_COMPLETED, result)
        self.log_info("Completed decision agent reasoning for mission %s (Confidence: %.2f)", mission_id, decision_record.confidence)
        return result
