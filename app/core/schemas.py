"""跨功能共用的資料型別（core 層，不依賴任何 module）。"""

from typing import Any

from pydantic import BaseModel, Field


class SourceSchema(BaseModel):
    tool: str
    ref: str
    snippet: str = ""


class ToolCallSchema(BaseModel):
    name: str
    args: dict[str, Any]


class ToolResultSchema(BaseModel):
    name: str
    is_ok: bool
    data: Any = None
    sources: list[SourceSchema] = Field(default_factory=list)
    error: str | None = None
