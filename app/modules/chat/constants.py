"""chat 模組內部常數（僅 chat 用；跨 module 的角色等常數見 app/core/constants.py）。"""

from enum import StrEnum

# 未指定時的預設對話 session id
DEFAULT_SESSION_ID = "default"

# 迴圈耗盡但已累積部分證據時的回覆（無證據時用 core.llm 的 NO_ANSWER）
PARTIAL_ANSWER = "根據目前資料尚無法完整回答，請提供更多細節。"

# Anthropic Messages API 的判別字串（online tool-use 迴圈用）
TOOL_USE = "tool_use"  # stop_reason 與 content block type 共用此值
TEXT = "text"  # 文字 content block
TOOL_RESULT = "tool_result"  # 我方回填的工具結果 content block
CONTENT_BLOCK_DELTA = "content_block_delta"  # 串流事件：某個 content block 有增量
TEXT_DELTA = "text_delta"  # 串流增量的型別：一段文字


class EventType(StrEnum):
    """stream_agent 逐步 yield 的事件類型（僅 chat 用；對照阻塞式的 run_agent）。"""

    STEP = "step"  # 進入新的一輪迴圈（呼叫模型 / 啟發式決策）
    TOOL = "tool"  # 正在呼叫某個工具
    DELTA = "delta"  # 一段答案文字，逐步串流（線上為真 token；離線為彙整後切片）
    DONE = "done"  # 收尾：完整答案 + 去重後來源 + 步數
