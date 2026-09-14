"""Conversation memory — in-memory per-session history.

Swap this for a SQL/Redis-backed store to persist across restarts.
"""
from collections import defaultdict

from app.schemas import Message


class ConversationStore:
    def __init__(self) -> None:
        self._history: dict[str, list[Message]] = defaultdict(list)

    def get(self, session_id: str) -> list[Message]:
        return self._history[session_id]

    def append(self, session_id: str, role: str, content: str) -> None:
        self._history[session_id].append(Message(role=role, content=content))

    def clear(self, session_id: str) -> None:
        self._history.pop(session_id, None)


conversations = ConversationStore()
