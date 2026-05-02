"""Property-based tests for state management tools.

This module tests the following properties:
- Property 3: State Query Response Structure
- Property 4: State Update Round Trip
- Property 5: State Deletion Removes Entity
- Property 6: Invalid Entity Error Handling

Validates Requirements: 3.1-3.10
"""

from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.homeassistant_mcp.tools.state.states import register_states_control_tool


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

    # Create mock client
    mock_client = Mock()
    mock_client.get_state = AsyncMock(return_value=mock_response_data)

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
    register_states_control_tool(mock_mcp, lambda: mock_client)

    # Call the tool with get action
    result = await tool_func(action="get", entity_id=entity_id)

    # Verify success
    assert result["success"] is True
    assert "entity" in result

    # Verify all required fields are present in the entity
    entity = result["entity"]
    assert "entity_id" in entity
    assert "state" in entity
    assert "attributes" in entity
    assert "last_changed" in entity
    assert "last_updated" in entity

    # Verify values match
    assert entity["entity_id"] == entity_id
    assert entity["state"] == state
    assert entity["attributes"] == attributes


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
    # Create mock response data
    mock_state_data = {
        "entity_id": entity_id,
        "state": state,
        "attributes": attributes,
        "last_changed": "2024-01-01T12:00:00+00:00",
        "last_updated": "2024-01-01T12:00:00+00:00",
        "context": {"id": "test", "parent_id": None, "user_id": None},
    }

    # Create mock client
    mock_client = Mock()
    mock_client.set_state = AsyncMock(return_value=mock_state_data)
    mock_client.get_state = AsyncMock(return_value=mock_state_data)

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
    register_states_control_tool(mock_mcp, lambda: mock_client)

    # Set state
    set_result = await tool_func(
        action="set", entity_id=entity_id, state=state, attributes=attributes
    )

    # Verify set was successful
    assert set_result["success"] is True

    # Get state
    get_result = await tool_func(action="get", entity_id=entity_id)

    # Verify get was successful
    assert get_result["success"] is True

    # Verify round trip: state and attributes should match
    entity = get_result["entity"]
    assert entity["state"] == state
    assert entity["attributes"] == attributes
    assert entity["entity_id"] == entity_id


# Feature: rest-api-overhaul, Property 5: State Deletion Removes Entity
@given(entity_id=entity_id_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_5_state_deletion_removes_entity(entity_id: str):
    """
    Property 5: State Deletion Removes Entity

    For any entity that exists, deleting its state then attempting to
    retrieve it SHALL return an entity not found error.

    Validates: Requirements 3.5
    """
    from src.homeassistant_mcp.exceptions import EntityNotFoundError

    # Create mock client
    mock_client = Mock()
    mock_client.delete_state = AsyncMock(return_value={"message": "State deleted"})
    mock_client.get_state = AsyncMock(
        side_effect=EntityNotFoundError(f"Entity '{entity_id}' not found in Home Assistant")
    )

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
    register_states_control_tool(mock_mcp, lambda: mock_client)

    # Delete state
    delete_result = await tool_func(action="delete", entity_id=entity_id)

    # Verify deletion was successful
    assert delete_result["success"] is True

    # Try to get the deleted entity
    get_result = await tool_func(action="get", entity_id=entity_id)

    # Verify that get returns an error
    assert get_result["success"] is False
    assert get_result["error_type"] == "entity_not_found"
    assert entity_id in get_result["error"]


# Feature: rest-api-overhaul, Property 6: Invalid Entity Error Handling
@given(entity_id=entity_id_strategy())
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_6_invalid_entity_error_handling(entity_id: str):
    """
    Property 6: Invalid Entity Error Handling

    For any non-existent entity ID, querying its state SHALL return an
    entity not found error with descriptive message.

    Validates: Requirements 3.6
    """
    from src.homeassistant_mcp.exceptions import EntityNotFoundError

    # Create mock client that raises EntityNotFoundError
    mock_client = Mock()
    mock_client.get_state = AsyncMock(
        side_effect=EntityNotFoundError(f"Entity '{entity_id}' not found in Home Assistant")
    )

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
    register_states_control_tool(mock_mcp, lambda: mock_client)

    # Try to get non-existent entity
    result = await tool_func(action="get", entity_id=entity_id)

    # Verify error response
    assert result["success"] is False
    assert result["error_type"] == "entity_not_found"
    assert "error" in result
    assert entity_id in result["error"]
    assert "not found" in result["error"].lower()
