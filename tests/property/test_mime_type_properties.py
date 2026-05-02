"""Property-based tests for MIME type and content format consistency.

This module tests the following properties:
- Property 15: MIME Type Consistency
- Property 16: Timestamp Format Consistency

Validates Requirements: 13.1, 13.2, 13.3, 13.4
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.homeassistant_mcp.resources.areas import register_area_resources
from src.homeassistant_mcp.resources.devices import register_device_resources
from src.homeassistant_mcp.resources.entities import register_entity_resources
from src.homeassistant_mcp.resources.history import register_history_resources
from src.homeassistant_mcp.resources.services import register_services_resources


# Custom strategies for generating test data
@st.composite
def entity_id_strategy(draw):
    """Generate valid Home Assistant entity IDs (domain.name)."""
    domains = ["light", "switch", "sensor", "climate", "binary_sensor", "cover"]
    domain = draw(st.sampled_from(domains))
    name = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
            min_size=1,
            max_size=20,
        )
    )
    return f"{domain}.{name}"


@st.composite
def area_id_strategy(draw):
    """Generate valid area IDs."""
    return draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
            min_size=1,
            max_size=20,
        )
    )


@st.composite
def device_id_strategy(draw):
    """Generate valid device IDs."""
    return draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Ll", "Nd", "Lu"), whitelist_characters="_-"
            ),
            min_size=1,
            max_size=32,
        )
    )


def is_valid_iso8601(timestamp_str: str) -> bool:
    """Validate that a string is a valid ISO8601 timestamp."""
    try:
        # Try to parse the timestamp
        datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return True
    except (ValueError, AttributeError):
        return False


# Feature: mcp-resources-layer, Property 15: MIME Type Consistency
@given(entity_id=entity_id_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_15_entity_resource_mime_type_consistency(entity_id: str):
    """
    **Validates: Requirements 13.1, 13.2, 13.3**

    Property: For any entity resource response, the MIME type must be
    application/json.
    """
    # Create mock MCP server and client
    mock_mcp = MagicMock()
    mock_client = AsyncMock()

    # Store the registered resource handler
    resource_handler = None

    def mock_resource_decorator(uri_pattern):
        def decorator(func):
            nonlocal resource_handler
            resource_handler = func
            return func

        return decorator

    mock_mcp.resource = mock_resource_decorator

    # Mock client response
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": entity_id,
            "state": "on",
            "attributes": {"friendly_name": "Test Entity"},
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
        }
    )

    # Register entity resources
    register_entity_resources(mock_mcp, lambda: mock_client)

    # Call the resource handler
    assert resource_handler is not None, "Resource handler should be registered"
    result = await resource_handler(entity_id)

    # Verify MIME type is application/json (Requirement 13.1)
    assert hasattr(result, "mime_type"), "Result must have mime_type attribute"
    assert (
        result.mime_type == "application/json"
    ), f"MIME type must be 'application/json', got: {result.mime_type}"

    # Verify the response is valid JSON (Requirement 13.2)
    assert hasattr(result, "text"), "Result must have text attribute"
    try:
        parsed = json.loads(result.text)
        assert isinstance(parsed, dict), "Parsed JSON must be a dictionary"
    except json.JSONDecodeError as e:
        pytest.fail(f"Response text must be valid JSON: {e}")

    # Verify JSON formatting (Requirement 13.3)
    # Check that the JSON is formatted with indentation
    assert "\n" in result.text, "JSON should be formatted with newlines"
    assert "  " in result.text, "JSON should be formatted with 2-space indentation"


# Feature: mcp-resources-layer, Property 15: MIME Type Consistency (Area Resources)
@given(area_id=area_id_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_15_area_resource_mime_type_consistency(area_id: str):
    """
    **Validates: Requirements 13.1, 13.2, 13.3**

    Property: For any area resource response, the MIME type must be
    application/json.
    """
    # Create mock MCP server and client
    mock_mcp = MagicMock()
    mock_client = AsyncMock()

    # Store the registered resource handler
    resource_handler = None

    def mock_resource_decorator(uri_pattern):
        def decorator(func):
            nonlocal resource_handler
            resource_handler = func
            return func

        return decorator

    mock_mcp.resource = mock_resource_decorator

    # Mock client response
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {"friendly_name": "Test Light"},
            }
        ]
    )

    # Register area resources
    register_area_resources(mock_mcp, lambda: mock_client)

    # Call the resource handler
    assert resource_handler is not None
    result = await resource_handler(area_id)

    # Verify MIME type is application/json
    assert result.mime_type == "application/json"

    # Verify the response is valid JSON
    try:
        parsed = json.loads(result.text)
        assert isinstance(parsed, dict)
    except json.JSONDecodeError as e:
        pytest.fail(f"Response text must be valid JSON: {e}")


# Feature: mcp-resources-layer, Property 15: MIME Type Consistency (Device Resources)
@given(device_id=device_id_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_15_device_resource_mime_type_consistency(device_id: str):
    """
    **Validates: Requirements 13.1, 13.2, 13.3**

    Property: For any device resource response, the MIME type must be
    application/json.
    """
    # Create mock MCP server and client
    mock_mcp = MagicMock()
    mock_client = AsyncMock()

    # Store the registered resource handler
    resource_handler = None

    def mock_resource_decorator(uri_pattern):
        def decorator(func):
            nonlocal resource_handler
            resource_handler = func
            return func

        return decorator

    mock_mcp.resource = mock_resource_decorator

    # Mock client response
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

    # Register device resources
    register_device_resources(mock_mcp, lambda: mock_client)

    # Call the resource handler
    assert resource_handler is not None
    result = await resource_handler(device_id)

    # Verify MIME type is application/json
    assert result.mime_type == "application/json"

    # Verify the response is valid JSON
    try:
        parsed = json.loads(result.text)
        assert isinstance(parsed, dict)
    except json.JSONDecodeError as e:
        pytest.fail(f"Response text must be valid JSON: {e}")


# Feature: mcp-resources-layer, Property 15: MIME Type Consistency (Services Resources)
@pytest.mark.asyncio
async def test_property_15_services_resource_mime_type_consistency():
    """
    **Validates: Requirements 13.1, 13.2, 13.3**

    Property: For the services resource response, the MIME type must be
    application/json.
    """
    # Create mock MCP server and client
    mock_mcp = MagicMock()
    mock_client = AsyncMock()

    # Store the registered resource handler
    resource_handler = None

    def mock_resource_decorator(uri_pattern):
        def decorator(func):
            nonlocal resource_handler
            resource_handler = func
            return func

        return decorator

    mock_mcp.resource = mock_resource_decorator

    # Mock client response
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

    # Register services resources
    register_services_resources(mock_mcp, lambda: mock_client)

    # Call the resource handler
    assert resource_handler is not None
    result = await resource_handler()

    # Verify MIME type is application/json
    assert result.mime_type == "application/json"

    # Verify the response is valid JSON
    try:
        parsed = json.loads(result.text)
        assert isinstance(parsed, dict)
    except json.JSONDecodeError as e:
        pytest.fail(f"Response text must be valid JSON: {e}")


# Feature: mcp-resources-layer, Property 15: MIME Type Consistency (History Resources)
@given(
    entity_id=entity_id_strategy(),
    hours=st.integers(min_value=1, max_value=168),
    limit=st.integers(min_value=1, max_value=1000),
    offset=st.integers(min_value=0, max_value=100),
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_15_history_resource_mime_type_consistency(
    entity_id: str,
    hours: int,
    limit: int,
    offset: int,
):
    """
    **Validates: Requirements 13.1, 13.2, 13.3**

    Property: For any history resource response, the MIME type must be
    application/json.
    """
    # Create mock MCP server and client
    mock_mcp = MagicMock()
    mock_client = AsyncMock()

    # Store the registered resource handler
    resource_handler = None

    def mock_resource_decorator(uri_pattern):
        def decorator(func):
            nonlocal resource_handler
            resource_handler = func
            return func

        return decorator

    mock_mcp.resource = mock_resource_decorator

    # Mock client response
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

    # Register history resources
    register_history_resources(mock_mcp, lambda: mock_client)

    # Call the resource handler
    assert resource_handler is not None
    result = await resource_handler(entity_id, hours, limit, offset)

    # Verify MIME type is application/json
    assert result.mime_type == "application/json"

    # Verify the response is valid JSON
    try:
        parsed = json.loads(result.text)
        assert isinstance(parsed, dict)
    except json.JSONDecodeError as e:
        pytest.fail(f"Response text must be valid JSON: {e}")


# Feature: mcp-resources-layer, Property 15: MIME Type Consistency (Error Responses)
@given(entity_id=entity_id_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_15_error_response_mime_type_consistency(entity_id: str):
    """
    **Validates: Requirements 13.1, 13.2, 13.3**

    Property: For any error response, the MIME type must be application/json.
    """
    # Create mock MCP server and client
    mock_mcp = MagicMock()
    mock_client = AsyncMock()

    # Store the registered resource handler
    resource_handler = None

    def mock_resource_decorator(uri_pattern):
        def decorator(func):
            nonlocal resource_handler
            resource_handler = func
            return func

        return decorator

    mock_mcp.resource = mock_resource_decorator

    # Mock client to raise EntityNotFoundError
    from src.homeassistant_mcp.exceptions import EntityNotFoundError

    mock_client.get_state = AsyncMock(side_effect=EntityNotFoundError(entity_id))

    # Register entity resources
    register_entity_resources(mock_mcp, lambda: mock_client)

    # Call the resource handler
    assert resource_handler is not None
    result = await resource_handler(entity_id)

    # Verify MIME type is application/json even for errors
    assert result.mime_type == "application/json"

    # Verify the error response is valid JSON
    try:
        parsed = json.loads(result.text)
        assert isinstance(parsed, dict)
        assert "error" in parsed, "Error response must contain 'error' field"
    except json.JSONDecodeError as e:
        pytest.fail(f"Error response text must be valid JSON: {e}")


# Feature: mcp-resources-layer, Property 16: Timestamp Format Consistency
@given(entity_id=entity_id_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_16_timestamp_format_consistency_entity(entity_id: str):
    """
    **Validates: Requirement 13.4**

    Property: For any resource response containing timestamps, all timestamp
    fields must be valid ISO8601 format strings.
    """
    # Create mock MCP server and client
    mock_mcp = MagicMock()
    mock_client = AsyncMock()

    # Store the registered resource handler
    resource_handler = None

    def mock_resource_decorator(uri_pattern):
        def decorator(func):
            nonlocal resource_handler
            resource_handler = func
            return func

        return decorator

    mock_mcp.resource = mock_resource_decorator

    # Mock client response with timestamps
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": entity_id,
            "state": "on",
            "attributes": {"friendly_name": "Test Entity"},
            "last_changed": "2024-01-15T10:00:00Z",
            "last_updated": "2024-01-15T10:00:00Z",
        }
    )

    # Register entity resources
    register_entity_resources(mock_mcp, lambda: mock_client)

    # Call the resource handler
    assert resource_handler is not None
    result = await resource_handler(entity_id)

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify last_updated in envelope is ISO8601 (Requirement 13.4)
    assert "last_updated" in parsed, "Response must contain last_updated field"
    assert is_valid_iso8601(
        parsed["last_updated"]
    ), f"last_updated must be valid ISO8601 format, got: {parsed['last_updated']}"

    # Verify timestamps in data are ISO8601
    data = parsed.get("data", {})
    if "last_changed" in data:
        assert is_valid_iso8601(
            data["last_changed"]
        ), f"last_changed must be valid ISO8601 format, got: {data['last_changed']}"

    if "last_updated" in data:
        assert is_valid_iso8601(
            data["last_updated"]
        ), f"last_updated in data must be valid ISO8601 format, got: {data['last_updated']}"


# Feature: mcp-resources-layer, Property 16: Timestamp Format Consistency (History)
@given(entity_id=entity_id_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_16_timestamp_format_consistency_history(entity_id: str):
    """
    **Validates: Requirement 13.4**

    Property: For any history resource response, all timestamp fields in
    history entries must be valid ISO8601 format strings.
    """
    # Create mock MCP server and client
    mock_mcp = MagicMock()
    mock_client = AsyncMock()

    # Store the registered resource handler
    resource_handler = None

    def mock_resource_decorator(uri_pattern):
        def decorator(func):
            nonlocal resource_handler
            resource_handler = func
            return func

        return decorator

    mock_mcp.resource = mock_resource_decorator

    # Mock client response with history entries containing timestamps
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

    # Register history resources
    register_history_resources(mock_mcp, lambda: mock_client)

    # Call the resource handler
    assert resource_handler is not None
    result = await resource_handler(entity_id, 24, 100, 0)

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify last_updated in envelope is ISO8601
    assert "last_updated" in parsed
    assert is_valid_iso8601(parsed["last_updated"])

    # Verify timestamps in history entries are ISO8601
    data = parsed.get("data", {})
    entries = data.get("entries", [])

    for i, entry in enumerate(entries):
        if "last_changed" in entry:
            assert is_valid_iso8601(entry["last_changed"]), (
                f"Entry {i} last_changed must be valid ISO8601 format, "
                f"got: {entry['last_changed']}"
            )

        if "last_updated" in entry:
            assert is_valid_iso8601(entry["last_updated"]), (
                f"Entry {i} last_updated must be valid ISO8601 format, "
                f"got: {entry['last_updated']}"
            )


# Feature: mcp-resources-layer, Property 16: Timestamp Format Consistency (Area)
@given(area_id=area_id_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_16_timestamp_format_consistency_area(area_id: str):
    """
    **Validates: Requirement 13.4**

    Property: For any area resource response, the last_updated timestamp
    must be valid ISO8601 format.
    """
    # Create mock MCP server and client
    mock_mcp = MagicMock()
    mock_client = AsyncMock()

    # Store the registered resource handler
    resource_handler = None

    def mock_resource_decorator(uri_pattern):
        def decorator(func):
            nonlocal resource_handler
            resource_handler = func
            return func

        return decorator

    mock_mcp.resource = mock_resource_decorator

    # Mock client response
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {"friendly_name": "Test Light"},
            }
        ]
    )

    # Register area resources
    register_area_resources(mock_mcp, lambda: mock_client)

    # Call the resource handler
    assert resource_handler is not None
    result = await resource_handler(area_id)

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify last_updated in envelope is ISO8601
    assert "last_updated" in parsed
    assert is_valid_iso8601(
        parsed["last_updated"]
    ), f"last_updated must be valid ISO8601 format, got: {parsed['last_updated']}"


# Feature: mcp-resources-layer, Property 16: Timestamp Format Consistency (Device)
@given(device_id=device_id_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_16_timestamp_format_consistency_device(device_id: str):
    """
    **Validates: Requirement 13.4**

    Property: For any device resource response, the last_updated timestamp
    must be valid ISO8601 format.
    """
    # Create mock MCP server and client
    mock_mcp = MagicMock()
    mock_client = AsyncMock()

    # Store the registered resource handler
    resource_handler = None

    def mock_resource_decorator(uri_pattern):
        def decorator(func):
            nonlocal resource_handler
            resource_handler = func
            return func

        return decorator

    mock_mcp.resource = mock_resource_decorator

    # Mock client response
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

    # Register device resources
    register_device_resources(mock_mcp, lambda: mock_client)

    # Call the resource handler
    assert resource_handler is not None
    result = await resource_handler(device_id)

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify last_updated in envelope is ISO8601
    assert "last_updated" in parsed
    assert is_valid_iso8601(
        parsed["last_updated"]
    ), f"last_updated must be valid ISO8601 format, got: {parsed['last_updated']}"


# Feature: mcp-resources-layer, Property 16: Timestamp Format Consistency (Services)
@pytest.mark.asyncio
async def test_property_16_timestamp_format_consistency_services():
    """
    **Validates: Requirement 13.4**

    Property: For the services resource response, the last_updated timestamp
    must be valid ISO8601 format.
    """
    # Create mock MCP server and client
    mock_mcp = MagicMock()
    mock_client = AsyncMock()

    # Store the registered resource handler
    resource_handler = None

    def mock_resource_decorator(uri_pattern):
        def decorator(func):
            nonlocal resource_handler
            resource_handler = func
            return func

        return decorator

    mock_mcp.resource = mock_resource_decorator

    # Mock client response
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

    # Register services resources
    register_services_resources(mock_mcp, lambda: mock_client)

    # Call the resource handler
    assert resource_handler is not None
    result = await resource_handler()

    # Parse the JSON response
    parsed = json.loads(result.text)

    # Verify last_updated in envelope is ISO8601
    assert "last_updated" in parsed
    assert is_valid_iso8601(
        parsed["last_updated"]
    ), f"last_updated must be valid ISO8601 format, got: {parsed['last_updated']}"
