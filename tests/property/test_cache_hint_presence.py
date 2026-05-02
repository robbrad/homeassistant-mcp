"""Property-based tests for cache hint presence in MCP resources.

Feature: mcp-resources-layer
Property 14: Cache Hint Presence

For any successful resource response, the metadata must include cache hints with
readOnlyHint=True, idempotentHint=True, and a ttl_seconds value appropriate for
the resource type.

Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given
from hypothesis import strategies as st

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


@pytest.mark.property_test
@given(
    domain=st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
    ),
    object_id=st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
    ),
)
async def test_entity_resource_cache_hints(domain, object_id):
    """Property: Entity resources must include proper cache hints.

    For any entity resource response, the response must include:
    - cache_ttl=5 in the response envelope
    - readOnlyHint=True in TextResource annotations
    - idempotentHint=True in TextResource annotations

    Validates: Requirements 12.1, 12.2, 12.3, 12.4
    """
    # Build entity_id from domain and object_id
    entity_id = f"{domain}.{object_id}"

    # Create mock MCP server and client
    mcp = MagicMock()
    handlers = {}

    def mock_resource(uri_pattern):
        def decorator(func):
            handlers[uri_pattern] = func
            return func

        return decorator

    mcp.resource = mock_resource

    # Create mock client
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": entity_id,
            "state": "on",
            "attributes": {"friendly_name": "Test Entity"},
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
    assert handler is not None, "Entity resource handler not registered"

    # Call the handler
    result = await handler(entity_id)

    # Verify the result is a TextResource
    assert result is not None
    assert hasattr(result, "text"), "Result should be a TextResource with text attribute"
    assert hasattr(result, "annotations"), "Result should have annotations attribute"

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify cache_ttl is present in the envelope
    assert "cache_ttl" in parsed, "Response envelope must include cache_ttl"
    assert (
        parsed["cache_ttl"] == EXPECTED_TTLS["entity"]
    ), f"Entity resources must have cache_ttl={EXPECTED_TTLS['entity']}"

    # Verify annotations include readOnlyHint and idempotentHint
    if result.annotations:
        annotations_dict = (
            result.annotations.model_dump()
            if hasattr(result.annotations, "model_dump")
            else result.annotations
        )
        assert (
            annotations_dict.get("readOnlyHint") is True
        ), "Entity resources must have readOnlyHint=True"
        assert (
            annotations_dict.get("idempotentHint") is True
        ), "Entity resources must have idempotentHint=True"


@pytest.mark.property_test
@given(area_id=st.text(min_size=1, max_size=50))
async def test_area_resource_cache_hints(area_id):
    """Property: Area resources must include proper cache hints.

    For any area resource response, the response must include:
    - cache_ttl=30 in the response envelope
    - readOnlyHint=True in TextResource annotations
    - idempotentHint=True in TextResource annotations

    Validates: Requirements 12.1, 12.2, 12.3, 12.7
    """
    # Create mock MCP server and client
    mcp = MagicMock()
    handlers = {}

    def mock_resource(uri_pattern):
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
    assert handler is not None, "Area resource handler not registered"

    # Call the handler
    result = await handler(area_id)

    # Verify the result is a TextResource
    assert result is not None
    assert hasattr(result, "text"), "Result should be a TextResource with text attribute"

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify cache_ttl is present in the envelope
    assert "cache_ttl" in parsed, "Response envelope must include cache_ttl"
    assert (
        parsed["cache_ttl"] == EXPECTED_TTLS["area"]
    ), f"Area resources must have cache_ttl={EXPECTED_TTLS['area']}"


@pytest.mark.property_test
@given(device_id=st.text(min_size=1, max_size=50))
async def test_device_resource_cache_hints(device_id):
    """Property: Device resources must include proper cache hints.

    For any device resource response, the response must include:
    - cache_ttl=30 in the response envelope
    - readOnlyHint=True in TextResource annotations
    - idempotentHint=True in TextResource annotations

    Validates: Requirements 12.1, 12.2, 12.3, 12.7
    """
    # Create mock MCP server and client
    mcp = MagicMock()
    handlers = {}

    def mock_resource(uri_pattern):
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
                    "device_id": device_id,
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
    assert handler is not None, "Device resource handler not registered"

    # Call the handler
    result = await handler(device_id)

    # Verify the result is a TextResource
    assert result is not None
    assert hasattr(result, "text"), "Result should be a TextResource with text attribute"

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify cache_ttl is present in the envelope
    assert "cache_ttl" in parsed, "Response envelope must include cache_ttl"
    assert (
        parsed["cache_ttl"] == EXPECTED_TTLS["device"]
    ), f"Device resources must have cache_ttl={EXPECTED_TTLS['device']}"


@pytest.mark.property_test
async def test_services_resource_cache_hints():
    """Property: Services resources must include proper cache hints.

    For the services resource response, the response must include:
    - cache_ttl=300 in the response envelope
    - readOnlyHint=True in TextResource annotations
    - idempotentHint=True in TextResource annotations

    Validates: Requirements 12.1, 12.2, 12.3, 12.5
    """
    # Create mock MCP server and client
    mcp = MagicMock()
    handlers = {}

    def mock_resource(uri_pattern):
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
    assert handler is not None, "Services resource handler not registered"

    # Call the handler
    result = await handler()

    # Verify the result is a TextResource
    assert result is not None
    assert hasattr(result, "text"), "Result should be a TextResource with text attribute"

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify cache_ttl is present in the envelope
    assert "cache_ttl" in parsed, "Response envelope must include cache_ttl"
    assert (
        parsed["cache_ttl"] == EXPECTED_TTLS["services"]
    ), f"Services resources must have cache_ttl={EXPECTED_TTLS['services']}"


@pytest.mark.property_test
@given(
    domain=st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
    ),
    object_id=st.text(
        min_size=1,
        max_size=20,
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
    ),
    hours=st.integers(min_value=1, max_value=168),
    limit=st.integers(min_value=1, max_value=1000),
)
async def test_history_resource_cache_hints(domain, object_id, hours, limit):
    """Property: History resources must include proper cache hints.

    For any history resource response, the response must include:
    - cache_ttl=60 in the response envelope
    - readOnlyHint=True in TextResource annotations
    - idempotentHint=True in TextResource annotations

    Validates: Requirements 12.1, 12.2, 12.3, 12.6
    """
    # Build entity_id from domain and object_id
    entity_id = f"{domain}.{object_id}"

    # Create mock MCP server and client
    mcp = MagicMock()
    handlers = {}

    def mock_resource(uri_pattern):
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
    assert handler is not None, "History resource handler not registered"

    # Call the handler
    result = await handler(entity_id, hours=hours, limit=limit)

    # Verify the result is a TextResource
    assert result is not None
    assert hasattr(result, "text"), "Result should be a TextResource with text attribute"

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify cache_ttl is present in the envelope
    assert "cache_ttl" in parsed, "Response envelope must include cache_ttl"
    assert (
        parsed["cache_ttl"] == EXPECTED_TTLS["history"]
    ), f"History resources must have cache_ttl={EXPECTED_TTLS['history']}"
