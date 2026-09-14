"""chat 模組的輸入/輸出型別。"""
from pydantic import BaseModel, Field

from app.core.schemas import Source


class ChatRequest(BaseModel):
    question: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source] = Field(default_factory=list)
    steps: int = 0
