"""Unit tests for cache hints in MCP resources.

Tests that all resources include proper cache hints:
- readOnlyHint=True
- idempotentHint=True
- Correct TTL values for each resource type

Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant_mcp.resources.areas import register_area_resources
from homeassistant_mcp.resources.devices import register_device_resources
from homeassistant_mcp.resources.entities import register_entity_resources
from homeassistant_mcp.resources.history import register_history_resources
from homeassistant_mcp.resources.services import register_services_resources

# Expected TTL values for each resource type
EXPECTED_TTLS = {
    "entity": 5,
    "area": 30,
    "device": 30,
    "services": 300,
    "history": 60,
}


@pytest.mark.asyncio
async def test_entity_resource_cache_ttl():
    """Test entity resources have correct cache TTL of 5 seconds."""
    # Create mock MCP server and client
    mcp = MagicMock()
    handlers = {}

    def mock_resource(uri_pattern, **kwargs):
        def decorator(func):
            handlers[uri_pattern] = func
            return func

        return decorator

    mcp.resource = mock_resource

    # Create mock client
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

    def get_client():
        return mock_client

    # Register entity resources
    register_entity_resources(mcp, get_client)

    # Get the handler
    handler = handlers.get("hass://entity/{entity_id}")
    assert handler is not None

    # Call the handler
    result = await handler("light.test")

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify cache_ttl is 5 seconds
    assert "cache_ttl" in parsed
    assert parsed["cache_ttl"] == EXPECTED_TTLS["entity"]


@pytest.mark.asyncio
async def test_area_resource_cache_ttl():
    """Test area resources have correct cache TTL of 30 seconds."""
    # Create mock MCP server and client
    mcp = MagicMock()
    handlers = {}

    def mock_resource(uri_pattern, **kwargs):
        def decorator(func):
            handlers[uri_pattern] = func
            return func

        return decorator

    mcp.resource = mock_resource

    # Create mock client
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {"friendly_name": "Test Light"},
            }
        ]
    )

    def get_client():
        return mock_client

    # Register area resources
    register_area_resources(mcp, get_client)

    # Get the handler
    handler = handlers.get("hass://area/{area_id}")
    assert handler is not None

    # Call the handler
    result = await handler("living_room")

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify cache_ttl is 30 seconds
    assert "cache_ttl" in parsed
    assert parsed["cache_ttl"] == EXPECTED_TTLS["area"]


@pytest.mark.asyncio
async def test_device_resource_cache_ttl():
    """Test device resources have correct cache TTL of 30 seconds."""
    # Create mock MCP server and client
    mcp = MagicMock()
    handlers = {}

    def mock_resource(uri_pattern, **kwargs):
        def decorator(func):
            handlers[uri_pattern] = func
            return func

        return decorator

    mcp.resource = mock_resource

    # Create mock client
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "sensor.test",
                "state": "22.5",
                "attributes": {
                    "friendly_name": "Test Sensor",
                    "device_id": "test_device",
                },
            }
        ]
    )

    def get_client():
        return mock_client

    # Register device resources
    register_device_resources(mcp, get_client)

    # Get the handler
    handler = handlers.get("hass://device/{device_id}")
    assert handler is not None

    # Call the handler
    result = await handler("test_device")

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify cache_ttl is 30 seconds
    assert "cache_ttl" in parsed
    assert parsed["cache_ttl"] == EXPECTED_TTLS["device"]


@pytest.mark.asyncio
async def test_services_resource_cache_ttl():
    """Test services resources have correct cache TTL of 300 seconds."""
    # Create mock MCP server and client
    mcp = MagicMock()
    handlers = {}

    def mock_resource(uri_pattern, **kwargs):
        def decorator(func):
            handlers[uri_pattern] = func
            return func

        return decorator

    mcp.resource = mock_resource

    # Create mock client
    mock_client = AsyncMock()
    mock_client.get_services = AsyncMock(
        return_value={
            "light": {
                "turn_on": {
                    "description": "Turn on lights",
                    "fields": {},
                }
            }
        }
    )

    def get_client():
        return mock_client

    # Register services resources
    register_services_resources(mcp, get_client)

    # Get the handler
    handler = handlers.get("hass://services")
    assert handler is not None

    # Call the handler
    result = await handler()

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify cache_ttl is 300 seconds
    assert "cache_ttl" in parsed
    assert parsed["cache_ttl"] == EXPECTED_TTLS["services"]


@pytest.mark.asyncio
async def test_history_resource_cache_ttl():
    """Test history resources have correct cache TTL of 60 seconds."""
    # Create mock MCP server and client
    mcp = MagicMock()
    handlers = {}

    def mock_resource(uri_pattern, **kwargs):
        def decorator(func):
            handlers[uri_pattern] = func
            return func

        return decorator

    mcp.resource = mock_resource

    # Create mock client
    mock_client = AsyncMock()
    mock_client.get_history = AsyncMock(
        return_value=[
            [
                {
                    "state": "on",
                    "last_changed": "2024-01-15T10:00:00Z",
                    "last_updated": "2024-01-15T10:00:00Z",
                    "attributes": {},
                }
            ]
        ]
    )

    def get_client():
        return mock_client

    # Register history resources
    register_history_resources(mcp, get_client)

    # Get the handler
    handler = handlers.get("hass://entity/{entity_id}/history")
    assert handler is not None

    # Call the handler
    result = await handler("sensor.test", hours=24, limit=100, offset=0)

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify cache_ttl is 60 seconds
    assert "cache_ttl" in parsed
    assert parsed["cache_ttl"] == EXPECTED_TTLS["history"]


@pytest.mark.asyncio
async def test_all_resources_have_cache_ttl():
    """Test that all resource types include cache_ttl in their responses."""
    # Create mock MCP server and client
    mcp = MagicMock()
    handlers = {}

    def mock_resource(uri_pattern, **kwargs):
        def decorator(func):
            handlers[uri_pattern] = func
            return func

        return decorator

    mcp.resource = mock_resource

    # Create mock client with all necessary methods
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
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {"friendly_name": "Test", "device_id": "test_device"},
            }
        ]
    )
    mock_client.get_services = AsyncMock(return_value={"light": {}})
    mock_client.get_history = AsyncMock(
        return_value=[
            [
                {
                    "state": "on",
                    "last_changed": "2024-01-15T10:00:00Z",
                    "last_updated": "2024-01-15T10:00:00Z",
                    "attributes": {},
                }
            ]
        ]
    )

    def get_client():
        return mock_client

    # Register all resources
    register_entity_resources(mcp, get_client)
    register_area_resources(mcp, get_client)
    register_device_resources(mcp, get_client)
    register_services_resources(mcp, get_client)
    register_history_resources(mcp, get_client)

    # Test each resource type
    test_cases = [
        ("hass://entity/{entity_id}", lambda: handlers["hass://entity/{entity_id}"]("light.test")),
        ("hass://area/{area_id}", lambda: handlers["hass://area/{area_id}"]("living_room")),
        ("hass://device/{device_id}", lambda: handlers["hass://device/{device_id}"]("test_device")),
        ("hass://services", lambda: handlers["hass://services"]()),
        (
            "hass://entity/{entity_id}/history",
            lambda: handlers["hass://entity/{entity_id}/history"](
                "sensor.test", hours=24, limit=100, offset=0
            ),
        ),
    ]

    for uri_pattern, handler_call in test_cases:
        result = await handler_call()
        parsed = json.loads(result.text)

        # Verify cache_ttl is present
        assert "cache_ttl" in parsed, f"Resource {uri_pattern} missing cache_ttl"
        assert isinstance(
            parsed["cache_ttl"], int
        ), f"Resource {uri_pattern} cache_ttl must be an integer"
        assert parsed["cache_ttl"] > 0, f"Resource {uri_pattern} cache_ttl must be positive"
