"""Property-based tests for resource discovery.

Tests universal correctness properties for MCP resource discovery functionality.

Feature: mcp-resources-layer
Properties tested:
- Property 13: Resource Discovery Completeness
"""

from unittest.mock import AsyncMock, Mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.homeassistant_mcp.resources import register_all_resources


# Feature: mcp-resources-layer, Property 13: Resource Discovery Completeness
@given(
    # Generate random entity states to ensure discovery works with any data
    entity_count=st.integers(min_value=0, max_value=100),
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_property_13_resource_discovery_completeness(entity_count: int):
    """Property 13: Resource Discovery Completeness.

    For any call to list_resources, the response must include at minimum:
    - The static hass://services URI
    - Resource templates for entity, area, device, and history resources

    Validates: Requirements 10.1, 10.2, 10.3
    """
    # Arrange - Create mock client with random number of entities
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": f"test.entity_{i}",
                "state": "on",
                "attributes": {"friendly_name": f"Test Entity {i}"},
            }
            for i in range(entity_count)
        ]
    )
    mock_client.get_services = AsyncMock(return_value={})

    def get_client():
        return mock_client

    # Create mock MCP server that tracks registered resources
    mock_mcp = Mock()
    registered_resources = []

    def mock_resource(uri_pattern: str):
        """Mock resource decorator that tracks registered URIs."""

        def decorator(func):
            # Store the resource pattern
            registered_resources.append(
                {
                    "uri_pattern": uri_pattern,
                    "handler": func,
                }
            )
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act - Register all resources
    register_all_resources(mock_mcp, get_client)

    # Assert - Verify minimum required resources are registered
    uri_patterns = [r["uri_pattern"] for r in registered_resources]

    # Requirement 10.2: Must include static services URI
    assert (
        "hass://services" in uri_patterns
    ), "Resource discovery must include static hass://services URI"

    # Requirement 10.3: Must include resource templates
    required_templates = [
        "hass://entity/{entity_id}",
        "hass://area/{area_id}",
        "hass://device/{device_id}",
        "hass://entity/{entity_id}/history",
    ]

    for template in required_templates:
        assert template in uri_patterns, f"Resource discovery must include template: {template}"

    # Requirement 10.1: Must return a list of available resource URIs
    assert len(uri_patterns) >= 5, (
        "Resource discovery must return at least 5 resource patterns " "(services + 4 templates)"
    )

    # Additional validation: Verify all URIs use hass:// scheme
    for uri in uri_patterns:
        assert uri.startswith("hass://"), f"All resource URIs must use hass:// scheme, found: {uri}"


# Additional property test: Resource templates must be valid URI patterns
@given(
    template_segment=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=97),
        min_size=1,
        max_size=20,
    )
)
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_resource_templates_use_valid_uri_patterns(template_segment: str):
    """Property: Resource templates must use valid RFC6570 URI patterns.

    For any resource template, dynamic segments must be enclosed in curly braces
    and follow RFC6570 syntax.
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])
    mock_client.get_services = AsyncMock(return_value={})

    def get_client():
        return mock_client

    mock_mcp = Mock()
    registered_resources = []

    def mock_resource(uri_pattern: str):
        def decorator(func):
            registered_resources.append(uri_pattern)
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_all_resources(mock_mcp, get_client)

    # Assert - Verify all templates with dynamic segments use proper syntax
    for uri in registered_resources:
        if "{" in uri:
            # Must have matching closing brace
            assert uri.count("{") == uri.count(
                "}"
            ), f"URI template must have matching braces: {uri}"

            # Extract dynamic segments
            import re

            segments = re.findall(r"\{([^}]+)\}", uri)

            # Each segment must be a valid identifier
            for segment in segments:
                # Remove query parameter prefix if present
                clean_segment = segment.lstrip("?")

                # Must be alphanumeric with underscores
                assert re.match(
                    r"^[a-zA-Z_][a-zA-Z0-9_]*$", clean_segment
                ), f"URI template segment must be valid identifier: {segment} in {uri}"


# Property test: Resource discovery must be consistent across multiple calls
@given(dummy=st.integers(min_value=0, max_value=10))
@settings(max_examples=20, deadline=None)
@pytest.mark.asyncio
@pytest.mark.property_test
async def test_resource_discovery_consistency(dummy: int):
    """Property: Resource discovery must return consistent results across calls.

    For any MCP server instance, calling list_resources multiple times
    must return the same set of resources.
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])
    mock_client.get_services = AsyncMock(return_value={})

    def get_client():
        return mock_client

    # Create two separate mock MCP instances
    mock_mcp_1 = Mock()
    registered_resources_1 = []

    def mock_resource_1(uri_pattern: str):
        def decorator(func):
            registered_resources_1.append(uri_pattern)
            return func

        return decorator

    mock_mcp_1.resource = mock_resource_1

    mock_mcp_2 = Mock()
    registered_resources_2 = []

    def mock_resource_2(uri_pattern: str):
        def decorator(func):
            registered_resources_2.append(uri_pattern)
            return func

        return decorator

    mock_mcp_2.resource = mock_resource_2

    # Act - Register resources twice
    register_all_resources(mock_mcp_1, get_client)
    register_all_resources(mock_mcp_2, get_client)

    # Assert - Both registrations must produce identical resource lists
    assert set(registered_resources_1) == set(
        registered_resources_2
    ), "Resource discovery must be consistent across multiple registrations"

    assert len(registered_resources_1) == len(
        registered_resources_2
    ), "Resource discovery must return same number of resources"
