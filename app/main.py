"""FastAPI entrypoint — the Backend in agent_loop.png."""
import logging

from fastapi import FastAPI

from app.api import router
from app.config import settings

logging.basicConfig(level=settings.log_level)

app = FastAPI(title="agent-loop", version="0.1.0")
app.include_router(router, prefix="/api")


@app.get("/")
def root() -> dict:
    return {"service": "agent-loop", "docs": "/docs", "mode": "offline" if settings.offline else "online"}
