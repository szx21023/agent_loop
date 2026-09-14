"""Tool framework (core) + registration bootstrap.

`base` provides the Tool abstraction and the REGISTRY. The concrete tools live
in feature modules (e.g. app/modules/knowledge/service.py) and self-register on
import; `register_tools()` triggers those imports so the REGISTRY is populated
before the agent loop runs (called from main.py and scripts/ask.py).
"""
from app.core.tools.base import REGISTRY, Tool, register, tool_definitions

__all__ = ["REGISTRY", "Tool", "register", "tool_definitions", "register_tools"]


def register_tools() -> None:
    """Import feature tool modules for their register() side effects.

    Idempotent: Python caches modules, so repeated calls import once and the
    register() calls run only on first import.
    """
    import app.modules.knowledge.service  # noqa: F401  (registers knowledge/action tools)
