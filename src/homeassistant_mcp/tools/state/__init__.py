"""State management tools for Home Assistant MCP server."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

__all__ = ["register_state_tools"]


def register_state_tools(mcp: "Any", get_client: "Callable") -> None:
    """Register all state management tools.

    Args:
        mcp: FastMCP server instance
        get_client: Function to get the HomeAssistantClient instance
    """
    from .states import register_states_control_tool

    register_states_control_tool(mcp, get_client)
