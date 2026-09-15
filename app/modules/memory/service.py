"""memory 模組對外服務：其他模組（如 chat）一律透過此層存取記憶，
不直接碰 repository 的 store 實例。
"""
from typing import Any

from app.modules.memory.repository import conversations, profiles
from app.modules.memory.schemas import MessageSchema


def get_history(session_id: str) -> list[MessageSchema]:
    return conversations.get(session_id)


def append_message(session_id: str, role: str, content: str) -> None:
    conversations.append(session_id, role, content)


def clear_session(session_id: str) -> None:
    conversations.clear(session_id)


def get_profile(user_id: str) -> dict[str, Any]:
    return profiles.get(user_id)


def set_profile(user_id: str, key: str, value: Any) -> None:
    profiles.set(user_id, key, value)
