"""The Agent Loop (see agent_loop.png).

  1. user asks → 2. assemble context + call LLM → 3. LLM decides next step
  4. need tool? no → 8 (answer) · yes → 5. execute tool
  6. add result to context → 7. evaluate → 8. goal met? no → loop · yes → answer
"""
from __future__ import annotations

from app.config import settings
from app.llm import llm
from app.memory import conversations
from app.schemas import ChatResponse, Source
from app.tools import REGISTRY, tool_definitions


def run_agent(question: str, session_id: str = "default") -> ChatResponse:
    conversations.append(session_id, "user", question)          # step 1
    messages = list(conversations.get(session_id))
    tools = tool_definitions()
    used: set[str] = set()
    sources: list[Source] = []
    steps = 0

    for steps in range(1, settings.max_loop_steps + 1):         # loop guard
        tool_call, answer = llm.decide(messages, tools, used)   # steps 2–4

        if answer is not None:                                  # step 8 → done
            conversations.append(session_id, "assistant", answer)
            return ChatResponse(answer=answer, sources=_dedup(sources), steps=steps)

        tool = REGISTRY.get(tool_call.name)                     # step 5
        if tool is None:
            messages.append(_note(f"[tool {tool_call.name}] error: unknown tool"))
            used.add(tool_call.name)
            continue

        result = tool.run(**tool_call.args)                     # step 6
        used.add(tool_call.name)
        sources.extend(result.sources)
        summary = result.data if result.ok else f"error: {result.error}"
        messages.append(_note(f"[tool {tool_call.name}] {summary}"))
        # step 7 (evaluate) is implicit: the next llm.decide sees the new context

    # loop exhausted without a final answer
    fallback = "查無相關資料。" if not sources else \
        "根據目前檢索到的資料，尚無法完整回答，請提供更多細節。"
    conversations.append(session_id, "assistant", fallback)
    return ChatResponse(answer=fallback, sources=_dedup(sources), steps=steps)


def _note(text: str):
    from app.schemas import Message
    return Message(role="assistant", content=text)


def _dedup(sources: list[Source]) -> list[Source]:
    seen, out = set(), []
    for s in sources:
        key = (s.tool, s.ref)
        if key not in seen:
            seen.add(key)
            out.append(s)
    return out
