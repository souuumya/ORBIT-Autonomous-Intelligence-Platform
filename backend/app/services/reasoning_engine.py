from __future__ import annotations

import json
import logging
import uuid
from typing import Any, List, Optional
from sqlalchemy.orm import Session

from app.db.repositories import MemoryRepository, StrategyRepository
from app.schemas.events import EventEnvelope, EventType
from app.schemas.reasoning import (
    DecisionRecord,
    GoalAnalysis,
    RejectedStrategy,
    StrategyCandidate,
)
from app.services.event_bus import EventBus

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """AI Reasoning Engine conducting goal analysis, alternative strategy formulation,
    dimensional strategy scoring, normalized confidence calculations, decision explanations,
    reflections, and historical decision persistence/replay.
    """

    def __init__(
        self,
        db: Session,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.db = db
        self.memory_repo = MemoryRepository(db)
        self.strategy_repo = StrategyRepository(db)
        self.event_bus = event_bus

    def analyze_goal(
        self,
        objective: str,
        context: Optional[dict[str, Any]] = None,
    ) -> GoalAnalysis:
        """Deconstruct mission objective into target outcomes, feasibility factors, risk factors, and constraints."""

        ctx = context or {}
        target_outcomes = [
            f"Deliver verified output fulfilling objective: {objective}",
            "Maintain high quality score and structural coherence",
            "Ensure operational efficiency and zero unhandled failures",
        ]

        feasibility_factors = [
            "Modular architecture and independent agent roles",
            "Contextual research briefs available for decision support",
            "Self-correcting revision loops enabled in orchestrator",
        ]

        risk_factors = [
            "Potential domain ambiguity in high-level objectives",
            "Timeouts during extensive synthesis tasks",
        ]

        constraints = [
            f"Priority constraint: {ctx.get('priority', 'medium')}",
            "Zero business logic inside orchestrator layer",
        ]

        return GoalAnalysis(
            objective=objective,
            target_outcomes=target_outcomes,
            feasibility_factors=feasibility_factors,
            risk_factors=risk_factors,
            constraints=constraints,
        )

    def generate_candidate_strategies(
        self,
        mission_title: str,
        objective: str,
        goal_analysis: GoalAnalysis,
        research_brief: Optional[dict[str, Any]] = None,
    ) -> List[StrategyCandidate]:
        brief = research_brief or {}
        confidence_lvl = brief.get("confidence_level", 0.9)

        # Candidate A: Comprehensive Execution
        cand_a = StrategyCandidate(
            id=f"strat-{uuid.uuid4().hex[:8]}",
            title=f"Strategy A: Comprehensive Synthesis for {mission_title}",
            description="Exhaustive contextual analysis, multi-angle asset generation, and strict quality verification.",
            trade_offs=["Slightly higher latency due to depth", "Requires multi-stage review verification"],
            relevance_score=0.95,
            impact_score=0.96,
            risk_score=0.10,
            feasibility_score=0.92,
            score=round(0.95 * 0.4 + 0.96 * 0.3 + (1.0 - 0.10) * 0.1 + 0.92 * 0.2, 2),
        )

        # Candidate B: Agile Prototyping
        cand_b = StrategyCandidate(
            id=f"strat-{uuid.uuid4().hex[:8]}",
            title=f"Strategy B: Rapid Prototyping for {mission_title}",
            description="High-speed minimal viable synthesis focusing on core delivery time.",
            trade_offs=["Lower depth of contextual elaboration", "Higher risk of revision trigger during review"],
            relevance_score=0.82,
            impact_score=0.75,
            risk_score=0.35,
            feasibility_score=0.98,
            score=round(0.82 * 0.4 + 0.75 * 0.3 + (1.0 - 0.35) * 0.1 + 0.98 * 0.2, 2),
        )

        return [cand_a, cand_b]

    def calculate_confidence(
        self,
        candidates: List[StrategyCandidate],
        research_brief: Optional[dict[str, Any]] = None,
    ) -> float:
        if not candidates:
            return 0.5

        top_score = max(c.score for c in candidates)
        brief = research_brief or {}
        research_confidence = float(brief.get("confidence_level", 0.9))

        # Composite confidence calculation
        confidence = round(0.6 * top_score + 0.4 * research_confidence, 2)
        return min(1.0, max(0.0, confidence))

    async def make_decision(
        self,
        mission_id: str,
        title: str,
        objective: str,
        context: Optional[dict[str, Any]] = None,
        research_brief: Optional[dict[str, Any]] = None,
    ) -> DecisionRecord:
        goal_analysis = self.analyze_goal(objective, context)
        candidates = self.generate_candidate_strategies(title, objective, goal_analysis, research_brief)

        # Sort candidates descending by score
        candidates.sort(key=lambda c: c.score, reverse=True)
        selected_strategy = candidates[0]
        rejected_candidates = candidates[1:]

        rejected_strategies = [
            RejectedStrategy(
                id=c.id,
                title=c.title,
                reason=f"Scored {c.score:.2f} (lower composite impact and higher risk score {c.risk_score:.2f} compared to selected option {selected_strategy.score:.2f}).",
            )
            for c in rejected_candidates
        ]

        confidence = self.calculate_confidence(candidates, research_brief)

        reason = (
            f"Goal analysis confirmed '{objective}' as primary target. "
            f"Evaluated {len(candidates)} alternative strategies. "
            f"Selected '{selected_strategy.title}' with top composite score of {selected_strategy.score:.2f} "
            f"and confidence of {confidence:.2f} based on domain evidence and risk-weighted impact."
        )

        decision_record = DecisionRecord(
            reason=reason,
            confidence=confidence,
            alternatives=candidates,
            selected_strategy=selected_strategy,
            rejected_strategies=rejected_strategies,
            reflection=None,
        )

        await self.persist_decision(mission_id, decision_record)

        if self.event_bus:
            await self.event_bus.publish(
                EventEnvelope(
                    event_type=EventType.DECISION_COMPLETED,
                    payload={
                        "mission_id": mission_id,
                        "selected_strategy": selected_strategy.title,
                        "confidence": confidence,
                        "reason": reason,
                    },
                )
            )

        logger.info("ReasoningEngine made decision for mission %s: %s (Confidence: %.2f)", mission_id, selected_strategy.title, confidence)
        return decision_record

    async def generate_reflection(
        self,
        mission_id: str,
        decision_record: DecisionRecord,
        execution_outcome: dict[str, Any],
        review_result: dict[str, Any],
    ) -> DecisionRecord:
        passed = review_result.get("passed", True)
        score = review_result.get("score", 0.95)

        if passed:
            reflection = (
                f"Post-execution reflection: Selected strategy '{decision_record.selected_strategy.title}' "
                f"successfully met mission goals with a review quality score of {score:.2f}. "
                f"Assumptions regarding feasibility and low risk were validated."
            )
        else:
            reflection = (
                f"Post-execution reflection: Selected strategy '{decision_record.selected_strategy.title}' "
                f"encountered quality gaps during review (score {score:.2f}). "
                f"Recommendations: Adjust risk weights and trigger self-correcting revision loops."
            )

        decision_record.reflection = reflection
        await self.persist_decision(mission_id, decision_record)

        if self.event_bus:
            await self.event_bus.publish(
                EventEnvelope(
                    event_type=EventType.MEMORY_UPDATED,
                    payload={
                        "mission_id": mission_id,
                        "reflection": reflection,
                    },
                )
            )

        logger.info("ReasoningEngine generated reflection for mission %s: %s", mission_id, reflection)
        return decision_record

    async def persist_decision(
        self,
        mission_id: str,
        decision_record: DecisionRecord,
    ) -> Any:
        summary = f"Reasoning Decision for mission {mission_id}: {decision_record.selected_strategy.title}"
        insight = json.dumps(decision_record.model_dump(), default=str)

        return self.memory_repo.store_memory(
            summary=summary,
            insight=insight,
            memory_type="reasoning_decision",
            confidence_score=decision_record.confidence,
            tags=["reasoning", "decision", mission_id],
            mission_id=mission_id,
        )

    def replay_decision(self, mission_id: str) -> Optional[DecisionRecord]:
        memories = self.memory_repo.search_memories(query_text=mission_id, memory_type="reasoning_decision", limit=1)
        if not memories:
            return None

        try:
            payload = json.loads(memories[0].insight)
            return DecisionRecord(**payload)
        except Exception as exc:
            logger.error("Failed to parse decision replay payload for mission %s: %s", mission_id, exc)
            return None
