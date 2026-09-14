"""Knowledge Tools: RAG (chunk re-ranking) + Graph (route + traversal).

Backed by the real BM25 + graph Retriever ported from notion-kb-agent, loaded
from the prebuilt index at settings.index_path. If the index is missing, the
tools return an error result instead of crashing the loop.
"""
import json
import logging
from functools import lru_cache
from pathlib import Path

from app.config import settings
from app.retrieval.retriever import Retriever
from app.schemas import Source, ToolResult
from app.tools.base import Tool, register

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _retriever() -> Retriever | None:
    path = Path(settings.index_path)
    if not path.exists():
        log.warning("index not found at %s — knowledge tools will return empty", path)
        return None
    index = json.loads(path.read_text(encoding="utf-8"))
    return Retriever(index)


def _search_rag(query: str, top_k: int = 8) -> ToolResult:
    r = _retriever()
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
    r = _retriever()
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
