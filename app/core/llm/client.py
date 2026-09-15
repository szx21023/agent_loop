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
from app.core.llm.constants import EVIDENCE_PREFIX, MAX_TOKENS, NO_ANSWER, SYSTEM_PROMPT
from app.core.schemas import ToolCallSchema
from app.core.tools.names import ToolName

log = logging.getLogger(__name__)


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
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

    # ── offline heuristic (no API key): graph → rag → answer ──
    def offline_decide(
        self, question: str, used_tools: set[str]
    ) -> tuple[Optional[ToolCallSchema], Optional[str]]:
        if ToolName.SEARCH_GRAPH not in used_tools:
            return ToolCallSchema(name=ToolName.SEARCH_GRAPH, args={"query": question}), None
        if ToolName.SEARCH_RAG not in used_tools:
            return ToolCallSchema(name=ToolName.SEARCH_RAG, args={"query": question}), None
        return None, None  # signal: caller should synthesize an answer from evidence

    @staticmethod
    def offline_answer(evidence: list[str]) -> str:
        if not evidence:
            return NO_ANSWER
        return EVIDENCE_PREFIX + "\n".join(f"- {item}" for item in evidence)


llm = LLM()
