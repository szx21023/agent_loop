"""chat 模組的輸入/輸出型別。"""
from pydantic import BaseModel, Field

from app.core.schemas import SourceSchema


class ChatRequestSchema(BaseModel):
    question: str
    session_id: str = "default"


class ChatResponseSchema(BaseModel):
    answer: str
    sources: list[SourceSchema] = Field(default_factory=list)
    steps: int = 0
