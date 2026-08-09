from __future__ import annotations

from datetime import UTC, datetime
import uuid
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("OrganizationModel", back_populates="users")
    missions = relationship("MissionModel", back_populates="creator")
    activity_feed_entries = relationship("ActivityFeedEntryModel", back_populates="user")
    memory_records = relationship("MemoryRecordModel", back_populates="user")


class OrganizationModel(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    users = relationship("UserModel", back_populates="organization")
    missions = relationship("MissionModel", back_populates="organization")


class MissionModel(Base):
    __tablename__ = "missions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    created_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    objective = Column(Text, nullable=False)
    description = Column(Text, default="", nullable=False)
    status = Column(String(50), nullable=False, index=True, default="INITIALIZED")
    priority = Column(String(50), default="medium", nullable=False)
    current_phase = Column(String(100), default="INITIALIZED", nullable=False)
    retries = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    last_error = Column(Text, nullable=True)
    cancellation_requested = Column(Boolean, default=False, nullable=False)
    context_json = Column(JSON, default=dict, nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    organization = relationship("OrganizationModel", back_populates="missions")
    creator = relationship("UserModel", back_populates="missions")
    milestones = relationship("MilestoneModel", back_populates="mission", cascade="all, delete-orphan")
    tasks = relationship("TaskModel", back_populates="mission", cascade="all, delete-orphan")
    strategies = relationship("StrategyModel", back_populates="mission", cascade="all, delete-orphan")
    outputs = relationship("OutputModel", back_populates="mission", cascade="all, delete-orphan")
    reviews = relationship("ReviewModel", back_populates="mission", cascade="all, delete-orphan")
    activity_feed_entries = relationship("ActivityFeedEntryModel", back_populates="mission", cascade="all, delete-orphan")
    mission_events = relationship("MissionEventModel", back_populates="mission", cascade="all, delete-orphan")
    memory_records = relationship("MemoryRecordModel", back_populates="mission", cascade="all, delete-orphan")


class MilestoneModel(Base):
    __tablename__ = "milestones"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="", nullable=False)
    sequence_number = Column(Integer, nullable=False, default=1)
    status = Column(String(50), default="PENDING", nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    mission = relationship("MissionModel", back_populates="milestones")
    tasks = relationship("TaskModel", back_populates="milestone", cascade="all, delete-orphan")


class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False, index=True)
    milestone_id = Column(String(36), ForeignKey("milestones.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="", nullable=False)
    task_type = Column(String(100), default="general", nullable=False)
    status = Column(String(50), default="PENDING", nullable=False, index=True)
    priority = Column(String(50), default="medium", nullable=False)
    assigned_agent_role = Column(String(100), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    mission = relationship("MissionModel", back_populates="tasks")
    milestone = relationship("MilestoneModel", back_populates="tasks")
    outputs = relationship("OutputModel", back_populates="task", cascade="all, delete-orphan")
    reviews = relationship("ReviewModel", back_populates="task", cascade="all, delete-orphan")
    strategy_options = relationship("StrategyOptionModel", back_populates="task", cascade="all, delete-orphan")


class StrategyModel(Base):
    __tablename__ = "strategies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="", nullable=False)
    rationale = Column(Text, default="", nullable=False)
    status = Column(String(50), default="PROPOSED", nullable=False, index=True)
    selected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    mission = relationship("MissionModel", back_populates="strategies")
    options = relationship("StrategyOptionModel", back_populates="strategy", cascade="all, delete-orphan")


class StrategyOptionModel(Base):
    __tablename__ = "strategy_options"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=False, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="", nullable=False)
    rationale = Column(Text, default="", nullable=False)
    score = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="CANDIDATE", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    strategy = relationship("StrategyModel", back_populates="options")
    task = relationship("TaskModel", back_populates="strategy_options")
    reviews = relationship("ReviewModel", back_populates="strategy_option")


class OutputModel(Base):
    __tablename__ = "outputs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True, index=True)
    output_type = Column(String(100), default="deliverable", nullable=False, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, default="", nullable=False)
    content = Column(Text, default="", nullable=False)
    content_reference = Column(String(500), nullable=True)
    quality_score = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    mission = relationship("MissionModel", back_populates="outputs")
    task = relationship("TaskModel", back_populates="outputs")
    artifacts = relationship("MissionArtifactModel", back_populates="output", cascade="all, delete-orphan")


class ReviewModel(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True, index=True)
    strategy_option_id = Column(String(36), ForeignKey("strategy_options.id"), nullable=True)
    review_type = Column(String(100), default="quality_assessment", nullable=False, index=True)
    score = Column(Float, default=0.0, nullable=False)
    summary = Column(Text, default="", nullable=False)
    recommendations = Column(Text, default="", nullable=False)
    passed = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    mission = relationship("MissionModel", back_populates="reviews")
    task = relationship("TaskModel", back_populates="reviews")
    strategy_option = relationship("StrategyOptionModel", back_populates="reviews")


class ActivityFeedEntryModel(Base):
    __tablename__ = "activity_feed_entries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)

    mission = relationship("MissionModel", back_populates="activity_feed_entries")
    user = relationship("UserModel", back_populates="activity_feed_entries")


class MissionEventModel(Base):
    __tablename__ = "mission_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False, index=True)
    milestone_id = Column(String(36), ForeignKey("milestones.id"), nullable=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    strategy_id = Column(String(36), ForeignKey("strategies.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    event_payload = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)

    mission = relationship("MissionModel", back_populates="mission_events")


class MissionArtifactModel(Base):
    __tablename__ = "mission_artifacts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False)
    output_id = Column(String(36), ForeignKey("outputs.id"), nullable=True)
    artifact_type = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=False)
    storage_reference = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    output = relationship("OutputModel", back_populates="artifacts")


class MemoryRecordModel(Base):
    __tablename__ = "memory_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=True)
    memory_type = Column(String(100), default="insight", nullable=False)
    summary = Column(Text, nullable=False)
    insight = Column(Text, nullable=False)
    confidence_score = Column(Float, default=1.0, nullable=False)
    tags_json = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    user = relationship("UserModel", back_populates="memory_records")
    mission = relationship("MissionModel", back_populates="memory_records")


class DecisionReplayStepModel(Base):
    __tablename__ = "decision_replay_steps"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False, index=True)
    agent = Column(String(100), nullable=False)
    action_type = Column(String(100), nullable=False)
    reason = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    duration_ms = Column(Float, default=0.0, nullable=False)
    output_summary = Column(Text, default="", nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)

    mission = relationship("MissionModel")

