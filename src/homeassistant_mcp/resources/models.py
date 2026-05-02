"""Response envelope utilities and data models for MCP resources.

This module provides standardized response envelopes, error responses, and data models
for all MCP resources to ensure consistency across the resources layer.
"""

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ResourceType(str, Enum):
    """Resource type identifiers for response envelopes."""

    ENTITY = "entity"
    AREA = "area"
    DEVICE = "device"
    SERVICES = "services"
    HISTORY = "history"
    INDEX = "index"


class ResourceErrorCode(str, Enum):
    """Resource error codes for standardized error responses."""

    INVALID_URI = "invalid_uri"
    NOT_FOUND = "not_found"
    BAD_REQUEST = "bad_request"
    INTERNAL = "internal"


class EntitySummary(BaseModel):
    """Lightweight entity summary for area/device resources.

    This model provides only essential entity information to avoid large payloads
    when listing entities in areas or devices.
    """

    entity_id: str = Field(..., description="Entity ID (e.g., 'light.living_room')")
    state: str = Field(..., description="Current state value")
    domain: str = Field(..., description="Entity domain (e.g., 'light', 'sensor')")
    friendly_name: str = Field(..., description="Human-readable entity name")


class HistoryEntry(BaseModel):
    """Historical state entry for entity history resources."""

    state: str = Field(..., description="State value at this point in time")
    last_changed: str = Field(..., description="ISO8601 timestamp when state last changed")
    last_updated: str = Field(..., description="ISO8601 timestamp when state was last updated")
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Entity attributes at this point in time"
    )


def build_resource_envelope(
    uri: str,
    resource_type: ResourceType | str,
    data: dict[str, Any],
    cache_ttl: int | None = None,
) -> dict[str, Any]:
    """Build a standardized resource response envelope.

    All MCP resources return responses wrapped in this standardized envelope
    to ensure consistency and predictability for AI assistants.

    Args:
        uri: The resource URI that was requested
        resource_type: Type of resource (entity, area, device, services, history, index)
        data: Resource-specific data to include in the envelope
        cache_ttl: Optional cache TTL hint in seconds

    Returns:
        Standardized response envelope with uri, type, last_updated, data, and optional cache_ttl

    Example:
        >>> envelope = build_resource_envelope(
        ...     uri="hass://entity/light.living_room",
        ...     resource_type=ResourceType.ENTITY,
        ...     data={"entity_id": "light.living_room", "state": "on"},
        ...     cache_ttl=5
        ... )
        >>> envelope["uri"]
        'hass://entity/light.living_room'
        >>> envelope["type"]
        'entity'
    """
    # Convert ResourceType enum to string if needed
    type_str = resource_type.value if isinstance(resource_type, ResourceType) else resource_type

    envelope: dict[str, Any] = {
        "uri": uri,
        "type": type_str,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }

    # Add cache TTL hint if provided
    if cache_ttl is not None:
        envelope["cache_ttl"] = cache_ttl

    return envelope


def sanitize_error_message(message: str | None) -> str:
    """Sanitize error messages to prevent information leakage.

    Removes sensitive information from error messages including:
    - Internal URLs (http://, https://)
    - IP addresses and ports
    - Authentication tokens (Bearer, JWT, API keys)
    - File system paths (Windows and Unix)
    - Home Assistant configuration paths

    Args:
        message: The error message to sanitize

    Returns:
        Sanitized error message safe for client consumption

    Example:
        >>> sanitize_error_message("Failed to connect to http://192.168.1.100:8123")
        'Failed to connect to Home Assistant'
    """
    # Return message as-is if empty or None (don't replace with generic message)
    if not message:
        return message or ""

    # Convert to string if needed
    sanitized = str(message)

    # Remove URLs (http:// and https://) - replace with placeholder
    # Pattern matches: http://host:port/path or https://host:port/path
    sanitized = re.sub(
        r"https?://[^\s]+",
        "Home Assistant",
        sanitized,
    )

    # Remove IP addresses with ports
    sanitized = re.sub(
        r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b",
        "the server",
        sanitized,
    )

    # Remove standalone IP addresses
    sanitized = re.sub(
        r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        "the server",
        sanitized,
    )

    # Remove localhost references
    sanitized = re.sub(
        r"\blocalhost:\d+\b",
        "the server",
        sanitized,
    )
    sanitized = re.sub(
        r"\blocalhost\b",
        "the server",
        sanitized,
    )

    # Remove Bearer tokens
    sanitized = re.sub(
        r"Bearer\s+[A-Za-z0-9_\-\.]+",
        "",
        sanitized,
    )

    # Remove JWT tokens (start with eyJ)
    sanitized = re.sub(
        r"eyJ[A-Za-z0-9_\-\.]+",
        "",
        sanitized,
    )

    # Remove long alphanumeric strings that look like API keys (20+ chars)
    # But preserve entity IDs and common words
    sanitized = re.sub(
        r"\b[A-Za-z0-9]{20,}\b",
        "",
        sanitized,
    )

    # Remove Windows file paths
    sanitized = re.sub(
        r"[A-Z]:\\[^\s]+",
        "",
        sanitized,
    )

    # Remove Home Assistant configuration paths (/config/*)
    sanitized = re.sub(
        r"/config/[^\s]*",
        "",
        sanitized,
    )

    # Remove Unix absolute paths (but be careful not to remove /api/ etc in URLs already handled)
    sanitized = re.sub(
        r"/(?:home|root|usr|var|etc|opt)/[^\s]*",
        "",
        sanitized,
    )

    # Remove relative paths
    sanitized = re.sub(
        r"\./[^\s]+",
        "",
        sanitized,
    )

    # Remove the word "token" when it appears alone or with "with"
    sanitized = re.sub(r"\bwith\s+token\b", "", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\btoken\s*:\s*$", "", sanitized, flags=re.IGNORECASE)

    # Remove trailing prepositions
    sanitized = re.sub(r"\bwith\s+$", "", sanitized)
    sanitized = re.sub(r"\bfrom\s+$", "", sanitized)
    sanitized = re.sub(r"\bto\s+$", "", sanitized)
    sanitized = re.sub(r":\s*$", "", sanitized)  # Remove trailing colons

    # Clean up multiple spaces
    sanitized = re.sub(r"\s+", " ", sanitized)
    sanitized = sanitized.strip()

    return sanitized


def build_error_response(
    uri: str,
    error_code: ResourceErrorCode | str,
    message: str,
) -> dict[str, Any]:
    """Build a standardized error response with sanitized message.

    All MCP resource errors return responses in this standardized format
    to ensure consistent error handling for AI assistants. Error messages
    are automatically sanitized to prevent information leakage.

    Args:
        uri: The resource URI that caused the error
        error_code: Error code (invalid_uri, not_found, bad_request, internal)
        message: Human-readable error message (will be sanitized)

    Returns:
        Standardized error envelope with error code, sanitized message, and uri

    Example:
        >>> error = build_error_response(
        ...     uri="hass://entity/light.nonexistent",
        ...     error_code=ResourceErrorCode.NOT_FOUND,
        ...     message="Entity 'light.nonexistent' not found"
        ... )
        >>> error["error"]["code"]
        'not_found'
    """
    # Convert ResourceErrorCode enum to string if needed
    code_str = error_code.value if isinstance(error_code, ResourceErrorCode) else error_code

    # Sanitize the error message to prevent information leakage
    sanitized_message = sanitize_error_message(message)

    return {
        "error": {
            "code": code_str,
            "message": sanitized_message,
            "uri": uri,
        }
    }
