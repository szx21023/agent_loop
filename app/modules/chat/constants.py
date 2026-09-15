"""chat 模組內部常數（僅 chat 用；跨 module 的角色等常數見 app/core/constants.py）。"""

# 未指定時的預設對話 session id
DEFAULT_SESSION_ID = "default"

# 迴圈耗盡但已累積部分證據時的回覆（無證據時用 core.llm 的 NO_ANSWER）
PARTIAL_ANSWER = "根據目前資料尚無法完整回答，請提供更多細節。"

# Anthropic Messages API 的判別字串（online tool-use 迴圈用）
TOOL_USE = "tool_use"  # stop_reason 與 content block type 共用此值
TEXT = "text"  # 文字 content block
TOOL_RESULT = "tool_result"  # 我方回填的工具結果 content block
