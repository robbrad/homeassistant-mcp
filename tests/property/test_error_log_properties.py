"""Property-based tests for error log retrieval tool.

This module tests the following properties:
- Property 16: Error Log Response Format
- Property 17: Error Log Access Error Handling

Validates Requirements: 7.1-7.4
"""

from unittest.mock import AsyncMock, Mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.homeassistant_mcp.tools.history.error_log import register_error_log_tool


# Custom strategies for generating test data
@st.composite
def error_log_content_strategy(draw):
    """Generate valid error log content (plain text)."""
    # Generate either empty string or error log content
    is_empty = draw(st.booleans())

    if is_empty:
        return ""

    # Generate realistic error log content
    log_lines = []
    num_lines = draw(st.integers(min_value=1, max_value=10))

    for _ in range(num_lines):
        # Generate timestamp
        timestamp = "2024-01-15 10:00:00"

        # Generate log level
        level = draw(st.sampled_from(["ERROR", "WARNING", "CRITICAL", "INFO"]))

        # Generate component
        component = draw(
            st.sampled_from(
                [
                    "homeassistant.core",
                    "homeassistant.components.light",
                    "homeassistant.components.sensor",
                    "custom_components.test",
                ]
            )
        )

        # Generate message
        messages = [
            "Connection timeout",
            "Entity not found",
            "Invalid configuration",
            "Service call failed",
            "Authentication error",
        ]
        message = draw(st.sampled_from(messages))

        log_lines.append(f"{timestamp} {level} ({component}) {message}")

    return "\n".join(log_lines)


# Feature: rest-api-overhaul, Property 16: Error Log Response Format
@given(error_log_content=error_log_content_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_16_error_log_response_format(error_log_content: str):
    """
    Property 16: Error Log Response Format

    For any error log request, the response SHALL return plain text content
    or an empty string if no errors exist.

    Validates: Requirements 7.1, 7.2, 7.4
    """
    # Create mock client
    mock_client = Mock()
    mock_client.get_error_log = AsyncMock(return_value=error_log_content)

    # Create mock MCP server
    mock_mcp = Mock()
    tool_func = None

    def mock_tool():
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp.tool = mock_tool

    # Register tool
    register_error_log_tool(mock_mcp, lambda: mock_client)

    # Call the tool
    result = await tool_func()

    # Verify success
    assert result["success"] is True

    # Verify response structure
    assert "error_log" in result
    assert "log_size" in result
    assert "has_errors" in result

    # Verify error_log is plain text (string)
    assert isinstance(result["error_log"], str)
    assert result["error_log"] == error_log_content

    # Verify log_size matches content length
    assert result["log_size"] == len(error_log_content)

    # Verify has_errors flag
    expected_has_errors = len(error_log_content) > 0
    assert result["has_errors"] == expected_has_errors

    # If empty, verify it's truly empty
    if not error_log_content:
        assert result["error_log"] == ""
        assert result["log_size"] == 0
        assert result["has_errors"] is False


# Feature: rest-api-overhaul, Property 17: Error Log Access Error Handling
@given(
    error_type=st.sampled_from(["authentication_error", "connection_error", "service_call_error"])
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_17_error_log_access_error_handling(error_type: str):
    """
    Property 17: Error Log Access Error Handling

    For any failed error log access, the response SHALL return an
    appropriate error message.

    Validates: Requirements 7.3
    """
    from src.homeassistant_mcp.exceptions import (
        AuthenticationError,
        ConnectionError,
        ServiceCallError,
    )

    # Map error types to exception classes
    error_map = {
        "authentication_error": AuthenticationError("Invalid token"),
        "connection_error": ConnectionError("Failed to connect"),
        "service_call_error": ServiceCallError("Service call failed"),
    }

    # Create mock client that raises the specified error
    mock_client = Mock()
    mock_client.get_error_log = AsyncMock(side_effect=error_map[error_type])

    # Create mock MCP server
    mock_mcp = Mock()
    tool_func = None

    def mock_tool():
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp.tool = mock_tool

    # Register tool
    register_error_log_tool(mock_mcp, lambda: mock_client)

    # Call the tool
    result = await tool_func()

    # Verify error response
    assert result["success"] is False
    assert "error" in result
    assert "error_type" in result

    # Verify error type matches
    assert result["error_type"] == error_type

    # Verify error message is descriptive
    assert isinstance(result["error"], str)
    assert len(result["error"]) > 0


# Additional property test: Error log content is always a string
@given(
    # Test with various potential return types to ensure string handling
    mock_return=st.one_of(
        st.text(min_size=0, max_size=1000),  # Normal text
        st.just(""),  # Empty string
    )
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_error_log_always_returns_string(mock_return: str):
    """
    Verify that error_log field is always a string, regardless of content.

    This ensures consistent response format for AI assistants.
    """
    # Create mock client
    mock_client = Mock()
    mock_client.get_error_log = AsyncMock(return_value=mock_return)

    # Create mock MCP server
    mock_mcp = Mock()
    tool_func = None

    def mock_tool():
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp.tool = mock_tool

    # Register tool
    register_error_log_tool(mock_mcp, lambda: mock_client)

    # Call the tool
    result = await tool_func()

    # Verify error_log is always a string
    assert isinstance(result["error_log"], str)
    assert result["error_log"] == mock_return


# Property test: log_size and has_errors consistency
@given(error_log_content=st.text(min_size=0, max_size=5000))
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_log_size_and_has_errors_consistency(error_log_content: str):
    """
    Verify that log_size and has_errors are always consistent.

    has_errors should be True if and only if log_size > 0.
    """
    # Create mock client
    mock_client = Mock()
    mock_client.get_error_log = AsyncMock(return_value=error_log_content)

    # Create mock MCP server
    mock_mcp = Mock()
    tool_func = None

    def mock_tool():
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp.tool = mock_tool

    # Register tool
    register_error_log_tool(mock_mcp, lambda: mock_client)

    # Call the tool
    result = await tool_func()

    # Verify consistency
    log_size = result["log_size"]
    has_errors = result["has_errors"]

    # has_errors should be True if and only if log_size > 0
    assert has_errors == (log_size > 0)

    # log_size should match actual content length
    assert log_size == len(error_log_content)
