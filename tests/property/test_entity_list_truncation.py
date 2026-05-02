"""Property-based tests for entity list truncation in area and device resources.

This module tests the following property:
- Property 18: Entity List Truncation

Validates Requirements: 5.6, 6.6, 20.5, 20.6, 20.7
"""

import json
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.homeassistant_mcp.resources.areas import register_area_resources
from src.homeassistant_mcp.resources.devices import register_device_resources


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
    """Generate valid entity attributes dictionaries with friendly_name."""
    # Generate simple attributes with string, int, float, or bool values
    keys = draw(
        st.lists(
            st.text(alphabet=st.characters(whitelist_categories=("Ll",)), min_size=1, max_size=15),
            min_size=0,
            max_size=10,
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
                        min_value=-1000.0,
                        max_value=1000.0,
                        allow_nan=False,
                        allow_infinity=False,
                    )
                )
            )
        else:
            values.append(draw(st.booleans()))

    attrs = dict(zip(keys, values, strict=False))

    # Always include friendly_name
    if "friendly_name" not in attrs:
        attrs["friendly_name"] = draw(st.text(min_size=1, max_size=30))

    return attrs


@st.composite
def area_id_strategy(draw):
    """Generate valid area IDs."""
    return draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
            min_size=1,
            max_size=20,
        )
    )


@st.composite
def device_id_strategy(draw):
    """Generate valid device IDs (typically UUIDs or hex strings)."""
    return draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Nd")),
            min_size=10,
            max_size=32,
        )
    )


@st.composite
def large_entity_list_strategy(draw):
    """Generate a list of entity states with more than 50 entities for truncation testing."""
    # Generate between 51 and 100 entities to test truncation
    num_entities = draw(st.integers(min_value=51, max_value=100))
    entities = []

    for _i in range(num_entities):
        entity_id = draw(entity_id_strategy())
        state = draw(entity_state_strategy())
        attributes = draw(attributes_strategy())

        entities.append(
            {
                "entity_id": entity_id,
                "state": state,
                "attributes": attributes,
                "last_changed": "2024-01-15T10:25:00+00:00",
                "last_updated": "2024-01-15T10:30:00+00:00",
                "context": {"id": "test", "parent_id": None, "user_id": None},
            }
        )

    return entities


# Feature: mcp-resources-layer, Property 18: Entity List Truncation
@given(
    area_id=area_id_strategy(),
    entities=large_entity_list_strategy(),
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_18_area_entity_list_truncation(
    area_id: str, entities: list[dict[str, Any]]
):
    """
    Property 18: Entity List Truncation (Area Resources)

    For any area with more than 50 entities, the response must include only
    the first 50 entities and set truncated=true.

    Validates: Requirements 5.6, 20.5, 20.6, 20.7
    """
    # Verify test precondition: we have more than 50 entities
    assert len(entities) > 50, "Test requires more than 50 entities"

    # Create mock client that returns entities for the area
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=entities)

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

    # Register area resources
    register_area_resources(mock_mcp, get_client)

    # Get the resource handler
    handler = resource_handlers["hass://area/{area_id}"]

    # Call the handler
    result = await handler(area_id)

    # Parse the response
    assert result is not None
    parsed = json.loads(result.text)

    # Verify response envelope structure
    assert "data" in parsed
    data = parsed["data"]

    # Property 18: Verify truncation behavior

    # 1. Verify entity_count reflects the TOTAL number of entities
    assert "entity_count" in data, "Response must include entity_count"
    assert data["entity_count"] == len(entities), (
        f"entity_count must reflect total entities ({len(entities)}), "
        f"but got {data['entity_count']}"
    )

    # 2. Verify entities list contains ONLY the first 50 entities
    assert "entities" in data, "Response must include entities list"
    entity_summaries = data["entities"]
    assert len(entity_summaries) == 50, (
        f"For areas with more than 50 entities, response must include exactly 50 entities, "
        f"but got {len(entity_summaries)}"
    )

    # 3. Verify truncated indicator is set to true
    assert "truncated" in data, "Response must include truncated indicator"
    assert data["truncated"] is True, (
        f"For areas with more than 50 entities, truncated must be true, "
        f"but got {data['truncated']}"
    )

    # 4. Verify the returned entities are the FIRST 50 from the original list
    for i, entity_summary in enumerate(entity_summaries):
        original_entity = entities[i]
        assert (
            entity_summary["entity_id"] == original_entity["entity_id"]
        ), f"Entity at index {i} must match the first 50 entities from the original list"


# Feature: mcp-resources-layer, Property 18: Entity List Truncation
@given(
    device_id=device_id_strategy(),
    entities=large_entity_list_strategy(),
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_18_device_entity_list_truncation(
    device_id: str, entities: list[dict[str, Any]]
):
    """
    Property 18: Entity List Truncation (Device Resources)

    For any device with more than 50 entities, the response must include only
    the first 50 entities and set truncated=true.

    Validates: Requirements 6.6, 20.5, 20.6, 20.7
    """
    # Verify test precondition: we have more than 50 entities
    assert len(entities) > 50, "Test requires more than 50 entities"

    # Add device_id to entity attributes so they'll be filtered correctly
    for entity in entities:
        entity["attributes"]["device_id"] = device_id

    # Create mock client that returns all entities
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=entities)

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

    # Register device resources
    register_device_resources(mock_mcp, get_client)

    # Get the resource handler
    handler = resource_handlers["hass://device/{device_id}"]

    # Call the handler
    result = await handler(device_id)

    # Parse the response - device resources now return TextResource like area resources
    assert result is not None
    parsed = json.loads(result.text)

    # Verify response envelope structure
    assert "data" in parsed
    data = parsed["data"]

    # Property 18: Verify truncation behavior

    # 1. Verify entity_count reflects the TOTAL number of entities
    assert "entity_count" in data, "Response must include entity_count"
    assert data["entity_count"] == len(entities), (
        f"entity_count must reflect total entities ({len(entities)}), "
        f"but got {data['entity_count']}"
    )

    # 2. Verify entities list contains ONLY the first 50 entities
    assert "entities" in data, "Response must include entities list"
    entity_list = data["entities"]
    assert len(entity_list) == 50, (
        f"For devices with more than 50 entities, response must include exactly 50 entities, "
        f"but got {len(entity_list)}"
    )

    # 3. Verify truncated indicator is set to true
    assert "truncated" in data, "Response must include truncated indicator"
    assert data["truncated"] is True, (
        f"For devices with more than 50 entities, truncated must be true, "
        f"but got {data['truncated']}"
    )

    # 4. Verify the returned entities are the FIRST 50 from the original list
    for i, entity_summary in enumerate(entity_list):
        original_entity = entities[i]
        assert (
            entity_summary["entity_id"] == original_entity["entity_id"]
        ), f"Entity at index {i} must match the first 50 entities from the original list"
