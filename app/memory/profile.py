"""User profile memory — long-lived per-user facts/preferences.

Stub: an in-memory dict. Back it with a real store (SQL/KV) later.
"""
from collections import defaultdict
from typing import Any


class ProfileStore:
    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = defaultdict(dict)

    def get(self, user_id: str) -> dict[str, Any]:
        return self._data[user_id]

    def set(self, user_id: str, key: str, value: Any) -> None:
        self._data[user_id][key] = value


profiles = ProfileStore()
