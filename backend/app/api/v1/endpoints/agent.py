from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.db.session import SessionLocal
from app.schemas.feed import FeedEntry, FeedResponse
from app.schemas.mission import MissionInitializeRequest, MissionInitializeResponse
from app.schemas.replay import MissionReplayTimeline
from app.schemas.reflection import MissionReflectionReport
from app.services.agent_orchestrator import AgentOrchestrator


from app.services.event_bus import EventBus
from app.services.memory_engine import MemoryEngine
from app.services.mission_state_manager import MissionStateManager

router = APIRouter()
logger = logging.getLogger(__name__)

_ACTIVE_EXECUTIONS: set[str] = set()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def run_orchestrated_mission(mission_id: str):
    if mission_id in _ACTIVE_EXECUTIONS:
        logger.info("[AGENT INIT] Mission %s is already being executed; skipping duplicate worker", mission_id)
        return

    _ACTIVE_EXECUTIONS.add(mission_id)
    logger.info("[AGENT STARTED] Launching autonomous execution for mission %s", mission_id)
    db = SessionLocal()
    try:
        event_bus = EventBus()
        memory_engine = MemoryEngine(db, event_bus)
        state_manager = MissionStateManager(db, event_bus)
        orchestrator = AgentOrchestrator(
            db=db,
            event_bus=event_bus,
            state_manager=state_manager,
            memory_engine=memory_engine,
        )
        await orchestrator.execute_mission(mission_id)
    except Exception as exc:
        logger.exception("[AGENT ERROR] Autonomous execution failed for mission %s: %s", mission_id, exc)
    finally:
        _ACTIVE_EXECUTIONS.discard(mission_id)
        db.close()


@router.post("/init", response_model=MissionInitializeResponse, status_code=status.HTTP_200_OK, summary="Initialize a mission")
async def initialize_agent_mission(
    request: MissionInitializeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> MissionInitializeResponse:
    logger.info("[AGENT INIT] Received initialization request for mission '%s'", request.title)
    event_bus = EventBus()
    state_manager = MissionStateManager(db, event_bus)
    response = await state_manager.initialize_mission(request)
    if getattr(response, "_is_new", True):
        logger.info("[AGENT INIT] Starting autonomous execution for mission %s", response.mission_id)
        background_tasks.add_task(run_orchestrated_mission, response.mission_id)
    else:
        logger.info("[AGENT INIT] Reusing existing mission %s; autonomous execution not restarted", response.mission_id)
    return response


@router.get("/feed", response_model=FeedResponse, summary="Retrieve progress feed for a mission")
async def get_agent_feed(
    mission_id: Optional[str] = Query(None, description="The ID of the mission"),
    limit: int = Query(50, ge=1, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
) -> FeedResponse:
    if mission_id is not None and not mission_id.strip():
        raise ValidationError("mission_id parameter is required")

    target_mission_id = mission_id.strip() if mission_id and mission_id.strip() else None

    if not target_mission_id:
        from app.db.repositories import MissionRepository
        repo = MissionRepository(db)
        missions, total = repo.list_missions(limit=1, offset=0)
        if not total:
            raise NotFoundError("No missions found")
        target_mission_id = missions[0].id

    state_manager = MissionStateManager(db)
    mission = state_manager.get_mission(target_mission_id)
    if not mission:
        raise NotFoundError(f"Mission {target_mission_id} not found")

    from app.services.feed_engine import FeedGenerationEngine
    feed_engine = FeedGenerationEngine(db)
    return await feed_engine.get_mission_feed(
        mission_id=target_mission_id,
        limit=limit,
        offset=offset,
        order_by_asc=True,
        use_cache=True,
    )



@router.get("/replay", response_model=MissionReplayTimeline, summary="Retrieve complete decision replay timeline for a mission")
async def get_agent_replay(
    mission_id: str = Query(..., description="The ID of the mission"),
    db: Session = Depends(get_db),
) -> MissionReplayTimeline:
    if not mission_id or not mission_id.strip():
        raise ValidationError("mission_id parameter is required")

    state_manager = MissionStateManager(db)
    mission = state_manager.get_mission(mission_id)
    if not mission:
        raise NotFoundError(f"Mission {mission_id} not found")

    from app.services.replay_engine import DecisionReplayService
    replay_service = DecisionReplayService(db)
    return replay_service.get_timeline(mission_id)


@router.get("/reflection", response_model=MissionReflectionReport, summary="Retrieve post-mission self-review reflection report")
async def get_agent_reflection(
    mission_id: str = Query(..., description="The ID of the mission"),
    db: Session = Depends(get_db),
) -> MissionReflectionReport:
    if not mission_id or not mission_id.strip():
        raise ValidationError("mission_id parameter is required")

    state_manager = MissionStateManager(db)
    mission = state_manager.get_mission(mission_id)
    if not mission:
        raise NotFoundError(f"Mission {mission_id} not found")

    from app.services.reflection_engine import ReflectionEngine
    reflection_engine = ReflectionEngine(db)
    report = reflection_engine.get_mission_reflection(mission_id)
    if not report:
        raise NotFoundError(f"No reflection report found for mission {mission_id}")
    return report


@router.get("/missions", summary="Retrieve list of missions")
async def list_agent_missions(
    status: Optional[str] = Query(None, description="Optional status filter"),
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    from app.db.repositories import MissionRepository
    repo = MissionRepository(db)
    missions, total = repo.list_missions(status=status, limit=limit, offset=offset)
    return {
        "missions": [
            {
                "id": m.id,
                "title": m.title,
                "objective": m.objective,
                "description": m.description,
                "status": m.status,
                "priority": m.priority,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            }
            for m in missions
        ],
        "total_count": total,
    }


@router.get("/memories", summary="Retrieve long-term memory records")
async def get_agent_memories(
    mission_id: Optional[str] = Query(None, description="Optional mission_id filter"),
    memory_type: Optional[str] = Query(None, description="Optional memory_type filter"),
    query_text: Optional[str] = Query(None, description="Optional search query"),
    limit: int = Query(50, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    from app.services.memory_engine import MemoryEngine
    memory_engine = MemoryEngine(db)
    records = memory_engine.retrieve_relevant_memories(
        query_text=query_text,
        memory_type=memory_type,
        limit=limit,
    )
    if mission_id:
        records = [r for r in records if r.mission_id == mission_id]

    return {
        "memories": [
            {
                "id": r.id,
                "mission_id": r.mission_id,
                "memory_type": r.memory_type,
                "summary": r.summary,
                "insight": r.insight,
                "confidence_score": r.confidence_score,
                "tags": r.tags_json or [],
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in records
        ],
        "total_count": len(records),
    }


@router.get("/memory/retrieval", summary="Retrieve experience retrieval records for a mission")
async def get_agent_memory_retrieval(
    mission_id: str = Query(..., description="The target mission ID"),
    db: Session = Depends(get_db),
):
    from app.db.repositories import MemoryRepository
    repo = MemoryRepository(db)
    retrieval_records = repo.search_memories(query_text=None, memory_type="experience_retrieval", limit=20)
    mission_retrievals = [r for r in retrieval_records if r.mission_id == mission_id]

    all_memories = repo.search_memories(query_text=None, memory_type=None, limit=50)

    return {
        "target_mission_id": mission_id,
        "retrievals": [
            {
                "id": r.id,
                "summary": r.summary,
                "insight": r.insight,
                "confidence_score": r.confidence_score,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in mission_retrievals
        ],
        "available_prior_experiences": [
            {
                "id": m.id,
                "mission_id": m.mission_id,
                "memory_type": m.memory_type,
                "summary": m.summary,
                "insight": m.insight,
                "confidence_score": m.confidence_score,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in all_memories
            if m.mission_id != mission_id
        ],
    }




