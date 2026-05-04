"""Unit tests for entity resources.

Tests entity resource handlers including successful fetches, error handling,
response envelope structure, and all required fields.

Requirements tested: 3.6, 4.1, 4.8, 12.4, 13.1
"""

import json
from unittest.mock import AsyncMock, Mock

import pytest

from src.homeassistant_mcp.exceptions import EntityNotFoundError
from src.homeassistant_mcp.resources.entities import register_entity_resources


@pytest.mark.asyncio
async def test_successful_entity_resource_fetch():
    """Test successful entity resource fetch with complete data.

    Validates: Requirements 3.6, 4.1
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "brightness": 255,
                "color_temp": 370,
            },
            "last_changed": "2024-01-15T10:25:00Z",
            "last_updated": "2024-01-15T10:30:00Z",
        }
    )

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("light.living_room")

    # Assert
    assert result is not None
    assert str(result.uri) == "hass://entity/light.living_room"
    assert result.mime_type == "application/json"

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify response envelope structure
    assert "uri" in parsed
    assert "type" in parsed
    assert "last_updated" in parsed
    assert "data" in parsed

    # Verify envelope values
    assert parsed["uri"] == "hass://entity/light.living_room"
    assert parsed["type"] == "entity"

    # Verify data contains all required fields
    data = parsed["data"]
    assert data["entity_id"] == "light.living_room"
    assert data["state"] == "on"
    assert data["domain"] == "light"
    assert data["friendly_name"] == "Living Room Light"

    # Verify client was called correctly
    mock_client.get_state.assert_called_once_with("light.living_room")


@pytest.mark.asyncio
async def test_entity_not_found_error():
    """Test entity not found error handling.

    Validates: Requirement 4.8
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        side_effect=EntityNotFoundError("Entity 'light.nonexistent' not found")
    )

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("light.nonexistent")

    # Assert
    assert result is not None
    assert result.mime_type == "application/json"

    # Parse the error response
    parsed = json.loads(result.text)

    # Verify error structure
    assert "error" in parsed
    assert "code" in parsed["error"]
    assert "message" in parsed["error"]
    assert "uri" in parsed["error"]

    # Verify error values
    assert parsed["error"]["code"] == "not_found"
    assert "light.nonexistent" in parsed["error"]["message"]
    assert parsed["error"]["uri"] == "hass://entity/light.nonexistent"


@pytest.mark.asyncio
async def test_response_envelope_structure():
    """Test response envelope has correct structure.

    Validates: Requirements 3.6, 4.1
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "attributes": {
                "friendly_name": "Temperature Sensor",
                "unit_of_measurement": "°C",
            },
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
        }
    )

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("sensor.temperature")

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
    assert parsed["uri"] == "hass://entity/sensor.temperature"

    # Verify type is correct
    assert parsed["type"] == "entity"


@pytest.mark.asyncio
async def test_all_required_fields_present_in_data():
    """Test all required fields are present in data section.

    Validates: Requirements 3.6, 4.1
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": "switch.kitchen",
            "state": "off",
            "attributes": {
                "friendly_name": "Kitchen Switch",
                "device_class": "outlet",
            },
            "last_changed": "2024-01-15T09:00:00Z",
            "last_updated": "2024-01-15T09:30:00Z",
        }
    )

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("switch.kitchen")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify all required fields are present
    required_fields = [
        "entity_id",
        "state",
        "attributes",
        "last_changed",
        "last_updated",
        "domain",
        "friendly_name",
    ]

    for field in required_fields:
        assert field in data, f"Required field '{field}' missing from data"

    # Verify field values
    assert data["entity_id"] == "switch.kitchen"
    assert data["state"] == "off"
    assert data["domain"] == "switch"
    assert data["friendly_name"] == "Kitchen Switch"
    assert isinstance(data["attributes"], dict)
    assert data["last_changed"] == "2024-01-15T09:00:00Z"
    assert data["last_updated"] == "2024-01-15T09:30:00Z"


@pytest.mark.asyncio
async def test_cache_ttl_hint_presence():
    """Test cache TTL hint is present in response.

    Validates: Requirement 12.4
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": "climate.living_room",
            "state": "heat",
            "attributes": {
                "friendly_name": "Living Room Thermostat",
                "temperature": 22,
            },
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
        }
    )

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("climate.living_room")

    # Assert
    parsed = json.loads(result.text)

    # Verify cache_ttl is present
    assert "cache_ttl" in parsed, "cache_ttl hint missing from response"

    # Verify cache_ttl value is correct for entity resources (5 seconds)
    assert parsed["cache_ttl"] == 5
    assert isinstance(parsed["cache_ttl"], int)


@pytest.mark.asyncio
async def test_mime_type_is_application_json():
    """Test MIME type is application/json.

    Validates: Requirement 13.1
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": "binary_sensor.door",
            "state": "on",
            "attributes": {
                "friendly_name": "Front Door",
                "device_class": "door",
            },
            "last_changed": "2024-01-15T08:00:00Z",
            "last_updated": "2024-01-15T08:00:00Z",
        }
    )

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("binary_sensor.door")

    # Assert
    assert result.mime_type == "application/json"

    # Verify the response is valid JSON
    parsed = json.loads(result.text)
    assert isinstance(parsed, dict)


@pytest.mark.asyncio
async def test_entity_with_missing_friendly_name():
    """Test entity resource when friendly_name is missing from attributes."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": "sensor.unknown",
            "state": "42",
            "attributes": {},  # No friendly_name
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
        }
    )

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("sensor.unknown")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Should fall back to entity_id when friendly_name is missing
    assert data["friendly_name"] == "sensor.unknown"


@pytest.mark.asyncio
async def test_entity_with_complex_attributes():
    """Test entity resource with complex nested attributes."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": "media_player.living_room",
            "state": "playing",
            "attributes": {
                "friendly_name": "Living Room Speaker",
                "volume_level": 0.5,
                "media_title": "Test Song",
                "media_artist": "Test Artist",
                "media_album": "Test Album",
                "supported_features": 152463,
            },
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
        }
    )

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("media_player.living_room")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify all attributes are preserved
    assert data["attributes"]["volume_level"] == 0.5
    assert data["attributes"]["media_title"] == "Test Song"
    assert data["attributes"]["media_artist"] == "Test Artist"
    assert data["attributes"]["supported_features"] == 152463


@pytest.mark.asyncio
async def test_internal_error_handling():
    """Test internal error handling with sanitized error message."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        side_effect=Exception("Internal error with sensitive data: token=abc123")
    )

    def get_client():
        return mock_client

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("light.test")

    # Assert
    parsed = json.loads(result.text)

    # Verify error structure
    assert "error" in parsed
    assert parsed["error"]["code"] == "internal"

    # Verify error message is sanitized (no sensitive data leaked)
    assert "token" not in parsed["error"]["message"]
    assert "abc123" not in parsed["error"]["message"]
    assert parsed["error"]["message"] == "Internal server error while fetching entity state"
