"""Home Assistant MCP Server using FastMCP."""

from .exceptions import (
    AuthenticationError,
    CacheError,
    ConnectionError,
    EntityNotFoundError,
    HomeAssistantError,
    ServiceCallError,
    ValidationError,
)

__version__ = "2.0.0"

__all__ = [
    "AuthenticationError",
    "CacheError",
    "ConnectionError",
    "EntityNotFoundError",
    "HomeAssistantError",
    "ServiceCallError",
    "ValidationError",
]
