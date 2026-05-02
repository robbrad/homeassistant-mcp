"""Property-based tests for services resources.

This module tests the following properties:
- Property 6: Services Domain Organization

Validates Requirements: 3.9, 7.2
"""

import json
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.homeassistant_mcp.resources.services import register_services_resources


# Custom strategies for generating test data
@st.composite
def services_data_strategy(draw):
    """Generate valid services data organized by domain."""
    # Generate 1-5 domains
    num_domains = draw(st.integers(min_value=1, max_value=5))
    domains = ["light", "switch", "climate", "automation", "script", "scene", "cover", "lock"]
    selected_domains = draw(
        st.lists(st.sampled_from(domains), min_size=num_domains, max_size=num_domains, unique=True)
    )

    services_dict = {}
    for domain in selected_domains:
        # Generate 1-3 services per domain
        num_services = draw(st.integers(min_value=1, max_value=3))
        service_names = ["turn_on", "turn_off", "toggle", "set_temperature", "open", "close"]
        selected_services = draw(
            st.lists(
                st.sampled_from(service_names),
                min_size=num_services,
                max_size=num_services,
                unique=True,
            )
        )

        domain_services = {}
        for service_name in selected_services:
            # Generate service definition
            domain_services[service_name] = {
                "description": draw(st.text(min_size=10, max_size=100)),
                "fields": {
                    "entity_id": {"description": "Entity ID", "required": draw(st.booleans())}
                },
            }

        services_dict[domain] = domain_services

    return services_dict


# Feature: mcp-resources-layer, Property 6: Services Domain Organization
@given(services_data=services_data_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_6_services_domain_organization(services_data: dict[str, Any]):
    """
    Property 6: Services Domain Organization

    For any services resource response, the `data` field must be organized as a dictionary
    where keys are domain names and values are dictionaries of service definitions.

    Validates: Requirements 3.9, 7.2
    """
    # Create mock client that returns services data
    mock_client = AsyncMock()
    mock_client.get_services = AsyncMock(return_value=services_data)

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

    # Register services resources
    register_services_resources(mock_mcp, get_client)

    # Get the resource handler
    handler = resource_handlers["hass://services"]

    # Call the handler
    result = await handler()

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

    # Property 6: Verify services are organized by domain
    assert isinstance(data, dict), "Services data must be a dictionary"

    # Verify all domains from input are present in output
    for domain in services_data.keys():
        assert domain in data, f"Domain '{domain}' missing from services data"

    # Verify each domain contains service definitions
    for domain, services in data.items():
        assert isinstance(services, dict), f"Services for domain '{domain}' must be a dictionary"

        # Verify services have expected structure
        for service_name, service_def in services.items():
            assert isinstance(
                service_def, dict
            ), f"Service '{service_name}' definition must be a dictionary"
            # Service definitions should have description and/or fields
            # (structure may vary, but must be a dict)

    # Verify the data matches the input structure
    assert data == services_data, "Services data should match the input from HomeAssistantClient"


# Feature: mcp-resources-layer, Property 6: Services Domain Organization (Empty Services)
@pytest.mark.asyncio
async def test_property_6_services_domain_organization_empty():
    """
    Property 6: Services Domain Organization (Empty Services)

    For services resource response with no services, the `data` field must still be
    a dictionary (empty dictionary).

    Validates: Requirements 3.9, 7.2
    """
    # Create mock client that returns empty services data
    mock_client = AsyncMock()
    mock_client.get_services = AsyncMock(return_value={})

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

    # Register services resources
    register_services_resources(mock_mcp, get_client)

    # Get the resource handler
    handler = resource_handlers["hass://services"]

    # Call the handler
    result = await handler()

    # Parse the response
    assert result is not None
    parsed = json.loads(result.text)

    # Verify response envelope structure
    assert "data" in parsed

    # Extract the data field
    data = parsed["data"]

    # Property 6: Verify data is a dictionary (even if empty)
    assert isinstance(data, dict), "Services data must be a dictionary"
    assert data == {}, "Empty services should return empty dictionary"
