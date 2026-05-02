"""Property-based tests for core API tools.

This module tests the following properties:
- Property 1: API Information Response Completeness
- Property 2: Service Listing Organization

Validates Requirements: 2.1-2.5
"""

from typing import Any
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.homeassistant_mcp.hass.client import HomeAssistantClient


# Custom strategies for generating test data
@st.composite
def api_status_strategy(draw):
    """Generate valid API status responses."""
    return {"message": draw(st.text(min_size=1, max_size=100))}


@st.composite
def config_strategy(draw):
    """Generate valid Home Assistant configuration responses."""
    return {
        "latitude": draw(
            st.floats(min_value=-90, max_value=90, allow_nan=False, allow_infinity=False)
        ),
        "longitude": draw(
            st.floats(min_value=-180, max_value=180, allow_nan=False, allow_infinity=False)
        ),
        "elevation": draw(st.integers(min_value=-500, max_value=9000)),
        "unit_system": draw(
            st.dictionaries(
                st.sampled_from(["length", "mass", "temperature", "volume"]),
                st.sampled_from(["km", "kg", "°C", "L", "mi", "lb", "°F", "gal"]),
                min_size=1,
                max_size=4,
            )
        ),
        "location_name": draw(st.text(min_size=1, max_size=50)),
        "time_zone": draw(
            st.sampled_from(["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"])
        ),
        "components": draw(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10)),
        "config_dir": draw(st.text(min_size=1, max_size=100)),
        "whitelist_external_dirs": draw(
            st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=5)
        ),
        "version": draw(st.text(min_size=1, max_size=20)),
        "config_source": draw(st.sampled_from(["yaml", "storage"])),
        "safe_mode": draw(st.booleans()),
        "state": draw(st.sampled_from(["RUNNING", "STARTING", "STOPPING"])),
        "external_url": draw(st.one_of(st.none(), st.text(min_size=1, max_size=100))),
        "internal_url": draw(st.one_of(st.none(), st.text(min_size=1, max_size=100))),
    }


@st.composite
def components_strategy(draw):
    """Generate valid component lists."""
    # Common Home Assistant components
    common_components = [
        "homeassistant",
        "api",
        "auth",
        "automation",
        "config",
        "frontend",
        "history",
        "light",
        "switch",
        "sensor",
        "climate",
        "media_player",
        "camera",
        "cover",
        "lock",
        "scene",
        "script",
        "zone",
        "person",
    ]

    # Select a subset of components
    num_components = draw(st.integers(min_value=5, max_value=len(common_components)))
    return draw(
        st.lists(
            st.sampled_from(common_components),
            min_size=num_components,
            max_size=num_components,
            unique=True,
        )
    )


@st.composite
def service_description_strategy(draw):
    """Generate valid service descriptions."""
    return {
        "name": draw(st.text(min_size=1, max_size=50)),
        "description": draw(st.text(min_size=1, max_size=200)),
        "fields": draw(
            st.dictionaries(
                st.text(
                    alphabet=st.characters(whitelist_categories=("Ll",)), min_size=1, max_size=20
                ),
                st.dictionaries(
                    st.sampled_from(["description", "example", "required"]),
                    st.one_of(st.text(min_size=1, max_size=100), st.booleans()),
                    min_size=1,
                    max_size=3,
                ),
                min_size=0,
                max_size=5,
            )
        ),
        "target": draw(
            st.one_of(
                st.none(),
                st.dictionaries(
                    st.sampled_from(["entity", "device", "area"]),
                    st.booleans(),
                    min_size=1,
                    max_size=3,
                ),
            )
        ),
    }


@st.composite
def services_by_domain_strategy(draw):
    """Generate valid services organized by domain."""
    domains = ["light", "switch", "climate", "automation", "script", "scene"]
    selected_domains = draw(
        st.lists(st.sampled_from(domains), min_size=1, max_size=len(domains), unique=True)
    )

    result = {}
    for domain in selected_domains:
        # Generate services for this domain
        service_names = draw(
            st.lists(
                st.text(
                    alphabet=st.characters(whitelist_categories=("Ll",)), min_size=1, max_size=20
                ),
                min_size=1,
                max_size=5,
                unique=True,
            )
        )

        domain_services = {}
        for service_name in service_names:
            domain_services[service_name] = draw(service_description_strategy())

        result[domain] = domain_services

    return result


# Feature: rest-api-overhaul, Property 1: API Information Response Completeness
@given(action=st.sampled_from(["status", "config", "components"]))
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_1_api_information_response_completeness(action: str):
    """
    Property 1: API Information Response Completeness

    For any API information query (status, config, components), the response
    SHALL contain all required fields for that query type and be properly structured.

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
    """
    # Create mock httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()

    # Generate appropriate mock data based on action
    if action == "status":
        mock_data = {"message": "API running."}
    elif action == "config":
        mock_data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "elevation": 10,
            "unit_system": {"length": "km", "mass": "kg", "temperature": "°C", "volume": "L"},
            "location_name": "Test Home",
            "time_zone": "America/New_York",
            "components": ["homeassistant", "api", "light"],
            "config_dir": "/config",
            "whitelist_external_dirs": [],
            "version": "2024.1.0",
            "config_source": "yaml",
            "safe_mode": False,
            "state": "RUNNING",
            "external_url": None,
            "internal_url": None,
        }
    else:  # components
        mock_data = ["homeassistant", "api", "auth", "automation", "light", "switch"]

    mock_response.json.return_value = mock_data
    mock_client.get.return_value = mock_response

    # Create HomeAssistantClient with mock
    client = HomeAssistantClient(base_url="http://test:8123", token="test_token")
    client.client = mock_client

    # Call the appropriate method
    if action == "status":
        result = await client.get_api_status()
        # Verify status response has message field
        assert "message" in result
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0

    elif action == "config":
        result = await client.get_config()
        # Verify config response has all required fields
        required_fields = [
            "latitude",
            "longitude",
            "elevation",
            "unit_system",
            "location_name",
            "time_zone",
            "components",
            "config_dir",
            "version",
            "config_source",
            "safe_mode",
            "state",
        ]
        for field in required_fields:
            assert field in result, f"Required field '{field}' missing from config response"

    else:  # components
        result = await client.get_components()
        # Verify components response is a list
        assert isinstance(result, list)
        assert len(result) > 0
        # All items should be strings
        for component in result:
            assert isinstance(component, str)
            assert len(component) > 0


# Feature: rest-api-overhaul, Property 2: Service Listing Organization
@given(services_data=services_by_domain_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_2_service_listing_organization(services_data: dict[str, dict[str, Any]]):
    """
    Property 2: Service Listing Organization

    For any services query response, all services SHALL be organized by domain
    with each service containing name, description, and field definitions.

    Validates: Requirements 2.5
    """
    # Create mock httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = services_data
    mock_response.raise_for_status = Mock()
    mock_client.get.return_value = mock_response

    # Create HomeAssistantClient with mock
    client = HomeAssistantClient(base_url="http://test:8123", token="test_token")
    client.client = mock_client

    # Get services
    result = await client.get_services()

    # Verify response is organized by domain
    assert isinstance(result, dict)
    assert len(result) > 0

    # Verify each domain contains services
    for domain, services in result.items():
        assert isinstance(domain, str)
        assert len(domain) > 0
        assert isinstance(services, dict)

        # Verify each service has required fields
        for service_name, service_info in services.items():
            assert isinstance(service_name, str)
            assert len(service_name) > 0
            assert isinstance(service_info, dict)

            # Each service should have name and description
            assert "name" in service_info
            assert isinstance(service_info["name"], str)

            assert "description" in service_info
            assert isinstance(service_info["description"], str)

            # Fields should be present (can be empty dict)
            assert "fields" in service_info
            assert isinstance(service_info["fields"], dict)

            # Target is optional but if present should be a dict
            if "target" in service_info:
                assert service_info["target"] is None or isinstance(service_info["target"], dict)


# Feature: rest-api-overhaul, Property 1: API Information Response Completeness (Extended)
@given(
    status_data=api_status_strategy(),
    config_data=config_strategy(),
    components_data=components_strategy(),
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_1_extended_api_information_completeness(
    status_data: dict[str, str], config_data: dict[str, Any], components_data: list[str]
):
    """
    Property 1 Extended: API Information Response Completeness with varied data

    For any API information query with randomly generated valid data, the response
    SHALL contain all required fields and maintain proper structure.

    Validates: Requirements 2.1, 2.2, 2.3
    """
    # Test status endpoint
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = status_data
    mock_response.raise_for_status = Mock()
    mock_client.get.return_value = mock_response

    client = HomeAssistantClient(base_url="http://test:8123", token="test_token")
    client.client = mock_client

    status_result = await client.get_api_status()
    assert "message" in status_result
    assert status_result["message"] == status_data["message"]

    # Test config endpoint
    mock_response.json.return_value = config_data
    config_result = await client.get_config()

    # Verify all fields from generated data are present
    for key, value in config_data.items():
        assert key in config_result
        assert config_result[key] == value

    # Test components endpoint
    mock_response.json.return_value = components_data
    components_result = await client.get_components()

    assert isinstance(components_result, list)
    assert len(components_result) == len(components_data)
    assert set(components_result) == set(components_data)


# Custom strategies for event testing
@st.composite
def event_type_strategy(draw):
    """Generate valid event type names."""
    # Event types are typically lowercase with underscores
    parts = draw(
        st.lists(
            st.text(alphabet=st.characters(whitelist_categories=("Ll",)), min_size=1, max_size=15),
            min_size=1,
            max_size=3,
        )
    )
    return "_".join(parts)


@st.composite
def event_data_strategy(draw):
    """Generate valid event data dictionaries."""
    return draw(
        st.dictionaries(
            st.text(alphabet=st.characters(whitelist_categories=("Ll",)), min_size=1, max_size=20),
            st.one_of(
                st.text(min_size=0, max_size=100),
                st.integers(min_value=-1000, max_value=1000),
                st.floats(
                    min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False
                ),
                st.booleans(),
            ),
            min_size=0,
            max_size=5,
        )
    )


# Feature: rest-api-overhaul, Property 14: Event Firing Success
@given(event_type=event_type_strategy(), event_data=event_data_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_14_event_firing_success(event_type: str, event_data: dict[str, Any]):
    """
    Property 14: Event Firing Success

    For any valid event type and optional event data, firing the event
    SHALL return success confirmation.

    Validates: Requirements 6.1, 6.2, 6.3
    """
    # Create mock httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = ""  # Empty response is valid
    mock_response.json.return_value = {"message": "Event fired"}
    mock_response.raise_for_status = Mock()
    mock_client.post.return_value = mock_response

    # Create HomeAssistantClient with mock
    client = HomeAssistantClient(base_url="http://test:8123", token="test_token")
    client.client = mock_client

    # Fire event
    result = await client.fire_event(event_type, event_data)

    # Verify success response
    assert isinstance(result, dict)
    # Response should indicate success (either has message or is empty dict)
    assert "message" in result or len(result) == 0

    # Verify the correct endpoint was called
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert f"/events/{event_type}" in str(call_args)

    # Verify event data was passed
    if event_data:
        assert call_args.kwargs["json"] == event_data


# Feature: rest-api-overhaul, Property 15: Invalid Event Type Error Handling
@given(
    invalid_event_type=st.sampled_from(
        [
            "",  # Empty string
            "   ",  # Whitespace only
            "\t",  # Tab
            "\n",  # Newline
            "  \t  ",  # Mixed whitespace
        ]
    )
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_15_invalid_event_type_error_handling(invalid_event_type: str):
    """
    Property 15: Invalid Event Type Error Handling

    For any invalid event type, firing the event SHALL return an error message.

    Validates: Requirements 6.4
    """
    # Create mock httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # For invalid event types, we expect the client to reject before making the call
    # or the server to return an error
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Invalid event type"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Bad Request", request=Mock(), response=mock_response
    )
    mock_client.post.return_value = mock_response

    # Create HomeAssistantClient with mock
    client = HomeAssistantClient(base_url="http://test:8123", token="test_token")
    client.client = mock_client

    # Attempt to fire event with invalid type
    # Should raise ServiceCallError
    from src.homeassistant_mcp.exceptions import ServiceCallError

    with pytest.raises(ServiceCallError):
        await client.fire_event(invalid_event_type, None)


# Feature: rest-api-overhaul, Property 14: Event Firing Success (No Data)
@given(event_type=event_type_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_14_event_firing_success_no_data(event_type: str):
    """
    Property 14: Event Firing Success (No Data)

    For any valid event type without event data, firing the event
    SHALL return success confirmation.

    Validates: Requirements 6.1, 6.3
    """
    # Create mock httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = ""
    mock_response.json.return_value = {"message": "Event fired"}
    mock_response.raise_for_status = Mock()
    mock_client.post.return_value = mock_response

    # Create HomeAssistantClient with mock
    client = HomeAssistantClient(base_url="http://test:8123", token="test_token")
    client.client = mock_client

    # Fire event without data
    result = await client.fire_event(event_type, None)

    # Verify success response
    assert isinstance(result, dict)

    # Verify the correct endpoint was called with empty dict
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert f"/events/{event_type}" in str(call_args)
    # When event_data is None, an empty dict should be sent
    assert call_args.kwargs["json"] == {}
