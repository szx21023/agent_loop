"""Claude wrapper with an offline fallback.

Online: exposes `stream()`, the agent loop's online entry — a thin pass-through
to the Anthropic **async** Messages streaming API, used by the native tool-use
loop (app/modules/chat/service.py). All network I/O is async (CLAUDE.md：所有 I/O
一律 async）。
Offline (no API key): `offline_decide()` / `offline_answer()` drive a
deterministic heuristic loop so the whole app runs end-to-end without network.
"""

from __future__ import annotations

import logging
from typing import Any

from app.config import settings
from app.core.llm.constants import EVIDENCE_PREFIX, MAX_TOKENS, NO_ANSWER, SYSTEM_PROMPT
from app.core.schemas import ToolCallSchema
from app.core.tools.constants import ToolName

log = logging.getLogger(__name__)


class LLM:
    def __init__(self) -> None:
        self._client = None
        if not settings.is_offline:
            try:
                import anthropic

                self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            except Exception:
                # 有金鑰卻建不出 client（套件缺失／版本不合…）是設定錯誤，不是正常
                # offline；記下來，否則會安靜降級成 offline 沒人察覺。
                log.exception(
                    "failed to init Anthropic client despite a key present; falling back to offline"
                )
                self._client = None

    @property
    def is_online(self) -> bool:
        return self._client is not None

    def stream(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]):
        """回傳 AsyncAnthropic 的串流 context manager（一輪 Messages API）。

        以 `async with llm.stream(...) as stream: async for event in stream` 消費，逐
        token 吐增量，讓 agent loop 在生成過程中就把進度往外送（見 chat.service.
        _stream_online）。`messages` 使用 Anthropic 原生 content blocks。僅 online 可用；
        offline 改串流彙整後的答案。
        """
        return self._client.messages.stream(
            model=settings.model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

    # ── offline heuristic (no API key): graph → rag → answer ──
    def offline_decide(
        self, question: str, used_tools: set[str]
    ) -> tuple[ToolCallSchema | None, str | None]:
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
