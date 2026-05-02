"""Property-based tests for camera proxy functionality.

Feature: rest-api-overhaul
Properties: 18, 19, 20, 46, 47, 48
"""

import base64
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from homeassistant_mcp.exceptions import EntityNotFoundError, HomeAssistantError
from homeassistant_mcp.tools.specialized.camera_proxy import register_camera_proxy_tool

# Strategies for generating test data
entity_id_strategy = st.from_regex(r"^[a-z_]+\.[a-z0-9_]+$", fullmatch=True)

dimension_strategy = st.integers(min_value=1, max_value=4096)

image_data_strategy = st.binary(min_size=100, max_size=10000)


def create_mock_mcp():
    """Create a mock MCP server."""
    mcp = MagicMock()
    # Store the registered tool function
    registered_tool = None

    def tool_decorator():
        def decorator(func):
            nonlocal registered_tool
            registered_tool = func
            return func

        return decorator

    mcp.tool = tool_decorator
    mcp.get_registered_tool = lambda: registered_tool
    return mcp


def create_mock_client():
    """Create a mock HomeAssistantClient."""
    return AsyncMock()


def create_get_client(mock_client):
    """Create a get_client function."""
    return lambda: mock_client


# Feature: rest-api-overhaul, Property 18: Camera Image Response Structure
@given(entity_id=entity_id_strategy, image_data=image_data_strategy)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_18_camera_image_response_structure(entity_id, image_data):
    """
    Property 18: For any valid camera entity, the response SHALL contain
    image data in the requested format (base64 or binary).

    Validates: Requirements 8.1, 8.6
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock to return image data
    mock_client.get_camera_proxy = AsyncMock(return_value=image_data)

    # Register tool
    register_camera_proxy_tool(mock_mcp, get_client)
    camera_proxy_get = mock_mcp.get_registered_tool()

    # Test base64 format
    result_base64 = await camera_proxy_get(entity_id=entity_id, return_base64=True)

    assert result_base64["success"] is True
    assert "image_data" in result_base64
    assert "content_type" in result_base64
    assert result_base64["entity_id"] == entity_id

    # Verify base64 data can be decoded back to original
    decoded = base64.b64decode(result_base64["image_data"])
    assert decoded == image_data

    # Test binary format
    result_binary = await camera_proxy_get(entity_id=entity_id, return_base64=False)

    assert result_binary["success"] is True
    assert "image_bytes" in result_binary
    assert "content_type" in result_binary
    assert result_binary["entity_id"] == entity_id
    assert result_binary["image_bytes"] == image_data


# Feature: rest-api-overhaul, Property 19: Camera Image Resizing
@given(
    entity_id=entity_id_strategy,
    width=dimension_strategy,
    height=dimension_strategy,
    image_data=image_data_strategy,
)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_19_camera_image_resizing(entity_id, width, height, image_data):
    """
    Property 19: For any camera image request with width or height parameters,
    the returned image dimensions SHALL match the requested dimensions.

    Validates: Requirements 8.2, 8.3

    Note: This test verifies that dimension parameters are passed to the client
    and included in the response. Actual image resizing is performed by Home Assistant.
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock
    mock_client.get_camera_proxy = AsyncMock(return_value=image_data)

    # Register tool
    register_camera_proxy_tool(mock_mcp, get_client)
    camera_proxy_get = mock_mcp.get_registered_tool()

    # Test with width parameter
    result_width = await camera_proxy_get(entity_id=entity_id, width=width)

    assert result_width["success"] is True
    assert result_width["width"] == width
    mock_client.get_camera_proxy.assert_called_with(entity_id=entity_id, width=width, height=None)

    # Reset mock
    mock_client.get_camera_proxy.reset_mock()

    # Test with height parameter
    result_height = await camera_proxy_get(entity_id=entity_id, height=height)

    assert result_height["success"] is True
    assert result_height["height"] == height
    mock_client.get_camera_proxy.assert_called_with(entity_id=entity_id, width=None, height=height)

    # Reset mock
    mock_client.get_camera_proxy.reset_mock()

    # Test with both parameters
    result_both = await camera_proxy_get(entity_id=entity_id, width=width, height=height)

    assert result_both["success"] is True
    assert result_both["width"] == width
    assert result_both["height"] == height
    mock_client.get_camera_proxy.assert_called_with(entity_id=entity_id, width=width, height=height)


# Feature: rest-api-overhaul, Property 20: Invalid Camera Error Handling
@given(entity_id=entity_id_strategy, error_message=st.text(min_size=1, max_size=200))
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_20_invalid_camera_error_handling(entity_id, error_message):
    """
    Property 20: For any non-existent camera entity or failed camera access,
    the response SHALL return an appropriate error message.

    Validates: Requirements 8.4, 8.5
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock to raise EntityNotFoundError
    mock_client.get_camera_proxy = AsyncMock(side_effect=EntityNotFoundError(error_message))

    # Register tool
    register_camera_proxy_tool(mock_mcp, get_client)
    camera_proxy_get = mock_mcp.get_registered_tool()

    # Test error handling
    result = await camera_proxy_get(entity_id=entity_id)

    assert result["success"] is False
    assert "error" in result
    assert "error_type" in result
    assert result["entity_id"] == entity_id
    assert error_message in result["error"]


# Feature: rest-api-overhaul, Property 46: Binary Data Handling
@given(entity_id=entity_id_strategy, image_data=image_data_strategy)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_46_binary_data_handling(entity_id, image_data):
    """
    Property 46: For any binary response (camera images), the data SHALL be
    handled correctly as bytes and support both binary and base64 encoding.

    Validates: Requirements 19.1, 19.2
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock
    mock_client.get_camera_proxy = AsyncMock(return_value=image_data)

    # Register tool
    register_camera_proxy_tool(mock_mcp, get_client)
    camera_proxy_get = mock_mcp.get_registered_tool()

    # Test binary format preserves data integrity
    result_binary = await camera_proxy_get(entity_id=entity_id, return_base64=False)

    assert result_binary["success"] is True
    assert isinstance(result_binary["image_bytes"], bytes)
    assert result_binary["image_bytes"] == image_data

    # Test base64 format preserves data integrity
    result_base64 = await camera_proxy_get(entity_id=entity_id, return_base64=True)

    assert result_base64["success"] is True
    assert isinstance(result_base64["image_data"], str)

    # Verify round-trip: original -> base64 -> decoded == original
    decoded_data = base64.b64decode(result_base64["image_data"])
    assert decoded_data == image_data


# Feature: rest-api-overhaul, Property 47: Binary Response Content Type
@given(entity_id=entity_id_strategy, image_data=image_data_strategy)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_47_binary_response_content_type(entity_id, image_data):
    """
    Property 47: For any binary response, the content type information
    SHALL be included in the response metadata.

    Validates: Requirements 19.3
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock
    mock_client.get_camera_proxy = AsyncMock(return_value=image_data)

    # Register tool
    register_camera_proxy_tool(mock_mcp, get_client)
    camera_proxy_get = mock_mcp.get_registered_tool()

    # Test content type is included
    result = await camera_proxy_get(entity_id=entity_id)

    assert result["success"] is True
    assert "content_type" in result
    assert isinstance(result["content_type"], str)
    assert result["content_type"].startswith("image/")


# Feature: rest-api-overhaul, Property 48: Binary Data Error Handling
@given(entity_id=entity_id_strategy, error_message=st.text(min_size=1, max_size=200))
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_48_binary_data_error_handling(entity_id, error_message):
    """
    Property 48: For any failed binary data retrieval, the response
    SHALL return an appropriate error message.

    Validates: Requirements 19.4
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock to raise HomeAssistantError
    mock_client.get_camera_proxy = AsyncMock(side_effect=HomeAssistantError(error_message))

    # Register tool
    register_camera_proxy_tool(mock_mcp, get_client)
    camera_proxy_get = mock_mcp.get_registered_tool()

    # Test error handling for both formats
    result_base64 = await camera_proxy_get(entity_id=entity_id, return_base64=True)

    assert result_base64["success"] is False
    assert "error" in result_base64
    assert error_message in result_base64["error"]

    result_binary = await camera_proxy_get(entity_id=entity_id, return_base64=False)

    assert result_binary["success"] is False
    assert "error" in result_binary
    assert error_message in result_binary["error"]
