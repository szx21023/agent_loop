"""chat 路由：Backend 層，只做參數驗證 → 呼叫 service → 回傳。"""
from fastapi import APIRouter

from app.modules.chat.schemas import ChatRequestSchema, ChatResponseSchema
from app.modules.chat.service import run_agent
from app.modules.memory import service as memory

router = APIRouter(tags=["chat"])


@router.post("/ask", response_model=ChatResponseSchema)
def ask(req: ChatRequestSchema) -> ChatResponseSchema:
    return run_agent(req.question, req.session_id)


@router.delete("/sessions/{session_id}")
def clear_session(session_id: str) -> dict:
    memory.clear_session(session_id)
    return {"cleared": session_id}
