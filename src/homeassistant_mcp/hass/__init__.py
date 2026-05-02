"""Home Assistant integration module."""

from homeassistant_mcp.exceptions import (
    AuthenticationError,
    ConnectionError,
    EntityNotFoundError,
    HomeAssistantError,
    ServiceCallError,
)

from .client import HomeAssistantClient

__all__ = [
    "HomeAssistantClient",
    "HomeAssistantError",
    "ConnectionError",
    "AuthenticationError",
    "EntityNotFoundError",
    "ServiceCallError",
]
