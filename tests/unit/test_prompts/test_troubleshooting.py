"""Unit tests for device troubleshooting prompt."""

from unittest.mock import AsyncMock, MagicMock

import pytest


def get_messages_text(result):
    """Helper to extract text from prompt messages."""
    return " ".join([str(msg.content) if hasattr(msg, 'content') else str(msg.get("content", "")) for msg in result])


@pytest.mark.asyncio
async def test_troubleshooting_prompt_available_device(mock_hass_client):
    """Test troubleshooting prompt with available device."""
    from src.homeassistant_mcp.prompts.troubleshooting import (
        register_troubleshooting_prompt,
    )

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

    mock_hass_client.get_state = AsyncMock(
        return_value={
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"brightness": 255},
            "last_changed": "2024-01-15T10:00:00",
            "last_updated": "2024-01-15T10:00:00",
        }
    )
    mock_hass_client.get_history = AsyncMock(return_value=[[]])
    mock_hass_client.get_error_log = AsyncMock(return_value="")

    register_troubleshooting_prompt(mcp, get_client)

    result = await prompt_func(entity_id="light.living_room")

    assert isinstance(result, list)
    assert len(result) > 0

    messages_text = get_messages_text(result)
    assert "light.living_room" in messages_text


@pytest.mark.asyncio
async def test_troubleshooting_prompt_unavailable_device(mock_hass_client):
    """Test troubleshooting prompt with unavailable device."""
    from src.homeassistant_mcp.prompts.troubleshooting import (
        register_troubleshooting_prompt,
    )

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

    mock_hass_client.get_state = AsyncMock(
        return_value={
            "entity_id": "sensor.temperature",
            "state": "unavailable",
            "attributes": {},
            "last_changed": "2024-01-15T10:00:00",
            "last_updated": "2024-01-15T10:00:00",
        }
    )
    mock_hass_client.get_history = AsyncMock(return_value=[[]])
    mock_hass_client.get_error_log = AsyncMock(return_value="")

    register_troubleshooting_prompt(mcp, get_client)

    result = await prompt_func(entity_id="sensor.temperature")

    assert isinstance(result, list)
    messages_text = get_messages_text(result)
    assert "unavailable" in messages_text.lower()


@pytest.mark.asyncio
async def test_troubleshooting_prompt_entity_not_found(mock_hass_client):
    """Test troubleshooting prompt when entity doesn't exist."""
    from src.homeassistant_mcp.prompts.troubleshooting import (
        register_troubleshooting_prompt,
    )

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

    mock_hass_client.get_state = AsyncMock(side_effect=Exception("Entity not found"))
    mock_hass_client.get_history = AsyncMock(return_value=[[]])
    mock_hass_client.get_error_log = AsyncMock(return_value="")

    register_troubleshooting_prompt(mcp, get_client)

    result = await prompt_func(entity_id="light.nonexistent")

    assert isinstance(result, list)
    messages_text = get_messages_text(result)
    assert "error" in messages_text.lower()


@pytest.mark.asyncio
async def test_troubleshooting_prompt_with_history(mock_hass_client):
    """Test troubleshooting prompt includes history analysis."""
    from src.homeassistant_mcp.prompts.troubleshooting import (
        register_troubleshooting_prompt,
    )

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

    mock_hass_client.get_state = AsyncMock(
        return_value={
            "entity_id": "light.test",
            "state": "on",
            "attributes": {},
            "last_changed": "2024-01-15T10:00:00",
            "last_updated": "2024-01-15T10:00:00",
        }
    )
    mock_hass_client.get_history = AsyncMock(
        return_value=[
            [
                {"state": "on", "last_changed": "2024-01-15T09:00:00"},
                {"state": "off", "last_changed": "2024-01-15T08:00:00"},
            ]
        ]
    )
    mock_hass_client.get_error_log = AsyncMock(return_value="")

    register_troubleshooting_prompt(mcp, get_client)

    result = await prompt_func(entity_id="light.test")

    assert isinstance(result, list)
    messages_text = get_messages_text(result)
    assert "history" in messages_text.lower() or "changes" in messages_text.lower()
