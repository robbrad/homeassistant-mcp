"""Property-based tests for intent handling functionality.

Feature: rest-api-overhaul
Properties: 30, 31, 32
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from homeassistant_mcp.exceptions import ServiceCallError
from homeassistant_mcp.tools.specialized.intent import register_intent_tool

# Strategies for generating test data
intent_type_strategy = st.sampled_from(
    [
        "HassTurnOn",
        "HassTurnOff",
        "HassToggle",
        "HassSetPosition",
        "HassLightSet",
        "HassClimateSetTemperature",
    ]
)

entity_name_strategy = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" "),
)

domain_strategy = st.sampled_from(["light", "switch", "cover", "climate", "fan", "lock"])

area_strategy = st.text(
    min_size=1,
    max_size=30,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll"), whitelist_characters=" "),
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


# Feature: rest-api-overhaul, Property 30: Intent Processing Success
@given(
    intent_type=intent_type_strategy,
    speech_text=st.text(min_size=1, max_size=200),
    language=st.sampled_from(["en", "es", "fr", "de"]),
)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_30_intent_processing_success(intent_type, speech_text, language):
    """
    Property 30: For any valid intent type and data, processing SHALL return
    an intent response with speech and optional card data.

    Validates: Requirements 12.1, 12.2
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock to return intent response
    intent_response = {
        "speech": {"plain": {"speech": speech_text, "extra_data": None}},
        "card": {"title": "Intent Result", "content": speech_text},
        "language": language,
        "response_type": "action_done",
        "data": {"targets": [], "success": [], "failed": []},
    }
    mock_client.handle_intent = AsyncMock(return_value=intent_response)

    # Register tool
    register_intent_tool(mock_mcp, get_client)
    intent_handle = mock_mcp.get_registered_tool()

    # Test intent handling
    result = await intent_handle(intent_type=intent_type, intent_data={"name": "test device"})

    assert result["success"] is True
    assert "speech" in result
    assert "card" in result
    assert result["intent_type"] == intent_type
    assert result["language"] == language
    assert result["response_type"] == "action_done"

    # Verify speech content
    assert isinstance(result["speech"], dict)

    # Verify client was called correctly
    mock_client.handle_intent.assert_called_once_with(
        intent_type=intent_type, intent_data={"name": "test device"}
    )


# Feature: rest-api-overhaul, Property 31: Intent Entity Data Propagation
@given(
    intent_type=intent_type_strategy,
    entity_name=entity_name_strategy,
    domain=domain_strategy,
    area=area_strategy,
)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_31_intent_entity_data_propagation(intent_type, entity_name, domain, area):
    """
    Property 31: For any intent with entity data, the entity information
    SHALL be included in the request to Home Assistant.

    Validates: Requirements 12.3
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock
    intent_response = {
        "speech": {"plain": {"speech": "Done"}},
        "language": "en",
        "response_type": "action_done",
    }
    mock_client.handle_intent = AsyncMock(return_value=intent_response)

    # Register tool
    register_intent_tool(mock_mcp, get_client)
    intent_handle = mock_mcp.get_registered_tool()

    # Create intent data with entity information
    intent_data = {"name": entity_name, "domain": domain, "area": area}

    # Test intent handling with entity data
    result = await intent_handle(intent_type=intent_type, intent_data=intent_data)

    assert result["success"] is True

    # Verify entity data was passed to client
    mock_client.handle_intent.assert_called_once()
    call_args = mock_client.handle_intent.call_args

    assert call_args.kwargs["intent_type"] == intent_type
    assert call_args.kwargs["intent_data"] == intent_data

    # Verify all entity fields were included
    passed_data = call_args.kwargs["intent_data"]
    assert passed_data["name"] == entity_name
    assert passed_data["domain"] == domain
    assert passed_data["area"] == area


# Feature: rest-api-overhaul, Property 32: Unrecognized Intent Error Handling
@given(
    invalid_intent=st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"),
    ),
    error_message=st.text(min_size=10, max_size=200),
)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_32_unrecognized_intent_error_handling(invalid_intent, error_message):
    """
    Property 32: For any unrecognized intent type, processing SHALL return
    an error message.

    Validates: Requirements 12.4
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock to raise ServiceCallError for unrecognized intent
    mock_client.handle_intent = AsyncMock(side_effect=ServiceCallError(error_message))

    # Register tool
    register_intent_tool(mock_mcp, get_client)
    intent_handle = mock_mcp.get_registered_tool()

    # Test error handling
    result = await intent_handle(intent_type=invalid_intent, intent_data={"name": "test"})

    assert result["success"] is False
    assert "error" in result
    assert "error_type" in result
    assert result["intent_type"] == invalid_intent
    assert error_message in result["error"]
    assert result["error_type"] == "ServiceCallError"


# Additional test: Intent without data
@given(intent_type=intent_type_strategy)
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_intent_without_data(intent_type):
    """
    Test that intents can be processed without intent_data parameter.
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock
    intent_response = {
        "speech": {"plain": {"speech": "Done"}},
        "language": "en",
        "response_type": "action_done",
    }
    mock_client.handle_intent = AsyncMock(return_value=intent_response)

    # Register tool
    register_intent_tool(mock_mcp, get_client)
    intent_handle = mock_mcp.get_registered_tool()

    # Test without intent_data
    result = await intent_handle(intent_type=intent_type)

    assert result["success"] is True

    # Verify client was called with None for intent_data
    mock_client.handle_intent.assert_called_once_with(intent_type=intent_type, intent_data=None)


# Additional test: Complex intent data
@given(
    intent_type=intent_type_strategy,
    temperature=st.integers(min_value=60, max_value=85),
    brightness=st.integers(min_value=0, max_value=100),
)
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_complex_intent_data(intent_type, temperature, brightness):
    """
    Test that complex intent data with multiple fields is handled correctly.
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock
    intent_response = {
        "speech": {"plain": {"speech": "Set successfully"}},
        "language": "en",
        "response_type": "action_done",
        "data": {
            "targets": [{"name": "device", "type": "entity"}],
            "success": [{"name": "device"}],
            "failed": [],
        },
    }
    mock_client.handle_intent = AsyncMock(return_value=intent_response)

    # Register tool
    register_intent_tool(mock_mcp, get_client)
    intent_handle = mock_mcp.get_registered_tool()

    # Create complex intent data
    intent_data = {
        "name": "living room",
        "domain": "light",
        "brightness": brightness,
        "temperature": temperature,
        "area": "living room",
    }

    # Test
    result = await intent_handle(intent_type=intent_type, intent_data=intent_data)

    assert result["success"] is True
    assert "data" in result

    # Verify all data was passed through
    call_args = mock_client.handle_intent.call_args
    passed_data = call_args.kwargs["intent_data"]
    assert passed_data["brightness"] == brightness
    assert passed_data["temperature"] == temperature


# Additional test: Intent response with card data
@given(
    intent_type=intent_type_strategy,
    card_title=st.text(min_size=1, max_size=50),
    card_content=st.text(min_size=1, max_size=200),
)
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_intent_response_with_card(intent_type, card_title, card_content):
    """
    Test that intent responses with card data are handled correctly.
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock with card data
    intent_response = {
        "speech": {"plain": {"speech": "Done"}},
        "card": {"title": card_title, "content": card_content},
        "language": "en",
        "response_type": "action_done",
    }
    mock_client.handle_intent = AsyncMock(return_value=intent_response)

    # Register tool
    register_intent_tool(mock_mcp, get_client)
    intent_handle = mock_mcp.get_registered_tool()

    # Test
    result = await intent_handle(intent_type=intent_type)

    assert result["success"] is True
    assert result["card"] is not None
    assert result["card"]["title"] == card_title
    assert result["card"]["content"] == card_content
