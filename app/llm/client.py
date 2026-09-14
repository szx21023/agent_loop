"""Thin Claude wrapper with an offline fallback.

`decide()` returns either a tool call or a final answer. When no API key is set
(settings.offline), a deterministic heuristic drives the loop so the whole app
runs end-to-end without network access.
"""
from __future__ import annotations
from typing import Any, Optional

from app.config import settings
from app.schemas import Message, ToolCall


class LLM:
    def __init__(self) -> None:
        self._client = None
        if not settings.offline:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            except Exception:
                self._client = None  # fall back to offline mode

    @property
    def online(self) -> bool:
        return self._client is not None

    def decide(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        used_tools: set[str],
    ) -> tuple[Optional[ToolCall], Optional[str]]:
        """Return (tool_call, None) to act, or (None, answer) to finish."""
        if not self.online:
            return self._offline_decide(messages, used_tools)

        resp = self._client.messages.create(
            model=settings.model,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            tools=tools,
            messages=[{"role": m.role, "content": m.content}
                      for m in messages if m.role in ("user", "assistant")],
        )
        for block in resp.content:
            if getattr(block, "type", None) == "tool_use":
                return ToolCall(name=block.name, args=dict(block.input)), None
        text = "".join(getattr(b, "text", "") for b in resp.content)
        return None, text.strip() or "查無相關資料。"

    def _offline_decide(self, messages, used_tools):
        """Heuristic loop: graph → rag → answer."""
        question = next((m.content for m in reversed(messages) if m.role == "user"), "")
        if "search_graph" not in used_tools:
            return ToolCall(name="search_graph", args={"query": question}), None
        if "search_rag" not in used_tools:
            return ToolCall(name="search_rag", args={"query": question}), None
        return None, self._offline_answer(messages)

    @staticmethod
    def _offline_answer(messages) -> str:
        evidence = [m.content for m in messages if m.role == "assistant"
                    and m.content.startswith("[tool ")]
        if not evidence:
            return "查無相關資料。"
        return "根據檢索到的資料：\n" + "\n".join(f"- {e}" for e in evidence)


_SYSTEM_PROMPT = (
    "你是一個企業知識庫 Agent。任務：\n"
    "1. 幫使用者找到相關資訊\n"
    "2. 可使用 Graph / RAG / Tools\n"
    "3. 必須根據證據回答，資訊不足時不得杜撰\n"
    "4. 資訊足夠時，產生附來源的最終答案\n"
)

llm = LLM()
