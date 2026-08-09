from __future__ import annotations

import logging
from typing import Any, List, Optional
from sqlalchemy.orm import Session

from app.db.repositories import DecisionReplayRepository
from app.schemas.reasoning import DecisionRecord
from app.schemas.replay import MissionReplayTimeline, ReplayStep

logger = logging.getLogger(__name__)


class DecisionReplayService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.replay_repo = DecisionReplayRepository(db)

    def record_mission_started(
        self,
        mission_id: str,
        title: str,
        objective: str,
    ) -> Any:
        return self.replay_repo.record_step(
            mission_id=mission_id,
            agent="System",
            action_type="MISSION_STARTED",
            reason=f"Mission initialized: '{title}'",
            confidence=1.0,
            duration_ms=0.0,
            output_summary=f"Objective: {objective}",
            metadata_json={"title": title, "objective": objective},
        )

    def record_planner_step(
        self,
        mission_id: str,
        plan_result: dict[str, Any],
        duration_ms: float,
    ) -> Any:
        m_count = plan_result.get("milestones_count", 0)
        t_count = plan_result.get("tasks_count", 0)
        return self.replay_repo.record_step(
            mission_id=mission_id,
            agent="PlannerAgent",
            action_type="PLANNER",
            reason=f"Planner decomposed mission into {m_count} milestones and {t_count} tasks.",
            confidence=0.95,
            duration_ms=duration_ms,
            output_summary=f"Created {m_count} milestones, {t_count} tasks.",
            metadata_json=plan_result,
        )

    def record_research_step(
        self,
        mission_id: str,
        research_result: dict[str, Any],
        duration_ms: float,
    ) -> Any:
        brief = research_result.get("research_brief", {})
        insights = brief.get("key_insights", [])
        return self.replay_repo.record_step(
            mission_id=mission_id,
            agent="ResearchAgent",
            action_type="RESEARCH",
            reason=f"ResearchAgent gathered {len(insights)} key domain evidence insights.",
            confidence=float(brief.get("confidence_level", 0.95)),
            duration_ms=duration_ms,
            output_summary=f"Compiled domain context brief with confidence {brief.get('confidence_level', 0.95)}.",
            metadata_json=research_result,
        )

    def record_decision_breakdown(
        self,
        mission_id: str,
        decision_result: dict[str, Any],
        duration_ms: float,
    ) -> List[Any]:
        recorded_steps = []

        confidence = float(decision_result.get("confidence", 0.95))
        reason = decision_result.get("reason", "Strategy reasoning complete.")

        # 1. Main Decision step
        step_dec = self.replay_repo.record_step(
            mission_id=mission_id,
            agent="DecisionAgent",
            action_type="DECISION",
            reason=reason,
            confidence=confidence,
            duration_ms=duration_ms,
            output_summary=f"Strategy evaluation completed with confidence {confidence:.2f}.",
            metadata_json={
                "confidence": confidence,
                "reason": reason,
                "selected_strategy": decision_result.get("selected_strategy", {}),
                "rejected_strategies": decision_result.get("rejected_strategies", []),
                "alternatives": decision_result.get("alternatives", []),
            },
        )
        recorded_steps.append(step_dec)


        # 2. Record Rejected Strategies
        rejected_list = decision_result.get("rejected_strategies", [])
        for rej in rejected_list:
            step_rej = self.replay_repo.record_step(
                mission_id=mission_id,
                agent="DecisionAgent",
                action_type="REJECTED_STRATEGY",
                reason=rej.get("reason", "Option scored lower than selected strategy."),
                confidence=confidence,
                duration_ms=0.0,
                output_summary=f"Rejected '{rej.get('title')}'",
                metadata_json=rej if isinstance(rej, dict) else {},
            )
            recorded_steps.append(step_rej)

        # 3. Record Selected Strategy
        selected_info = decision_result.get("selected_strategy", {})
        selected_title = selected_info.get("title") if isinstance(selected_info, dict) else decision_result.get("selected_title", "Selected Strategy")
        step_sel = self.replay_repo.record_step(
            mission_id=mission_id,
            agent="DecisionAgent",
            action_type="SELECTED_STRATEGY",
            reason=f"Approved '{selected_title}' as primary strategy.",
            confidence=confidence,
            duration_ms=0.0,
            output_summary=f"Selected '{selected_title}' (Score: {decision_result.get('score', 1.0)})",
            metadata_json=selected_info if isinstance(selected_info, dict) else {"title": selected_title},
        )
        recorded_steps.append(step_sel)

        return recorded_steps

    def record_creator_step(
        self,
        mission_id: str,
        creator_result: dict[str, Any],
        duration_ms: float,
    ) -> Any:
        title = creator_result.get("title", "Generated Output")
        return self.replay_repo.record_step(
            mission_id=mission_id,
            agent="CreatorAgent",
            action_type="CREATOR",
            reason=f"CreatorAgent synthesized deliverable artifact: '{title}'",
            confidence=0.95,
            duration_ms=duration_ms,
            output_summary=f"Produced deliverable '{title}' (Status: {creator_result.get('status', 'DRAFT')}).",
            metadata_json=creator_result,
        )

    def record_reviewer_step(
        self,
        mission_id: str,
        reviewer_result: dict[str, Any],
        duration_ms: float,
    ) -> Any:
        passed = reviewer_result.get("passed", True)
        score = float(reviewer_result.get("score", 0.95))
        return self.replay_repo.record_step(
            mission_id=mission_id,
            agent="ReviewerAgent",
            action_type="REVIEWER",
            reason=f"ReviewerAgent quality check {'passed' if passed else 'failed'}: {reviewer_result.get('recommendations', '')}",
            confidence=score,
            duration_ms=duration_ms,
            output_summary=f"Review {'VERIFIED' if passed else 'REJECTED'} (Quality Score: {score:.2f}).",
            metadata_json=reviewer_result,
        )

    def record_memory_update_step(
        self,
        mission_id: str,
        memory_summary: str,
        duration_ms: float = 0.0,
    ) -> Any:
        return self.replay_repo.record_step(
            mission_id=mission_id,
            agent="MemoryEngine",
            action_type="MEMORY_UPDATE",
            reason=f"MemoryEngine stored long-term lessons learned.",
            confidence=1.0,
            duration_ms=duration_ms,
            output_summary=memory_summary,
            metadata_json={"memory_summary": memory_summary},
        )

    def record_mission_completed(
        self,
        mission_id: str,
        duration_ms: float = 0.0,
    ) -> Any:
        return self.replay_repo.record_step(
            mission_id=mission_id,
            agent="System",
            action_type="MISSION_COMPLETE",
            reason="Autonomous mission execution completed successfully.",
            confidence=1.0,
            duration_ms=duration_ms,
            output_summary="Mission execution finished.",
            metadata_json={},
        )

    def get_timeline(self, mission_id: str) -> MissionReplayTimeline:
        db_steps = self.replay_repo.get_timeline(mission_id)
        replay_steps = [
            ReplayStep(
                id=s.id,
                mission_id=s.mission_id,
                step_number=s.step_number,
                timestamp=s.timestamp,
                agent=s.agent,
                action_type=s.action_type,
                reason=s.reason,
                confidence=s.confidence,
                duration_ms=s.duration_ms,
                output_summary=s.output_summary,
                metadata=s.metadata_json or {},
            )
            for s in db_steps
        ]

        return MissionReplayTimeline(
            mission_id=mission_id,
            total_steps=len(replay_steps),
            steps=replay_steps,
        )
