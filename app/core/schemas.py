"""跨功能共用的資料型別（core 層，不依賴任何 module）。"""
from typing import Any, Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    tool: str
    ref: str
    snippet: str = ""


class ToolCall(BaseModel):
    name: str
    args: dict[str, Any]


class ToolResult(BaseModel):
    name: str
    ok: bool
    data: Any = None
    sources: list[Source] = Field(default_factory=list)
    error: Optional[str] = None
