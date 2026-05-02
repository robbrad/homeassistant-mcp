"""Unit tests for area resources.

Tests area resource handlers including successful fetches, lightweight entity summaries,
truncation behavior, and error handling.

Requirements tested: 3.7, 5.6, 12.7, 20.1, 20.2, 20.3, 20.4
"""

import json
from unittest.mock import AsyncMock, Mock

import pytest

from src.homeassistant_mcp.resources.areas import register_area_resources


@pytest.mark.asyncio
async def test_successful_area_resource_fetch():
    """Test successful area resource fetch with complete data.

    Validates: Requirements 3.7, 5.6, 20.1
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {
                    "friendly_name": "Living Room Light",
                    "brightness": 255,
                    "color_temp": 370,
                },
            },
            {
                "entity_id": "switch.living_room_fan",
                "state": "off",
                "attributes": {
                    "friendly_name": "Living Room Fan",
                },
            },
            {
                "entity_id": "sensor.living_room_temperature",
                "state": "22.5",
                "attributes": {
                    "friendly_name": "Living Room Temperature",
                    "unit_of_measurement": "°C",
                },
            },
        ]
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
    register_area_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://area/{area_id}"]
    result = await handler("living_room")

    # Assert
    assert result is not None
    assert str(result.uri) == "hass://area/living_room"
    assert result.mime_type == "application/json"

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify response envelope structure
    assert "uri" in parsed
    assert "type" in parsed
    assert "last_updated" in parsed
    assert "data" in parsed

    # Verify envelope values
    assert parsed["uri"] == "hass://area/living_room"
    assert parsed["type"] == "area"

    # Verify data structure
    data = parsed["data"]
    assert data["area_id"] == "living_room"
    assert data["entity_count"] == 3
    assert "entities" in data
    assert "truncated" in data
    assert data["truncated"] is False

    # Verify client was called correctly
    mock_client.get_states.assert_called_once_with(area="living_room")


@pytest.mark.asyncio
async def test_lightweight_entity_summaries():
    """Test that entity summaries contain only 4 required fields.

    Validates: Requirements 3.7, 20.1, 20.2, 20.3, 20.4
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "light.bedroom",
                "state": "on",
                "attributes": {
                    "friendly_name": "Bedroom Light",
                    "brightness": 200,
                    "color_temp": 300,
                    "supported_features": 63,
                    "extra_field": "should_not_appear",
                },
            },
        ]
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
    register_area_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://area/{area_id}"]
    result = await handler("bedroom")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]
    entities = data["entities"]

    # Verify we have entities
    assert len(entities) == 1

    # Verify entity summary has exactly 4 fields
    entity = entities[0]
    assert len(entity) == 4, f"Entity summary should have exactly 4 fields, got {len(entity)}"

    # Verify the 4 required fields are present
    assert "entity_id" in entity
    assert "state" in entity
    assert "domain" in entity
    assert "friendly_name" in entity

    # Verify field values
    assert entity["entity_id"] == "light.bedroom"
    assert entity["state"] == "on"
    assert entity["domain"] == "light"
    assert entity["friendly_name"] == "Bedroom Light"

    # Verify full attributes are NOT included
    assert "attributes" not in entity
    assert "brightness" not in entity
    assert "color_temp" not in entity
    assert "supported_features" not in entity
    assert "extra_field" not in entity


@pytest.mark.asyncio
async def test_truncation_at_50_entities():
    """Test that entity list is truncated at 50 entities.

    Validates: Requirements 5.6, 20.5
    """
    # Arrange - Create 60 entities
    entities = []
    for i in range(60):
        entities.append(
            {
                "entity_id": f"light.light_{i}",
                "state": "on" if i % 2 == 0 else "off",
                "attributes": {
                    "friendly_name": f"Light {i}",
                },
            }
        )

    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=entities)

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
    register_area_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://area/{area_id}"]
    result = await handler("large_area")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify entity_count shows total count
    assert data["entity_count"] == 60

    # Verify entities list is truncated to 50
    assert len(data["entities"]) == 50

    # Verify truncated indicator is True
    assert data["truncated"] is True


@pytest.mark.asyncio
async def test_truncated_indicator_when_more_than_50_entities():
    """Test truncated indicator is set correctly when >50 entities.

    Validates: Requirements 5.6, 20.6
    """
    # Arrange - Create exactly 51 entities (just over the limit)
    entities = []
    for i in range(51):
        entities.append(
            {
                "entity_id": f"sensor.sensor_{i}",
                "state": str(i),
                "attributes": {
                    "friendly_name": f"Sensor {i}",
                },
            }
        )

    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=entities)

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
    register_area_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://area/{area_id}"]
    result = await handler("test_area")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify truncated is True
    assert data["truncated"] is True

    # Verify only 50 entities returned
    assert len(data["entities"]) == 50

    # Verify entity_count shows full count
    assert data["entity_count"] == 51


@pytest.mark.asyncio
async def test_truncated_indicator_false_when_50_or_fewer_entities():
    """Test truncated indicator is False when ≤50 entities.

    Validates: Requirements 5.6, 20.6
    """
    # Arrange - Create exactly 50 entities (at the limit)
    entities = []
    for i in range(50):
        entities.append(
            {
                "entity_id": f"switch.switch_{i}",
                "state": "on",
                "attributes": {
                    "friendly_name": f"Switch {i}",
                },
            }
        )

    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=entities)

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
    register_area_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://area/{area_id}"]
    result = await handler("test_area")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify truncated is False
    assert data["truncated"] is False

    # Verify all 50 entities returned
    assert len(data["entities"]) == 50

    # Verify entity_count matches
    assert data["entity_count"] == 50


@pytest.mark.asyncio
async def test_entity_count_field():
    """Test entity_count field shows total count before truncation.

    Validates: Requirements 5.6, 20.7
    """
    # Arrange - Create 75 entities
    entities = []
    for i in range(75):
        entities.append(
            {
                "entity_id": f"light.light_{i}",
                "state": "on",
                "attributes": {
                    "friendly_name": f"Light {i}",
                },
            }
        )

    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=entities)

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
    register_area_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://area/{area_id}"]
    result = await handler("test_area")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify entity_count shows the full count (75), not truncated count (50)
    assert data["entity_count"] == 75
    assert len(data["entities"]) == 50
    assert data["truncated"] is True


@pytest.mark.asyncio
async def test_cache_ttl_hint_presence():
    """Test cache TTL hint is present in response.

    Validates: Requirement 12.7
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {
                    "friendly_name": "Test Light",
                },
            },
        ]
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
    register_area_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://area/{area_id}"]
    result = await handler("test_area")

    # Assert
    parsed = json.loads(result.text)

    # Verify cache_ttl is present
    assert "cache_ttl" in parsed, "cache_ttl hint missing from response"

    # Verify cache_ttl value is correct for area resources (30 seconds)
    assert parsed["cache_ttl"] == 30
    assert isinstance(parsed["cache_ttl"], int)


@pytest.mark.asyncio
async def test_empty_area():
    """Test area resource with no entities."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])

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
    register_area_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://area/{area_id}"]
    result = await handler("empty_area")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify empty area handling
    assert data["area_id"] == "empty_area"
    assert data["entity_count"] == 0
    assert data["entities"] == []
    assert data["truncated"] is False


@pytest.mark.asyncio
async def test_entity_without_friendly_name():
    """Test entity summary when friendly_name is missing."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "sensor.unknown",
                "state": "42",
                "attributes": {},  # No friendly_name
            },
        ]
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
    register_area_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://area/{area_id}"]
    result = await handler("test_area")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]
    entity = data["entities"][0]

    # Should fall back to entity_id when friendly_name is missing
    assert entity["friendly_name"] == "sensor.unknown"


@pytest.mark.asyncio
async def test_entity_without_domain_separator():
    """Test entity summary when entity_id has no domain separator."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "malformed_entity",
                "state": "on",
                "attributes": {
                    "friendly_name": "Malformed Entity",
                },
            },
        ]
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
    register_area_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://area/{area_id}"]
    result = await handler("test_area")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]
    entity = data["entities"][0]

    # Should fall back to "unknown" domain
    assert entity["domain"] == "unknown"


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling when area fetch fails."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(side_effect=Exception("Connection error"))

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
    register_area_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://area/{area_id}"]
    result = await handler("test_area")

    # Assert
    parsed = json.loads(result.text)

    # Verify error structure
    assert "error" in parsed
    assert "code" in parsed["error"]
    assert "message" in parsed["error"]
    assert "uri" in parsed["error"]

    # Verify error values
    assert parsed["error"]["code"] == "internal"
    assert "Internal server error" in parsed["error"]["message"]
    # Error message is sanitized and doesn't leak exception details
    assert "Connection error" not in parsed["error"]["message"]
    assert parsed["error"]["uri"] == "hass://area/test_area"


@pytest.mark.asyncio
async def test_mime_type_is_application_json():
    """Test MIME type is application/json."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {
                    "friendly_name": "Test Light",
                },
            },
        ]
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
    register_area_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://area/{area_id}"]
    result = await handler("test_area")

    # Assert
    assert result.mime_type == "application/json"

    # Verify the response is valid JSON
    parsed = json.loads(result.text)
    assert isinstance(parsed, dict)


@pytest.mark.asyncio
async def test_multiple_domains_in_area():
    """Test area with entities from multiple domains."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "light.kitchen",
                "state": "on",
                "attributes": {"friendly_name": "Kitchen Light"},
            },
            {
                "entity_id": "switch.kitchen_fan",
                "state": "off",
                "attributes": {"friendly_name": "Kitchen Fan"},
            },
            {
                "entity_id": "sensor.kitchen_temperature",
                "state": "23.5",
                "attributes": {"friendly_name": "Kitchen Temperature"},
            },
            {
                "entity_id": "binary_sensor.kitchen_motion",
                "state": "off",
                "attributes": {"friendly_name": "Kitchen Motion"},
            },
            {
                "entity_id": "climate.kitchen",
                "state": "heat",
                "attributes": {"friendly_name": "Kitchen Thermostat"},
            },
        ]
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
    register_area_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://area/{area_id}"]
    result = await handler("kitchen")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify all entities are included
    assert data["entity_count"] == 5
    assert len(data["entities"]) == 5

    # Verify domains are correctly extracted
    domains = [entity["domain"] for entity in data["entities"]]
    assert "light" in domains
    assert "switch" in domains
    assert "sensor" in domains
    assert "binary_sensor" in domains
    assert "climate" in domains
