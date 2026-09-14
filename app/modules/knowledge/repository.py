"""知識檢索資料層：Retriever + 索引載入。

Retriever 對齊 notion_graph.png 第 3 節（Agent 查詢與搜尋流程）：
  父頁面路由（Top-k）→ 圖譜展開（Graph Traversal）→ 子樹 chunk 重排序。

父頁面（root，parent 為空）的路由文本 = 自身摘要 + 整個子樹（子頁/附檔）的標題與摘要彙整，
讓 Top-k 能把「API timeout」這種問題路由到正確部門，再靠 traversal + rerank 命中精確段落。

索引由 settings.index_path 載入（lru_cache 單例）；索引不存在時回 None，讓上層工具回傳
錯誤結果而非讓整個 agent loop 崩潰。
"""
import json
import logging
from functools import lru_cache
from pathlib import Path

from app.config import settings
from app.core.retrieval.bm25 import BM25
from app.core.retrieval.tokenizer import tokenize

log = logging.getLogger(__name__)


class Retriever:
    def __init__(self, index: dict):
        self.nodes: dict[str, dict] = index["nodes"]
        self.roots = [nid for nid, n in self.nodes.items()
                      if n["type"] == "page" and not n.get("parent")]

        self._parent_bm25 = BM25()
        for rid in self.roots:
            self._parent_bm25.add(rid, tokenize(self._routing_text(rid)))
        self._parent_bm25.finalize()

    # ── 路由文本：root 摘要 + 子樹彙整 ──
    def _routing_text(self, root_id: str) -> str:
        n = self.nodes[root_id]
        parts = [n["title"], n["summary"]]
        for did in self._descendants(root_id):
            d = self.nodes[did]
            parts.append(d["title"])
            parts.append(d["summary"])
        return " \n".join(parts)

    def _descendants(self, root_id: str) -> list[str]:
        out, stack = [], list(self.nodes[root_id]["children"])
        while stack:
            cur = stack.pop()
            if cur not in self.nodes:
                continue
            out.append(cur)
            stack.extend(self.nodes[cur]["children"])
        return out

    # ── 1. 父頁面路由 ──
    def route(self, question: str, top_k: int = 3) -> list[tuple[str, float]]:
        return self._parent_bm25.search(tokenize(question), top_k)

    # ── 2. 圖譜展開：選定父頁面的子樹 + 跨頁關聯節點 ──
    def gather(self, parent_ids: list[str]) -> list[str]:
        collected: set[str] = set()
        for pid in parent_ids:
            collected.add(pid)
            collected.update(self._descendants(pid))
        for nid in list(collected):
            for _rtype, target in self.nodes[nid]["relations"]:
                if target in self.nodes:
                    collected.add(target)
        return list(collected)

    # ── 3. 子樹 chunk 重排序 ──
    def rerank(self, question: str, node_ids: list[str], top_k: int = 8) -> list[dict]:
        bm = BM25()
        cmap: dict[str, tuple[str, int]] = {}
        for nid in node_ids:
            n = self.nodes[nid]
            for ci, ch in enumerate(n["chunks"]):
                cid = f"{nid}#{ci}"
                cmap[cid] = (nid, ci)
                bm.add(cid, tokenize(f"{n['title']} {ch}"))
        if not cmap:
            return []
        bm.finalize()
        results = []
        for cid, score in bm.search(tokenize(question), top_k):
            nid, ci = cmap[cid]
            n = self.nodes[nid]
            results.append({
                "node_id": nid, "title": n["title"], "type": n["type"],
                "department": n.get("department"), "chunk": n["chunks"][ci],
                "score": round(score, 3),
            })
        return results


@lru_cache(maxsize=1)
def get_retriever() -> Retriever | None:
    """載入預建索引並回傳 Retriever（單例）；索引不存在時回 None。"""
    path = Path(settings.index_path)
    if not path.exists():
        log.warning("index not found at %s — knowledge tools will return empty", path)
        return None
    index = json.loads(path.read_text(encoding="utf-8"))
    return Retriever(index)
