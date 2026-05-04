"""Property-based tests for calendar access functionality.

Feature: rest-api-overhaul
Properties: 21, 22, 23, 24
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from homeassistant_mcp.exceptions import EntityNotFoundError
from homeassistant_mcp.tools.specialized.calendar import register_calendar_tool

# Strategies for generating test data
entity_id_strategy = st.from_regex(r"^calendar\.[a-z0-9_]+$", fullmatch=True)

calendar_name_strategy = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" "),
)


# ISO 8601 datetime strategy
def iso_datetime_strategy():
    """Generate valid ISO 8601 datetime strings."""
    return st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)).map(
        lambda dt: dt.isoformat()
    )


def create_mock_mcp():
    """Create a mock MCP server."""
    mcp = MagicMock()
    registered_tool = None

    def tool_decorator(**kwargs):
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


# Feature: rest-api-overhaul, Property 21: Calendar Listing Response
@given(
    calendars=st.lists(
        st.fixed_dictionaries(
            {
                "entity_id": entity_id_strategy,
                "name": calendar_name_strategy,
            }
        ),
        min_size=0,
        max_size=20,
    )
)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_21_calendar_listing_response(calendars):
    """
    Property 21: For any calendar list request, the response SHALL return
    a list of calendar entities.

    Validates: Requirements 9.1
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock to return calendars
    mock_client.get_calendars = AsyncMock(return_value=calendars)

    # Register tool
    register_calendar_tool(mock_mcp, get_client)
    calendar_access = mock_mcp.get_registered_tool()

    # Test list action
    result = await calendar_access(action="list")

    assert result["success"] is True
    assert "calendars" in result
    assert isinstance(result["calendars"], list)
    assert len(result["calendars"]) == len(calendars)
    assert result["count"] == len(calendars)

    # Verify all calendars are present
    for calendar in calendars:
        assert calendar in result["calendars"]


# Feature: rest-api-overhaul, Property 22: Calendar Event Date Range Filtering
@given(
    entity_id=entity_id_strategy,
    start_dt=st.datetimes(min_value=datetime(2024, 1, 1), max_value=datetime(2024, 6, 30)),
    duration_days=st.integers(min_value=1, max_value=30),
)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_22_calendar_event_date_range_filtering(entity_id, start_dt, duration_days):
    """
    Property 22: For any calendar query with a date range, all returned events
    SHALL have start and end times within or overlapping that range.

    Validates: Requirements 9.2
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Calculate date range
    start = start_dt.isoformat()
    end_dt = start_dt + timedelta(days=duration_days)
    end = end_dt.isoformat()

    # Generate events within the range
    events = []
    for i in range(3):
        event_start = start_dt + timedelta(days=i * (duration_days // 4))
        event_end = event_start + timedelta(hours=2)
        events.append(
            {
                "start": event_start.isoformat(),
                "end": event_end.isoformat(),
                "summary": f"Event {i}",
                "description": f"Test event {i}",
            }
        )

    # Setup mock
    mock_client.get_calendar_events = AsyncMock(return_value=events)

    # Register tool
    register_calendar_tool(mock_mcp, get_client)
    calendar_access = mock_mcp.get_registered_tool()

    # Test get_events with date range
    result = await calendar_access(
        action="get_events", calendar_entity_id=entity_id, start=start, end=end
    )

    assert result["success"] is True
    assert "events" in result
    assert result["start"] == start
    assert result["end"] == end

    # Verify client was called with correct parameters
    mock_client.get_calendar_events.assert_called_once_with(
        calendar_entity_id=entity_id, start=start, end=end
    )

    # Verify all events are within or overlap the range
    for event in result["events"]:
        event_start = datetime.fromisoformat(event["start"])
        event_end = datetime.fromisoformat(event["end"])

        # Event should start before range end and end after range start (overlap)
        assert event_start <= end_dt
        assert event_end >= start_dt


# Feature: rest-api-overhaul, Property 23: Calendar Event Response Structure
@given(
    entity_id=entity_id_strategy,
    events=st.lists(
        st.fixed_dictionaries(
            {
                "start": iso_datetime_strategy(),
                "end": iso_datetime_strategy(),
                "summary": st.text(min_size=1, max_size=100),
                "description": st.one_of(st.none(), st.text(max_size=500)),
            }
        ),
        min_size=0,
        max_size=10,
    ),
)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_23_calendar_event_response_structure(entity_id, events):
    """
    Property 23: For any calendar event, the response SHALL contain start, end,
    summary, and optional description fields.

    Validates: Requirements 9.3, 9.6
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock
    mock_client.get_calendar_events = AsyncMock(return_value=events)

    # Register tool
    register_calendar_tool(mock_mcp, get_client)
    calendar_access = mock_mcp.get_registered_tool()

    # Test get_events
    result = await calendar_access(action="get_events", calendar_entity_id=entity_id)

    assert result["success"] is True
    assert "events" in result
    assert result["count"] == len(events)

    # Verify each event has required fields
    for event in result["events"]:
        assert "start" in event
        assert "end" in event
        assert "summary" in event
        # description is optional
        assert "description" in event or event.get("description") is None


# Feature: rest-api-overhaul, Property 24: Invalid Calendar Error Handling
@given(entity_id=entity_id_strategy, error_message=st.text(min_size=1, max_size=200))
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_24_invalid_calendar_error_handling(entity_id, error_message):
    """
    Property 24: For any non-existent calendar entity or invalid date format,
    the response SHALL return an appropriate error message.

    Validates: Requirements 9.4, 9.5
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Test 1: Non-existent calendar entity
    mock_client.get_calendar_events = AsyncMock(side_effect=EntityNotFoundError(error_message))

    # Register tool
    register_calendar_tool(mock_mcp, get_client)
    calendar_access = mock_mcp.get_registered_tool()

    # Test error handling for non-existent entity
    result = await calendar_access(action="get_events", calendar_entity_id=entity_id)

    assert result["success"] is False
    assert "error" in result
    assert "error_type" in result
    assert error_message in result["error"]

    # Test 2: Missing required parameter
    result_missing = await calendar_access(
        action="get_events"
        # Missing calendar_entity_id
    )

    assert result_missing["success"] is False
    assert "error" in result_missing
    assert "calendar_entity_id is required" in result_missing["error"]
    assert result_missing["error_type"] == "validation_error"

    # Test 3: Invalid action
    result_invalid_action = await calendar_access(
        action="invalid_action", calendar_entity_id=entity_id  # type: ignore
    )

    assert result_invalid_action["success"] is False
    assert "error" in result_invalid_action
    assert "Unknown action" in result_invalid_action["error"]
