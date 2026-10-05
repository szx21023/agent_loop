"""The Agent Loop (see agent_loop.png).

單一來源的串流實作，兩種模式：
  - online:  Anthropic-native tool-use loop (assistant tool_use → user tool_result)，
             looping until the model stops requesting tools。
  - offline: deterministic heuristic (graph → rag → answer)，讓 app 無金鑰也能跑。

阻塞式的 run_agent 不再自成一套迴圈，而是「消費 stream_agent 的事件、摺疊成一次性
結果」——確保阻塞與串流兩種呼叫方式行為必然一致（過去各寫一份迴圈，收尾／memory
邏輯容易改漏）。兩種模式都以 settings.max_loop_steps 設迴圈上限。
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import Any

from app.config import settings
from app.core.constants import Role
from app.core.llm import llm
from app.core.llm.constants import NO_ANSWER
from app.core.schemas import SourceSchema, ToolResultSchema
from app.core.tools import REGISTRY, tool_definitions
from app.modules.chat.constants import (
    CONTENT_BLOCK_DELTA,
    DEFAULT_SESSION_ID,
    PARTIAL_ANSWER,
    TEXT_DELTA,
    TOOL_RESULT,
    TOOL_USE,
    EventType,
)
from app.modules.chat.schemas import ChatEventSchema, ChatResponseSchema
from app.modules.memory import service as memory

log = logging.getLogger(__name__)


def run_agent(question: str, session_id: str = DEFAULT_SESSION_ID) -> ChatResponseSchema:
    """Agent Loop 的阻塞式進入點：消費串流事件並摺疊成一次性結果。

    流程本身只存在於 stream_agent（online/offline）；此處只取收尾的 DONE 事件
    （已含答案、去重來源、步數），因此阻塞與串流結果保證一致。

    Args:
        question: 使用者問題。
        session_id: 對話 session；用於讀寫對話歷史。
    Returns:
        ChatResponseSchema（答案、去重後的來源、迴圈步數）。
    """
    answer, sources, steps = NO_ANSWER, [], 0
    for event in stream_agent(question, session_id):
        if event.type == EventType.DONE:
            answer, sources, steps = event.text, event.sources, event.step
    return ChatResponseSchema(answer=answer, sources=sources, steps=steps)


def stream_agent(question: str, session_id: str = DEFAULT_SESSION_ID) -> Iterator[ChatEventSchema]:
    """Agent Loop：逐步 yield 事件（step / tool / delta / done）。

    迴圈一有進展（進入下一步、呼叫工具、生出一段文字）就立刻 yield，呼叫端不必等
    整輪跑完。online 走 Anthropic 真串流；offline 沒有真 token 串流，改把彙整後的
    答案切片吐出（維持雙模式對稱，讓無金鑰也能端到端跑）。

    Args:
        question: 使用者問題。
        session_id: 對話 session；用於讀寫對話歷史。
    Yields:
        ChatEventSchema，型別見 EventType。
    """
    if llm.is_online:
        yield from _stream_online(question, session_id)
    else:
        yield from _stream_offline(question, session_id)


# ── online: native Anthropic tool-use loop ──
def _stream_online(question: str, session_id: str) -> Iterator[ChatEventSchema]:
    tools = tool_definitions()
    messages: list[dict[str, Any]] = _history_blocks(session_id)
    messages.append({"role": Role.USER, "content": question})
    sources: list[SourceSchema] = []
    answer_parts: list[str] = []
    steps = 0

    for steps in range(1, settings.max_loop_steps + 1):
        yield ChatEventSchema(type=EventType.STEP, step=steps)
        # 只保留當輪文字：最終答案僅取收尾那一輪，避免把中間輪的敘述一起串進答案、
        # 污染 memory 與 DONE.text。逐 token 的畫面串流不受影響。
        answer_parts.clear()
        with llm.stream(messages, tools) as stream:
            for event in stream:
                if event.type == CONTENT_BLOCK_DELTA and event.delta.type == TEXT_DELTA:
                    answer_parts.append(event.delta.text)
                    yield ChatEventSchema(type=EventType.DELTA, text=event.delta.text)
            final = stream.get_final_message()
        messages.append({"role": Role.ASSISTANT, "content": final.content})

        if final.stop_reason != TOOL_USE:
            answer = "".join(answer_parts).strip() or NO_ANSWER
            memory.append_message(session_id, Role.USER, question)
            yield _done(session_id, answer, sources, steps)
            return

        tool_results = []
        for block in final.content:
            if block.type != TOOL_USE:
                continue
            yield ChatEventSchema(type=EventType.TOOL, tool=block.name)
            result = _run_tool(block.name, dict(block.input))
            sources.extend(result.sources)
            tool_results.append(
                {
                    "type": TOOL_RESULT,
                    "tool_use_id": block.id,
                    "content": _stringify(
                        result.data if result.is_ok else f"error: {result.error}"
                    ),
                    "is_error": not result.is_ok,
                }
            )
        messages.append({"role": Role.USER, "content": tool_results})

    # loop exhausted without a final answer
    fallback = NO_ANSWER if not sources else PARTIAL_ANSWER
    memory.append_message(session_id, Role.USER, question)
    yield _done(session_id, fallback, sources, steps)


# ── offline: heuristic graph → rag → answer ──
def _stream_offline(question: str, session_id: str) -> Iterator[ChatEventSchema]:
    memory.append_message(session_id, Role.USER, question)
    used: set[str] = set()
    sources: list[SourceSchema] = []
    evidence: list[str] = []
    steps = 0

    for steps in range(1, settings.max_loop_steps + 1):
        yield ChatEventSchema(type=EventType.STEP, step=steps)
        tool_call, _ = llm.offline_decide(question, used)
        if tool_call is None:
            break
        yield ChatEventSchema(type=EventType.TOOL, tool=tool_call.name)
        result = _run_tool(tool_call.name, tool_call.args)
        used.add(tool_call.name)
        sources.extend(result.sources)
        if result.is_ok and result.data:
            evidence.append(f"[{tool_call.name}] {_stringify(result.data)}")

    answer = llm.offline_answer(evidence)
    # 離線沒有真 token 串流：逐字吐出彙整後的答案，讓 CLI 呈現「打字」效果
    for char in answer:
        yield ChatEventSchema(type=EventType.DELTA, text=char)
    yield _done(session_id, answer, sources, steps)


def _done(session_id: str, answer: str, sources: list[SourceSchema], step: int) -> ChatEventSchema:
    """收尾：寫入 assistant 回覆並回傳 DONE 事件（來源去重）。

    online/offline 收尾共用；兩者都已在各自路徑把 user 問題寫進 memory，故此處只補
    assistant 這一筆，避免重複。
    """
    memory.append_message(session_id, Role.ASSISTANT, answer)
    return ChatEventSchema(type=EventType.DONE, text=answer, sources=_dedup(sources), step=step)


def _run_tool(name: str, args: dict[str, Any]) -> ToolResultSchema:
    tool = REGISTRY.get(name)
    if tool is None:
        return ToolResultSchema(name=name, is_ok=False, error=f"unknown tool: {name}")
    try:
        return tool.run(**args)
    except Exception as exc:
        # 兌現「工具內部失敗不拋例外中斷 loop」的約定：記錄後轉成錯誤結果，
        # 讓迴圈能把 is_error 回饋給模型（online）或跳過（offline），而非讓 request 500。
        log.exception("tool %s failed with args %s", name, args)
        return ToolResultSchema(name=name, is_ok=False, error=f"{type(exc).__name__}: {exc}")


def _history_blocks(session_id: str) -> list[dict[str, Any]]:
    """Prior turns as plain user/assistant text (tool blocks are per-run only)."""
    return [
        {"role": message.role, "content": message.content}
        for message in memory.get_history(session_id)
        if message.role in (Role.USER, Role.ASSISTANT)
    ]


def _stringify(data: Any) -> str:
    if isinstance(data, str):
        return data
    return json.dumps(data, ensure_ascii=False)


def _dedup(sources: list[SourceSchema]) -> list[SourceSchema]:
    seen, out = set(), []
    for source in sources:
        key = (source.tool, source.ref)
        if key not in seen:
            seen.add(key)
            out.append(source)
    return out
