"""FastAPI entrypoint — the Backend in agent_loop.png."""
import logging

from fastapi import FastAPI

from app.config import settings
from app.core.llm import llm
from app.core.tools import register_tools
from app.exceptions import register_exception_handlers
from app.modules.chat.router import router as chat_router

logging.basicConfig(level=settings.log_level)

# 在建立 app 前把功能模組的工具註冊進 REGISTRY，確保 agent loop 執行時可用。
register_tools()

app = FastAPI(title="agent-loop", version="0.1.0")
register_exception_handlers(app)
app.include_router(chat_router, prefix="/api")


@app.get("/")
def root() -> dict:
    return {"service": "agent-loop", "docs": "/docs", "mode": "offline" if settings.offline else "online"}


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "mode": "online" if llm.online else "offline", "model": settings.model}
