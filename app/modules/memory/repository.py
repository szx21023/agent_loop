"""記憶層儲存實作（目前為記憶體內；接 SQL/Redis 後在此抽換）。

- ConversationStore：per-session 對話歷史。
- ProfileStore：per-user 長期偏好/事實。
"""
from collections import defaultdict
from typing import Any

from app.core.constants import Role
from app.modules.memory.schemas import MessageSchema


class ConversationStore:
    def __init__(self) -> None:
        self._history: dict[str, list[MessageSchema]] = defaultdict(list)

    def get(self, session_id: str) -> list[MessageSchema]:
        return self._history[session_id]

    def append(self, session_id: str, role: Role, content: str) -> None:
        self._history[session_id].append(MessageSchema(role=role, content=content))

    def clear(self, session_id: str) -> None:
        self._history.pop(session_id, None)


class ProfileStore:
    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = defaultdict(dict)

    def get(self, user_id: str) -> dict[str, Any]:
        return self._data[user_id]

    def set(self, user_id: str, key: str, value: Any) -> None:
        self._data[user_id][key] = value


conversations = ConversationStore()
profiles = ProfileStore()
