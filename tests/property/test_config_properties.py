"""Property-based tests for configuration check functionality.

Feature: rest-api-overhaul
Properties: 29
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from homeassistant_mcp.exceptions import ServiceCallError
from homeassistant_mcp.tools.specialized.config_check import register_config_check_tool

# Strategies for generating test data
error_message_strategy = st.text(
    min_size=10,
    max_size=200,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" .,:-_"),
)

warning_message_strategy = st.text(
    min_size=10,
    max_size=200,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" .,:-_"),
)


def create_mock_mcp():
    """Create a mock MCP server."""
    mcp = MagicMock()
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


# Feature: rest-api-overhaul, Property 29: Configuration Check Response Structure
@given(
    errors=st.lists(error_message_strategy, min_size=0, max_size=5),
    warnings=st.lists(warning_message_strategy, min_size=0, max_size=5),
)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_29_configuration_check_response_structure(errors, warnings):
    """
    Property 29: For any configuration check request, the response SHALL contain
    result status and lists of errors and warnings.

    Validates: Requirements 11.1, 11.2, 11.3, 11.4
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock to return configuration check result
    check_result = {"errors": errors, "warnings": warnings}
    mock_client.check_config = AsyncMock(return_value=check_result)

    # Register tool
    register_config_check_tool(mock_mcp, get_client)
    config_check = mock_mcp.get_registered_tool()

    # Test configuration check
    result = await config_check()

    assert result["success"] is True
    assert "result" in result
    assert "errors" in result
    assert "warnings" in result

    # Verify result status
    if len(errors) == 0:
        assert result["result"] == "valid"
    else:
        assert result["result"] == "invalid"

    # Verify errors and warnings are lists
    assert isinstance(result["errors"], list)
    assert isinstance(result["warnings"], list)

    # Verify error and warning content
    assert len(result["errors"]) == len(errors)
    assert len(result["warnings"]) == len(warnings)

    for error in errors:
        assert error in result["errors"]

    for warning in warnings:
        assert warning in result["warnings"]


# Test: Valid configuration (no errors)
@given(warnings=st.lists(warning_message_strategy, min_size=0, max_size=3))
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_valid_configuration_no_errors(warnings):
    """
    Test that a valid configuration (no errors) returns result="valid".

    Validates: Requirement 11.2
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock with no errors
    check_result = {"errors": [], "warnings": warnings}
    mock_client.check_config = AsyncMock(return_value=check_result)

    # Register tool
    register_config_check_tool(mock_mcp, get_client)
    config_check = mock_mcp.get_registered_tool()

    # Test
    result = await config_check()

    assert result["success"] is True
    assert result["result"] == "valid"
    assert len(result["errors"]) == 0
    assert len(result["warnings"]) == len(warnings)


# Test: Invalid configuration (with errors)
@given(
    errors=st.lists(error_message_strategy, min_size=1, max_size=5),
    warnings=st.lists(warning_message_strategy, min_size=0, max_size=3),
)
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_invalid_configuration_with_errors(errors, warnings):
    """
    Test that an invalid configuration (with errors) returns result="invalid"
    and includes detailed error messages.

    Validates: Requirement 11.3
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock with errors
    check_result = {"errors": errors, "warnings": warnings}
    mock_client.check_config = AsyncMock(return_value=check_result)

    # Register tool
    register_config_check_tool(mock_mcp, get_client)
    config_check = mock_mcp.get_registered_tool()

    # Test
    result = await config_check()

    assert result["success"] is True
    assert result["result"] == "invalid"
    assert len(result["errors"]) > 0

    # Verify all errors are present
    for error in errors:
        assert error in result["errors"]


# Test: Configuration with warnings
@given(warnings=st.lists(warning_message_strategy, min_size=1, max_size=5))
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_configuration_with_warnings(warnings):
    """
    Test that configuration warnings are returned in the response.

    Validates: Requirement 11.4
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock with warnings but no errors
    check_result = {"errors": [], "warnings": warnings}
    mock_client.check_config = AsyncMock(return_value=check_result)

    # Register tool
    register_config_check_tool(mock_mcp, get_client)
    config_check = mock_mcp.get_registered_tool()

    # Test
    result = await config_check()

    assert result["success"] is True
    assert result["result"] == "valid"  # Still valid with only warnings
    assert len(result["warnings"]) > 0

    # Verify all warnings are present
    for warning in warnings:
        assert warning in result["warnings"]


# Test: Configuration check error handling
@given(error_message=st.text(min_size=10, max_size=200))
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_configuration_check_error_handling(error_message):
    """
    Test that errors during configuration check are handled gracefully.

    Validates: Requirement 11.5 (validation without restart)
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock to raise an error
    mock_client.check_config = AsyncMock(side_effect=ServiceCallError(error_message))

    # Register tool
    register_config_check_tool(mock_mcp, get_client)
    config_check = mock_mcp.get_registered_tool()

    # Test error handling
    result = await config_check()

    assert result["success"] is False
    assert "error" in result
    assert "error_type" in result
    assert error_message in result["error"]
    assert result["error_type"] == "ServiceCallError"


# Test: Non-list error/warning format handling
@given(
    error_string=st.text(min_size=10, max_size=100),
    warning_string=st.text(min_size=10, max_size=100),
)
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_non_list_error_warning_format(error_string, warning_string):
    """
    Test that non-list error/warning formats are normalized to lists.

    Some Home Assistant versions may return strings instead of lists.
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock with string format (not list)
    check_result = {
        "errors": error_string,  # String instead of list
        "warnings": warning_string,  # String instead of list
    }
    mock_client.check_config = AsyncMock(return_value=check_result)

    # Register tool
    register_config_check_tool(mock_mcp, get_client)
    config_check = mock_mcp.get_registered_tool()

    # Test
    result = await config_check()

    assert result["success"] is True

    # Verify errors and warnings are normalized to lists
    assert isinstance(result["errors"], list)
    assert isinstance(result["warnings"], list)

    # Verify content is preserved
    assert str(error_string) in result["errors"]
    assert str(warning_string) in result["warnings"]
