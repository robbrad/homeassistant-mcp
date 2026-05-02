"""Property-based tests for MCP resources.

This module tests the following properties:
- Property 4: Entity Resource Completeness
- Property 49: Resource URI Format Compliance
- Property 50: Resource Response Structure
- Property 51: Invalid Resource URI Error Handling

Validates Requirements: 3.6, 4.1, 22.1, 22.2, 22.9
"""

import json
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.homeassistant_mcp.exceptions import EntityNotFoundError
from src.homeassistant_mcp.resources.entities import register_entity_resources


# Custom strategies for generating test data
@st.composite
def entity_id_strategy(draw):
    """Generate valid Home Assistant entity IDs (domain.name)."""
    domains = ["light", "switch", "sensor", "climate", "binary_sensor", "cover"]
    domain = draw(st.sampled_from(domains))
    # Generate valid entity names (alphanumeric and underscore)
    name = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
            min_size=1,
            max_size=20,
        )
    )
    return f"{domain}.{name}"


@st.composite
def entity_state_strategy(draw):
    """Generate valid entity states."""
    states = ["on", "off", "heat", "cool", "auto", "open", "closed", "locked", "unlocked"]
    return draw(st.sampled_from(states))


@st.composite
def attributes_strategy(draw):
    """Generate valid entity attributes dictionaries."""
    # Generate simple attributes with string, int, float, or bool values
    keys = draw(
        st.lists(
            st.text(alphabet=st.characters(whitelist_categories=("Ll",)), min_size=1, max_size=15),
            min_size=0,
            max_size=5,
            unique=True,
        )
    )

    values = []
    for _ in keys:
        value_type = draw(st.sampled_from(["str", "int", "float", "bool"]))
        if value_type == "str":
            values.append(draw(st.text(min_size=0, max_size=50)))
        elif value_type == "int":
            values.append(draw(st.integers(min_value=-1000, max_value=1000)))
        elif value_type == "float":
            values.append(
                draw(
                    st.floats(
                        min_value=-1000.0,
                        max_value=1000.0,
                        allow_nan=False,
                        allow_infinity=False,
                    )
                )
            )
        else:
            values.append(draw(st.booleans()))

    return dict(zip(keys, values, strict=False))


# Feature: mcp-resources-layer, Property 4: Entity Resource Completeness
@given(
    entity_id=entity_id_strategy(),
    state=entity_state_strategy(),
    attributes=attributes_strategy(),
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_4_entity_resource_completeness(
    entity_id: str, state: str, attributes: dict[str, Any]
):
    """
    Property 4: Entity Resource Completeness

    For any entity resource response, the `data` field must include all required fields:
    entity_id, state, attributes, last_changed, last_updated, domain, and friendly_name.

    Validates: Requirements 3.6, 4.1
    """
    # Add friendly_name to attributes if not present
    if "friendly_name" not in attributes:
        attributes["friendly_name"] = f"Test {entity_id}"

    # Create mock client with complete entity state
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": entity_id,
            "state": state,
            "attributes": attributes,
            "last_changed": "2024-01-15T10:25:00+00:00",
            "last_updated": "2024-01-15T10:30:00+00:00",
            "context": {"id": "test", "parent_id": None, "user_id": None},
        }
    )

    def get_client():
        return mock_client

    # Create mock MCP server
    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Register entity resources
    register_entity_resources(mock_mcp, get_client)

    # Get the resource handler
    handler = resource_handlers["hass://entity/{entity_id}"]

    # Call the handler
    result = await handler(entity_id)

    # Parse the response
    assert result is not None
    parsed = json.loads(result.text)

    # Verify response envelope structure
    assert "uri" in parsed
    assert "type" in parsed
    assert "last_updated" in parsed
    assert "data" in parsed

    # Extract the data field
    data = parsed["data"]

    # Property 4: Verify ALL required fields are present in data
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
        assert field in data, f"Required field '{field}' missing from entity resource data"

    # Verify field values are correct
    assert data["entity_id"] == entity_id
    assert data["state"] == state
    assert data["attributes"] == attributes
    assert data["last_changed"] == "2024-01-15T10:25:00+00:00"
    assert data["last_updated"] == "2024-01-15T10:30:00+00:00"

    # Verify domain is extracted correctly from entity_id
    expected_domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
    assert data["domain"] == expected_domain

    # Verify friendly_name is extracted from attributes
    expected_friendly_name = attributes.get("friendly_name", entity_id)
    assert data["friendly_name"] == expected_friendly_name


# Feature: rest-api-overhaul, Property 49: Resource URI Format Compliance
@given(entity_id=entity_id_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_49_resource_uri_format_compliance(entity_id: str):
    """
    Property 49: Resource URI Format Compliance

    For any resource type (entity, area, device, services), the URI SHALL follow
    the format `hass://{type}/{id}` or `hass://{type}` for collections.

    Validates: Requirements 22.1, 22.3, 22.5, 22.7
    """
    # Create mock client
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": entity_id,
            "state": "on",
            "attributes": {},
            "last_changed": "2024-01-01T12:00:00+00:00",
            "last_updated": "2024-01-01T12:00:00+00:00",
            "context": {"id": "test", "parent_id": None, "user_id": None},
        }
    )

    def get_client():
        return mock_client

    # Create mock MCP server
    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Register entity resources
    register_entity_resources(mock_mcp, get_client)

    # Verify URI format compliance
    assert "hass://entity/{entity_id}" in resource_handlers

    # Test the resource handler - FastMCP extracts the entity_id from the URI
    # so we pass just the entity_id parameter
    handler = resource_handlers["hass://entity/{entity_id}"]

    result = await handler(entity_id)

    # Verify the handler was called and returned data
    assert result is not None
    mock_client.get_state.assert_called_once_with(entity_id)


# Feature: rest-api-overhaul, Property 50: Resource Response Structure
@given(
    entity_id=entity_id_strategy(),
    state=entity_state_strategy(),
    attributes=attributes_strategy(),
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_50_resource_response_structure(
    entity_id: str, state: str, attributes: dict[str, Any]
):
    """
    Property 50: Resource Response Structure

    For any valid resource URI, the response SHALL return JSON-formatted data
    with all required fields for that resource type.

    Validates: Requirements 22.2, 22.4, 22.6, 22.8
    """
    # Create mock client with entity state
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": entity_id,
            "state": state,
            "attributes": attributes,
            "last_changed": "2024-01-01T12:00:00+00:00",
            "last_updated": "2024-01-01T12:00:00+00:00",
            "context": {"id": "test", "parent_id": None, "user_id": None},
        }
    )

    def get_client():
        return mock_client

    # Create mock MCP server
    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Register entity resources
    register_entity_resources(mock_mcp, get_client)

    # Get the resource handler
    handler = resource_handlers["hass://entity/{entity_id}"]

    # Call the handler - FastMCP extracts entity_id from URI, so we pass just the parameter
    result = await handler(entity_id)

    # Verify response is JSON-formatted - extract text from TextResource
    assert result is not None
    parsed = json.loads(result.text)

    # Verify response envelope structure
    assert "data" in parsed
    data = parsed["data"]

    # Verify all required fields are present in data
    assert "entity_id" in data
    assert "state" in data
    assert "attributes" in data
    assert "last_changed" in data
    assert "last_updated" in data

    # Verify field values match
    assert data["entity_id"] == entity_id
    assert data["state"] == state
    assert data["attributes"] == attributes


# Feature: rest-api-overhaul, Property 51: Invalid Resource URI Error Handling
@given(
    entity_id=st.one_of(
        st.just(""),  # Empty entity_id
        st.text(min_size=1, max_size=10).filter(
            lambda x: "." not in x
        ),  # Invalid format (no domain)
    )
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_51_invalid_resource_uri_error_handling(entity_id: str):
    """
    Property 51: Invalid Resource URI Error Handling

    For any invalid entity_id (empty or malformed), the response SHALL handle it appropriately.
    Note: FastMCP validates URI format at the framework level, so we test with invalid entity_id values.

    Validates: Requirements 22.9
    """
    # Create mock client that raises EntityNotFoundError for invalid entities
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        side_effect=EntityNotFoundError(f"Entity {entity_id} not found")
    )

    def get_client():
        return mock_client

    # Create mock MCP server
    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Register entity resources
    register_entity_resources(mock_mcp, get_client)

    # Get the resource handler
    handler = resource_handlers["hass://entity/{entity_id}"]

    # Test with invalid entity_id - FastMCP extracts this from the URI
    # Empty or malformed entity_ids should result in an error response (not an exception)
    result = await handler(entity_id)

    # Verify we got an error response
    assert result is not None
    parsed = json.loads(result.text)

    # Should contain an error object with not_found code
    assert "error" in parsed
    assert parsed["error"]["code"] == "not_found"
    assert "message" in parsed["error"]
    assert "uri" in parsed["error"]


# Feature: rest-api-overhaul, Property 51: Invalid Resource URI Error Handling (Non-existent Entity)
@given(entity_id=entity_id_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_51_nonexistent_entity_error_handling(entity_id: str):
    """
    Property 51: Invalid Resource URI Error Handling (Non-existent Entity)

    For any non-existent entity ID, the response SHALL return an EntityNotFoundError.

    Validates: Requirements 22.9
    """
    # Create mock client that raises EntityNotFoundError
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        side_effect=EntityNotFoundError(f"Entity {entity_id} not found")
    )

    def get_client():
        return mock_client

    # Create mock MCP server
    mock_mcp = Mock()
    resource_handlers = {}

    def mock_resource(uri_pattern: str):
        def decorator(func):
            resource_handlers[uri_pattern] = func
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Register entity resources
    register_entity_resources(mock_mcp, get_client)

    # Get the resource handler
    handler = resource_handlers["hass://entity/{entity_id}"]

    # Test with non-existent entity - should return error response (not raise exception)
    # FastMCP extracts entity_id from URI, so we pass just the parameter
    result = await handler(entity_id)

    # Verify we got an error response
    assert result is not None
    parsed = json.loads(result.text)

    # Should contain an error object with not_found code
    assert "error" in parsed
    assert parsed["error"]["code"] == "not_found"
    assert "message" in parsed["error"]
    assert "uri" in parsed["error"]

    # Verify the client was called
    mock_client.get_state.assert_called_once_with(entity_id)
