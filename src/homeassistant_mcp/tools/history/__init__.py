"""Historical data tools for Home Assistant MCP server."""

from typing import Any

__all__ = [
    "register_history_tools",
]


def register_history_tools(mcp: Any, get_client: Any) -> None:
    """Register all historical data tools.

    Args:
        mcp: FastMCP server instance
        get_client: Function that returns the HomeAssistantClient instance
    """
    from .error_log import register_error_log_tool
    from .history import register_history_tool
    from .logbook import register_logbook_tool

    register_history_tool(mcp, get_client)
    register_logbook_tool(mcp, get_client)
    register_error_log_tool(mcp, get_client)
