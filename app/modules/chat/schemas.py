"""chat 模組的輸入/輸出型別。"""

from pydantic import BaseModel, Field

from app.core.schemas import SourceSchema
from app.modules.chat.constants import DEFAULT_SESSION_ID, EventType


class ChatRequestSchema(BaseModel):
    question: str
    session_id: str = DEFAULT_SESSION_ID


class ChatResponseSchema(BaseModel):
    answer: str
    sources: list[SourceSchema] = Field(default_factory=list)
    steps: int = 0


class ChatEventSchema(BaseModel):
    """stream_agent 的串流事件；type 決定哪些欄位有意義（見 EventType）。"""

    type: EventType
    text: str = ""  # DELTA 的文字片段；DONE 的完整答案
    tool: str = ""  # TOOL 事件呼叫的工具名
    step: int = 0  # STEP／DONE 的迴圈步數
    sources: list[SourceSchema] = Field(default_factory=list)  # DONE 的去重來源
