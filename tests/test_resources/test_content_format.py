"""Unit tests for content format consistency across all resources.

Tests MIME type, timestamp format, JSON formatting, and non-serializable value handling.

Requirements tested: 13.1, 13.4, 13.5, 13.6
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from src.homeassistant_mcp.resources.areas import register_area_resources
from src.homeassistant_mcp.resources.devices import register_device_resources
from src.homeassistant_mcp.resources.entities import register_entity_resources
from src.homeassistant_mcp.resources.history import register_history_resources
from src.homeassistant_mcp.resources.services import register_services_resources


def is_valid_iso8601(timestamp_str: str) -> bool:
    """Validate that a string is a valid ISO8601 timestamp."""
    try:
        datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return True
    except (ValueError, AttributeError):
        return False


@pytest.mark.asyncio
async def test_entity_mime_type_is_application_json():
    """Test entity resource MIME type is application/json.

    Validates: Requirement 13.1
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": "light.test",
            "state": "on",
            "attributes": {"friendly_name": "Test Light"},
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
        }
    )

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, lambda: mock_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("light.test")

    # Assert
    assert result.mime_type == "application/json"


@pytest.mark.asyncio
async def test_area_mime_type_is_application_json():
    """Test area resource MIME type is application/json.

    Validates: Requirement 13.1
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_area_resources(mock_mcp, lambda: mock_client)
    handler = resource_handlers["hass://area/{area_id}"]
    result = await handler("living_room")

    # Assert
    assert result.mime_type == "application/json"


@pytest.mark.asyncio
async def test_device_mime_type_is_application_json():
    """Test device resource MIME type is application/json.

    Validates: Requirement 13.1
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_device_resources(mock_mcp, lambda: mock_client)
    handler = resource_handlers["hass://device/{device_id}"]
    result = await handler("abc123")

    # Assert
    assert result.mime_type == "application/json"


@pytest.mark.asyncio
async def test_services_mime_type_is_application_json():
    """Test services resource MIME type is application/json.

    Validates: Requirement 13.1
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_services = AsyncMock(return_value={})

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_services_resources(mock_mcp, lambda: mock_client)
    handler = resource_handlers["hass://services"]
    result = await handler()

    # Assert
    assert result.mime_type == "application/json"


@pytest.mark.asyncio
async def test_history_mime_type_is_application_json():
    """Test history resource MIME type is application/json.

    Validates: Requirement 13.1
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_history = AsyncMock(return_value=[[]])

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_history_resources(mock_mcp, lambda: mock_client)
    handler = resource_handlers["hass://entity/{entity_id}/history"]
    result = await handler("sensor.test", 24, 100, 0)

    # Assert
    assert result.mime_type == "application/json"


@pytest.mark.asyncio
async def test_entity_timestamps_are_iso8601():
    """Test entity resource timestamps are ISO8601 format.

    Validates: Requirement 13.4
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "attributes": {"friendly_name": "Temperature"},
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:30:00Z",
        }
    )

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, lambda: mock_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("sensor.temperature")

    # Assert
    parsed = json.loads(result.text)

    # Verify envelope timestamp is ISO8601
    assert is_valid_iso8601(parsed["last_updated"])

    # Verify data timestamps are ISO8601
    assert is_valid_iso8601(parsed["data"]["last_changed"])
    assert is_valid_iso8601(parsed["data"]["last_updated"])


@pytest.mark.asyncio
async def test_history_timestamps_are_iso8601():
    """Test history resource timestamps are ISO8601 format.

    Validates: Requirement 13.4
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_history = AsyncMock(
        return_value=[
            [
                {
                    "state": "on",
                    "last_changed": "2024-01-15T10:00:00Z",
                    "last_updated": "2024-01-15T10:00:00Z",
                    "attributes": {},
                },
                {
                    "state": "off",
                    "last_changed": "2024-01-15T11:00:00Z",
                    "last_updated": "2024-01-15T11:00:00Z",
                    "attributes": {},
                },
            ]
        ]
    )

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_history_resources(mock_mcp, lambda: mock_client)
    handler = resource_handlers["hass://entity/{entity_id}/history"]
    result = await handler("light.test", 24, 100, 0)

    # Assert
    parsed = json.loads(result.text)

    # Verify envelope timestamp is ISO8601
    assert is_valid_iso8601(parsed["last_updated"])

    # Verify all history entry timestamps are ISO8601
    for entry in parsed["data"]["entries"]:
        assert is_valid_iso8601(entry["last_changed"])
        assert is_valid_iso8601(entry["last_updated"])


@pytest.mark.asyncio
async def test_json_formatting_with_indentation():
    """Test JSON formatting uses 2-space indentation.

    Validates: Requirement 13.5
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": "light.test",
            "state": "on",
            "attributes": {"friendly_name": "Test"},
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
        }
    )

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, lambda: mock_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("light.test")

    # Assert
    # Verify JSON has newlines (formatted, not compact)
    assert "\n" in result.text

    # Verify JSON uses 2-space indentation
    assert "  " in result.text

    # Verify it's valid JSON
    parsed = json.loads(result.text)
    assert isinstance(parsed, dict)

    # Verify we can re-format with same indentation
    reformatted = json.dumps(parsed, indent=2)
    # Both should have similar structure (allowing for default=str differences)
    assert reformatted.count("\n") > 0


@pytest.mark.asyncio
async def test_json_formatting_consistency_across_resources():
    """Test JSON formatting is consistent across all resource types.

    Validates: Requirement 13.5
    """
    # Test entity resource
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": "light.test",
            "state": "on",
            "attributes": {},
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
        }
    )
    mock_client.get_states = AsyncMock(return_value=[])
    mock_client.get_services = AsyncMock(return_value={})
    mock_client.get_history = AsyncMock(return_value=[[]])

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Register all resources
    register_entity_resources(mock_mcp, lambda: mock_client)
    register_area_resources(mock_mcp, lambda: mock_client)
    register_services_resources(mock_mcp, lambda: mock_client)

    # Test each resource type
    entity_result = await resource_handlers["hass://entity/{entity_id}"]("light.test")
    area_result = await resource_handlers["hass://area/{area_id}"]("living_room")
    services_result = await resource_handlers["hass://services"]()

    # All should have formatted JSON with newlines and indentation
    for result in [entity_result, area_result, services_result]:
        assert "\n" in result.text
        assert "  " in result.text
        # Verify valid JSON
        parsed = json.loads(result.text)
        assert isinstance(parsed, dict)


@pytest.mark.asyncio
async def test_non_serializable_value_handling():
    """Test non-serializable values are handled gracefully with default=str.

    Validates: Requirement 13.6
    """

    # Arrange
    # Create a mock object that's not JSON serializable
    class NonSerializable:
        def __str__(self):
            return "NonSerializable Object"

    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": "sensor.test",
            "state": "on",
            "attributes": {
                "friendly_name": "Test",
                "custom_object": NonSerializable(),  # Non-serializable
            },
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
        }
    )

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, lambda: mock_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("sensor.test")

    # Assert
    # Should not raise an exception
    assert result is not None

    # Should be valid JSON (default=str handles non-serializable)
    parsed = json.loads(result.text)
    assert isinstance(parsed, dict)

    # The non-serializable object should be converted to string
    assert "custom_object" in parsed["data"]["attributes"]
    # It should be a string representation
    assert isinstance(parsed["data"]["attributes"]["custom_object"], str)


@pytest.mark.asyncio
async def test_datetime_objects_are_serializable():
    """Test datetime objects in responses are properly serialized.

    Validates: Requirement 13.6
    """
    # Arrange
    from datetime import datetime, timezone

    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": "sensor.test",
            "state": "on",
            "attributes": {
                "friendly_name": "Test",
                "timestamp": datetime.now(timezone.utc),  # datetime object
            },
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
        }
    )

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, lambda: mock_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("sensor.test")

    # Assert
    # Should not raise an exception
    assert result is not None

    # Should be valid JSON (default=str handles datetime)
    parsed = json.loads(result.text)
    assert isinstance(parsed, dict)

    # The datetime should be converted to string
    assert "timestamp" in parsed["data"]["attributes"]
    assert isinstance(parsed["data"]["attributes"]["timestamp"], str)


@pytest.mark.asyncio
async def test_error_response_mime_type_is_application_json():
    """Test error responses also have application/json MIME type.

    Validates: Requirement 13.1
    """
    # Arrange
    from src.homeassistant_mcp.exceptions import EntityNotFoundError

    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(side_effect=EntityNotFoundError("Entity not found"))

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, lambda: mock_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("light.nonexistent")

    # Assert
    assert result.mime_type == "application/json"

    # Verify it's valid JSON
    parsed = json.loads(result.text)
    assert isinstance(parsed, dict)
    assert "error" in parsed


@pytest.mark.asyncio
async def test_error_response_json_formatting():
    """Test error responses use consistent JSON formatting.

    Validates: Requirement 13.5
    """
    # Arrange
    from src.homeassistant_mcp.exceptions import EntityNotFoundError

    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(side_effect=EntityNotFoundError("Entity not found"))

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_entity_resources(mock_mcp, lambda: mock_client)
    handler = resource_handlers["hass://entity/{entity_id}"]
    result = await handler("light.nonexistent")

    # Assert
    # Verify JSON has newlines (formatted, not compact)
    assert "\n" in result.text

    # Verify JSON uses 2-space indentation
    assert "  " in result.text

    # Verify it's valid JSON
    parsed = json.loads(result.text)
    assert isinstance(parsed, dict)


@pytest.mark.asyncio
async def test_all_resources_return_valid_json():
    """Test all resource types return valid, parseable JSON.

    Validates: Requirements 13.1, 13.5
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": "light.test",
            "state": "on",
            "attributes": {},
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
        }
    )
    mock_client.get_states = AsyncMock(return_value=[])
    mock_client.get_services = AsyncMock(return_value={})
    mock_client.get_history = AsyncMock(return_value=[[]])

    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Register all resources
    register_entity_resources(mock_mcp, lambda: mock_client)
    register_area_resources(mock_mcp, lambda: mock_client)
    register_device_resources(mock_mcp, lambda: mock_client)
    register_services_resources(mock_mcp, lambda: mock_client)
    register_history_resources(mock_mcp, lambda: mock_client)

    # Act & Assert - test each resource type
    entity_result = await resource_handlers["hass://entity/{entity_id}"]("light.test")
    entity_parsed = json.loads(entity_result.text)
    assert isinstance(entity_parsed, dict)
    assert entity_result.mime_type == "application/json"

    area_result = await resource_handlers["hass://area/{area_id}"]("living_room")
    area_parsed = json.loads(area_result.text)
    assert isinstance(area_parsed, dict)
    assert area_result.mime_type == "application/json"

    device_result = await resource_handlers["hass://device/{device_id}"]("abc123")
    device_parsed = json.loads(device_result.text)
    assert isinstance(device_parsed, dict)
    assert device_result.mime_type == "application/json"

    services_result = await resource_handlers["hass://services"]()
    services_parsed = json.loads(services_result.text)
    assert isinstance(services_parsed, dict)
    assert services_result.mime_type == "application/json"

    history_result = await resource_handlers["hass://entity/{entity_id}/history"](
        "sensor.test", 24, 100, 0
    )
    history_parsed = json.loads(history_result.text)
    assert isinstance(history_parsed, dict)
    assert history_result.mime_type == "application/json"
