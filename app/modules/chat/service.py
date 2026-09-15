"""The Agent Loop (see agent_loop.png).

Two implementations behind one entrypoint:
  - online:  Anthropic-native tool-use loop (assistant tool_use → user tool_result),
             looping until the model stops requesting tools.
  - offline: deterministic heuristic (graph → rag → answer) so the app runs with
             no API key.

Both cap iterations with settings.max_loop_steps and return a ChatResponse.
"""
from __future__ import annotations
import json
import logging
from typing import Any

from app.config import settings
from app.core.llm import llm
from app.core.schemas import Source, ToolResult
from app.core.tools import REGISTRY, tool_definitions
from app.modules.chat.schemas import ChatResponse
from app.modules.memory import service as memory

log = logging.getLogger(__name__)


def run_agent(question: str, session_id: str = "default") -> ChatResponse:
    """Agent Loop 進入點：依是否有可用的 LLM client 分派 online/offline 路徑。

    Args:
        question: 使用者問題。
        session_id: 對話 session；用於讀寫對話歷史。
    Returns:
        ChatResponse（答案、去重後的來源、迴圈步數）。
    """
    if llm.is_online:
        return _run_online(question, session_id)
    return _run_offline(question, session_id)


# ── online: native Anthropic tool-use loop ──
def _run_online(question: str, session_id: str) -> ChatResponse:
    tools = tool_definitions()
    messages: list[dict[str, Any]] = _history_blocks(session_id)
    messages.append({"role": "user", "content": question})
    sources: list[Source] = []
    steps = 0

    for steps in range(1, settings.max_loop_steps + 1):
        resp = llm.create(messages, tools)
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason != "tool_use":
            answer = "".join(block.text for block in resp.content if block.type == "text").strip()
            answer = answer or "查無相關資料。"
            memory.append_message(session_id, "user", question)
            memory.append_message(session_id, "assistant", answer)
            return ChatResponse(answer=answer, sources=_dedup(sources), steps=steps)

        # execute every requested tool, return all results in one user turn
        tool_results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            result = _run_tool(block.name, dict(block.input))
            sources.extend(result.sources)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": _stringify(result.data if result.is_ok else f"error: {result.error}"),
                "is_error": not result.is_ok,
            })
        messages.append({"role": "user", "content": tool_results})

    # loop exhausted without a final answer
    fallback = "查無相關資料。" if not sources else "根據目前資料尚無法完整回答，請提供更多細節。"
    memory.append_message(session_id, "user", question)
    memory.append_message(session_id, "assistant", fallback)
    return ChatResponse(answer=fallback, sources=_dedup(sources), steps=steps)


# ── offline: heuristic graph → rag → answer ──
def _run_offline(question: str, session_id: str) -> ChatResponse:
    memory.append_message(session_id, "user", question)
    used: set[str] = set()
    sources: list[Source] = []
    evidence: list[str] = []
    steps = 0

    for steps in range(1, settings.max_loop_steps + 1):
        tool_call, _ = llm.offline_decide(question, used)
        if tool_call is None:
            break
        result = _run_tool(tool_call.name, tool_call.args)
        used.add(tool_call.name)
        sources.extend(result.sources)
        if result.is_ok and result.data:
            evidence.append(f"[{tool_call.name}] {_stringify(result.data)}")

    answer = llm.offline_answer(evidence)
    memory.append_message(session_id, "assistant", answer)
    return ChatResponse(answer=answer, sources=_dedup(sources), steps=steps)


def _run_tool(name: str, args: dict[str, Any]) -> ToolResult:
    tool = REGISTRY.get(name)
    if tool is None:
        return ToolResult(name=name, is_ok=False, error=f"unknown tool: {name}")
    try:
        return tool.run(**args)
    except Exception as exc:
        # 兌現「工具內部失敗不拋例外中斷 loop」的約定：記錄後轉成錯誤結果，
        # 讓迴圈能把 is_error 回饋給模型（online）或跳過（offline），而非讓 request 500。
        log.exception("tool %s failed with args %s", name, args)
        return ToolResult(name=name, is_ok=False, error=f"{type(exc).__name__}: {exc}")


def _history_blocks(session_id: str) -> list[dict[str, Any]]:
    """Prior turns as plain user/assistant text (tool blocks are per-run only)."""
    return [
        {"role": message.role, "content": message.content}
        for message in memory.get_history(session_id)
        if message.role in ("user", "assistant")
    ]


def _stringify(data: Any) -> str:
    if isinstance(data, str):
        return data
    return json.dumps(data, ensure_ascii=False)


def _dedup(sources: list[Source]) -> list[Source]:
    seen, out = set(), []
    for source in sources:
        key = (source.tool, source.ref)
        if key not in seen:
            seen.add(key)
            out.append(source)
    return out
