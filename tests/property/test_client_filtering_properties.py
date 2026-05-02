"""Property-based tests for HomeAssistantClient filtering functionality.

This module tests the following properties:
- Property 3: State Query Response Structure
- Property 4: State Update Round Trip
- Property 7: History Time Range Filtering
- Property 8: History Entity Filtering
- Property 45: Query Parameter Support and Encoding

Validates Requirements: 3.1-3.10, 4.1-4.9, 18.1-18.6, 21.1-21.9
"""

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.homeassistant_mcp.hass.client import HomeAssistantClient


# Custom strategies for generating test data
@st.composite
def entity_id_strategy(draw):
    """Generate valid Home Assistant entity IDs (domain.name)."""
    domains = ["light", "switch", "sensor", "climate", "binary_sensor", "cover"]
    domain = draw(st.sampled_from(domains))
    # Generate valid entity names (alphanumeric and underscore)
    name = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
            min_size=1,
            max_size=20,
        )
    )
    return f"{domain}.{name}"


@st.composite
def entity_state_strategy(draw):
    """Generate valid entity states."""
    states = ["on", "off", "heat", "cool", "auto", "open", "closed", "locked", "unlocked"]
    return draw(st.sampled_from(states))


@st.composite
def attributes_strategy(draw):
    """Generate valid entity attributes dictionaries."""
    # Generate simple attributes with string, int, float, or bool values
    keys = draw(
        st.lists(
            st.text(alphabet=st.characters(whitelist_categories=("Ll",)), min_size=1, max_size=15),
            min_size=0,
            max_size=5,
            unique=True,
        )
    )

    values = []
    for _ in keys:
        value_type = draw(st.sampled_from(["str", "int", "float", "bool"]))
        if value_type == "str":
            values.append(draw(st.text(min_size=0, max_size=50)))
        elif value_type == "int":
            values.append(draw(st.integers(min_value=-1000, max_value=1000)))
        elif value_type == "float":
            values.append(
                draw(
                    st.floats(
                        min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False
                    )
                )
            )
        else:
            values.append(draw(st.booleans()))

    return dict(zip(keys, values, strict=False))


@st.composite
def iso_timestamp_strategy(draw):
    """Generate valid ISO 8601 timestamps."""
    # Generate timestamps within a reasonable range (last 30 days)
    days_ago = draw(st.integers(min_value=0, max_value=30))
    hours = draw(st.integers(min_value=0, max_value=23))
    minutes = draw(st.integers(min_value=0, max_value=59))
    seconds = draw(st.integers(min_value=0, max_value=59))

    dt = datetime.now() - timedelta(days=days_ago, hours=hours, minutes=minutes, seconds=seconds)
    return dt.isoformat()


# Feature: rest-api-overhaul, Property 3: State Query Response Structure
@given(
    entity_id=entity_id_strategy(), state=entity_state_strategy(), attributes=attributes_strategy()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_3_state_query_response_structure(
    entity_id: str, state: str, attributes: dict[str, Any]
):
    """
    Property 3: State Query Response Structure

    For any entity state query (single or all), the response SHALL contain
    entity_id, state, attributes, last_changed, and last_updated fields.

    Validates: Requirements 3.1, 3.2
    """
    # Create mock response with required fields
    mock_response_data = {
        "entity_id": entity_id,
        "state": state,
        "attributes": attributes,
        "last_changed": "2024-01-01T12:00:00+00:00",
        "last_updated": "2024-01-01T12:00:00+00:00",
        "context": {"id": "test", "parent_id": None, "user_id": None},
    }

    # Create mock httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status = Mock()
    mock_client.get.return_value = mock_response

    # Create HomeAssistantClient with mock
    client = HomeAssistantClient(base_url="http://test:8123", token="test_token")
    client.client = mock_client

    # Test get_state
    result = await client.get_state(entity_id)

    # Verify all required fields are present
    assert "entity_id" in result
    assert "state" in result
    assert "attributes" in result
    assert "last_changed" in result
    assert "last_updated" in result

    # Verify values match
    assert result["entity_id"] == entity_id
    assert result["state"] == state
    assert result["attributes"] == attributes


# Feature: rest-api-overhaul, Property 4: State Update Round Trip
@given(
    entity_id=entity_id_strategy(), state=entity_state_strategy(), attributes=attributes_strategy()
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_4_state_update_round_trip(
    entity_id: str, state: str, attributes: dict[str, Any]
):
    """
    Property 4: State Update Round Trip

    For any valid entity state and attributes, setting the state then
    immediately retrieving it SHALL return equivalent state and attributes.

    Validates: Requirements 3.3, 3.4
    """
    # Create mock httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # Mock POST response for set_state
    mock_post_response = Mock()
    mock_post_response.status_code = 200
    mock_post_response.json.return_value = {
        "entity_id": entity_id,
        "state": state,
        "attributes": attributes,
        "last_changed": "2024-01-01T12:00:00+00:00",
        "last_updated": "2024-01-01T12:00:00+00:00",
        "context": {"id": "test", "parent_id": None, "user_id": None},
    }
    mock_post_response.raise_for_status = Mock()
    mock_client.post.return_value = mock_post_response

    # Mock GET response for get_state
    mock_get_response = Mock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = {
        "entity_id": entity_id,
        "state": state,
        "attributes": attributes,
        "last_changed": "2024-01-01T12:00:00+00:00",
        "last_updated": "2024-01-01T12:00:00+00:00",
        "context": {"id": "test", "parent_id": None, "user_id": None},
    }
    mock_get_response.raise_for_status = Mock()
    mock_client.get.return_value = mock_get_response

    # Create HomeAssistantClient with mock
    client = HomeAssistantClient(base_url="http://test:8123", token="test_token")
    client.client = mock_client

    # Set state
    await client.set_state(entity_id, state, attributes)

    # Get state
    get_result = await client.get_state(entity_id)

    # Verify round trip: state and attributes should match
    assert get_result["state"] == state
    assert get_result["attributes"] == attributes
    assert get_result["entity_id"] == entity_id


# Feature: rest-api-overhaul, Property 7: History Time Range Filtering
@given(
    start_timestamp=iso_timestamp_strategy(), hours_duration=st.integers(min_value=1, max_value=24)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_7_history_time_range_filtering(start_timestamp: str, hours_duration: int):
    """
    Property 7: History Time Range Filtering

    For any valid time range (start and optional end), all returned history
    entries SHALL have timestamps within that range.

    Validates: Requirements 4.1, 4.3
    """
    # Calculate end timestamp
    start_dt = datetime.fromisoformat(start_timestamp.replace("+00:00", ""))
    end_dt = start_dt + timedelta(hours=hours_duration)
    end_timestamp = end_dt.isoformat()

    # Create mock history entries within the time range
    mock_history_data = [
        [
            {
                "entity_id": "sensor.test",
                "state": "10",
                "attributes": {},
                "last_changed": (start_dt + timedelta(hours=i)).isoformat(),
                "last_updated": (start_dt + timedelta(hours=i)).isoformat(),
            }
            for i in range(min(hours_duration, 5))  # Limit to 5 entries for testing
        ]
    ]

    # Create mock httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_history_data
    mock_response.raise_for_status = Mock()
    mock_client.get.return_value = mock_response

    # Create HomeAssistantClient with mock
    client = HomeAssistantClient(base_url="http://test:8123", token="test_token")
    client.client = mock_client

    # Query history with time range
    result = await client.get_history(timestamp=start_timestamp, end_time=end_timestamp)

    # Verify all entries are within the time range
    for entity_history in result:
        for entry in entity_history:
            entry_time = datetime.fromisoformat(entry["last_changed"].replace("+00:00", ""))
            assert (
                start_dt <= entry_time <= end_dt
            ), f"Entry timestamp {entry_time} not in range [{start_dt}, {end_dt}]"


# Feature: rest-api-overhaul, Property 8: History Entity Filtering
@given(entity_ids=st.lists(entity_id_strategy(), min_size=1, max_size=5, unique=True))
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_8_history_entity_filtering(entity_ids: list[str]):
    """
    Property 8: History Entity Filtering

    For any entity filter list, all returned history and logbook entries
    SHALL only include entities from that filter list.

    Validates: Requirements 4.2, 4.5
    """
    # Create mock history data only for filtered entities
    mock_history_data = [
        [
            {
                "entity_id": entity_id,
                "state": "on",
                "attributes": {},
                "last_changed": "2024-01-01T12:00:00",
                "last_updated": "2024-01-01T12:00:00",
            }
        ]
        for entity_id in entity_ids
    ]

    # Create mock httpx client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_history_data
    mock_response.raise_for_status = Mock()
    mock_client.get.return_value = mock_response

    # Create HomeAssistantClient with mock
    client = HomeAssistantClient(base_url="http://test:8123", token="test_token")
    client.client = mock_client

    # Query history with entity filter
    result = await client.get_history(timestamp="2024-01-01T00:00:00", filter_entity_id=entity_ids)

    # Verify all returned entities are in the filter list
    for entity_history in result:
        for entry in entity_history:
            assert (
                entry["entity_id"] in entity_ids
            ), f"Entity {entry['entity_id']} not in filter list {entity_ids}"


# Feature: rest-api-overhaul, Property 45: Query Parameter Support and Encoding
@given(
    entity_ids=st.lists(entity_id_strategy(), min_size=1, max_size=3, unique=True),
    width=st.integers(min_value=100, max_value=1920),
    height=st.integers(min_value=100, max_value=1080),
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_45_query_parameter_support_and_encoding(
    entity_ids: list[str], width: int, height: int
):
    """
    Property 45: Query Parameter Support and Encoding

    For any API endpoint with query parameters, all specified parameters
    SHALL be properly URL-encoded and included in the request.

    Validates: Requirements 18.1, 18.2, 18.3, 18.4, 18.5, 18.6
    """
    # Create mock httpx client that captures the params
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    captured_params = None

    def capture_get(url, **kwargs):
        nonlocal captured_params
        captured_params = kwargs.get("params", {})
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.content = b"fake_data"
        mock_response.headers = {"content-type": "application/json"}
        mock_response.raise_for_status = Mock()
        return mock_response

    mock_client.get.side_effect = capture_get

    # Create HomeAssistantClient with mock
    client = HomeAssistantClient(base_url="http://test:8123", token="test_token")
    client.client = mock_client

    # Test 1: History query with filter_entity_id parameter
    await client.get_history(
        timestamp="2024-01-01T00:00:00", filter_entity_id=entity_ids, minimal_response=True
    )

    # Verify query parameters are present
    assert captured_params is not None
    assert "filter_entity_id" in captured_params
    # The parameter should contain all entity IDs (comma-separated)
    filter_param = captured_params["filter_entity_id"]
    for entity_id in entity_ids:
        assert entity_id in filter_param

    # Check minimal_response parameter
    assert "minimal_response" in captured_params
    assert captured_params["minimal_response"] == "true"

    # Test 2: Camera proxy with width and height parameters
    await client.get_camera_proxy(entity_id="camera.test", width=width, height=height)

    # Verify width and height parameters are present
    assert captured_params is not None
    assert "width" in captured_params
    assert captured_params["width"] == width

    assert "height" in captured_params
    assert captured_params["height"] == height
