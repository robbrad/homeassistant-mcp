"""Unit tests for resource discovery.

Tests that list_resources includes all required resource templates,
static URIs, descriptions, example URIs, and query parameter documentation.

Requirements tested: 10.1, 10.2, 10.3, 10.4, 10.6, 10.7
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.homeassistant_mcp.resources import register_all_resources


@pytest.mark.asyncio
async def test_list_resources_includes_all_templates():
    """Test list_resources includes all resource templates.

    Validates: Requirements 10.1, 10.3
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])
    mock_client.get_services = AsyncMock(return_value={})

    def get_client():
        return mock_client

    mock_mcp = Mock()
    registered_resources = []

    def mock_resource(uri_pattern: str, **kwargs):
        """Mock resource decorator that tracks registered URIs."""

        def decorator(func):
            registered_resources.append(
                {
                    "uri": uri_pattern,
                    "name": func.__name__,
                    "description": func.__doc__ or "",
                }
            )
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_all_resources(mock_mcp, get_client)

    # Assert - Verify all required templates are present
    uri_patterns = [r["uri"] for r in registered_resources]

    required_templates = [
        "hass://entity/{entity_id}",
        "hass://area/{area_id}",
        "hass://device/{device_id}",
        "hass://entity/{entity_id}/history",
    ]

    for template in required_templates:
        assert template in uri_patterns, f"list_resources must include template: {template}"


@pytest.mark.asyncio
async def test_list_resources_includes_static_services_uri():
    """Test list_resources includes static services URI.

    Validates: Requirement 10.2
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])
    mock_client.get_services = AsyncMock(return_value={})

    def get_client():
        return mock_client

    mock_mcp = Mock()
    registered_resources = []

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            registered_resources.append(uri_pattern)
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_all_resources(mock_mcp, get_client)

    # Assert
    assert (
        "hass://services" in registered_resources
    ), "list_resources must include static hass://services URI"


@pytest.mark.asyncio
async def test_resource_descriptions_are_present():
    """Test resource descriptions are present for each resource.

    Validates: Requirements 10.4, 19.2
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])
    mock_client.get_services = AsyncMock(return_value={})

    def get_client():
        return mock_client

    mock_mcp = Mock()
    registered_resources = []

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            registered_resources.append(
                {
                    "uri": uri_pattern,
                    "name": func.__name__,
                    "description": func.__doc__ or "",
                }
            )
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_all_resources(mock_mcp, get_client)

    # Assert - Verify all resources have descriptions
    for resource in registered_resources:
        assert resource["description"], f"Resource {resource['uri']} must have a description"
        assert (
            len(resource["description"]) > 10
        ), f"Resource {resource['uri']} description must be meaningful"


@pytest.mark.asyncio
async def test_example_uris_can_be_constructed():
    """Test example URIs can be constructed from templates.

    Validates: Requirements 10.4, 10.7, 19.4
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])
    mock_client.get_services = AsyncMock(return_value={})

    def get_client():
        return mock_client

    mock_mcp = Mock()
    registered_resources = []

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            registered_resources.append(uri_pattern)
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_all_resources(mock_mcp, get_client)

    # Assert - Verify example URIs can be constructed
    example_mappings = {
        "hass://entity/{entity_id}": "hass://entity/light.living_room",
        "hass://area/{area_id}": "hass://area/living_room",
        "hass://device/{device_id}": "hass://device/abc123",
        "hass://services": "hass://services",
        "hass://entity/{entity_id}/history": "hass://entity/sensor.temperature/history?hours=24&limit=100",
    }

    for template in registered_resources:
        if template in example_mappings:
            example = example_mappings[template]
            # Verify example follows the template pattern
            if "{" in template:
                # Template has dynamic segments
                base_template = template.split("{")[0]
                assert example.startswith(
                    base_template
                ), f"Example URI {example} must match template {template}"


@pytest.mark.asyncio
async def test_query_parameter_documentation():
    """Test query parameters are documented for history resources.

    Validates: Requirements 10.6, 19.3
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])
    mock_client.get_services = AsyncMock(return_value={})

    def get_client():
        return mock_client

    mock_mcp = Mock()
    registered_resources = []

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            # Extract function signature to get query parameters
            import inspect

            sig = inspect.signature(func)
            params = {}
            for param_name, param in sig.parameters.items():
                if param_name not in ["entity_id", "area_id", "device_id"]:
                    # This is likely a query parameter
                    params[param_name] = {
                        "default": (
                            param.default if param.default != inspect.Parameter.empty else None
                        ),
                        "annotation": (
                            param.annotation
                            if param.annotation != inspect.Parameter.empty
                            else None
                        ),
                    }

            registered_resources.append(
                {
                    "uri": uri_pattern,
                    "name": func.__name__,
                    "description": func.__doc__ or "",
                    "query_params": params,
                }
            )
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_all_resources(mock_mcp, get_client)

    # Assert - Find history resource and verify query parameters
    history_resource = None
    for resource in registered_resources:
        if "history" in resource["uri"]:
            history_resource = resource
            break

    assert history_resource is not None, "History resource must be registered"

    # Verify query parameters are documented
    query_params = history_resource["query_params"]

    # History resource should have hours, limit, offset parameters
    expected_params = ["hours", "limit", "offset"]
    for param in expected_params:
        assert param in query_params, f"History resource must document query parameter: {param}"

        # Verify defaults are documented
        assert (
            query_params[param]["default"] is not None
        ), f"Query parameter {param} must have a default value"


@pytest.mark.asyncio
async def test_all_resources_use_hass_scheme():
    """Test all resources use hass:// URI scheme.

    Validates: Requirement 10.1
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])
    mock_client.get_services = AsyncMock(return_value={})

    def get_client():
        return mock_client

    mock_mcp = Mock()
    registered_resources = []

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            registered_resources.append(uri_pattern)
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_all_resources(mock_mcp, get_client)

    # Assert - All URIs must use hass:// scheme
    for uri in registered_resources:
        assert uri.startswith("hass://"), f"All resource URIs must use hass:// scheme, found: {uri}"


@pytest.mark.asyncio
async def test_resource_count_is_correct():
    """Test correct number of resources are registered.

    Validates: Requirement 10.1
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])
    mock_client.get_services = AsyncMock(return_value={})

    def get_client():
        return mock_client

    mock_mcp = Mock()
    registered_resources = []

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            registered_resources.append(uri_pattern)
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_all_resources(mock_mcp, get_client)

    # Assert - Should have exactly 5 resources
    # 1. hass://entity/{entity_id}
    # 2. hass://area/{area_id}
    # 3. hass://device/{device_id}
    # 4. hass://services
    # 5. hass://entity/{entity_id}/history
    assert (
        len(registered_resources) == 5
    ), f"Expected 5 resources, found {len(registered_resources)}: {registered_resources}"


@pytest.mark.asyncio
async def test_resource_templates_have_dynamic_segments():
    """Test resource templates properly identify dynamic segments.

    Validates: Requirement 10.3
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])
    mock_client.get_services = AsyncMock(return_value={})

    def get_client():
        return mock_client

    mock_mcp = Mock()
    registered_resources = []

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            registered_resources.append(uri_pattern)
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_all_resources(mock_mcp, get_client)

    # Assert - Verify templates have proper dynamic segments
    templates_with_segments = {
        "hass://entity/{entity_id}": ["entity_id"],
        "hass://area/{area_id}": ["area_id"],
        "hass://device/{device_id}": ["device_id"],
        "hass://entity/{entity_id}/history": ["entity_id"],
    }

    for template, expected_segments in templates_with_segments.items():
        assert template in registered_resources, f"Template {template} must be registered"

        # Extract segments from template
        import re

        segments = re.findall(r"\{([^}]+)\}", template)

        for expected_segment in expected_segments:
            assert (
                expected_segment in segments
            ), f"Template {template} must have segment {expected_segment}"


@pytest.mark.asyncio
async def test_static_resources_have_no_dynamic_segments():
    """Test static resources have no dynamic segments.

    Validates: Requirement 10.2
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])
    mock_client.get_services = AsyncMock(return_value={})

    def get_client():
        return mock_client

    mock_mcp = Mock()
    registered_resources = []

    def mock_resource(uri_pattern: str, **kwargs):
        def decorator(func):
            registered_resources.append(uri_pattern)
            return func

        return decorator

    mock_mcp.resource = mock_resource

    # Act
    register_all_resources(mock_mcp, get_client)

    # Assert - Static services URI should have no dynamic segments
    services_uri = "hass://services"
    assert services_uri in registered_resources, "Services URI must be registered"

    # Verify no curly braces (dynamic segments)
    assert "{" not in services_uri, "Static services URI must not have dynamic segments"
    assert "}" not in services_uri, "Static services URI must not have dynamic segments"
