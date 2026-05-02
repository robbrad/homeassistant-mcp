"""Unit tests for device resources.

Tests device resource handlers including successful fetches, lightweight entity summaries,
truncation behavior, and error handling.

Requirements tested: 3.8, 6.6, 12.7, 20.1, 20.2, 20.3, 20.4
"""

import json
from unittest.mock import AsyncMock, Mock

import pytest

from src.homeassistant_mcp.resources.devices import register_device_resources


@pytest.mark.asyncio
async def test_successful_device_resource_fetch():
    """Test successful device resource fetch with complete data.

    Validates: Requirements 3.8, 6.6, 20.1
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "sensor.temperature",
                "state": "22.5",
                "attributes": {
                    "friendly_name": "Temperature Sensor",
                    "unit_of_measurement": "°C",
                    "device_id": "abc123def456",
                },
            },
            {
                "entity_id": "sensor.humidity",
                "state": "45",
                "attributes": {
                    "friendly_name": "Humidity Sensor",
                    "unit_of_measurement": "%",
                    "device_id": "abc123def456",
                },
            },
            {
                "entity_id": "binary_sensor.motion",
                "state": "off",
                "attributes": {
                    "friendly_name": "Motion Sensor",
                    "device_id": "abc123def456",
                },
            },
            # Entity from different device (should be filtered out)
            {
                "entity_id": "light.other_device",
                "state": "on",
                "attributes": {
                    "friendly_name": "Other Light",
                    "device_id": "different_device",
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
    register_device_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://device/{device_id}"]
    result = await handler("abc123def456")

    # Assert
    assert result is not None
    assert str(result.uri) == "hass://device/abc123def456"
    assert result.mime_type == "application/json"

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify response envelope structure
    assert "uri" in parsed
    assert "type" in parsed
    assert "last_updated" in parsed
    assert "data" in parsed

    # Verify envelope values
    assert parsed["uri"] == "hass://device/abc123def456"
    assert parsed["type"] == "device"

    # Verify data structure
    data = parsed["data"]
    assert data["device_id"] == "abc123def456"
    assert data["entity_count"] == 3  # Only entities from this device
    assert "entities" in data
    assert "truncated" in data
    assert data["truncated"] is False

    # Verify client was called correctly
    mock_client.get_states.assert_called_once()


@pytest.mark.asyncio
async def test_lightweight_entity_summaries():
    """Test that entity summaries contain only 4 required fields.

    Validates: Requirements 3.8, 20.1, 20.2, 20.3, 20.4
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "sensor.power",
                "state": "150.5",
                "attributes": {
                    "friendly_name": "Power Sensor",
                    "unit_of_measurement": "W",
                    "device_id": "test_device",
                    "device_class": "power",
                    "state_class": "measurement",
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
    register_device_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://device/{device_id}"]
    result = await handler("test_device")

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
    assert entity["entity_id"] == "sensor.power"
    assert entity["state"] == "150.5"
    assert entity["domain"] == "sensor"
    assert entity["friendly_name"] == "Power Sensor"

    # Verify full attributes are NOT included
    assert "attributes" not in entity
    assert "unit_of_measurement" not in entity
    assert "device_class" not in entity
    assert "state_class" not in entity
    assert "extra_field" not in entity


@pytest.mark.asyncio
async def test_truncation_at_50_entities():
    """Test that entity list is truncated at 50 entities.

    Validates: Requirements 6.6, 20.5
    """
    # Arrange - Create 60 entities for the same device
    entities = []
    for i in range(60):
        entities.append(
            {
                "entity_id": f"sensor.sensor_{i}",
                "state": str(i),
                "attributes": {
                    "friendly_name": f"Sensor {i}",
                    "device_id": "large_device",
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
    register_device_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://device/{device_id}"]
    result = await handler("large_device")

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

    Validates: Requirements 6.6, 20.6
    """
    # Arrange - Create exactly 51 entities (just over the limit)
    entities = []
    for i in range(51):
        entities.append(
            {
                "entity_id": f"switch.switch_{i}",
                "state": "on" if i % 2 == 0 else "off",
                "attributes": {
                    "friendly_name": f"Switch {i}",
                    "device_id": "test_device",
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
    register_device_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://device/{device_id}"]
    result = await handler("test_device")

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

    Validates: Requirements 6.6, 20.6
    """
    # Arrange - Create exactly 50 entities (at the limit)
    entities = []
    for i in range(50):
        entities.append(
            {
                "entity_id": f"light.light_{i}",
                "state": "on",
                "attributes": {
                    "friendly_name": f"Light {i}",
                    "device_id": "test_device",
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
    register_device_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://device/{device_id}"]
    result = await handler("test_device")

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

    Validates: Requirements 6.6, 20.7
    """
    # Arrange - Create 75 entities
    entities = []
    for i in range(75):
        entities.append(
            {
                "entity_id": f"sensor.sensor_{i}",
                "state": str(i * 10),
                "attributes": {
                    "friendly_name": f"Sensor {i}",
                    "device_id": "test_device",
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
    register_device_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://device/{device_id}"]
    result = await handler("test_device")

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
                "entity_id": "sensor.test",
                "state": "42",
                "attributes": {
                    "friendly_name": "Test Sensor",
                    "device_id": "test_device",
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
    register_device_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://device/{device_id}"]
    result = await handler("test_device")

    # Assert
    parsed = json.loads(result.text)

    # Verify cache_ttl is present
    assert "cache_ttl" in parsed, "cache_ttl hint missing from response"

    # Verify cache_ttl value is correct for device resources (30 seconds)
    assert parsed["cache_ttl"] == 30
    assert isinstance(parsed["cache_ttl"], int)


@pytest.mark.asyncio
async def test_empty_device():
    """Test device resource with no entities."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            # Return entities but none match the device_id
            {
                "entity_id": "light.other",
                "state": "on",
                "attributes": {
                    "friendly_name": "Other Light",
                    "device_id": "different_device",
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
    register_device_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://device/{device_id}"]
    result = await handler("empty_device")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify empty device handling
    assert data["device_id"] == "empty_device"
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
                "attributes": {
                    "device_id": "test_device",
                    # No friendly_name
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
    register_device_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://device/{device_id}"]
    result = await handler("test_device")

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
                    "device_id": "test_device",
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
    register_device_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://device/{device_id}"]
    result = await handler("test_device")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]
    entity = data["entities"][0]

    # Should fall back to "unknown" domain
    assert entity["domain"] == "unknown"


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling when device fetch fails."""
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
    register_device_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://device/{device_id}"]
    result = await handler("test_device")

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
    assert parsed["error"]["uri"] == "hass://device/test_device"


@pytest.mark.asyncio
async def test_mime_type_is_application_json():
    """Test MIME type is application/json."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "sensor.test",
                "state": "42",
                "attributes": {
                    "friendly_name": "Test Sensor",
                    "device_id": "test_device",
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
    register_device_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://device/{device_id}"]
    result = await handler("test_device")

    # Assert
    assert result.mime_type == "application/json"

    # Verify the response is valid JSON
    parsed = json.loads(result.text)
    assert isinstance(parsed, dict)


@pytest.mark.asyncio
async def test_multiple_domains_in_device():
    """Test device with entities from multiple domains."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "sensor.temperature",
                "state": "22.5",
                "attributes": {
                    "friendly_name": "Temperature",
                    "device_id": "multi_sensor",
                },
            },
            {
                "entity_id": "sensor.humidity",
                "state": "45",
                "attributes": {
                    "friendly_name": "Humidity",
                    "device_id": "multi_sensor",
                },
            },
            {
                "entity_id": "binary_sensor.motion",
                "state": "off",
                "attributes": {
                    "friendly_name": "Motion",
                    "device_id": "multi_sensor",
                },
            },
            {
                "entity_id": "light.indicator",
                "state": "on",
                "attributes": {
                    "friendly_name": "Indicator Light",
                    "device_id": "multi_sensor",
                },
            },
            {
                "entity_id": "switch.power",
                "state": "on",
                "attributes": {
                    "friendly_name": "Power Switch",
                    "device_id": "multi_sensor",
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
    register_device_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://device/{device_id}"]
    result = await handler("multi_sensor")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify all entities are included
    assert data["entity_count"] == 5
    assert len(data["entities"]) == 5

    # Verify domains are correctly extracted
    domains = [entity["domain"] for entity in data["entities"]]
    assert "sensor" in domains
    assert "binary_sensor" in domains
    assert "light" in domains
    assert "switch" in domains


@pytest.mark.asyncio
async def test_device_filtering():
    """Test that only entities with matching device_id are included."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "sensor.device_a_temp",
                "state": "20",
                "attributes": {
                    "friendly_name": "Device A Temperature",
                    "device_id": "device_a",
                },
            },
            {
                "entity_id": "sensor.device_b_temp",
                "state": "25",
                "attributes": {
                    "friendly_name": "Device B Temperature",
                    "device_id": "device_b",
                },
            },
            {
                "entity_id": "sensor.device_a_humidity",
                "state": "50",
                "attributes": {
                    "friendly_name": "Device A Humidity",
                    "device_id": "device_a",
                },
            },
            {
                "entity_id": "sensor.no_device",
                "state": "30",
                "attributes": {
                    "friendly_name": "No Device Sensor",
                    # No device_id attribute
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
    register_device_resources(mock_mcp, get_client)
    handler = resource_handlers["hass://device/{device_id}"]
    result = await handler("device_a")

    # Assert
    parsed = json.loads(result.text)
    data = parsed["data"]

    # Verify only device_a entities are included
    assert data["entity_count"] == 2
    assert len(data["entities"]) == 2

    # Verify correct entities
    entity_ids = [entity["entity_id"] for entity in data["entities"]]
    assert "sensor.device_a_temp" in entity_ids
    assert "sensor.device_a_humidity" in entity_ids
    assert "sensor.device_b_temp" not in entity_ids
    assert "sensor.no_device" not in entity_ids
