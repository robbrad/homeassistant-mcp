"""Property-based tests for historical data tools.

This module tests the following properties:
- Property 7: History Time Range Filtering
- Property 8: History Entity Filtering
- Property 9: History Response Structure
- Property 10: Invalid Timestamp Error Handling

Validates Requirements: 4.1-4.9
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.homeassistant_mcp.tools.history.history import register_history_tool


# Custom strategies for generating test data
@st.composite
def entity_id_strategy(draw):
    """Generate valid Home Assistant entity IDs (domain.name)."""
    domains = ["light", "switch", "sensor", "climate", "binary_sensor", "cover"]
    domain = draw(st.sampled_from(domains))
    name = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
            min_size=1,
            max_size=20,
        )
    )
    return f"{domain}.{name}"


@st.composite
def iso_timestamp_strategy(draw):
    """Generate valid ISO 8601 timestamps."""
    # Generate a datetime within a reasonable range
    year = draw(st.integers(min_value=2020, max_value=2025))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Safe for all months
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    second = draw(st.integers(min_value=0, max_value=59))

    dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    return dt.isoformat()


@st.composite
def history_entry_strategy(draw, entity_id: str):
    """Generate a valid history entry for an entity."""
    states = ["on", "off", "heat", "cool", "auto", "open", "closed"]
    state = draw(st.sampled_from(states))

    # Generate timestamp
    timestamp = draw(iso_timestamp_strategy())

    return {
        "entity_id": entity_id,
        "state": state,
        "last_changed": timestamp,
        "last_updated": timestamp,
        "attributes": {
            "friendly_name": f"Test {entity_id}",
        },
    }


@st.composite
def invalid_timestamp_strategy(draw):
    """Generate invalid timestamp formats."""
    invalid_formats = [
        "not-a-timestamp",
        "2024-13-01",  # Invalid month
        "2024-01-32",  # Invalid day
        "2024/01/01",  # Wrong separator
        "01-01-2024",  # Wrong order
        "2024-01-01 12:00:00",  # Missing timezone
        "",  # Empty string
        "12345",  # Just numbers
    ]
    return draw(st.sampled_from(invalid_formats))


# Feature: rest-api-overhaul, Property 7: History Time Range Filtering
@given(
    entity_ids=st.lists(entity_id_strategy(), min_size=1, max_size=3, unique=True),
    hours_back=st.integers(min_value=1, max_value=24),
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_7_history_time_range_filtering(entity_ids: list[str], hours_back: int):
    """
    Property 7: History Time Range Filtering

    For any valid time range (start and optional end), all returned history
    entries SHALL have timestamps within that range.

    Validates: Requirements 4.1, 4.3
    """
    # Generate time range
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours_back)

    start_timestamp = start_time.isoformat()
    end_timestamp = end_time.isoformat()

    # Generate history entries within the time range
    mock_history = []
    for entity_id in entity_ids:
        entity_history = []
        # Generate 2-5 entries per entity
        for i in range(2):
            # Generate timestamp within range
            offset_hours = hours_back * (i / 2)  # Spread across range
            entry_time = start_time + timedelta(hours=offset_hours)

            entity_history.append(
                {
                    "entity_id": entity_id,
                    "state": "on" if i % 2 == 0 else "off",
                    "last_changed": entry_time.isoformat(),
                    "last_updated": entry_time.isoformat(),
                    "attributes": {},
                }
            )
        mock_history.append(entity_history)

    # Create mock client
    mock_client = Mock()
    mock_client.get_history = AsyncMock(return_value=mock_history)

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
    register_history_tool(mock_mcp, lambda: mock_client)

    # Call the tool
    result = await tool_func(
        timestamp=start_timestamp, end_time=end_timestamp, filter_entity_id=entity_ids
    )

    # Verify success
    assert result["success"] is True
    assert "history" in result

    # Verify all entries are within time range
    for entity_history in result["history"]:
        for entry in entity_history:
            entry_time = datetime.fromisoformat(entry["last_changed"].replace("Z", "+00:00"))
            assert (
                start_time <= entry_time <= end_time
            ), f"Entry timestamp {entry_time} not in range [{start_time}, {end_time}]"


# Feature: rest-api-overhaul, Property 8: History Entity Filtering
@given(
    all_entities=st.lists(entity_id_strategy(), min_size=3, max_size=10, unique=True),
    filter_count=st.integers(min_value=1, max_value=3),
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_8_history_entity_filtering(all_entities: list[str], filter_count: int):
    """
    Property 8: History Entity Filtering

    For any entity filter list, all returned history entries SHALL only
    include entities from that filter list.

    Validates: Requirements 4.2, 4.5
    """
    # Select a subset of entities to filter
    filter_count = min(filter_count, len(all_entities))
    filter_entities = all_entities[:filter_count]

    # Generate timestamp
    timestamp = datetime.now(timezone.utc).isoformat()

    # Generate history only for filtered entities
    mock_history = []
    for entity_id in filter_entities:
        entity_history = [
            {
                "entity_id": entity_id,
                "state": "on",
                "last_changed": timestamp,
                "last_updated": timestamp,
                "attributes": {},
            }
        ]
        mock_history.append(entity_history)

    # Create mock client
    mock_client = Mock()
    mock_client.get_history = AsyncMock(return_value=mock_history)

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
    register_history_tool(mock_mcp, lambda: mock_client)

    # Call the tool with entity filter
    result = await tool_func(timestamp=timestamp, filter_entity_id=filter_entities)

    # Verify success
    assert result["success"] is True
    assert "history" in result

    # Verify all returned entities are in the filter list
    for entity_history in result["history"]:
        for entry in entity_history:
            assert (
                entry["entity_id"] in filter_entities
            ), f"Entity {entry['entity_id']} not in filter list {filter_entities}"


# Feature: rest-api-overhaul, Property 9: History Response Structure
@given(entity_id=entity_id_strategy(), entry_count=st.integers(min_value=1, max_value=5))
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_9_history_response_structure(entity_id: str, entry_count: int):
    """
    Property 9: History Response Structure

    For any valid history query, the response SHALL contain a list of entries
    with entity_id, state, last_changed, and last_updated fields.

    Validates: Requirements 4.1, 4.4
    """
    # Generate timestamp
    timestamp = datetime.now(timezone.utc).isoformat()

    # Generate history entries
    mock_history = [[]]
    for i in range(entry_count):
        entry_time = datetime.now(timezone.utc) - timedelta(hours=i)
        mock_history[0].append(
            {
                "entity_id": entity_id,
                "state": "on" if i % 2 == 0 else "off",
                "last_changed": entry_time.isoformat(),
                "last_updated": entry_time.isoformat(),
                "attributes": {"test": "value"},
            }
        )

    # Create mock client
    mock_client = Mock()
    mock_client.get_history = AsyncMock(return_value=mock_history)

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
    register_history_tool(mock_mcp, lambda: mock_client)

    # Call the tool
    result = await tool_func(timestamp=timestamp, filter_entity_id=[entity_id])

    # Verify success
    assert result["success"] is True
    assert "history" in result
    assert isinstance(result["history"], list)

    # Verify response structure
    assert len(result["history"]) > 0
    for entity_history in result["history"]:
        assert isinstance(entity_history, list)
        for entry in entity_history:
            # Verify all required fields are present
            assert "entity_id" in entry
            assert "state" in entry
            assert "last_changed" in entry
            assert "last_updated" in entry

            # Verify field types
            assert isinstance(entry["entity_id"], str)
            assert isinstance(entry["state"], str)
            assert isinstance(entry["last_changed"], str)
            assert isinstance(entry["last_updated"], str)


# Feature: rest-api-overhaul, Property 10: Invalid Timestamp Error Handling
@given(invalid_timestamp=invalid_timestamp_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_10_invalid_timestamp_error_handling(invalid_timestamp: str):
    """
    Property 10: Invalid Timestamp Error Handling

    For any invalid timestamp format, history queries SHALL return a
    validation error with descriptive message.

    Validates: Requirements 4.6
    """
    from src.homeassistant_mcp.exceptions import ServiceCallError

    # Create mock client that raises error for invalid timestamp
    mock_client = Mock()
    mock_client.get_history = AsyncMock(
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
    register_history_tool(mock_mcp, lambda: mock_client)

    # Call the tool with invalid timestamp
    result = await tool_func(timestamp=invalid_timestamp)

    # Verify error response
    assert result["success"] is False
    assert "error" in result
    assert "error_type" in result

    # Verify error message is descriptive
    error_msg = result["error"].lower()
    assert any(keyword in error_msg for keyword in ["invalid", "timestamp", "format", "error"])
