from datetime import UTC, datetime
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.db.session import SessionLocal

router = APIRouter()


@router.get("", summary="Health check")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "Autonomous AI Creator Backend",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/ready", summary="Readiness check")
def readiness_check() -> dict[str, str | bool]:
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "ready": True,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database readiness check failed: {exc}",
        ) from exc
    finally:
        db.close()
