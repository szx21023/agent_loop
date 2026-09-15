"""Knowledge 模組服務：對 LLM 曝露的知識工具，import 時自我註冊到 REGISTRY。

- Knowledge Tools：search_rag（chunk 重排序）、search_graph（路由 + 圖譜展開）。
- Action Tool：get_document（依 id 取全文）。其餘外部動作（Notion/Gmail/GitHub…）待接。

工具內部失敗一律回 ToolResultSchema(is_ok=False)，不拋例外，以免中斷 agent loop。
"""
from app.core.schemas import SourceSchema, ToolResultSchema
from app.core.tools.base import Tool, register
from app.modules.knowledge.repository import get_retriever


def _search_rag(query: str, top_k: int = 8) -> ToolResultSchema:
    retriever = get_retriever()
    if retriever is None:
        return ToolResultSchema(name="search_rag", is_ok=False, error="index not loaded")
    routes = retriever.route(query, top_k=3)
    if not routes:
        return ToolResultSchema(name="search_rag", is_ok=True, data=[], sources=[])
    node_ids = retriever.gather([nid for nid, _ in routes])
    chunks = retriever.rerank(query, node_ids, top_k=top_k)
    sources = [
        SourceSchema(tool="search_rag", ref=chunk["node_id"], snippet=chunk["chunk"])
        for chunk in chunks
    ]
    return ToolResultSchema(name="search_rag", is_ok=True, data=[source.snippet for source in sources], sources=sources)


def _search_graph(query: str) -> ToolResultSchema:
    retriever = get_retriever()
    if retriever is None:
        return ToolResultSchema(name="search_graph", is_ok=False, error="index not loaded")
    routes = retriever.route(query, top_k=3)
    if not routes:
        return ToolResultSchema(name="search_graph", is_ok=True, data=[], sources=[])
    node_ids = retriever.gather([nid for nid, _ in routes])
    sources = [
        SourceSchema(tool="search_graph", ref=nid, snippet=retriever.nodes[nid].get("summary", ""))
        for nid in node_ids if nid in retriever.nodes
    ]
    return ToolResultSchema(name="search_graph", is_ok=True, data=[source.ref for source in sources], sources=sources)


def _get_document(doc_id: str) -> ToolResultSchema:
    retriever = get_retriever()
    if retriever is not None and doc_id in retriever.nodes:
        node = retriever.nodes[doc_id]
        return ToolResultSchema(name="get_document", is_ok=True, data=node.get("body") or node.get("summary", ""))
    return ToolResultSchema(name="get_document", is_ok=False, error=f"unknown doc: {doc_id}")


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
