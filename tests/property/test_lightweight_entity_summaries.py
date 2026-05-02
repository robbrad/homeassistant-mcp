"""Property-based tests for lightweight entity summaries in area and device resources.

This module tests the following property:
- Property 5: Lightweight Entity Summaries

Validates Requirements: 3.7, 3.8, 20.1, 20.2, 20.3, 20.4
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
def entity_list_strategy(draw):
    """Generate a list of entity states for testing."""
    num_entities = draw(st.integers(min_value=1, max_value=10))
    entities = []

    for _ in range(num_entities):
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


# Feature: mcp-resources-layer, Property 5: Lightweight Entity Summaries
@given(
    area_id=area_id_strategy(),
    entities=entity_list_strategy(),
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_5_area_lightweight_entity_summaries(
    area_id: str, entities: list[dict[str, Any]]
):
    """
    Property 5: Lightweight Entity Summaries (Area Resources)

    For any area resource response, each entity in the entities list must contain
    only these fields: entity_id, state, domain, and friendly_name (no full attributes).

    Validates: Requirements 3.7, 20.1, 20.2, 20.3, 20.4
    """
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

    # Verify entities list exists
    assert "entities" in data
    entity_summaries = data["entities"]

    # Property 5: Verify each entity has ONLY the 4 required fields
    required_fields = {"entity_id", "state", "domain", "friendly_name"}

    for entity_summary in entity_summaries:
        # Check that entity_summary is a dict
        assert isinstance(entity_summary, dict), "Entity summary must be a dictionary"

        # Get the actual fields in the entity summary
        actual_fields = set(entity_summary.keys())

        # Verify EXACTLY the required fields are present (no more, no less)
        assert actual_fields == required_fields, (
            f"Entity summary must contain exactly {required_fields}, "
            f"but got {actual_fields}. "
            f"Extra fields: {actual_fields - required_fields}, "
            f"Missing fields: {required_fields - actual_fields}"
        )

        # Verify no 'attributes' field is present (full attributes should not be included)
        assert (
            "attributes" not in entity_summary
        ), "Entity summary must NOT include full 'attributes' field"

        # Verify all required fields have non-empty values
        assert entity_summary["entity_id"], "entity_id must not be empty"
        assert entity_summary["state"], "state must not be empty"
        assert entity_summary["domain"], "domain must not be empty"
        assert entity_summary["friendly_name"], "friendly_name must not be empty"

        # Verify domain is correctly extracted from entity_id
        expected_domain = entity_summary["entity_id"].split(".")[0]
        assert entity_summary["domain"] == expected_domain, (
            f"Domain '{entity_summary['domain']}' does not match "
            f"expected domain '{expected_domain}' from entity_id"
        )


# Feature: mcp-resources-layer, Property 5: Lightweight Entity Summaries
@given(
    device_id=device_id_strategy(),
    entities=entity_list_strategy(),
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_5_device_lightweight_entity_summaries(
    device_id: str, entities: list[dict[str, Any]]
):
    """
    Property 5: Lightweight Entity Summaries (Device Resources)

    For any device resource response, each entity in the entities list must contain
    only these fields: entity_id, state, domain, and friendly_name (no full attributes).

    Validates: Requirements 3.8, 20.1, 20.2, 20.3, 20.4
    """
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

    # Parse the response - device resources return TextResource
    assert result is not None
    # Extract text from TextResource
    result_text = result.text if hasattr(result, "text") else result
    parsed = json.loads(result_text)

    # Verify entities list exists
    assert "data" in parsed
    data = parsed["data"]
    assert "entities" in data
    entity_list = data["entities"]

    # NOTE: Current device resource implementation includes full attributes
    # This test will FAIL until task 5 is completed to update device resources
    # with lightweight summaries like area resources

    # Property 5: Verify each entity has ONLY the 4 required fields
    required_fields = {"entity_id", "state", "domain", "friendly_name"}

    for entity_summary in entity_list:
        # Check that entity_summary is a dict
        assert isinstance(entity_summary, dict), "Entity summary must be a dictionary"

        # Get the actual fields in the entity summary
        actual_fields = set(entity_summary.keys())

        # Verify EXACTLY the required fields are present (no more, no less)
        assert actual_fields == required_fields, (
            f"Entity summary must contain exactly {required_fields}, "
            f"but got {actual_fields}. "
            f"Extra fields: {actual_fields - required_fields}, "
            f"Missing fields: {required_fields - actual_fields}"
        )

        # Verify no 'attributes' field is present (full attributes should not be included)
        assert (
            "attributes" not in entity_summary
        ), "Entity summary must NOT include full 'attributes' field"

        # Verify all required fields have non-empty values
        assert entity_summary["entity_id"], "entity_id must not be empty"
        assert entity_summary["state"], "state must not be empty"
        assert entity_summary["domain"], "domain must not be empty"
        assert entity_summary["friendly_name"], "friendly_name must not be empty"

        # Verify domain is correctly extracted from entity_id
        expected_domain = entity_summary["entity_id"].split(".")[0]
        assert entity_summary["domain"] == expected_domain, (
            f"Domain '{entity_summary['domain']}' does not match "
            f"expected domain '{expected_domain}' from entity_id"
        )
