"""CLI: ask the agent a question.

阻塞式（預設）：   python -m scripts.ask "你的問題"
串流式（--stream）：python -m scripts.ask --stream "你的問題"

兩種模式跑同一個 agent loop，差別只在「怎麼把結果交還」：
  - 阻塞：等整輪跑完，答案一次印出（過程中畫面全黑）。
  - 串流：迴圈一有進展就即時輸出（進入下一步、呼叫工具、逐字冒出答案）。
"""

import sys
import time

from app.bootstrap import register_tools
from app.core.llm import llm
from app.core.schemas import SourceSchema
from app.modules.chat.constants import EventType
from app.modules.chat.schemas import ChatEventSchema
from app.modules.chat.service import run_agent, stream_agent

register_tools()  # 確保工具已註冊到 REGISTRY

DEFAULT_QUESTION = "A 專案之前有沒有 API timeout 問題？"
# 離線無真 token 串流，逐字加一點延遲才看得出「打字」效果；線上有真串流節奏，不加。
OFFLINE_DELTA_DELAY = 0.02


def _print_sources(sources: list[SourceSchema]) -> None:
    if not sources:
        return
    print("sources:")
    for source in sources:
        print(f"  - [{source.tool}] {source.ref}: {source.snippet[:60]}")


def _ask_blocking(question: str) -> None:
    print(f"\n[阻塞模式] Q: {question}\n")
    print("（等待整個 agent loop 跑完，過程中畫面不會有任何輸出…）")
    start = time.perf_counter()
    resp = run_agent(question)
    elapsed = time.perf_counter() - start
    print(f"\nA: {resp.answer}\n")
    print(f"(steps: {resp.steps}，等了 {elapsed:.1f}s 才一次看到整段答案)")
    _print_sources(resp.sources)


def _ask_streaming(question: str) -> None:
    print(f"\n[串流模式] Q: {question}\n")
    typewriter = not llm.is_online  # 線上靠真 delta 的節奏；離線才需人工延遲
    sources: list[SourceSchema] = []
    steps = 0
    for event in stream_agent(question):
        _render_event(event, typewriter)
        if event.type == EventType.DONE:
            sources = event.sources
            steps = event.step
    print(f"\n\n(steps: {steps}，答案邊生成邊浮現，不必等整輪跑完)")
    _print_sources(sources)


def _render_event(event: ChatEventSchema, typewriter: bool) -> None:
    if event.type == EventType.STEP:
        print(f"\n· 第 {event.step} 步")
    elif event.type == EventType.TOOL:
        print(f"  ⚙ 呼叫工具：{event.tool}")
    elif event.type == EventType.DELTA:
        print(event.text, end="", flush=True)
        if typewriter:
            time.sleep(OFFLINE_DELTA_DELAY)


def main() -> None:
    raw = sys.argv[1:]
    use_stream = "--stream" in raw
    question = " ".join(arg for arg in raw if arg != "--stream") or DEFAULT_QUESTION
    if use_stream:
        _ask_streaming(question)
    else:
        _ask_blocking(question)


if __name__ == "__main__":
    main()
