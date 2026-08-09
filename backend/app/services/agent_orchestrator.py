from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.agents import (
    BaseAgent,
    CreatorAgent,
    DecisionAgent,
    PlannerAgent,
    ResearchAgent,
    ReviewerAgent,
)
from app.core.exceptions import NotFoundError, MissionEngineError
from app.schemas.events import EventEnvelope, EventType
from app.schemas.mission import MissionStatus
from app.schemas.orchestrator import (
    AgentState,
    AgentStatusSummary,
    OrchestratorExecutionResult,
    StageConfig,
    WorkflowConfig,
)
from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine
from app.services.feed_engine import FeedGenerationEngine
from app.services.mission_state_manager import MissionStateManager
from app.services.reasoning_engine import ReasoningEngine
from app.services.reflection_engine import ReflectionEngine
from app.services.replay_engine import DecisionReplayService

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Central intelligence layer coordinating multi-agent workflows, stage timeouts, retries,
    rollbacks, decision replays, reflections, and evaluator feeds.
    """

    def __init__(
        self,
        db: Session,
        event_bus: Optional[EventBus] = None,
        state_manager: Optional[MissionStateManager] = None,
        memory_engine: Optional[MemoryEngine] = None,
        workflow_config: Optional[WorkflowConfig] = None,
        agents: Optional[Dict[str, BaseAgent]] = None,
        replay_service: Optional[DecisionReplayService] = None,
        feed_engine: Optional[FeedGenerationEngine] = None,
        reasoning_engine: Optional[ReasoningEngine] = None,
        reflection_engine: Optional[ReflectionEngine] = None,
    ) -> None:
        self.db = db
        self.event_bus = event_bus or EventBus()
        self.memory_engine = memory_engine or MemoryEngine(db, self.event_bus)
        self.state_manager = state_manager or MissionStateManager(db, self.event_bus)
        self.workflow_config = workflow_config or WorkflowConfig()
        self.replay_service = replay_service or DecisionReplayService(db)
        self.feed_engine = feed_engine or FeedGenerationEngine(db, self.event_bus)
        self.reasoning_engine = reasoning_engine or ReasoningEngine(db, self.event_bus)
        self.reflection_engine = reflection_engine or ReflectionEngine(db, self.memory_engine, self.event_bus)




        if agents:
            self.agents = agents
        else:
            self.planner = PlannerAgent(db, self.event_bus, self.memory_engine)
            self.researcher = ResearchAgent(db, self.event_bus, self.memory_engine)
            self.decision_maker = DecisionAgent(db, self.event_bus, self.memory_engine)
            self.creator = CreatorAgent(db, self.event_bus, self.memory_engine)
            self.reviewer = ReviewerAgent(db, self.event_bus, self.memory_engine)
            self.agents = {
                "PlannerAgent": self.planner,
                "ResearchAgent": self.researcher,
                "DecisionAgent": self.decision_maker,
                "CreatorAgent": self.creator,
                "ReviewerAgent": self.reviewer,
            }

        self._agent_statuses: Dict[str, AgentStatusSummary] = {
            role: AgentStatusSummary(agent_role=role, status=AgentState.IDLE)
            for role in self.agents.keys()
        }

    def get_agent_statuses(self) -> Dict[str, AgentStatusSummary]:
        return dict(self._agent_statuses)

    async def execute_mission(self, mission_id: str, **kwargs: Any) -> OrchestratorExecutionResult:
        logger.info("[AGENT STARTED] Autonomous Orchestrator starting execution for mission %s", mission_id)

        mission = self.state_manager.get_mission(mission_id)
        if not mission:
            raise NotFoundError(f"Mission {mission_id} not found")

        stage_results: Dict[str, Any] = {}
        total_stages = len(self.workflow_config.stages)

        try:
            return await asyncio.wait_for(
                self._run_pipeline(mission, mission_id, stage_results, total_stages, **kwargs),
                timeout=self.workflow_config.global_timeout_seconds,
            )
        except asyncio.TimeoutError:
            err_msg = f"Global mission execution timed out after {self.workflow_config.global_timeout_seconds} seconds"
            logger.error("[AGENT ERROR] Mission %s global timeout: %s", mission_id, err_msg)
            return await self._execute_rollback(mission_id, "GlobalTimeout", err_msg)
        except Exception as exc:
            err_msg = f"Unrecoverable orchestrator error: {exc}"
            logger.exception("[AGENT ERROR] Mission %s execution failed: %s", mission_id, err_msg)
            return await self._execute_rollback(mission_id, "SystemExecution", err_msg)

    async def _run_pipeline(
        self,
        mission: Any,
        mission_id: str,
        stage_results: Dict[str, Any],
        total_stages: int,
        **kwargs: Any,
    ) -> OrchestratorExecutionResult:
        # Record 1: Mission Started Replay Step
        self.replay_service.record_mission_started(mission_id, mission.title, mission.objective)
        post_content = (
            f"Autonomous agent initialized for mission '{mission.title}'. "
            f"Objective: {mission.objective}"
        )
        await self.feed_engine.generate_entry(
            mission_id=mission_id,
            current_stage="INITIALIZED",
            agent_responsible="System",
            progress_percentage=0.0,
            summary_of_work=post_content,
            decision_made="Autonomous post generated",
            confidence=0.99,
            event_type="AUTONOMOUS_POST",
            extra_metadata={
                "content": post_content,
                "generated_by": "autonomous_agent",
                "generatedBy": "autonomous_agent",
                "createdAt": datetime.now(UTC).isoformat(),
                "post_type": "autonomous_agent",
            },
            publish_event=False,
        )
        logger.info("[AGENT POST CREATED] Persisted autonomous post for mission %s", mission_id)

        for idx, stage in enumerate(self.workflow_config.stages):
            progress_pct = round(((idx + 1) / max(1, total_stages)) * 100.0, 2)

            t_start = time.perf_counter()
            logger.info("[AGENT EXECUTION] Mission %s is executing stage %s", mission_id, stage.stage_name)
            stage_res = await self._execute_stage(stage, mission_id, progress_pct, **kwargs)
            duration_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

            if not stage_res["success"]:
                await self.feed_engine.generate_entry(
                    mission_id=mission_id,
                    current_stage=stage.stage_name,
                    agent_responsible=stage.agent_role,
                    progress_percentage=progress_pct,
                    summary_of_work=f"Stage '{stage.stage_name}' execution failed.",
                    decision_made=f"Triggered rollback: {stage_res['error']}",
                    confidence=0.0,
                )
                return await self._execute_rollback(mission_id, stage.stage_name, stage_res["error"])

            stage_data = stage_res["data"]
            stage_results[stage.stage_name] = stage_data

            # Record Replay Step & Evaluator Feed Entry per Agent
            if stage.agent_role == "PlannerAgent":
                self.replay_service.record_planner_step(mission_id, stage_data, duration_ms)
                logger.info("[AGENT DECISION] Mission %s selected planning output", mission_id)
                await self.feed_engine.generate_entry(
                    mission_id=mission_id,
                    current_stage=stage.stage_name,
                    agent_responsible=stage.agent_role,
                    progress_percentage=progress_pct,
                    summary_of_work=f"Decomposed objective into {stage_data.get('milestones_count', 0)} milestones and {stage_data.get('tasks_count', 0)} tasks.",
                    decision_made="Structured mission milestone roadmap",
                    confidence=0.95,
                )
            elif stage.agent_role == "ResearchAgent":
                self.replay_service.record_research_step(mission_id, stage_data, duration_ms)
                brief = stage_data.get("research_brief", {})
                logger.info("[AGENT DECISION] Mission %s completed research synthesis", mission_id)
                await self.feed_engine.generate_entry(
                    mission_id=mission_id,
                    current_stage=stage.stage_name,
                    agent_responsible=stage.agent_role,
                    progress_percentage=progress_pct,
                    summary_of_work="Compiled domain research context and competitive landscape brief.",
                    decision_made="Validated evidence alignment for strategy evaluation",
                    confidence=float(brief.get("confidence_level", 0.95)),
                )
            elif stage.agent_role == "DecisionAgent":
                self.replay_service.record_decision_breakdown(mission_id, stage_data, duration_ms)
                logger.info("[AGENT DECISION] Mission %s selected strategy '%s'", mission_id, stage_data.get("selected_title"))
                await self.feed_engine.generate_entry(
                    mission_id=mission_id,
                    current_stage=stage.stage_name,
                    agent_responsible=stage.agent_role,
                    progress_percentage=progress_pct,
                    summary_of_work=stage_data.get("reason", "Evaluated alternative strategies."),
                    decision_made=f"Selected '{stage_data.get('selected_title')}'",
                    confidence=float(stage_data.get("confidence", 0.95)),
                )
            elif stage.agent_role == "CreatorAgent":
                self.replay_service.record_creator_step(mission_id, stage_data, duration_ms)
                logger.info("[AGENT DECISION] Mission %s generated deliverable output", mission_id)
                await self.feed_engine.generate_entry(
                    mission_id=mission_id,
                    current_stage=stage.stage_name,
                    agent_responsible=stage.agent_role,
                    progress_percentage=progress_pct,
                    summary_of_work=f"Synthesized deliverable artifact: '{stage_data.get('title', 'Deliverable')}'",
                    decision_made="Drafted asset outputs for quality review",
                    confidence=0.95,
                )
            elif stage.agent_role == "ReviewerAgent":
                self.replay_service.record_reviewer_step(mission_id, stage_data, duration_ms)
                passed = stage_data.get("passed", True)
                logger.info("[AGENT DECISION] Mission %s review completed with score %.2f", mission_id, stage_data.get("score", 0.95))
                await self.feed_engine.generate_entry(
                    mission_id=mission_id,
                    current_stage=stage.stage_name,
                    agent_responsible=stage.agent_role,
                    progress_percentage=progress_pct,
                    summary_of_work=f"Evaluated output quality (Score: {stage_data.get('score', 0.95):.2f}).",
                    decision_made="Approved deliverable quality" if passed else "Requested revision",
                    confidence=float(stage_data.get("score", 0.95)),
                )

            # Handle Decision -> Creator -> Reviewer revision loop if Reviewer rejects output
            if stage.agent_role == "ReviewerAgent":
                review_data = stage_res["data"]
                max_revisions = 2
                revision_count = 0

                while not review_data.get("passed", False) and revision_count < max_revisions:
                    revision_count += 1
                    logger.warning(
                        "Mission %s review failed (score=%.2f). Starting revision loop %d/%d",
                        mission_id,
                        review_data.get("score", 0.0),
                        revision_count,
                        max_revisions,
                    )

                    can_retry = await self.state_manager.retry_mission(
                        mission_id,
                        f"Review failed: {review_data.get('recommendations')}",
                    )

                    if not can_retry:
                        return await self._execute_rollback(
                            mission_id,
                            "ReviewerAgent",
                            "Exceeded max retries during review revision loop",
                        )

                    # Re-execute Creator & Reviewer stages
                    creator_stage = next(s for s in self.workflow_config.stages if s.agent_role == "CreatorAgent")
                    c_start = time.perf_counter()
                    creator_res = await self._execute_stage(creator_stage, mission_id, progress_pct, **kwargs)
                    c_dur = round((time.perf_counter() - c_start) * 1000.0, 2)
                    if not creator_res["success"]:
                        return await self._execute_rollback(mission_id, "CreatorAgent", creator_res["error"])
                    stage_results["Creation"] = creator_res["data"]
                    self.replay_service.record_creator_step(mission_id, creator_res["data"], c_dur)

                    r_start = time.perf_counter()
                    reviewer_res = await self._execute_stage(stage, mission_id, progress_pct, **kwargs)
                    r_dur = round((time.perf_counter() - r_start) * 1000.0, 2)
                    if not reviewer_res["success"]:
                        return await self._execute_rollback(mission_id, "ReviewerAgent", reviewer_res["error"])
                    stage_results["Review"] = reviewer_res["data"]
                    review_data = reviewer_res["data"]
                    self.replay_service.record_reviewer_step(mission_id, reviewer_res["data"], r_dur)

                if not review_data.get("passed", False):
                    return await self._execute_rollback(
                        mission_id,
                        "ReviewerAgent",
                        f"Output quality rejected after {revision_count} revisions",
                    )

        # Generate post-execution reflection via ReflectionEngine & ReasoningEngine
        decision_res = stage_results.get("Decision", {})
        review_res = stage_results.get("Review", {})

        decision_record = self.reasoning_engine.replay_decision(mission_id)
        reflection_report = await self.reflection_engine.analyze_and_reflect(
            mission_id=mission_id,
            stage_results=stage_results,
            review_result=review_res,
            decision_record=decision_record,
            revision_count=revision_count if 'revision_count' in locals() else 0,
        )

        reflection_text = f"Performance Score: {reflection_report.performance_score:.2f} | Lessons Learned: {', '.join(reflection_report.lessons_learned)}"


        m_start = time.perf_counter()
        summary_text = f"Selected strategy '{decision_res.get('selected_title')}' achieved score {review_res.get('score', 1.0):.2f}."
        await self.memory_engine.store_long_term_memory(
            summary=f"Successful execution of mission: {mission.title}",
            insight=summary_text,
            memory_type="lesson_learned",
            confidence_score=review_res.get("score", 0.95),
            tags=["success", mission.title.lower().replace(" ", "_")],
            mission_id=mission_id,
        )
        m_dur = round((time.perf_counter() - m_start) * 1000.0, 2)
        self.replay_service.record_memory_update_step(mission_id, summary_text, m_dur)

        await self.feed_engine.generate_entry(
            mission_id=mission_id,
            current_stage="COMPLETED",
            agent_responsible="System",
            progress_percentage=100.0,
            summary_of_work="Autonomous mission completed successfully.",
            decision_made="Completed multi-agent campaign execution",
            confidence=1.0,
            reflection=reflection_text,
        )

        await self.state_manager.transition_state(
            mission_id,
            MissionStatus.COMPLETED,
            "Autonomous Orchestrator successfully finished mission workflow.",
        )
        self.replay_service.record_mission_completed(mission_id)

        logger.info("Autonomous Orchestrator successfully completed mission %s", mission_id)
        return OrchestratorExecutionResult(
            mission_id=mission_id,
            status=MissionStatus.COMPLETED.value,
            progress_percentage=100.0,
            agent_statuses=self._agent_statuses,
            stage_results=stage_results,
        )


    async def _execute_stage(
        self,
        stage: StageConfig,
        mission_id: str,
        progress_pct: float,
        **kwargs: Any,
    ) -> dict[str, Any]:
        agent = self.agents.get(stage.agent_role)
        if not agent:
            return {"success": False, "error": f"Agent role {stage.agent_role} not registered"}

        mapped_status = MissionStatus.PLANNING
        if stage.agent_role == "ResearchAgent":
            mapped_status = MissionStatus.RESEARCHING
        elif stage.agent_role in {"DecisionAgent", "CreatorAgent"}:
            mapped_status = MissionStatus.CREATING
        elif stage.agent_role == "ReviewerAgent":
            mapped_status = MissionStatus.REVIEWING

        await self.state_manager.transition_state(
            mission_id,
            mapped_status,
            f"Stage '{stage.stage_name}' started by agent {stage.agent_role}.",
            metadata={"progress_percentage": progress_pct},
        )

        self._update_agent_status(stage.agent_role, AgentState.RUNNING)

        attempts = 0
        last_error = ""

        while attempts <= stage.max_retries:
            attempts += 1
            try:
                self.log_info(
                    "Executing stage '%s' (Attempt %d/%d, Timeout: %.1fs)",
                    stage.stage_name,
                    attempts,
                    stage.max_retries + 1,
                    stage.timeout_seconds,
                )

                result = await asyncio.wait_for(
                    agent.run(mission_id, **kwargs),
                    timeout=stage.timeout_seconds,
                )

                self._update_agent_status(stage.agent_role, AgentState.COMPLETED)
                return {"success": True, "data": result}

            except asyncio.TimeoutError:
                last_error = f"Stage '{stage.stage_name}' timed out after {stage.timeout_seconds}s"
                logger.warning("Stage %s attempt %d timed out", stage.stage_name, attempts)
            except Exception as exc:
                last_error = str(exc)
                logger.warning("Stage %s attempt %d failed: %s", stage.stage_name, attempts, exc)

            if attempts <= stage.max_retries:
                self._update_agent_status(stage.agent_role, AgentState.RETRYING, error=last_error)
                await asyncio.sleep(stage.backoff_seconds * attempts)

        self._update_agent_status(stage.agent_role, AgentState.FAILED, error=last_error)
        return {"success": False, "error": last_error}

    async def _execute_rollback(
        self,
        mission_id: str,
        failed_stage: str,
        reason: str,
    ) -> OrchestratorExecutionResult:
        logger.error("Executing rollback for mission %s (Failed Stage: %s, Reason: %s)", mission_id, failed_stage, reason)

        for role, summary in self._agent_statuses.items():
            if summary.status in {AgentState.RUNNING, AgentState.RETRYING, AgentState.FAILED}:
                summary.status = AgentState.ROLLED_BACK
                summary.last_updated = datetime.now(UTC)
                summary.error = reason

        await self.state_manager.fail_mission(mission_id, f"Rollback triggered at stage '{failed_stage}': {reason}")

        if self.event_bus:
            await self.event_bus.publish(
                EventEnvelope(
                    event_type=EventType.ADAPTATION_TRIGGERED,
                    payload={
                        "mission_id": mission_id,
                        "action": "ROLLBACK",
                        "failed_stage": failed_stage,
                        "reason": reason,
                    },
                )
            )

        return OrchestratorExecutionResult(
            mission_id=mission_id,
            status=MissionStatus.FAILED.value,
            progress_percentage=0.0,
            agent_statuses=self._agent_statuses,
            error=reason,
        )

    def _update_agent_status(
        self,
        role: str,
        status: AgentState,
        error: Optional[str] = None,
    ) -> None:
        self._agent_statuses[role] = AgentStatusSummary(
            agent_role=role,
            status=status,
            last_updated=datetime.now(UTC),
            error=error,
        )

    def log_info(self, msg: str, *args: Any) -> None:
        logger.info(f"[AutonomousOrchestrator] " + msg, *args)
