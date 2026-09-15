"""工具相關常數（core 層）。

工具名稱同時被 knowledge 模組（註冊/回傳）與 core.llm 的 offline 啟發式引用，
屬跨 module 共用，故上提到 core，讓兩邊都能合法 import（core 不可反向 import modules）。
"""
from enum import StrEnum


class ToolName(StrEnum):
    SEARCH_RAG = "search_rag"
    SEARCH_GRAPH = "search_graph"
    GET_DOCUMENT = "get_document"
