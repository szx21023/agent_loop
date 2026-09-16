"""memory 模組的資料型別。"""

from pydantic import BaseModel

from app.core.constants import Role


class MessageSchema(BaseModel):
    role: Role
    content: str
