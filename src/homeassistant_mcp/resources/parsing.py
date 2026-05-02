"""URI parsing and validation utilities for MCP resources.

This module provides utilities for parsing and validating Home Assistant resource URIs,
ensuring they conform to the hass:// scheme and expected patterns.
"""

import re
from typing import Any
from urllib.parse import parse_qs, urlparse


def parse_resource_uri(uri: str) -> dict[str, Any]:
    """Parse a resource URI into components.

    Extracts the scheme, resource type, resource ID, and query parameters from a
    Home Assistant resource URI.

    Args:
        uri: Resource URI to parse (e.g., "hass://entity/light.living_room")

    Returns:
        Dictionary with keys:
            - scheme: URI scheme (should be "hass")
            - resource_type: Type of resource (entity, area, device, services, history)
            - resource_id: Resource identifier (entity_id, area_id, device_id, or None)
            - query_params: Dictionary of query parameters (empty dict if none)

    Raises:
        ValueError: If URI format is invalid or scheme is not "hass://"

    Examples:
        >>> parse_resource_uri("hass://entity/light.living_room")
        {'scheme': 'hass', 'resource_type': 'entity', 'resource_id': 'light.living_room', 'query_params': {}}

        >>> parse_resource_uri("hass://entity/sensor.temp/history?hours=12&limit=50")
        {'scheme': 'hass', 'resource_type': 'history', 'resource_id': 'sensor.temp', 'query_params': {'hours': ['12'], 'limit': ['50']}}
    """
    if not uri:
        raise ValueError("URI cannot be empty")

    # Parse the URI
    parsed = urlparse(uri)

    # Validate scheme
    if parsed.scheme != "hass":
        raise ValueError(f"Invalid URI scheme: expected 'hass', got '{parsed.scheme}'")

    # For hass:// URIs, urlparse treats the first segment as netloc (hostname)
    # and the rest as path. We need to combine them.
    # Example: hass://entity/light.room -> netloc="entity", path="/light.room"
    # Example: hass://services -> netloc="services", path=""
    full_path = parsed.netloc
    if parsed.path:
        full_path += parsed.path

    if not full_path:
        raise ValueError("URI path cannot be empty")

    path_parts = full_path.strip("/").split("/")

    # Determine resource type and ID based on path structure
    if len(path_parts) == 1:
        # Could be static resource like "services" or resource type without ID
        if path_parts[0] == "services":
            return {
                "scheme": parsed.scheme,
                "resource_type": "services",
                "resource_id": None,
                "query_params": parse_qs(parsed.query) if parsed.query else {},
            }
        elif path_parts[0] in ("entity", "area", "device"):
            # Resource type without ID - this is invalid
            raise ValueError(f"Resource ID cannot be empty for {path_parts[0]} resources")
        else:
            raise ValueError(f"Invalid static resource: '{path_parts[0]}'")

    elif len(path_parts) == 2:
        # Resource with ID: entity/{id}, area/{id}, device/{id}
        resource_type = path_parts[0]
        resource_id = path_parts[1]

        if resource_type not in ("entity", "area", "device"):
            raise ValueError(
                f"Invalid resource type: '{resource_type}'. "
                "Expected 'entity', 'area', or 'device'"
            )

        if not resource_id:
            raise ValueError(f"Resource ID cannot be empty for {resource_type} resources")

        # Validate entity_id format if it's an entity resource
        if resource_type == "entity":
            validate_entity_id(resource_id)

        return {
            "scheme": parsed.scheme,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "query_params": parse_qs(parsed.query) if parsed.query else {},
        }

    elif len(path_parts) == 3:
        # History resource: entity/{id}/history
        if path_parts[0] != "entity":
            raise ValueError(
                f"Invalid resource path: '{full_path}'. "
                "Three-part paths must start with 'entity'"
            )

        if path_parts[2] != "history":
            raise ValueError(
                f"Invalid resource path: '{full_path}'. " "Third path segment must be 'history'"
            )

        resource_id = path_parts[1]
        if not resource_id:
            raise ValueError("Entity ID cannot be empty for history resources")

        # Validate entity_id format
        validate_entity_id(resource_id)

        return {
            "scheme": parsed.scheme,
            "resource_type": "history",
            "resource_id": resource_id,
            "query_params": parse_qs(parsed.query) if parsed.query else {},
        }

    else:
        raise ValueError(
            f"Invalid URI path: '{full_path}'. "
            "Expected format: entity/{{id}}, area/{{id}}, device/{{id}}, "
            "services, or entity/{{id}}/history"
        )


def validate_entity_id(entity_id: str) -> bool:
    """Validate entity_id format (domain.object_id).

    Home Assistant entity IDs must follow the pattern: {domain}.{object_id}
    where domain and object_id contain only lowercase letters, numbers, and underscores.

    Args:
        entity_id: Entity ID to validate (e.g., "light.living_room")

    Returns:
        True if valid

    Raises:
        ValueError: If entity_id format is invalid

    Examples:
        >>> validate_entity_id("light.living_room")
        True

        >>> validate_entity_id("sensor.temperature_1")
        True

        >>> validate_entity_id("invalid")  # doctest: +SKIP
        Traceback (most recent call last):
        ValueError: Invalid entity_id format: 'invalid'. Expected format: domain.object_id
    """
    if not entity_id:
        raise ValueError("Entity ID cannot be empty")

    # Entity ID pattern: domain.object_id
    # Domain and object_id can contain lowercase letters, numbers, and underscores
    pattern = r"^[a-z0-9_]+\.[a-z0-9_]+$"

    if not re.match(pattern, entity_id):
        raise ValueError(
            f"Invalid entity_id format: '{entity_id}'. "
            "Expected format: domain.object_id (lowercase letters, numbers, underscores only)"
        )

    return True


def validate_query_params(
    params: dict[str, list[str]],
    expected: dict[str, type],
) -> dict[str, Any]:
    """Validate and coerce query parameters to expected types.

    Takes query parameters from parse_qs (which returns lists of strings) and
    validates/coerces them to the expected types.

    Args:
        params: Query parameters from parse_qs (values are lists of strings)
        expected: Dictionary mapping parameter names to expected types

    Returns:
        Dictionary with validated and coerced parameters

    Raises:
        ValueError: If parameter types are invalid or coercion fails

    Examples:
        >>> validate_query_params(
        ...     {"hours": ["24"], "limit": ["100"]},
        ...     {"hours": int, "limit": int}
        ... )
        {'hours': 24, 'limit': 100}

        >>> validate_query_params(
        ...     {"hours": ["invalid"]},
        ...     {"hours": int}
        ... )  # doctest: +SKIP
        Traceback (most recent call last):
        ValueError: Invalid value for parameter 'hours': expected int, got 'invalid'
    """
    result: dict[str, Any] = {}

    for param_name, expected_type in expected.items():
        if param_name not in params:
            # Parameter not provided, skip it
            continue

        # Get the first value from the list (parse_qs returns lists)
        param_values = params[param_name]
        if not param_values:
            raise ValueError(f"Parameter '{param_name}' has no value")

        param_value = param_values[0]

        # Coerce to expected type
        try:
            if expected_type is int:
                result[param_name] = int(param_value)
            elif expected_type is float:
                result[param_name] = float(param_value)
            elif expected_type is bool:
                # Handle boolean conversion
                if param_value.lower() in ("true", "1", "yes"):
                    result[param_name] = True
                elif param_value.lower() in ("false", "0", "no"):
                    result[param_name] = False
                else:
                    raise ValueError(f"Invalid boolean value: '{param_value}'")
            elif expected_type is str:
                result[param_name] = param_value
            else:
                raise ValueError(f"Unsupported type: {expected_type}")
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid value for parameter '{param_name}': "
                f"expected {expected_type.__name__}, got '{param_value}'"
            ) from e

    return result
