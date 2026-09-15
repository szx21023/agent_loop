"""Tool abstraction + a simple in-process registry.

A Tool exposes a name, a JSON-schema description (fed to the LLM as a tool
definition), and a `run(**args)` that returns a ToolResult.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

from app.core.schemas import ToolResult

RunFn = Callable[..., ToolResult]


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema for the args
    run: RunFn


REGISTRY: dict[str, Tool] = {}


def register(tool: Tool) -> Tool:
    if tool.name in REGISTRY:
        raise ValueError(f"duplicate tool: {tool.name}")
    REGISTRY[tool.name] = tool
    return tool


def tool_definitions() -> list[dict[str, Any]]:
    """Anthropic-style tool definitions for every registered tool."""
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.parameters,
        }
        for tool in REGISTRY.values()
    ]
