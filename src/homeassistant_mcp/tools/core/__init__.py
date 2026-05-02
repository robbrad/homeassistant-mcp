"""Core API tools for Home Assistant MCP server.

This module provides tools for accessing core Home Assistant API endpoints:
- API information (status, config, components)
- Event management (listing and firing events)
- Service management (listing and calling services)
"""

from collections.abc import Callable
from typing import Any

__all__ = [
    "register_api_info_tool",
    "register_events_control_tool",
    "register_services_control_tool",
]


def register_api_info_tool(mcp: Any, get_client: Callable[[], Any]) -> None:
    """Register the api_info tool.

    Args:
        mcp: FastMCP server instance
        get_client: Function that returns the HomeAssistantClient instance
    """
    from .api_info import register_tool

    register_tool(mcp, get_client)


def register_events_control_tool(mcp: Any, get_client: Callable[[], Any]) -> None:
    """Register the events_control tool.

    Args:
        mcp: FastMCP server instance
        get_client: Function that returns the HomeAssistantClient instance
    """
    from .events import register_tool

    register_tool(mcp, get_client)


def register_services_control_tool(mcp: Any, get_client: Callable[[], Any]) -> None:
    """Register the services_control tool.

    Args:
        mcp: FastMCP server instance
        get_client: Function that returns the HomeAssistantClient instance
    """
    from .services import register_tool

    register_tool(mcp, get_client)
