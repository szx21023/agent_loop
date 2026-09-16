"""Tool framework (core): the Tool abstraction and the REGISTRY.

`base` provides the Tool abstraction and the registry. Concrete tools live in
feature modules (e.g. app/modules/knowledge/service.py) and self-register on
import; wiring those imports at startup is the composition root's job — see
`app/bootstrap.py::register_tools()` (core stays feature-agnostic).
"""

from app.core.tools.base import REGISTRY, Tool, register, tool_definitions

__all__ = ["REGISTRY", "Tool", "register", "tool_definitions"]
