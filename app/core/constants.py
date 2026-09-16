"""跨功能共用常數（core 層，不依賴任何 module）。

Role 同時被 memory（MessageSchema.role）與 chat（建 Anthropic 訊息、寫入記憶）使用，
屬跨 module 的對話詞彙，故放在 core 供兩邊 import。
"""

from enum import StrEnum


class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
