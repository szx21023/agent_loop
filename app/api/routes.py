"""HTTP routes — the Backend layer that fronts the Agent."""
from fastapi import APIRouter

from app.agent import run_agent
from app.config import settings
from app.llm import llm
from app.memory import conversations
from app.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "mode": "online" if llm.online else "offline", "model": settings.model}


@router.post("/ask", response_model=ChatResponse)
def ask(req: ChatRequest) -> ChatResponse:
    return run_agent(req.question, req.session_id)


@router.delete("/sessions/{session_id}")
def clear_session(session_id: str) -> dict:
    conversations.clear(session_id)
    return {"cleared": session_id}
