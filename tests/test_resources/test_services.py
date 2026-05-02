"""Unit tests for services resources.

Tests services resource handlers including successful fetches, response envelope structure,
services organized by domain, service descriptions, service parameters, and cache TTL hints.

Requirements tested: 3.9, 7.2, 7.3, 7.4, 7.5, 12.5
"""

import json
from unittest.mock import AsyncMock, Mock

import pytest

from src.homeassistant_mcp.resources.services import register_services_resources


@pytest.mark.asyncio
async def test_successful_services_resource_fetch():
    """Test successful services resource fetch with complete data.

    Validates: Requirements 3.9, 7.2
    """
    # Arrange
    mock_services_data = {
        "light": {
            "turn_on": {
                "description": "Turn on one or more lights",
                "fields": {
                    "entity_id": {
                        "description": "Entity ID of the light",
                        "required": True,
                    },
                    "brightness": {
                        "description": "Brightness value (0-255)",
                        "required": False,
                    },
                },
            },
            "turn_off": {
                "description": "Turn off one or more lights",
                "fields": {
                    "entity_id": {
                        "description": "Entity ID of the light",
                        "required": True,
                    },
                },
            },
        },
        "switch": {
            "turn_on": {
                "description": "Turn on a switch",
                "fields": {
                    "entity_id": {
                        "description": "Entity ID of the switch",
                        "required": True,
                    },
                },
            },
            "turn_off": {
                "description": "Turn off a switch",
                "fields": {
                    "entity_id": {
                        "description": "Entity ID of the switch",
                        "required": True,
                    },
                },
            },
        },
    }

    mock_client = AsyncMock()
    mock_client.get_services = AsyncMock(return_value=mock_services_data)

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_services_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://services"]
    result = await handler()

    # Assert
    assert result is not None
    assert str(result.uri) == "hass://services"
    assert result.mime_type == "application/json"

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify response envelope structure
    assert "uri" in parsed
    assert "type" in parsed
    assert "last_updated" in parsed
    assert "data" in parsed

    # Verify envelope values
    assert parsed["uri"] == "hass://services"
    assert parsed["type"] == "services"

    # Verify data contains services
    data = parsed["data"]
    assert "light" in data
    assert "switch" in data

    # Verify client was called correctly
    mock_client.get_services.assert_called_once()


@pytest.mark.asyncio
async def test_services_organized_by_domain():
    """Test services are organized by domain.

    Validates: Requirements 3.9, 7.2
    """
    # Arrange
    mock_services_data = {
        "climate": {
            "set_temperature": {
                "description": "Set target temperature",
                "fields": {},
            },
            "set_hvac_mode": {
                "description": "Set HVAC mode",
                "fields": {},
            },
        },
        "automation": {
            "trigger": {
                "description": "Trigger an automation",
                "fields": {},
            },
            "turn_on": {
                "description": "Enable an automation",
                "fields": {},
            },
        },
    }

    mock_client = AsyncMock()
    mock_client.get_services = AsyncMock(return_value=mock_services_data)

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_services_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://services"]
    result = await handler()

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify data is a dictionary organized by domain
    assert isinstance(data, dict)

    # Verify domains are present
    assert "climate" in data
    assert "automation" in data

    # Verify each domain contains services
    assert isinstance(data["climate"], dict)
    assert isinstance(data["automation"], dict)

    # Verify services are present under each domain
    assert "set_temperature" in data["climate"]
    assert "set_hvac_mode" in data["climate"]
    assert "trigger" in data["automation"]
    assert "turn_on" in data["automation"]


@pytest.mark.asyncio
async def test_service_descriptions_present():
    """Test service descriptions are present.

    Validates: Requirements 7.3
    """
    # Arrange
    mock_services_data = {
        "scene": {
            "turn_on": {
                "description": "Activate a scene",
                "fields": {
                    "entity_id": {
                        "description": "Entity ID of the scene",
                        "required": True,
                    },
                },
            },
        },
    }

    mock_client = AsyncMock()
    mock_client.get_services = AsyncMock(return_value=mock_services_data)

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_services_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://services"]
    result = await handler()

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify service has description
    scene_turn_on = data["scene"]["turn_on"]
    assert "description" in scene_turn_on
    assert scene_turn_on["description"] == "Activate a scene"
    assert isinstance(scene_turn_on["description"], str)
    assert len(scene_turn_on["description"]) > 0


@pytest.mark.asyncio
async def test_service_parameters_present():
    """Test service parameters are present.

    Validates: Requirements 7.4, 7.5
    """
    # Arrange
    mock_services_data = {
        "cover": {
            "set_position": {
                "description": "Set cover position",
                "fields": {
                    "entity_id": {
                        "description": "Entity ID of the cover",
                        "required": True,
                    },
                    "position": {
                        "description": "Position to set (0-100)",
                        "required": True,
                    },
                    "tilt_position": {
                        "description": "Tilt position (0-100)",
                        "required": False,
                    },
                },
            },
        },
    }

    mock_client = AsyncMock()
    mock_client.get_services = AsyncMock(return_value=mock_services_data)

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_services_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://services"]
    result = await handler()

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify service has fields
    cover_set_position = data["cover"]["set_position"]
    assert "fields" in cover_set_position
    assert isinstance(cover_set_position["fields"], dict)

    # Verify parameters are present
    fields = cover_set_position["fields"]
    assert "entity_id" in fields
    assert "position" in fields
    assert "tilt_position" in fields

    # Verify parameter details
    assert "description" in fields["entity_id"]
    assert "required" in fields["entity_id"]
    assert fields["entity_id"]["required"] is True

    assert "description" in fields["position"]
    assert "required" in fields["position"]
    assert fields["position"]["required"] is True

    assert "description" in fields["tilt_position"]
    assert "required" in fields["tilt_position"]
    assert fields["tilt_position"]["required"] is False


@pytest.mark.asyncio
async def test_cache_ttl_hint_presence():
    """Test cache TTL hint is present in response.

    Validates: Requirement 12.5
    """
    # Arrange
    mock_services_data = {
        "homeassistant": {
            "restart": {
                "description": "Restart Home Assistant",
                "fields": {},
            },
        },
    }

    mock_client = AsyncMock()
    mock_client.get_services = AsyncMock(return_value=mock_services_data)

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_services_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://services"]
    result = await handler()

    # Assert
    parsed = json.loads(result.text)

    # Verify cache_ttl is present
    assert "cache_ttl" in parsed, "cache_ttl hint missing from response"

    # Verify cache_ttl value is correct for services resources (300 seconds)
    assert parsed["cache_ttl"] == 300
    assert isinstance(parsed["cache_ttl"], int)


@pytest.mark.asyncio
async def test_response_envelope_structure():
    """Test response envelope has correct structure.

    Validates: Requirements 3.9
    """
    # Arrange
    mock_services_data = {
        "notify": {
            "send_message": {
                "description": "Send a notification",
                "fields": {},
            },
        },
    }

    mock_client = AsyncMock()
    mock_client.get_services = AsyncMock(return_value=mock_services_data)

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_services_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://services"]
    result = await handler()

    # Assert
    parsed = json.loads(result.text)

    # Verify envelope has exactly the required top-level fields
    assert "uri" in parsed
    assert "type" in parsed
    assert "last_updated" in parsed
    assert "data" in parsed

    # Verify types
    assert isinstance(parsed["uri"], str)
    assert isinstance(parsed["type"], str)
    assert isinstance(parsed["last_updated"], str)
    assert isinstance(parsed["data"], dict)

    # Verify URI matches request
    assert parsed["uri"] == "hass://services"

    # Verify type is correct
    assert parsed["type"] == "services"


@pytest.mark.asyncio
async def test_mime_type_is_application_json():
    """Test MIME type is application/json.

    Validates: Requirement 13.1
    """
    # Arrange
    mock_services_data = {
        "lock": {
            "lock": {
                "description": "Lock a lock",
                "fields": {},
            },
        },
    }

    mock_client = AsyncMock()
    mock_client.get_services = AsyncMock(return_value=mock_services_data)

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_services_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://services"]
    result = await handler()

    # Assert
    assert result.mime_type == "application/json"

    # Verify the response is valid JSON
    parsed = json.loads(result.text)
    assert isinstance(parsed, dict)


@pytest.mark.asyncio
async def test_empty_services_response():
    """Test services resource with no services available."""
    # Arrange
    mock_services_data = {}

    mock_client = AsyncMock()
    mock_client.get_services = AsyncMock(return_value=mock_services_data)

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_services_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://services"]
    result = await handler()

    # Assert
    parsed = json.loads(result.text)

    # Verify response envelope structure is still correct
    assert "uri" in parsed
    assert "type" in parsed
    assert "data" in parsed

    # Verify data is an empty dictionary
    assert parsed["data"] == {}
    assert isinstance(parsed["data"], dict)


@pytest.mark.asyncio
async def test_internal_error_handling():
    """Test internal error handling with sanitized error message."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_services = AsyncMock(
        side_effect=Exception("Internal error with sensitive data: token=abc123")
    )

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_services_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://services"]
    result = await handler()

    # Assert
    parsed = json.loads(result.text)

    # Verify error structure
    assert "error" in parsed
    assert parsed["error"]["code"] == "internal"

    # Verify error message is sanitized (no sensitive data leaked)
    assert "token" not in parsed["error"]["message"]
    assert "abc123" not in parsed["error"]["message"]
    assert parsed["error"]["message"] == "Internal server error while fetching services"
    assert parsed["error"]["uri"] == "hass://services"


@pytest.mark.asyncio
async def test_multiple_domains_with_multiple_services():
    """Test services resource with multiple domains and services."""
    # Arrange
    mock_services_data = {
        "light": {
            "turn_on": {"description": "Turn on lights", "fields": {}},
            "turn_off": {"description": "Turn off lights", "fields": {}},
            "toggle": {"description": "Toggle lights", "fields": {}},
        },
        "switch": {
            "turn_on": {"description": "Turn on switch", "fields": {}},
            "turn_off": {"description": "Turn off switch", "fields": {}},
        },
        "climate": {
            "set_temperature": {"description": "Set temperature", "fields": {}},
            "set_hvac_mode": {"description": "Set HVAC mode", "fields": {}},
            "set_fan_mode": {"description": "Set fan mode", "fields": {}},
        },
    }

    mock_client = AsyncMock()
    mock_client.get_services = AsyncMock(return_value=mock_services_data)

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_services_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://services"]
    result = await handler()

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify all domains are present
    assert "light" in data
    assert "switch" in data
    assert "climate" in data

    # Verify service counts
    assert len(data["light"]) == 3
    assert len(data["switch"]) == 2
    assert len(data["climate"]) == 3

    # Verify all services are present
    assert "turn_on" in data["light"]
    assert "turn_off" in data["light"]
    assert "toggle" in data["light"]

    assert "turn_on" in data["switch"]
    assert "turn_off" in data["switch"]

    assert "set_temperature" in data["climate"]
    assert "set_hvac_mode" in data["climate"]
    assert "set_fan_mode" in data["climate"]
