"""Unit tests for scene creation prompt."""

from unittest.mock import AsyncMock, MagicMock

import pytest


def get_messages_text(result):
    """Helper to extract text from prompt messages."""
    return " ".join([str(msg.content) if hasattr(msg, 'content') else str(msg.get("content", "")) for msg in result])


@pytest.mark.asyncio
async def test_scene_prompt_basic_flow(mock_hass_client):
    """Test basic scene prompt conversation flow."""
    from src.homeassistant_mcp.prompts.scene import register_scene_prompt

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
            {"entity_id": "light.bedroom", "state": "off", "attributes": {}},
            {"entity_id": "switch.fan", "state": "on", "attributes": {}},
        ]
    )

    register_scene_prompt(mcp, get_client)

    result = await prompt_func(name="Evening Scene", area="Bedroom")

    assert isinstance(result, list)
    assert len(result) > 0

    # Verify conversation includes entity selection and state definition
    messages_text = get_messages_text(result)
    assert "entities" in messages_text.lower() or "entity" in messages_text.lower()
    assert "state" in messages_text.lower()


@pytest.mark.asyncio
async def test_scene_prompt_without_area(mock_hass_client):
    """Test scene prompt without area filter."""
    from src.homeassistant_mcp.prompts.scene import register_scene_prompt

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

    register_scene_prompt(mcp, get_client)

    result = await prompt_func(name="Test Scene")

    assert isinstance(result, list)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_scene_prompt_groups_by_domain(mock_hass_client):
    """Test scene prompt groups entities by domain."""
    from src.homeassistant_mcp.prompts.scene import register_scene_prompt

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
            {"entity_id": "light.bedroom", "state": "off", "attributes": {}},
            {"entity_id": "switch.fan", "state": "on", "attributes": {}},
        ]
    )

    register_scene_prompt(mcp, get_client)

    result = await prompt_func(name="Test Scene", area="")

    assert isinstance(result, list)
    # Should group lights and switches separately
    messages_text = get_messages_text(result)
    assert "light" in messages_text.lower()
