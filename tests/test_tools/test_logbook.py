"""Unit tests for logbook query tool."""

from unittest.mock import AsyncMock, Mock

import pytest

from src.homeassistant_mcp.exceptions import (
    AuthenticationError,
    ConnectionError,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.history.logbook import register_logbook_tool


@pytest.mark.asyncio
async def test_logbook_query_success():
    """Test successful logbook query."""
    # Mock logbook data
    timestamp = "2024-01-15T10:00:00Z"
    mock_logbook = [
        {
            "when": "2024-01-15T10:05:00Z",
            "name": "Living Room Light",
            "message": "turned on",
            "domain": "light",
            "entity_id": "light.living_room",
        },
        {
            "when": "2024-01-15T10:10:00Z",
            "name": "Front Door",
            "message": "opened",
            "domain": "binary_sensor",
            "entity_id": "binary_sensor.front_door",
        },
    ]

    # Create mock client
    mock_client = Mock()
    mock_client.get_logbook = AsyncMock(return_value=mock_logbook)

    # Create mock MCP server
    mock_mcp = Mock()
    tool_func = None

    def mock_tool(**kwargs):
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp.tool = mock_tool

    # Register tool
    register_logbook_tool(mock_mcp, lambda: mock_client)

    # Call the tool
    result = await tool_func(timestamp=timestamp)

    # Verify result
    assert result["success"] is True
    assert result["timestamp"] == timestamp
    assert result["end_time"] is None
    assert result["entity"] is None
    assert result["limit"] == 100
    assert result["entry_count"] == 2
    assert result["truncated"] is False
    assert result["logbook"] == mock_logbook

    # Verify client was called correctly
    mock_client.get_logbook.assert_called_once_with(
        timestamp=timestamp, end_time=None, entity=None, limit=100
    )


@pytest.mark.asyncio
async def test_logbook_query_with_entity_filter():
    """Test logbook query with entity filter."""
    timestamp = "2024-01-15T10:00:00Z"
    entity = "light.living_room"

    mock_logbook = [
        {
            "when": "2024-01-15T10:05:00Z",
            "name": "Living Room Light",
            "message": "turned on",
            "domain": "light",
            "entity_id": entity,
        }
    ]

    # Create mock client
    mock_client = Mock()
    mock_client.get_logbook = AsyncMock(return_value=mock_logbook)

    # Create mock MCP server
    mock_mcp = Mock()
    tool_func = None

    def mock_tool(**kwargs):
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp.tool = mock_tool

    # Register tool
    register_logbook_tool(mock_mcp, lambda: mock_client)

    # Call the tool with entity filter
    result = await tool_func(timestamp=timestamp, entity=entity)

    # Verify result
    assert result["success"] is True
    assert result["entity"] == entity
    assert result["entry_count"] == 1
    assert len(result["logbook"]) == 1
    assert result["logbook"][0]["entity_id"] == entity

    # Verify client was called with entity filter
    mock_client.get_logbook.assert_called_once_with(
        timestamp=timestamp, end_time=None, entity=entity, limit=100
    )


@pytest.mark.asyncio
async def test_logbook_query_with_time_range():
    """Test logbook query with start and end time."""
    timestamp = "2024-01-15T10:00:00Z"
    end_time = "2024-01-15T12:00:00Z"

    mock_logbook = [
        {
            "when": "2024-01-15T11:00:00Z",
            "name": "Test Entity",
            "message": "changed",
            "domain": "sensor",
            "entity_id": "sensor.test",
        }
    ]

    # Create mock client
    mock_client = Mock()
    mock_client.get_logbook = AsyncMock(return_value=mock_logbook)

    # Create mock MCP server
    mock_mcp = Mock()
    tool_func = None

    def mock_tool(**kwargs):
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp.tool = mock_tool

    # Register tool
    register_logbook_tool(mock_mcp, lambda: mock_client)

    # Call the tool with time range
    result = await tool_func(timestamp=timestamp, end_time=end_time)

    # Verify result
    assert result["success"] is True
    assert result["timestamp"] == timestamp
    assert result["end_time"] == end_time

    # Verify client was called with time range
    mock_client.get_logbook.assert_called_once_with(
        timestamp=timestamp, end_time=end_time, entity=None, limit=100
    )


@pytest.mark.asyncio
async def test_logbook_query_with_custom_limit():
    """Test logbook query with custom limit."""
    timestamp = "2024-01-15T10:00:00Z"
    limit = 50

    # Create mock logbook with exactly limit entries
    mock_logbook = [
        {
            "when": f"2024-01-15T10:{i:02d}:00Z",
            "name": f"Entity {i}",
            "message": "changed",
            "domain": "sensor",
            "entity_id": f"sensor.test_{i}",
        }
        for i in range(limit)
    ]

    # Create mock client
    mock_client = Mock()
    mock_client.get_logbook = AsyncMock(return_value=mock_logbook)

    # Create mock MCP server
    mock_mcp = Mock()
    tool_func = None

    def mock_tool(**kwargs):
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp.tool = mock_tool

    # Register tool
    register_logbook_tool(mock_mcp, lambda: mock_client)

    # Call the tool with custom limit
    result = await tool_func(timestamp=timestamp, limit=limit)

    # Verify result
    assert result["success"] is True
    assert result["limit"] == limit
    assert result["entry_count"] == limit
    assert result["truncated"] is True  # Hit the limit

    # Verify client was called with custom limit
    mock_client.get_logbook.assert_called_once_with(
        timestamp=timestamp, end_time=None, entity=None, limit=limit
    )


@pytest.mark.asyncio
async def test_logbook_query_empty_result():
    """Test logbook query with no entries."""
    timestamp = "2024-01-15T10:00:00Z"

    # Create mock client returning empty list
    mock_client = Mock()
    mock_client.get_logbook = AsyncMock(return_value=[])

    # Create mock MCP server
    mock_mcp = Mock()
    tool_func = None

    def mock_tool(**kwargs):
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp.tool = mock_tool

    # Register tool
    register_logbook_tool(mock_mcp, lambda: mock_client)

    # Call the tool
    result = await tool_func(timestamp=timestamp)

    # Verify result
    assert result["success"] is True
    assert result["entry_count"] == 0
    assert result["truncated"] is False
    assert result["logbook"] == []


@pytest.mark.asyncio
async def test_logbook_query_authentication_error():
    """Test logbook query with authentication error."""
    timestamp = "2024-01-15T10:00:00Z"

    # Create mock client that raises AuthenticationError
    mock_client = Mock()
    mock_client.get_logbook = AsyncMock(side_effect=AuthenticationError("Invalid token"))

    # Create mock MCP server
    mock_mcp = Mock()
    tool_func = None

    def mock_tool(**kwargs):
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp.tool = mock_tool

    # Register tool
    register_logbook_tool(mock_mcp, lambda: mock_client)

    # Call the tool
    result = await tool_func(timestamp=timestamp)

    # Verify error response
    assert result["success"] is False
    assert result["error_type"] == "authentication_error"
    assert "Invalid token" in result["error"]


@pytest.mark.asyncio
async def test_logbook_query_connection_error():
    """Test logbook query with connection error."""
    timestamp = "2024-01-15T10:00:00Z"

    # Create mock client that raises ConnectionError
    mock_client = Mock()
    mock_client.get_logbook = AsyncMock(side_effect=ConnectionError("Failed to connect"))

    # Create mock MCP server
    mock_mcp = Mock()
    tool_func = None

    def mock_tool(**kwargs):
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp.tool = mock_tool

    # Register tool
    register_logbook_tool(mock_mcp, lambda: mock_client)

    # Call the tool
    result = await tool_func(timestamp=timestamp)

    # Verify error response
    assert result["success"] is False
    assert result["error_type"] == "connection_error"
    assert "Failed to connect" in result["error"]


@pytest.mark.asyncio
async def test_logbook_query_invalid_timestamp():
    """Test logbook query with invalid timestamp format."""
    invalid_timestamp = "not-a-timestamp"

    # Create mock client that raises ServiceCallError
    mock_client = Mock()
    mock_client.get_logbook = AsyncMock(
        side_effect=ServiceCallError(f"Invalid timestamp format: {invalid_timestamp}")
    )

    # Create mock MCP server
    mock_mcp = Mock()
    tool_func = None

    def mock_tool(**kwargs):
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp.tool = mock_tool

    # Register tool
    register_logbook_tool(mock_mcp, lambda: mock_client)

    # Call the tool with invalid timestamp
    result = await tool_func(timestamp=invalid_timestamp)

    # Verify error response
    assert result["success"] is False
    assert "error" in result
    assert "timestamp" in result["error"].lower()
