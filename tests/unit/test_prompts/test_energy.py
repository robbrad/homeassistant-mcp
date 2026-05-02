"""Unit tests for energy optimization prompt."""

from unittest.mock import AsyncMock, MagicMock

import pytest


def get_messages_text(result):
    """Helper to extract text from prompt messages."""
    return " ".join([str(msg.content) if hasattr(msg, 'content') else str(msg.get("content", "")) for msg in result])


@pytest.mark.asyncio
async def test_energy_prompt_basic_flow(mock_hass_client):
    """Test basic energy optimization prompt flow."""
    from src.homeassistant_mcp.prompts.energy import register_energy_prompt

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
            {"entity_id": "light.living_room", "state": "on", "attributes": {"brightness": 255}},
            {"entity_id": "climate.bedroom", "state": "heat", "attributes": {"temperature": 72}},
            {"entity_id": "switch.heater", "state": "on", "attributes": {}},
        ]
    )

    register_energy_prompt(mcp, get_client)

    result = await prompt_func(area="")

    assert isinstance(result, list)
    assert len(result) > 0

    messages_text = get_messages_text(result)
    assert "energy" in messages_text.lower() or "optimization" in messages_text.lower()


@pytest.mark.asyncio
async def test_energy_prompt_with_area_filter(mock_hass_client):
    """Test energy prompt with area filter."""
    from src.homeassistant_mcp.prompts.energy import register_energy_prompt

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
            {"entity_id": "light.bedroom", "state": "on", "attributes": {}},
        ]
    )

    register_energy_prompt(mcp, get_client)

    result = await prompt_func(area="Bedroom")

    assert isinstance(result, list)
    messages_text = get_messages_text(result)
    assert "bedroom" in messages_text.lower()


@pytest.mark.asyncio
async def test_energy_prompt_categorizes_devices(mock_hass_client):
    """Test energy prompt categorizes devices by type."""
    from src.homeassistant_mcp.prompts.energy import register_energy_prompt

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
            {"entity_id": "light.living_room", "state": "on", "attributes": {}},
            {"entity_id": "climate.bedroom", "state": "heat", "attributes": {}},
            {"entity_id": "switch.fan", "state": "on", "attributes": {}},
            {"entity_id": "media_player.tv", "state": "playing", "attributes": {}},
        ]
    )

    register_energy_prompt(mcp, get_client)

    result = await prompt_func(area="")

    assert isinstance(result, list)
    messages_text = get_messages_text(result)
    # Should mention different device categories
    assert "light" in messages_text.lower()
    assert "climate" in messages_text.lower()


@pytest.mark.asyncio
async def test_energy_prompt_handles_no_devices(mock_hass_client):
    """Test energy prompt when no devices found."""
    from src.homeassistant_mcp.prompts.energy import register_energy_prompt

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

    register_energy_prompt(mcp, get_client)

    result = await prompt_func(area="")

    assert isinstance(result, list)
    assert len(result) > 0
