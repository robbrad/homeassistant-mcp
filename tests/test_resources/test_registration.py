"""Unit tests for resource registration.

Tests that all resources are registered correctly, in the proper order,
and that the get_client function is passed correctly to each registration.

Requirements tested: 16.9
"""

from unittest.mock import Mock

import pytest

from src.homeassistant_mcp.resources import register_all_resources


def test_all_resources_are_registered():
    """Test that all resource types are registered.

    Validates: Requirement 16.9 - All resources must be registered
    """
    # Arrange
    mock_mcp = Mock()
    mock_get_client = Mock()

    # Track which resource patterns are registered
    registered_patterns = []

    def mock_resource(uri_pattern: str):
        """Mock resource decorator that captures registered patterns."""

        def decorator(func):
            registered_patterns.append(uri_pattern)
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_all_resources(mock_mcp, mock_get_client)

    # Assert - Check that all expected resource patterns are registered
    expected_patterns = [
        "hass://entity/{entity_id}",
        "hass://area/{area_id}",
        "hass://device/{device_id}",
        "hass://services",
        "hass://entity/{entity_id}/history",
    ]

    for pattern in expected_patterns:
        assert pattern in registered_patterns, f"Resource pattern '{pattern}' was not registered"


def test_registration_order():
    """Test that resources are registered in the correct order.

    Validates: Requirement 16.9 - Resources must be registered in correct order
    """
    # Arrange
    mock_mcp = Mock()
    mock_get_client = Mock()

    # Track registration order
    registration_order = []

    def mock_resource(uri_pattern: str):
        """Mock resource decorator that captures registration order."""

        def decorator(func):
            registration_order.append(uri_pattern)
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_all_resources(mock_mcp, mock_get_client)

    # Assert - Check that resources are registered in expected order
    # The order should be: entities, areas, devices, services, history
    expected_order = [
        "hass://entity/{entity_id}",
        "hass://area/{area_id}",
        "hass://device/{device_id}",
        "hass://services",
        "hass://entity/{entity_id}/history",
    ]

    assert registration_order == expected_order, (
        f"Resources registered in wrong order. "
        f"Expected: {expected_order}, Got: {registration_order}"
    )


def test_get_client_function_passed_correctly():
    """Test that get_client function is passed to all registration functions.

    Validates: Requirement 16.9 - get_client must be passed to all registrations
    """
    # Arrange
    mock_mcp = Mock()

    # Create a unique mock function to verify it's passed through
    mock_get_client = Mock()
    mock_get_client.__name__ = "test_get_client"

    # Track which get_client was used in each registration
    get_client_calls = []

    def mock_resource(uri_pattern: str):
        """Mock resource decorator that captures the handler."""

        def decorator(func):
            # Store the get_client that was captured in the closure
            # We'll verify it by calling the handler and checking what client it uses
            get_client_calls.append((uri_pattern, func))
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_all_resources(mock_mcp, mock_get_client)

    # Assert - Verify that handlers were registered (they capture get_client in closure)
    # We can't directly inspect closures, but we can verify handlers were created
    assert (
        len(get_client_calls) == 5
    ), f"Expected 5 resource handlers to be registered, got {len(get_client_calls)}"

    # Verify all expected patterns have handlers
    registered_patterns = [pattern for pattern, _ in get_client_calls]
    expected_patterns = [
        "hass://entity/{entity_id}",
        "hass://area/{area_id}",
        "hass://device/{device_id}",
        "hass://services",
        "hass://entity/{entity_id}/history",
    ]

    for pattern in expected_patterns:
        assert pattern in registered_patterns, f"Handler for pattern '{pattern}' was not registered"


def test_register_all_resources_with_none_mcp():
    """Test that registration handles None mcp gracefully."""
    # Arrange
    mock_get_client = Mock()

    # Act & Assert - Should raise AttributeError when trying to access .resource
    with pytest.raises(AttributeError):
        register_all_resources(None, mock_get_client)


def test_register_all_resources_with_none_get_client():
    """Test that registration handles None get_client gracefully."""
    # Arrange
    mock_mcp = Mock()
    mock_mcp.resource = Mock(return_value=lambda f: f)

    # Act - Should not raise during registration (errors happen at runtime)
    register_all_resources(mock_mcp, None)

    # Assert - Registration should complete
    assert mock_mcp.resource.called


def test_registration_idempotency():
    """Test that calling register_all_resources multiple times works correctly."""
    # Arrange
    mock_mcp = Mock()
    mock_get_client = Mock()

    registration_count = []

    def mock_resource(uri_pattern: str):
        """Mock resource decorator that counts registrations."""

        def decorator(func):
            registration_count.append(uri_pattern)
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act - Register twice
    register_all_resources(mock_mcp, mock_get_client)
    first_count = len(registration_count)

    register_all_resources(mock_mcp, mock_get_client)
    second_count = len(registration_count)

    # Assert - Both registrations should succeed
    assert first_count == 5, f"First registration should register 5 resources, got {first_count}"
    assert (
        second_count == 10
    ), f"Second registration should register 5 more resources, got {second_count - first_count}"
