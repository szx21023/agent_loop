"""Knowledge 模組服務：對 LLM 曝露的知識工具，import 時自我註冊到 REGISTRY。

- Knowledge Tools：search_rag（chunk 重排序）、search_graph（路由 + 圖譜展開）。
- Action Tool：get_document（依 id 取全文）。其餘外部動作（Notion/Gmail/GitHub…）待接。

工具內部失敗一律回 ToolResult(ok=False)，不拋例外，以免中斷 agent loop。
"""
from app.core.schemas import Source, ToolResult
from app.core.tools.base import Tool, register
from app.modules.knowledge.repository import get_retriever


def _search_rag(query: str, top_k: int = 8) -> ToolResult:
    r = get_retriever()
    if r is None:
        return ToolResult(name="search_rag", ok=False, error="index not loaded")
    routes = r.route(query, top_k=3)
    if not routes:
        return ToolResult(name="search_rag", ok=True, data=[], sources=[])
    node_ids = r.gather([nid for nid, _ in routes])
    chunks = r.rerank(query, node_ids, top_k=top_k)
    sources = [
        Source(tool="search_rag", ref=c["node_id"], snippet=c["chunk"])
        for c in chunks
    ]
    return ToolResult(name="search_rag", ok=True, data=[s.snippet for s in sources], sources=sources)


def _search_graph(query: str) -> ToolResult:
    r = get_retriever()
    if r is None:
        return ToolResult(name="search_graph", ok=False, error="index not loaded")
    routes = r.route(query, top_k=3)
    if not routes:
        return ToolResult(name="search_graph", ok=True, data=[], sources=[])
    node_ids = r.gather([nid for nid, _ in routes])
    sources = [
        Source(tool="search_graph", ref=nid, snippet=r.nodes[nid].get("summary", ""))
        for nid in node_ids if nid in r.nodes
    ]
    return ToolResult(name="search_graph", ok=True, data=[s.ref for s in sources], sources=sources)


def _get_document(doc_id: str) -> ToolResult:
    r = get_retriever()
    if r is not None and doc_id in r.nodes:
        n = r.nodes[doc_id]
        return ToolResult(name="get_document", ok=True, data=n.get("body") or n.get("summary", ""))
    return ToolResult(name="get_document", ok=False, error=f"unknown doc: {doc_id}")


register(Tool(
    name="search_rag",
    description="Vector/keyword search over documents (route -> traverse -> re-rank). Returns relevant chunks.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer", "default": 8},
        },
        "required": ["query"],
    },
    run=lambda query, top_k=8: _search_rag(query, top_k),
))

register(Tool(
    name="search_graph",
    description="Graph search: route to relevant parent pages, then expand the subtree and related nodes.",
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
    run=lambda query: _search_graph(query),
))

register(Tool(
    name="get_document",
    description="Fetch the full text of a document by its id.",
    parameters={
        "type": "object",
        "properties": {"doc_id": {"type": "string"}},
        "required": ["doc_id"],
    },
    run=lambda doc_id: _get_document(doc_id),
))
