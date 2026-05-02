"""Home Assistant MCP Server using FastMCP."""

from importlib.metadata import version as _get_version

from .exceptions import (
    AuthenticationError,
    CacheError,
    ConnectionError,
    EntityNotFoundError,
    HomeAssistantError,
    ServiceCallError,
    ValidationError,
)

__version__ = _get_version("homeassistant-mcp")

__all__ = [
    "AuthenticationError",
    "CacheError",
    "ConnectionError",
    "EntityNotFoundError",
    "HomeAssistantError",
    "ServiceCallError",
    "ValidationError",
]
