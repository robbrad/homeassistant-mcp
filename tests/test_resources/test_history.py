"""Unit tests for history resources.

Tests history resource handlers including successful fetches, query parameters,
error handling, response envelope structure, and pagination.

Requirements tested: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 8.1, 8.6, 8.7, 8.8, 12.6
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from src.homeassistant_mcp.exceptions import EntityNotFoundError
from src.homeassistant_mcp.resources.history import register_history_resources


@pytest.mark.asyncio
async def test_successful_history_resource_fetch():
    """Test successful history resource fetch with complete data.

    Validates: Requirements 8.1, 8.6
    """
    # Arrange
    mock_history_entries = [
        {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
            "attributes": {"unit_of_measurement": "°C"},
        },
        {
            "entity_id": "sensor.temperature",
            "state": "23.0",
            "last_changed": "2024-01-15T11:00:00Z",
            "last_updated": "2024-01-15T11:00:00Z",
            "attributes": {"unit_of_measurement": "°C"},
        },
    ]

    mock_client = AsyncMock()
    mock_client.get_history = AsyncMock(return_value=[mock_history_entries])

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
    register_history_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}/history"]
    result = await handler("sensor.temperature", hours=24, limit=100, offset=0)

    # Assert
    assert result is not None
    assert result.mime_type == "application/json"

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify response envelope structure
    assert "uri" in parsed
    assert "type" in parsed
    assert "last_updated" in parsed
    assert "data" in parsed

    # Verify envelope values
    assert parsed["type"] == "history"

    # Verify data contains all required fields
    data = parsed["data"]
    assert data["entity_id"] == "sensor.temperature"
    assert data["hours"] == 24
    assert data["limit"] == 100
    assert data["offset"] == 0
    assert "entries" in data
    assert "entry_count" in data
    assert "has_more" in data

    # Verify entries
    assert len(data["entries"]) == 2
    assert data["entry_count"] == 2
    assert data["has_more"] is False


@pytest.mark.asyncio
async def test_default_query_parameters():
    """Test history resource with default query parameters.

    Validates: Requirements 2.4, 2.5
    """
    # Arrange
    mock_history_entries = [
        {
            "entity_id": "light.living_room",
            "state": "on",
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
            "attributes": {},
        }
    ]

    mock_client = AsyncMock()
    mock_client.get_history = AsyncMock(return_value=[mock_history_entries])

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
    register_history_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}/history"]

    # Call without specifying query parameters (should use defaults)
    result = await handler("light.living_room")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify default values are used
    assert data["hours"] == 24  # Default hours
    assert data["limit"] == 100  # Default limit
    assert data["offset"] == 0  # Default offset


@pytest.mark.asyncio
async def test_custom_query_parameters():
    """Test history resource with custom query parameters.

    Validates: Requirements 2.1, 2.2, 2.3
    """
    # Arrange
    mock_history_entries = [
        {
            "entity_id": "switch.kitchen",
            "state": "off",
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
            "attributes": {},
        }
    ]

    mock_client = AsyncMock()
    mock_client.get_history = AsyncMock(return_value=[mock_history_entries])

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
    register_history_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}/history"]

    # Call with custom query parameters
    result = await handler("switch.kitchen", hours=12, limit=50, offset=10)

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify custom values are used
    assert data["hours"] == 12
    assert data["limit"] == 50
    assert data["offset"] == 10


@pytest.mark.asyncio
async def test_history_entry_structure():
    """Test history entry structure contains all required fields.

    Validates: Requirement 8.6
    """
    # Arrange
    mock_history_entries = [
        {
            "entity_id": "climate.bedroom",
            "state": "heat",
            "last_changed": "2024-01-15T09:00:00Z",
            "last_updated": "2024-01-15T09:30:00Z",
            "attributes": {
                "temperature": 22,
                "current_temperature": 21.5,
            },
        }
    ]

    mock_client = AsyncMock()
    mock_client.get_history = AsyncMock(return_value=[mock_history_entries])

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
    register_history_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}/history"]
    result = await handler("climate.bedroom")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify entries structure
    assert len(data["entries"]) == 1
    entry = data["entries"][0]

    # Verify all required fields are present
    required_fields = ["state", "last_changed", "last_updated", "attributes"]
    for field in required_fields:
        assert field in entry, f"Required field '{field}' missing from history entry"

    # Verify field values
    assert entry["state"] == "heat"
    assert entry["last_changed"] == "2024-01-15T09:00:00Z"
    assert entry["last_updated"] == "2024-01-15T09:30:00Z"
    assert isinstance(entry["attributes"], dict)


@pytest.mark.asyncio
async def test_empty_history_handling():
    """Test empty history handling returns empty entries array.

    Validates: Requirement 8.8
    """
    # Arrange
    mock_client = AsyncMock()
    # Return empty history (empty list for the entity)
    mock_client.get_history = AsyncMock(return_value=[[]])

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
    register_history_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}/history"]
    result = await handler("sensor.new_sensor")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify empty entries array is returned
    assert "entries" in data
    assert isinstance(data["entries"], list)
    assert len(data["entries"]) == 0
    assert data["entry_count"] == 0
    assert data["has_more"] is False


@pytest.mark.asyncio
async def test_entity_not_found_error():
    """Test entity not found error handling.

    Validates: Requirement 8.7
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_history = AsyncMock(
        side_effect=EntityNotFoundError("Entity 'sensor.nonexistent' not found")
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
    register_history_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}/history"]
    result = await handler("sensor.nonexistent")

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
    assert "sensor.nonexistent" in parsed["error"]["message"]


@pytest.mark.asyncio
async def test_pagination_with_offset():
    """Test pagination with offset parameter.

    Validates: Requirements 2.3, 8.3, 8.4
    """
    # Arrange - Generate 150 history entries
    mock_history_entries = []
    for i in range(150):
        hours_ago = i / 10
        timestamp = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
        mock_history_entries.append(
            {
                "entity_id": "sensor.test",
                "state": str(i),
                "last_changed": timestamp,
                "last_updated": timestamp,
                "attributes": {},
            }
        )

    mock_client = AsyncMock()
    mock_client.get_history = AsyncMock(return_value=[mock_history_entries])

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
    register_history_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}/history"]

    # Test with offset=50, limit=25
    result = await handler("sensor.test", hours=24, limit=25, offset=50)

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify pagination
    assert data["offset"] == 50
    assert data["limit"] == 25
    assert len(data["entries"]) == 25
    assert data["entry_count"] == 25

    # Verify entries are from the correct offset
    # First entry should be the 51st entry (index 50)
    assert data["entries"][0]["state"] == "50"


@pytest.mark.asyncio
async def test_has_more_indicator():
    """Test has_more indicator when more entries are available.

    Validates: Requirements 8.4
    """
    # Arrange - Generate 150 history entries
    mock_history_entries = []
    for i in range(150):
        hours_ago = i / 10
        timestamp = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
        mock_history_entries.append(
            {
                "entity_id": "sensor.test",
                "state": str(i),
                "last_changed": timestamp,
                "last_updated": timestamp,
                "attributes": {},
            }
        )

    mock_client = AsyncMock()
    mock_client.get_history = AsyncMock(return_value=[mock_history_entries])

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
    register_history_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}/history"]

    # Test with limit=100, offset=0 (should have more)
    result = await handler("sensor.test", hours=24, limit=100, offset=0)

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify has_more is True (150 total, showing 100)
    assert data["has_more"] is True
    assert data["entry_count"] == 100

    # Test with limit=100, offset=100 (should not have more)
    result2 = await handler("sensor.test", hours=24, limit=100, offset=100)
    parsed2 = json.loads(result2.text)
    data2 = parsed2["data"]

    # Verify has_more is False (showing last 50)
    assert data2["has_more"] is False
    assert data2["entry_count"] == 50


@pytest.mark.asyncio
async def test_cache_ttl_hint_presence():
    """Test cache TTL hint is present in response.

    Validates: Requirement 12.6
    """
    # Arrange
    mock_history_entries = [
        {
            "entity_id": "light.test",
            "state": "on",
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
            "attributes": {},
        }
    ]

    mock_client = AsyncMock()
    mock_client.get_history = AsyncMock(return_value=[mock_history_entries])

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
    register_history_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}/history"]
    result = await handler("light.test")

    # Assert
    parsed = json.loads(result.text)

    # Verify cache_ttl is present
    assert "cache_ttl" in parsed, "cache_ttl hint missing from response"

    # Verify cache_ttl value is correct for history resources (60 seconds)
    assert parsed["cache_ttl"] == 60
    assert isinstance(parsed["cache_ttl"], int)


@pytest.mark.asyncio
async def test_internal_error_handling():
    """Test internal error handling with sanitized error message."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_history = AsyncMock(
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
    register_history_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}/history"]
    result = await handler("sensor.test")

    # Assert
    parsed = json.loads(result.text)

    # Verify error structure
    assert "error" in parsed
    assert parsed["error"]["code"] == "internal"

    # Verify error message is sanitized (no sensitive data leaked)
    assert "token" not in parsed["error"]["message"]
    assert "abc123" not in parsed["error"]["message"]
    assert parsed["error"]["message"] == "Internal server error while fetching entity history"


@pytest.mark.asyncio
async def test_history_with_no_data_returned():
    """Test history when Home Assistant returns empty list."""
    # Arrange
    mock_client = AsyncMock()
    # Return completely empty list (no entity data at all)
    mock_client.get_history = AsyncMock(return_value=[])

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
    register_history_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://entity/{entity_id}/history"]
    result = await handler("sensor.test")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify empty entries array is returned
    assert "entries" in data
    assert isinstance(data["entries"], list)
    assert len(data["entries"]) == 0
    assert data["entry_count"] == 0
    assert data["has_more"] is False
