import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    if settings.environment == "testing":
        DATABASE_URL = "sqlite:///:memory:"
    else:
        DATABASE_URL = (
            f"postgresql+psycopg://{settings.postgres_user}:{settings.postgres_password}@"
            f"{settings.postgres_server}/{settings.postgres_db}"
        )

connect_args = {}
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    if ":memory:" in DATABASE_URL:
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(
    DATABASE_URL,
    echo=settings.environment == "development",
    connect_args=connect_args,
    **engine_kwargs,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


