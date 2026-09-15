"""Claude wrapper with an offline fallback.

Online: exposes `create()`, a thin pass-through to the Anthropic Messages API
used by the agent loop's native tool-use path (app/modules/chat/service.py).
Offline (no API key): `offline_decide()` / `offline_answer()` drive a
deterministic heuristic loop so the whole app runs end-to-end without network.
"""
from __future__ import annotations
import logging
from typing import Any, Optional

from app.config import settings
from app.core.schemas import ToolCall

log = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一個企業知識庫 Agent。任務：\n"
    "1. 幫使用者找到相關資訊\n"
    "2. 可使用 search_graph / search_rag / get_document 等工具\n"
    "3. 必須根據工具回傳的證據回答，並在答案中標註來源節點 id\n"
    "4. 若證據不足以回答，直接回覆「查無相關資料」，絕對不要杜撰\n"
    "以繁體中文作答。"
)


class LLM:
    def __init__(self) -> None:
        self._client = None
        if not settings.is_offline:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            except Exception:
                # 有金鑰卻建不出 client（套件缺失／版本不合…）是設定錯誤，不是正常
                # offline；記下來，否則會安靜降級成 offline 沒人察覺。
                log.exception("failed to init Anthropic client despite a key present; falling back to offline")
                self._client = None

    @property
    def is_online(self) -> bool:
        return self._client is not None

    def create(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]):
        """One Anthropic Messages API turn. `messages` uses native content blocks."""
        return self._client.messages.create(
            model=settings.model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

    # ── offline heuristic (no API key): graph → rag → answer ──
    def offline_decide(
        self, question: str, used_tools: set[str]
    ) -> tuple[Optional[ToolCall], Optional[str]]:
        if "search_graph" not in used_tools:
            return ToolCall(name="search_graph", args={"query": question}), None
        if "search_rag" not in used_tools:
            return ToolCall(name="search_rag", args={"query": question}), None
        return None, None  # signal: caller should synthesize an answer from evidence

    @staticmethod
    def offline_answer(evidence: list[str]) -> str:
        if not evidence:
            return "查無相關資料。"
        return "根據檢索到的資料：\n" + "\n".join(f"- {item}" for item in evidence)


llm = LLM()
