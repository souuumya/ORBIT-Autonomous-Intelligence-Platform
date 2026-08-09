from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.core.exceptions import MissionEngineError, NotFoundError, ValidationError
from app.db.repositories import ActivityFeedRepository, MissionRepository
from app.schemas.events import EventEnvelope, EventType
from app.schemas.mission import (
    MissionInitializeRequest,
    MissionInitializeResponse,
    MissionStatus,
)
from app.services.event_bus import EventBus

logger = logging.getLogger(__name__)


class MissionStateManager:
    def __init__(
        self,
        db: Session,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.db = db
        self.mission_repo = MissionRepository(db)
        self.feed_repo = ActivityFeedRepository(db)
        self.event_bus = event_bus

    async def initialize_mission(self, request: MissionInitializeRequest) -> MissionInitializeResponse:
        if not request.title or not request.title.strip():
            raise ValidationError("Mission title is required")
        if not request.objective or not request.objective.strip():
            raise ValidationError("Mission objective is required")

        from app.db.models import MissionModel
        existing = (
            self.db.query(MissionModel)
            .filter(
                MissionModel.title == request.title.strip(),
                MissionModel.objective == request.objective.strip(),
                MissionModel.status != MissionStatus.FAILED.value,
            )
            .order_by(MissionModel.created_at.desc())
            .first()
        )
        if existing:
            logger.info("Found existing mission %s for '%s'. Reusing worker.", existing.id, existing.title)
            res = MissionInitializeResponse(
                mission_id=existing.id,
                status=MissionStatus(existing.status),
                created_at=existing.created_at,
                message="Mission already active",
            )
            object.__setattr__(res, "_is_new", False)
            return res

        mission_model = self.mission_repo.create({
            "title": request.title.strip(),
            "objective": request.objective.strip(),
            "description": request.description.strip() if request.description else "",
            "priority": request.priority if isinstance(request.priority, str) else request.priority.value,
            "context_json": request.context or {},
            "created_by_user_id": request.created_by,
            "status": MissionStatus.INITIALIZED.value,
            "current_phase": MissionStatus.INITIALIZED.value,
            "started_at": datetime.now(UTC),
        })

        self.feed_repo.add_entry(
            mission_id=mission_model.id,
            event_type=EventType.MISSION_CREATED.value,
            message=f"Mission '{mission_model.title}' initialized successfully",
            metadata_json={"priority": mission_model.priority},
            user_id=request.created_by,
        )

        if self.event_bus:
            await self.event_bus.publish(
                EventEnvelope(
                    event_type=EventType.MISSION_CREATED,
                    payload={
                        "mission_id": mission_model.id,
                        "title": mission_model.title,
                        "objective": mission_model.objective,
                        "status": mission_model.status,
                    },
                )
            )

        logger.info("Initialized mission %s: %s", mission_model.id, mission_model.title)

        res = MissionInitializeResponse(
            mission_id=mission_model.id,
            status=MissionStatus(mission_model.status),
            created_at=mission_model.created_at,
            message="Mission initialized successfully",
        )
        object.__setattr__(res, "_is_new", True)
        return res

    async def transition_state(
        self,
        mission_id: str,
        new_state: MissionStatus,
        message: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        mission = self.mission_repo.get_by_id(mission_id)
        if not mission:
            raise NotFoundError(f"Mission {mission_id} not found")

        terminal_states = {MissionStatus.COMPLETED.value, MissionStatus.CANCELLED.value, MissionStatus.FAILED.value}
        if mission.status in terminal_states:
            logger.warning("Attempted state transition on terminal mission %s (status=%s)", mission_id, mission.status)
            return

        previous_state = mission.status
        updates: dict[str, Any] = {
            "status": new_state.value,
            "current_phase": new_state.value,
        }

        if new_state == MissionStatus.COMPLETED:
            updates["completed_at"] = datetime.now(UTC)

        self.mission_repo.update(mission_id, updates)

        feed_meta = {
            "from_state": previous_state,
            "to_state": new_state.value,
            "current_stage": new_state.value,
            "agent_responsible": "System",
        }
        if metadata:
            feed_meta.update(metadata)

        self.feed_repo.add_entry(
            mission_id=mission_id,
            event_type=EventType.MISSION_STATE_CHANGED.value,
            message=message,
            metadata_json=feed_meta,
        )

        if self.event_bus:
            event_type = EventType.MISSION_STATE_CHANGED
            if new_state == MissionStatus.COMPLETED:
                event_type = EventType.MISSION_COMPLETED
            elif new_state == MissionStatus.FAILED:
                event_type = EventType.MISSION_FAILED

            await self.event_bus.publish(
                EventEnvelope(
                    event_type=event_type,
                    payload={
                        "mission_id": mission_id,
                        "previous_state": previous_state,
                        "current_state": new_state.value,
                        "message": message,
                        "metadata": metadata or {},
                    },
                )
            )

        logger.info("Mission %s state transitioned from %s -> %s: %s", mission_id, previous_state, new_state.value, message)

    async def fail_mission(self, mission_id: str, reason: str) -> None:
        mission = self.mission_repo.get_by_id(mission_id)
        if not mission:
            raise NotFoundError(f"Mission {mission_id} not found")

        self.mission_repo.update(mission_id, {
            "status": MissionStatus.FAILED.value,
            "current_phase": MissionStatus.FAILED.value,
            "last_error": reason,
        })

        self.feed_repo.add_entry(
            mission_id=mission_id,
            event_type=EventType.MISSION_FAILED.value,
            message=f"Mission failed: {reason}",
            metadata_json={"error": reason},
        )

        if self.event_bus:
            await self.event_bus.publish(
                EventEnvelope(
                    event_type=EventType.MISSION_FAILED,
                    payload={"mission_id": mission_id, "reason": reason},
                )
            )

    async def retry_mission(self, mission_id: str, reason: str) -> bool:
        mission = self.mission_repo.get_by_id(mission_id)
        if not mission:
            raise NotFoundError(f"Mission {mission_id} not found")

        if mission.retries >= mission.max_retries:
            await self.fail_mission(mission_id, f"Exceeded max retries ({mission.max_retries}). Last error: {reason}")
            return False

        new_retries = mission.retries + 1
        self.mission_repo.update(mission_id, {
            "retries": new_retries,
            "last_error": reason,
        })

        self.feed_repo.add_entry(
            mission_id=mission_id,
            event_type=EventType.ADAPTATION_TRIGGERED.value,
            message=f"Retry attempt {new_retries}/{mission.max_retries}: {reason}",
            metadata_json={"retry": new_retries, "reason": reason},
        )

        return True

    def get_mission(self, mission_id: str) -> Optional[Any]:
        return self.mission_repo.get_by_id(mission_id)

    def get_activity_feed(self, mission_id: str, limit: int = 50, offset: int = 0) -> tuple[list[Any], int]:
        return self.feed_repo.get_feed(mission_id, limit=limit, offset=offset)

    def get_completed_mission_summary(self, mission_id: str) -> dict[str, Any]:
        mission = self.get_mission(mission_id)
        if not mission:
            raise NotFoundError(f"Mission {mission_id} not found")

        from app.db.repositories import (
            DecisionReplayRepository,
            MilestoneRepository,
            OutputRepository,
            ReviewRepository,
            StrategyRepository,
        )
        from app.services.reflection_engine import ReflectionEngine

        milestone_repo = MilestoneRepository(self.db)
        strategy_repo = StrategyRepository(self.db)
        output_repo = OutputRepository(self.db)
        review_repo = ReviewRepository(self.db)
        replay_repo = DecisionReplayRepository(self.db)
        reflection_engine = ReflectionEngine(self.db)

        milestones = milestone_repo.get_by_mission(mission_id)
        strategies = strategy_repo.get_by_mission(mission_id)
        outputs = output_repo.get_by_mission(mission_id)
        reviews = review_repo.get_by_mission(mission_id)
        replay_steps = replay_repo.get_timeline(mission_id)
        feed_entries, _ = self.feed_repo.get_feed(mission_id, limit=100, order_by_asc=True)
        reflection_report = reflection_engine.get_mission_reflection(mission_id)

        decisions = []
        rejected_alternatives = []
        for strat in strategies:
            for opt in getattr(strat, "options", []):
                opt_info = {
                    "id": opt.id,
                    "title": opt.title,
                    "description": opt.description,
                    "rationale": opt.rationale,
                    "score": opt.score,
                    "status": opt.status,
                }
                if opt.status == "SELECTED":
                    decisions.append(opt_info)
                else:
                    rejected_alternatives.append(opt_info)

        if not decisions:
            from app.services.reasoning_engine import ReasoningEngine
            reasoning_engine = ReasoningEngine(self.db)
            decision_rec = reasoning_engine.replay_decision(mission_id)
            if decision_rec:
                decisions.append(decision_rec.selected_strategy.model_dump())
                rejected_alternatives.extend([r.model_dump() for r in decision_rec.rejected_strategies])

        reflection_data = reflection_report.model_dump() if reflection_report else None
        lessons_learned = reflection_report.lessons_learned if reflection_report else []

        created_output = None
        if outputs:
            out = outputs[0]
            created_output = {
                "id": out.id,
                "title": out.title,
                "summary": out.summary,
                "content": out.content,
                "quality_score": out.quality_score,
                "status": out.status,
            }

        review_result = None
        if reviews:
            rev = reviews[0]
            review_result = {
                "id": rev.id,
                "score": rev.score,
                "passed": rev.passed,
                "recommendations": rev.recommendations,
                "summary": rev.summary,
            }

        return {
            "mission_id": mission.id,
            "original_objective": mission.objective,
            "execution_status": mission.status,
            "milestones": [
                {
                    "id": m.id,
                    "title": m.title,
                    "description": m.description,
                    "sequence_number": m.sequence_number,
                    "status": m.status,
                }
                for m in milestones
            ],
            "decisions": decisions,
            "rejected_alternatives": rejected_alternatives,
            "created_output": created_output,
            "review_result": review_result,
            "reflection": reflection_data,
            "lessons_learned": lessons_learned,
            "timeline_events": [
                {
                    "step_number": s.step_number,
                    "agent": s.agent,
                    "action_type": s.action_type,
                    "reason": s.reason,
                    "duration_ms": s.duration_ms,
                    "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                }
                for s in replay_steps
            ] or [
                {
                    "event_type": f.event_type,
                    "message": f.message,
                    "timestamp": f.created_at.isoformat() if f.created_at else None,
                }
                for f in feed_entries
            ],
        }

