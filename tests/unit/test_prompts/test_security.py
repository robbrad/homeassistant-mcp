"""Unit tests for security check prompt."""

from unittest.mock import AsyncMock, MagicMock

import pytest


def get_messages_text(result):
    """Helper to extract text from prompt messages."""
    return " ".join([str(msg.content) if hasattr(msg, 'content') else str(msg.get("content", "")) for msg in result])


@pytest.mark.asyncio
async def test_security_prompt_basic_flow(mock_hass_client):
    """Test basic security check prompt flow."""
    from src.homeassistant_mcp.prompts.security import register_security_prompt

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
            {"entity_id": "lock.front_door", "state": "locked", "attributes": {}},
            {"entity_id": "alarm_control_panel.home", "state": "armed_away", "attributes": {}},
            {"entity_id": "camera.driveway", "state": "idle", "attributes": {}},
        ]
    )

    register_security_prompt(mcp, get_client)

    result = await prompt_func()

    assert isinstance(result, list)
    assert len(result) > 0

    messages_text = get_messages_text(result)
    assert "security" in messages_text.lower()


@pytest.mark.asyncio
async def test_security_prompt_detects_unlocked_locks(mock_hass_client):
    """Test security prompt detects unlocked locks."""
    from src.homeassistant_mcp.prompts.security import register_security_prompt

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
            {"entity_id": "lock.front_door", "state": "unlocked", "attributes": {}},
            {"entity_id": "lock.back_door", "state": "locked", "attributes": {}},
        ]
    )

    register_security_prompt(mcp, get_client)

    result = await prompt_func()

    assert isinstance(result, list)
    messages_text = get_messages_text(result)
    assert "unlocked" in messages_text.lower()


@pytest.mark.asyncio
async def test_security_prompt_detects_disarmed_alarm(mock_hass_client):
    """Test security prompt detects disarmed alarm."""
    from src.homeassistant_mcp.prompts.security import register_security_prompt

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
            {"entity_id": "alarm_control_panel.home", "state": "disarmed", "attributes": {}},
        ]
    )

    register_security_prompt(mcp, get_client)

    result = await prompt_func()

    assert isinstance(result, list)
    messages_text = get_messages_text(result)
    assert "disarmed" in messages_text.lower()


@pytest.mark.asyncio
async def test_security_prompt_checks_sensors(mock_hass_client):
    """Test security prompt checks door and window sensors."""
    from src.homeassistant_mcp.prompts.security import register_security_prompt

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
            {"entity_id": "binary_sensor.front_door", "state": "on", "attributes": {}},
            {"entity_id": "binary_sensor.window_bedroom", "state": "off", "attributes": {}},
        ]
    )

    register_security_prompt(mcp, get_client)

    result = await prompt_func()

    assert isinstance(result, list)
    messages_text = get_messages_text(result)
    assert "door" in messages_text.lower() or "sensor" in messages_text.lower()


@pytest.mark.asyncio
async def test_security_prompt_handles_no_devices(mock_hass_client):
    """Test security prompt when no security devices found."""
    from src.homeassistant_mcp.prompts.security import register_security_prompt

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

    register_security_prompt(mcp, get_client)

    result = await prompt_func()

    assert isinstance(result, list)
    assert len(result) > 0
