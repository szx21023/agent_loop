"""Tool registry — import tool modules so they self-register."""
from app.tools.base import REGISTRY, Tool, tool_definitions
from app.tools import knowledge, actions  # noqa: F401  (registers tools on import)

__all__ = ["REGISTRY", "Tool", "tool_definitions"]
