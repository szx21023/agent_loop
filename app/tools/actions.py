"""Action Tools: external side-effecting capabilities (Notion / Gmail / GitHub…).

Stubbed for now — they echo intent instead of performing real actions. Wire up
real API clients (and auth) when you're ready.
"""
from app.schemas import ToolResult
from app.tools.base import Tool, register


def _get_document(doc_id: str) -> ToolResult:
    from app.tools.knowledge import _DOCS
    if doc_id in _DOCS:
        return ToolResult(name="get_document", ok=True, data=_DOCS[doc_id][0])
    return ToolResult(name="get_document", ok=False, error=f"unknown doc: {doc_id}")


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

# Example placeholder for a real Action Tool. Uncomment + implement when ready.
# register(Tool(
#     name="create_notion_page",
#     description="Create a page in Notion.",
#     parameters={"type": "object", "properties": {
#         "title": {"type": "string"}, "content": {"type": "string"}},
#         "required": ["title"]},
#     run=lambda title, content="": ToolResult(
#         name="create_notion_page", ok=False, error="not implemented"),
# ))
