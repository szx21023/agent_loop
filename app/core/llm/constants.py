"""LLM/作答層常數。

SYSTEM_PROMPT、EVIDENCE_PREFIX、MAX_TOKENS 僅 core.llm 自己用（module-local）；
NO_ANSWER 因 chat 與 core.llm 都會用到（跨 module），放在此共用層供兩邊 import。
"""

# 單次 Messages API 回應的 token 上限
MAX_TOKENS = 4096

SYSTEM_PROMPT = (
    "你是一個企業知識庫 Agent。任務：\n"
    "1. 幫使用者找到相關資訊\n"
    "2. 可使用 search_graph / search_rag / get_document 等工具\n"
    "3. 必須根據工具回傳的證據回答，並在答案中標註來源節點 id\n"
    "4. 若證據不足以回答，直接回覆「查無相關資料」，絕對不要杜撰\n"
    "以繁體中文作答。"
)

# 找不到證據時的統一回覆（chat 與 offline_answer 共用）
NO_ANSWER = "查無相關資料。"

# offline 模式彙整證據時的前綴
EVIDENCE_PREFIX = "根據檢索到的資料：\n"
