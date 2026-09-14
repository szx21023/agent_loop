"""極簡 BM25（純標準函式庫）。用於：父頁面路由檢索 + 子樹 chunk 重排序。"""
import math
from collections import Counter


class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self._docs: list[tuple[str, Counter, int]] = []
        self.idf: dict[str, float] = {}
        self.avgdl = 0.0
        self._final = False

    def add(self, doc_id: str, tokens: list[str]) -> None:
        self._docs.append((doc_id, Counter(tokens), len(tokens)))

    def finalize(self) -> "BM25":
        n = len(self._docs)
        df: Counter = Counter()
        for _, c, _ in self._docs:
            df.update(c.keys())
        self.avgdl = (sum(l for _, _, l in self._docs) / n) if n else 0.0
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}
        self._final = True
        return self

    def search(self, query_tokens: list[str], top_k: int = 5) -> list[tuple[str, float]]:
        assert self._final, "call finalize() first"
        q = Counter(query_tokens)
        out: list[tuple[str, float]] = []
        for doc_id, c, length in self._docs:
            s = 0.0
            for t, _qf in q.items():
                f = c.get(t)
                if not f:
                    continue
                idf = self.idf.get(t, 0.0)
                s += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * length / (self.avgdl or 1)))
            if s > 0:
                out.append((doc_id, s))
        out.sort(key=lambda x: -x[1])
        return out[:top_k]
