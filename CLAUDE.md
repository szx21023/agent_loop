# CLAUDE.md

本檔案為本專案的開發規範，Claude 每次協作時皆會自動載入並遵循。
規範源自 `claude_instruction` 範本，並已對齊 agent-loop 的實際架構。

## 專案概述

- 後端服務，技術棧：Python 3.11+ + FastAPI。
- agent-loop 是一個以 **Agent Loop 模式**運作的企業知識庫助理：一個推理迴圈，
  由 LLM 決定下一步、呼叫工具、評估結果，反覆迭代直到能附來源作答。
- **雙模式**：設定 `anthropic_api_key` 時走 Anthropic 原生 tool-use 迴圈（online）；
  未設金鑰時走 `graph → rag → answer` 的確定性啟發式（offline），讓整個 app 無需網路也能端到端執行。
- 作答一律以工具回傳的證據為準、標註來源節點 id，證據不足時回「查無相關資料」，絕不杜撰。

## 常用指令

- 安裝執行相依：`pip install -r requirements.txt`
- 安裝開發相依（含 ruff/pytest/pre-commit）：`pip install -r requirements-dev.txt`
- 首次啟用 pre-commit：`pre-commit install`
- 啟動開發伺服器：`uvicorn app.main:app --reload`
- CLI 問答：`python -m scripts.ask "你的問題"`
- 跑測試：`pytest`
- lint + 格式檢查：`ruff check . && ruff format --check .`
- 自動修正：`ruff check --fix . && ruff format .`
- 手動對所有檔案跑 pre-commit：`pre-commit run --all-files`

## 專案架構

採**分層（layered）架構**：由外而內為 `Backend → Agent → 工具/檢索/記憶/LLM`，
依 `agent_loop.png` 的 Agent Loop 設計。

### 目錄結構（現況）
```
app/
├── main.py            # FastAPI 進入點：建立 app、掛 router、設定 logging
├── config.py          # pydantic-settings 設定（settings 單例；.offline 判斷是否有金鑰）
├── schemas.py         # 跨層共用 Pydantic 型別（ChatRequest/Response、Source、ToolCall、ToolResult…）
├── bm25.py            # BM25 檢索基礎元件
├── tokenizer.py       # 斷詞
├── api/               # Backend 層：HTTP 路由
│   └── routes.py      #   POST /ask、GET /health、DELETE /sessions/{id}
├── agent/             # Agent Loop 本體
│   └── loop.py        #   run_agent：online（原生 tool-use）/ offline（啟發式）兩條路徑
├── llm/               # LLM 封裝
│   └── client.py      #   Claude 封裝 + offline fallback + SYSTEM_PROMPT
├── tools/             # 工具層（註冊給 LLM 使用）
│   ├── base.py        #   Tool 抽象 + REGISTRY + tool_definitions()
│   ├── knowledge.py   #   Knowledge Tools：search_rag / search_graph
│   └── actions.py     #   Action Tools：get_document（其餘外部動作暫為 stub）
├── retrieval/         # 檢索層
│   └── retriever.py   #   Retriever：route（父頁面路由）→ gather（圖譜展開）→ rerank
└── memory/            # 記憶層
    ├── conversation.py#   對話歷史（per-session，目前 in-memory）
    └── profile.py     #   使用者 profile（目前 in-memory）

data/index.json        # 預建知識索引（Retriever 載入來源）
scripts/ask.py         # CLI 入口
tests/                 # 測試（conftest.py + 各層測試）
```
> 註：`memory` 與 `profile` 目前為記憶體內實作，接 SQL/Redis 後再抽換；
> Action Tools（Notion/Gmail/GitHub…）多為 stub，串接真實 API 與 auth 時再補。

### 架構規則
- **依賴方向單向**：`api → agent → (llm / tools / retrieval / memory)`，不可反向
  （工具/檢索/記憶不 import agent 或 api）
- **schema 與內部資料分離**：跨層一律傳 `schemas.py` 的 Pydantic 型別，不在層與層之間傳裸 dict
- **工具透過 REGISTRY 註冊**：新增工具在 `tools/` 內 `register(Tool(...))`，
  由 `tool_definitions()` 自動產生給 LLM 的定義；agent 只透過 `REGISTRY` 呼叫工具，不直接 import 個別工具函式
- **雙模式對稱**：新增能力時 online 與 offline 兩條路徑都要能運作（offline 至少回退為合理結果，不可拋例外中斷迴圈）
- **迴圈必須有界**：agent loop 一律以 `settings.max_loop_steps` 設上限，避免無窮迴圈
- **api（router）保持薄**：只做「參數驗證 → 呼叫 `run_agent` → 回傳」，不在 router 寫推理/檢索邏輯

## 程式風格

### 語言與工具鏈
- Python 3.11+；所有函式簽名必須有 type hints，不允許裸露的 `Any`
- 格式化與 lint 統一用 `ruff`（`ruff format` + `ruff check`），提交前必須零錯誤；ruff 規則設定見 `pyproject.toml` 的 `[tool.ruff]`
- lint/格式在 `git commit` 時由 pre-commit 自動執行並擋關（設定見 `.pre-commit-config.yaml`）；首次需執行 `pre-commit install`
- import 排序交給 ruff，不要手動調整；不使用相對 import，一律絕對 import（`from app...` / `from scripts...`）
- 資料模型一律用 Pydantic v2（`BaseModel`），不要用裸 dict 在層與層之間傳資料

### 命名慣例
- 變數/函式：snake_case；類別：PascalCase；常數：UPPER_SNAKE
- 變數名稱用完整單字，不要用縮寫或單一字元（用 `ticket` 不要用 `t`、用 `index` 不要用 `i`）；例外：慣用的 loop 計數短名視情況可接受，但有語意時一律用完整單字
- 布林值用 is_/has_/should_ 開頭（如 is_active）
- Pydantic schema 命名：輸入用 `XxxCreate` / `XxxUpdate` / `XxxRequest`，輸出用 `XxxRead` / `XxxResponse`
- 私有成員以單底線開頭 `_internal`

### FastAPI 慣例
- 路由函式只做「參數驗證 → 呼叫 agent/service → 回傳」，推理與檢索邏輯放 agent/tools/retrieval，不寫在 router 裡
- 依賴注入用 `Depends`，不要在函式內自行建立 client / session
- I/O（外部 API、DB）優先用 async；不要在 async 路由裡呼叫同步阻塞函式
- response_model 一定要明確指定，不要回傳未經 schema 過濾的物件
- 路徑用複數名詞（`/sessions`、`/sessions/{id}`），不要動詞化路徑（既有的 `/ask` 為問答動作端點，屬例外）

### 錯誤處理
- 業務錯誤拋自訂 exception，由統一的 exception handler 轉成 HTTP 回應；工具內部的失敗回傳 `ToolResult(ok=False, error=...)`，不要讓例外中斷 agent loop
- 不要在 router 直接 raise `HTTPException` 散落各處；不要吞例外（禁止空的 except）
- 禁止 print（`scripts/` 下的 CLI 輸出除外）；一律用 logging 模組，並帶上相關 context

### 結構與複雜度
- 函式超過 50 行或巢狀超過 3 層就拆分
- 優先 early return，避免深層 else 巢狀
- 設定值只從 config（pydantic-settings 的 `settings`）讀取，禁止散落的 os.getenv

### 註解
- 註解寫「為什麼」，不寫「做什麼」
- 公開函式與工具的 `run` 用 docstring 說明參數、回傳、可能拋的例外
- 不要為顯而易見的程式碼加註解
