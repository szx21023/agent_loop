"""Pydantic models shared across the API and agent layers."""
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str
    session_id: str = "default"


class Source(BaseModel):
    tool: str
    ref: str
    snippet: str = ""


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source] = Field(default_factory=list)
    steps: int = 0


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ToolCall(BaseModel):
    name: str
    args: dict[str, Any]


class ToolResult(BaseModel):
    name: str
    ok: bool
    data: Any = None
    sources: list[Source] = Field(default_factory=list)
    error: Optional[str] = None
