"""Watch4U FastAPI entrypoint.

Skeleton only - wire up routers as each teammate ships their component.
"""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db import init_surreal, shutdown_surreal
<<<<<<< HEAD
from app.routers import fall_detection, health, rag, triage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger("watch4u")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Watch4U backend starting (env=%s)", settings.app_env)
    await init_surreal(app, settings)
    yield
    await shutdown_surreal(app)
    log.info("Watch4U backend shutting down")


app = FastAPI(
    title="Watch4U API",
    version="0.1.0",
    description="Context-Aware AI Fall Detection with Multilingual Staged Escalation",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(triage.router, prefix="/api/triage")
app.include_router(fall_detection.router, prefix="/api/fall-detection")
app.include_router(rag.router, prefix="/api/rag")
# TODO: include feature routers as they land
# app.include_router(wifi_detection.router, prefix="/api/wifi-detection")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
