from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings


def register_middlewares(app: FastAPI) -> None:
    origins = [o.strip() for o in settings.backend_cors_origins.split(",") if o.strip()]
    if "http://localhost:3000" not in origins:
        origins.append("http://localhost:3000")
    if "http://127.0.0.1:3000" not in origins:
        origins.append("http://127.0.0.1:3000")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

