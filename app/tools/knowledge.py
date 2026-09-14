"""Knowledge Tools: RAG (vector) + Graph (relations).

These are stubs backed by a tiny in-memory corpus so the loop runs end-to-end.
Swap the internals for a real vector DB / graph DB later.
"""
from app.schemas import Source, ToolResult
from app.tools.base import Tool, register

# Toy corpus: (id, text, related_ids)
_DOCS = {
    "eng-inc-014": ("A 專案在 2024 Q3 出現 API timeout，root cause 是連線池耗盡，"
                    "已透過調大 pool size + retry 修復。", ["eng-doc-002"]),
    "eng-doc-002": ("連線池設定與重試策略指南。", ["eng-inc-014"]),
    "sec-pol-001": ("密碼政策：至少 12 碼，每 90 天更換，啟用 MFA。", []),
}


def _search_rag(query: str, top_k: int = 3) -> ToolResult:
    q = query.lower()
    hits = [
        (doc_id, text)
        for doc_id, (text, _rel) in _DOCS.items()
        if any(tok in text.lower() or tok in doc_id for tok in q.split())
    ][:top_k]
    sources = [Source(tool="search_rag", ref=doc_id, snippet=text) for doc_id, text in hits]
    return ToolResult(name="search_rag", ok=True, data=[s.snippet for s in sources], sources=sources)


def _search_graph(query: str) -> ToolResult:
    """Find a seed doc by keyword, then expand to related nodes."""
    q = query.lower()
    seeds = [d for d in _DOCS if any(tok in _DOCS[d][0].lower() or tok in d for tok in q.split())]
    seen: dict[str, str] = {}
    for seed in seeds:
        seen[seed] = _DOCS[seed][0]
        for rel in _DOCS[seed][1]:
            seen[rel] = _DOCS[rel][0]
    sources = [Source(tool="search_graph", ref=doc_id, snippet=text) for doc_id, text in seen.items()]
    return ToolResult(name="search_graph", ok=True, data=list(seen), sources=sources)


register(Tool(
    name="search_rag",
    description="Vector/keyword search over documents. Returns relevant snippets.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer", "default": 3},
        },
        "required": ["query"],
    },
    run=lambda query, top_k=3: _search_rag(query, top_k),
))

register(Tool(
    name="search_graph",
    description="Graph search: find a node by keyword and expand related nodes/edges.",
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
    run=lambda query: _search_graph(query),
))
