from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import register_middlewares
from app.db.session import Base, SessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from app.db.repositories import UserRepository
        UserRepository(db).ensure_user_exists("user-1")
    finally:
        db.close()
    yield


setup_logging()

app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description="Architecture foundation for the Autonomous AI Creator platform.",
    lifespan=lifespan,
)

register_middlewares(app)
register_exception_handlers(app)
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api")

from app.api.v1.endpoints.health import router as health_router
app.include_router(health_router, prefix="/health", tags=["health"])

