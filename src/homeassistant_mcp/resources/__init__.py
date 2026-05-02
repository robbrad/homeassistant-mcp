"""MCP Resources for Home Assistant.

This module provides MCP resource handlers for read-only access to Home Assistant
data through URIs. Resources allow AI assistants to access entity states,
area information, device details, service listings, and historical data without
invoking tools.

Resource URI Patterns:
- hass://entity/{entity_id} - Entity state and attributes
- hass://area/{area_id} - Area information and associated entities
- hass://device/{device_id} - Device information and associated entities
- hass://services - All available services organized by domain
- hass://entity/{entity_id}/history - Entity historical state changes with query parameters
"""

from collections.abc import Callable
from typing import Any

from .areas import register_area_resources
from .devices import register_device_resources
from .entities import register_entity_resources
from .history import register_history_resources
from .services import register_services_resources

__all__ = [
    "register_entity_resources",
    "register_area_resources",
    "register_device_resources",
    "register_services_resources",
    "register_history_resources",
    "register_all_resources",
]


def register_all_resources(mcp: Any, get_client: Callable[[], Any]) -> None:
    """Register all MCP resources with the server.

    Args:
        mcp: The FastMCP server instance
        get_client: Function that returns the HomeAssistantClient instance
    """
    register_entity_resources(mcp, get_client)
    register_area_resources(mcp, get_client)
    register_device_resources(mcp, get_client)
    register_services_resources(mcp, get_client)
    register_history_resources(mcp, get_client)
