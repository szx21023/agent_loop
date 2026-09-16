"""FastAPI entrypoint — the Backend in agent_loop.png."""

import logging

from fastapi import FastAPI

from app.bootstrap import register_tools
from app.config import settings
from app.core.llm import llm
from app.exceptions import register_exception_handlers
from app.modules.chat.router import router as chat_router

logging.basicConfig(level=settings.log_level)

# 在建立 app 前把功能模組的工具註冊進 REGISTRY，確保 agent loop 執行時可用。
register_tools()

app = FastAPI(title="agent-loop", version="0.1.0")
register_exception_handlers(app)
app.include_router(chat_router, prefix="/api")


# `/` 與 `/api/health` 都以 llm.is_online（實際是否成功建立 client）為準，
# 而非 settings.is_offline（只看有沒有金鑰）——否則有金鑰但 client 建立失敗時，
# 兩個端點會對「online/offline」各說一套。
@app.get("/")
def root() -> dict:
    return {
        "service": "agent-loop",
        "docs": "/docs",
        "mode": "online" if llm.is_online else "offline",
    }


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "mode": "online" if llm.is_online else "offline",
        "model": settings.model,
    }
