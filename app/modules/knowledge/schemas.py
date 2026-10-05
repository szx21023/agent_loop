"""knowledge 模組的資料型別。

工具的輸入/輸出目前直接複用 core 的共用型別（`ToolResultSchema` / `SourceSchema`）。

此外定義預建知識索引（`data/index.json`）的 schema：於載入時驗證，缺必要欄位就當場
報錯，而不是等檢索途中以 `node["..."]` 直接取值時才噴難解讀的 KeyError。
"""

from pydantic import BaseModel, Field


class IndexNodeSchema(BaseModel):
    """知識索引中的單一節點（頁面或附檔）。

    `type` / `title` 為必要；其餘結構欄位給預設值，容忍索引省略，也確保下游取值安全。
    """

    type: str
    title: str
    summary: str = ""
    parent: str | None = None
    children: list[str] = Field(default_factory=list)
    relations: list[tuple[str, str]] = Field(default_factory=list)  # (關係類型, 目標節點 id)
    chunks: list[str] = Field(default_factory=list)
    body: str | None = None
    department: str | None = None


class IndexSchema(BaseModel):
    """預建知識索引的頂層結構：node id → 節點。"""

    nodes: dict[str, IndexNodeSchema]
