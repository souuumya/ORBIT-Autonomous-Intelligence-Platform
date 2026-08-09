from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, List, Optional
from sqlalchemy.orm import Session

from app.db.models import (
    ActivityFeedEntryModel,
    DecisionReplayStepModel,
    MemoryRecordModel,
    MilestoneModel,
    MissionArtifactModel,
    MissionEventModel,
    MissionModel,
    OutputModel,
    ReviewModel,
    StrategyModel,
    StrategyOptionModel,
    TaskModel,
    UserModel,
)



class MissionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, mission_data: dict[str, Any]) -> MissionModel:
        mission = MissionModel(**mission_data)
        self.db.add(mission)
        self.db.commit()
        self.db.refresh(mission)
        return mission

    def get_by_id(self, mission_id: str) -> Optional[MissionModel]:
        return self.db.query(MissionModel).filter(MissionModel.id == mission_id).first()

    def list_missions(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[MissionModel], int]:
        query = self.db.query(MissionModel)
        if status:
            query = query.filter(MissionModel.status == status)
        total = query.count()
        missions = query.order_by(MissionModel.created_at.desc()).offset(offset).limit(limit).all()
        return missions, total

    def update(self, mission_id: str, updates: dict[str, Any]) -> Optional[MissionModel]:
        mission = self.get_by_id(mission_id)
        if not mission:
            return None
        for key, value in updates.items():
            if hasattr(mission, key):
                setattr(mission, key, value)
        mission.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(mission)
        return mission


class TaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_task(self, task_data: dict[str, Any]) -> TaskModel:
        task = TaskModel(**task_data)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_by_id(self, task_id: str) -> Optional[TaskModel]:
        return self.db.query(TaskModel).filter(TaskModel.id == task_id).first()

    def get_by_mission(self, mission_id: str) -> List[TaskModel]:
        return self.db.query(TaskModel).filter(TaskModel.mission_id == mission_id).order_by(TaskModel.created_at.asc()).all()

    def update(self, task_id: str, updates: dict[str, Any]) -> Optional[TaskModel]:
        task = self.get_by_id(task_id)
        if not task:
            return None
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        task.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(task)
        return task


class MilestoneRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, milestone_data: dict[str, Any]) -> MilestoneModel:
        milestone = MilestoneModel(**milestone_data)
        self.db.add(milestone)
        self.db.commit()
        self.db.refresh(milestone)
        return milestone

    def get_by_mission(self, mission_id: str) -> List[MilestoneModel]:
        return self.db.query(MilestoneModel).filter(MilestoneModel.mission_id == mission_id).order_by(MilestoneModel.sequence_number.asc()).all()


class StrategyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_strategy(self, strategy_data: dict[str, Any]) -> StrategyModel:
        strategy = StrategyModel(**strategy_data)
        self.db.add(strategy)
        self.db.commit()
        self.db.refresh(strategy)
        return strategy

    def add_option(self, option_data: dict[str, Any]) -> StrategyOptionModel:
        option = StrategyOptionModel(**option_data)
        self.db.add(option)
        self.db.commit()
        self.db.refresh(option)
        return option

    def get_by_mission(self, mission_id: str) -> List[StrategyModel]:
        return self.db.query(StrategyModel).filter(StrategyModel.mission_id == mission_id).all()


class OutputRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, output_data: dict[str, Any]) -> OutputModel:
        output = OutputModel(**output_data)
        self.db.add(output)
        self.db.commit()
        self.db.refresh(output)
        return output

    def get_by_mission(self, mission_id: str) -> List[OutputModel]:
        return self.db.query(OutputModel).filter(OutputModel.mission_id == mission_id).order_by(OutputModel.created_at.desc()).all()

    def update(self, output_id: str, updates: dict[str, Any]) -> Optional[OutputModel]:
        output = self.db.query(OutputModel).filter(OutputModel.id == output_id).first()
        if not output:
            return None
        for key, value in updates.items():
            if hasattr(output, key):
                setattr(output, key, value)
        output.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(output)
        return output


class ReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, review_data: dict[str, Any]) -> ReviewModel:
        review = ReviewModel(**review_data)
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def get_by_mission(self, mission_id: str) -> List[ReviewModel]:
        return self.db.query(ReviewModel).filter(ReviewModel.mission_id == mission_id).order_by(ReviewModel.created_at.desc()).all()


class ActivityFeedRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _make_json_safe(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {str(k): self._make_json_safe(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._make_json_safe(x) for x in obj]
        return obj

    def add_entry(
        self,
        mission_id: str,
        event_type: str,
        message: str,
        metadata_json: Optional[dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> ActivityFeedEntryModel:
        safe_metadata = self._make_json_safe(metadata_json or {})
        entry = ActivityFeedEntryModel(
            mission_id=mission_id,
            user_id=user_id,
            event_type=event_type,
            message=message,
            metadata_json=safe_metadata,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def add_feed_entry(
        self,
        mission_id: str,
        current_stage: str,
        agent_responsible: str,
        progress_percentage: float,
        summary_of_work: str,
        decision_made: str,
        confidence: float = 1.0,
        reflection: Optional[str] = None,
        event_type: str = "STAGE_PROGRESS",
        user_id: Optional[str] = None,
        extra_metadata: Optional[dict[str, Any]] = None,
    ) -> ActivityFeedEntryModel:
        meta = extra_metadata or {}
        meta.update({
            "current_stage": current_stage,
            "agent_responsible": agent_responsible,
            "progress_percentage": progress_percentage,
            "summary_of_work": summary_of_work,
            "decision_made": decision_made,
            "confidence": confidence,
            "reflection": reflection,
        })

        message = f"[{current_stage}] {summary_of_work} - Decision: {decision_made}"
        return self.add_entry(
            mission_id=mission_id,
            event_type=event_type,
            message=message,
            metadata_json=meta,
            user_id=user_id,
        )

    def get_feed(
        self,
        mission_id: str,
        limit: int = 50,
        offset: int = 0,
        order_by_asc: bool = False,
    ) -> tuple[List[ActivityFeedEntryModel], int]:
        query = self.db.query(ActivityFeedEntryModel).filter(ActivityFeedEntryModel.mission_id == mission_id)
        total = query.count()
        order_clause = ActivityFeedEntryModel.created_at.asc() if order_by_asc else ActivityFeedEntryModel.created_at.desc()
        entries = query.order_by(order_clause).offset(offset).limit(limit).all()
        return entries, total




class MemoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def store_memory(
        self,
        summary: str,
        insight: str,
        memory_type: str = "insight",
        confidence_score: float = 1.0,
        tags: Optional[List[str]] = None,
        mission_id: Optional[str] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
    ) -> MemoryRecordModel:
        record = MemoryRecordModel(
            summary=summary,
            insight=insight,
            memory_type=memory_type,
            confidence_score=confidence_score,
            tags_json=tags or [],
            mission_id=mission_id,
            user_id=user_id,
            organization_id=organization_id,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def search_memories(
        self,
        query_text: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[MemoryRecordModel]:
        query = self.db.query(MemoryRecordModel)
        if memory_type:
            query = query.filter(MemoryRecordModel.memory_type == memory_type)
        if query_text:
            search_pattern = f"%{query_text.lower()}%"
            query = query.filter(
                (MemoryRecordModel.summary.ilike(search_pattern)) |
                (MemoryRecordModel.insight.ilike(search_pattern))
            )
        return query.order_by(MemoryRecordModel.confidence_score.desc(), MemoryRecordModel.created_at.desc()).limit(limit).all()


class DecisionReplayRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record_step(
        self,
        mission_id: str,
        agent: str,
        action_type: str,
        reason: str,
        confidence: float = 1.0,
        duration_ms: float = 0.0,
        output_summary: str = "",
        metadata_json: Optional[dict[str, Any]] = None,
    ) -> DecisionReplayStepModel:
        # Determine next step_number chronologically for this mission
        max_step = (
            self.db.query(DecisionReplayStepModel.step_number)
            .filter(DecisionReplayStepModel.mission_id == mission_id)
            .order_by(DecisionReplayStepModel.step_number.desc())
            .first()
        )
        step_number = (max_step[0] + 1) if max_step else 1

        step = DecisionReplayStepModel(
            mission_id=mission_id,
            step_number=step_number,
            agent=agent,
            action_type=action_type,
            reason=reason,
            confidence=confidence,
            duration_ms=duration_ms,
            output_summary=output_summary,
            metadata_json=metadata_json or {},
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def get_timeline(self, mission_id: str) -> List[DecisionReplayStepModel]:
        return (
            self.db.query(DecisionReplayStepModel)
            .filter(DecisionReplayStepModel.mission_id == mission_id)
            .order_by(DecisionReplayStepModel.step_number.asc())
            .all()
        )


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_user_exists(self, user_id: str = "user-1") -> UserModel:
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if user:
            return user

        email = f"{user_id}@orbit.system"
        existing_by_email = self.db.query(UserModel).filter(
            (UserModel.email == email) | (UserModel.username == user_id)
        ).first()
        if existing_by_email:
            return existing_by_email

        user = UserModel(
            id=user_id,
            email=email,
            username=user_id,
            full_name="System Default User",
            role="system",
            is_active=True,
        )
        self.db.add(user)
        try:
            self.db.commit()
            self.db.refresh(user)
        except Exception:
            self.db.rollback()
            user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return user

