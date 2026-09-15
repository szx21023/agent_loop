"""memory 模組的資料型別。"""
from typing import Literal

from pydantic import BaseModel


class MessageSchema(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
