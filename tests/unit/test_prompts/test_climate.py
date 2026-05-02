"""Unit tests for climate optimization prompt."""

from unittest.mock import AsyncMock, MagicMock

import pytest


def get_messages_text(result):
    """Helper to extract text from prompt messages."""
    return " ".join([str(msg.content) if hasattr(msg, 'content') else str(msg.get("content", "")) for msg in result])


@pytest.mark.asyncio
async def test_climate_prompt_basic_flow(mock_hass_client):
    """Test basic climate optimization prompt flow."""
    from src.homeassistant_mcp.prompts.climate import register_climate_prompt

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt
    def get_client():
        return mock_hass_client

    mock_hass_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "climate.bedroom",
                "state": "heat",
                "attributes": {
                    "current_temperature": 68,
                    "temperature": 72,
                    "hvac_mode": "heat",
                    "fan_mode": "auto",
                },
            }
        ]
    )

    register_climate_prompt(mcp, get_client)

    result = await prompt_func(area="")

    assert isinstance(result, list)
    assert len(result) > 0

    messages_text = get_messages_text(result)
    assert "climate" in messages_text.lower() or "temperature" in messages_text.lower()


@pytest.mark.asyncio
async def test_climate_prompt_with_area_filter(mock_hass_client):
    """Test climate prompt with area filter."""
    from src.homeassistant_mcp.prompts.climate import register_climate_prompt

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt
    def get_client():
        return mock_hass_client

    mock_hass_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "climate.bedroom",
                "state": "heat",
                "attributes": {"temperature": 70},
            }
        ]
    )

    register_climate_prompt(mcp, get_client)

    result = await prompt_func(area="Bedroom")

    assert isinstance(result, list)
    messages_text = get_messages_text(result)
    assert "bedroom" in messages_text.lower()


@pytest.mark.asyncio
async def test_climate_prompt_includes_weather_context(mock_hass_client):
    """Test climate prompt includes weather information."""
    from src.homeassistant_mcp.prompts.climate import register_climate_prompt

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt
    def get_client():
        return mock_hass_client

    # First call for climate devices
    # Second call for weather
    mock_hass_client.get_states = AsyncMock(
        side_effect=[
            [
                {
                    "entity_id": "climate.living_room",
                    "state": "heat",
                    "attributes": {"temperature": 70},
                }
            ],
            [
                {
                    "entity_id": "weather.home",
                    "state": "sunny",
                    "attributes": {"temperature": 45, "humidity": 60},
                }
            ],
        ]
    )

    register_climate_prompt(mcp, get_client)

    result = await prompt_func(area="")

    assert isinstance(result, list)
    messages_text = get_messages_text(result)
    assert "weather" in messages_text.lower()


@pytest.mark.asyncio
async def test_climate_prompt_handles_no_devices(mock_hass_client):
    """Test climate prompt when no climate devices found."""
    from src.homeassistant_mcp.prompts.climate import register_climate_prompt

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt
    def get_client():
        return mock_hass_client

    mock_hass_client.get_states = AsyncMock(return_value=[])

    register_climate_prompt(mcp, get_client)

    result = await prompt_func(area="")

    assert isinstance(result, list)
    messages_text = get_messages_text(result)
    assert "no climate" in messages_text.lower() or "not found" in messages_text.lower()


@pytest.mark.asyncio
async def test_climate_prompt_provides_recommendations(mock_hass_client):
    """Test climate prompt provides optimization recommendations."""
    from src.homeassistant_mcp.prompts.climate import register_climate_prompt

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt
    def get_client():
        return mock_hass_client

    mock_hass_client.get_states = AsyncMock(return_value=[])

    register_climate_prompt(mcp, get_client)

    result = await prompt_func(area="")

    assert isinstance(result, list)
    messages_text = get_messages_text(result)
    # Should include recommendations even without devices
    assert "recommendation" in messages_text.lower() or "optimization" in messages_text.lower()
