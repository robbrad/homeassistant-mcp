"""Unit tests for automation prompts."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant_mcp.exceptions import ConnectionError, EntityNotFoundError


@pytest.mark.asyncio
async def test_create_automation_basic_flow(mock_hass_client):
    """Test basic create_automation prompt conversation flow."""
    from src.homeassistant_mcp.prompts.automation import register_automation_prompts

    mcp = MagicMock()
    prompts = {}

    def capture_prompt(**kwargs):
        def decorator(func):
            prompts[func.__name__] = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    def get_client():
        return mock_hass_client

    mock_hass_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"brightness": 255},
            }
        ]
    )

    register_automation_prompts(mcp, get_client)

    result = await prompts["create_automation"](
        name="Test Automation", description="Test description"
    )

    assert isinstance(result, list)
    assert len(result) > 0

    # Verify conversation flow includes key steps
    messages_text = ""
    for msg in result:
        if hasattr(msg, "content"):
            if hasattr(msg.content, "text"):
                messages_text += msg.content.text
    assert "trigger" in messages_text.lower()
    assert "condition" in messages_text.lower()
    assert "action" in messages_text.lower()


@pytest.mark.asyncio
async def test_create_automation_without_description(mock_hass_client):
    """Test create_automation prompt with no description."""
    from src.homeassistant_mcp.prompts.automation import register_automation_prompts

    mcp = MagicMock()
    prompts = {}

    def capture_prompt(**kwargs):
        def decorator(func):
            prompts[func.__name__] = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    def get_client():
        return mock_hass_client

    mock_hass_client.get_states = AsyncMock(return_value=[])

    register_automation_prompts(mcp, get_client)

    result = await prompts["create_automation"](name="Test Automation")

    assert isinstance(result, list)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_create_automation_handles_client_error(mock_hass_client):
    """Test create_automation prompt handles client errors gracefully."""
    from src.homeassistant_mcp.prompts.automation import register_automation_prompts

    mcp = MagicMock()
    prompts = {}

    def capture_prompt(**kwargs):
        def decorator(func):
            prompts[func.__name__] = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    def get_client():
        return mock_hass_client

    mock_hass_client.get_states = AsyncMock(side_effect=Exception("API error"))

    register_automation_prompts(mcp, get_client)

    # Should not raise exception
    result = await prompts["create_automation"](name="Test Automation")

    assert isinstance(result, list)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_diagnose_automation_enabled(mock_hass_client):
    """Test diagnose_automation with an enabled automation."""
    from src.homeassistant_mcp.prompts.automation import register_automation_prompts

    mcp = MagicMock()
    prompts = {}

    def capture_prompt(**kwargs):
        def decorator(func):
            prompts[func.__name__] = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    def get_client():
        return mock_hass_client

    mock_hass_client.get_state = AsyncMock(
        return_value={
            "entity_id": "automation.morning_lights",
            "state": "on",
            "attributes": {
                "friendly_name": "Morning Lights",
                "last_triggered": "2024-01-15T07:00:00",
                "trigger": [{"platform": "time", "at": "07:00:00"}],
                "condition": [],
                "action": [
                    {"service": "light.turn_on", "target": {"entity_id": "light.bedroom"}}
                ],
            },
        }
    )

    register_automation_prompts(mcp, get_client)

    result = await prompts["diagnose_automation"](automation_id="automation.morning_lights")

    assert isinstance(result, list)
    assert len(result) > 0

    # Extract text content
    messages_text = ""
    for msg in result:
        if hasattr(msg, "content"):
            if hasattr(msg.content, "text"):
                messages_text += msg.content.text

    # Verify diagnostic content
    assert "automation.morning_lights" in messages_text
    assert "enabled" in messages_text.lower()
    assert "trigger" in messages_text.lower()


@pytest.mark.asyncio
async def test_diagnose_automation_disabled(mock_hass_client):
    """Test diagnose_automation with a disabled automation."""
    from src.homeassistant_mcp.prompts.automation import register_automation_prompts

    mcp = MagicMock()
    prompts = {}

    def capture_prompt(**kwargs):
        def decorator(func):
            prompts[func.__name__] = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    def get_client():
        return mock_hass_client

    mock_hass_client.get_state = AsyncMock(
        return_value={
            "entity_id": "automation.test",
            "state": "off",
            "attributes": {
                "friendly_name": "Test Automation",
                "last_triggered": "Never",
                "trigger": [],
                "condition": [],
                "action": [],
            },
        }
    )

    register_automation_prompts(mcp, get_client)

    result = await prompts["diagnose_automation"](automation_id="automation.test")

    assert isinstance(result, list)
    assert len(result) > 0

    # Extract text content
    messages_text = ""
    for msg in result:
        if hasattr(msg, "content"):
            if hasattr(msg.content, "text"):
                messages_text += msg.content.text

    # Verify warning about disabled state
    assert "disabled" in messages_text.lower() or "not" in messages_text.lower()


@pytest.mark.asyncio
async def test_diagnose_automation_not_found(mock_hass_client):
    """Test diagnose_automation with non-existent automation."""
    from src.homeassistant_mcp.prompts.automation import register_automation_prompts

    mcp = MagicMock()
    prompts = {}

    def capture_prompt(**kwargs):
        def decorator(func):
            prompts[func.__name__] = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    def get_client():
        return mock_hass_client

    mock_hass_client.get_state = AsyncMock(side_effect=EntityNotFoundError("Not found"))

    register_automation_prompts(mcp, get_client)

    result = await prompts["diagnose_automation"](automation_id="automation.nonexistent")

    assert isinstance(result, list)
    assert len(result) > 0

    # Extract text content
    messages_text = ""
    for msg in result:
        if hasattr(msg, "content"):
            if hasattr(msg.content, "text"):
                messages_text += msg.content.text

    # Verify error message
    assert "not found" in messages_text.lower()


@pytest.mark.asyncio
async def test_diagnose_automation_connection_error(mock_hass_client):
    """Test diagnose_automation handles connection errors."""
    from src.homeassistant_mcp.prompts.automation import register_automation_prompts

    mcp = MagicMock()
    prompts = {}

    def capture_prompt(**kwargs):
        def decorator(func):
            prompts[func.__name__] = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    def get_client():
        return mock_hass_client

    mock_hass_client.get_state = AsyncMock(side_effect=ConnectionError("Connection failed"))

    register_automation_prompts(mcp, get_client)

    result = await prompts["diagnose_automation"](automation_id="automation.test")

    assert isinstance(result, list)
    assert len(result) > 0

    # Extract text content
    messages_text = ""
    for msg in result:
        if hasattr(msg, "content"):
            if hasattr(msg.content, "text"):
                messages_text += msg.content.text

    # Verify connection error message
    assert "connect" in messages_text.lower()


@pytest.mark.asyncio
async def test_suggest_automation_time_based(mock_hass_client):
    """Test suggest_automation with time-based intent."""
    from src.homeassistant_mcp.prompts.automation import register_automation_prompts

    mcp = MagicMock()
    prompts = {}

    def capture_prompt(**kwargs):
        def decorator(func):
            prompts[func.__name__] = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    def get_client():
        return mock_hass_client

    mock_hass_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "light.porch",
                "state": "off",
                "attributes": {"friendly_name": "Porch Light"},
            }
        ]
    )

    register_automation_prompts(mcp, get_client)

    result = await prompts["suggest_automation"](
        intent="Turn on porch light at 7 PM", constraints="Only on weekdays"
    )

    assert isinstance(result, list)
    assert len(result) > 0

    # Extract text content
    messages_text = ""
    for msg in result:
        if hasattr(msg, "content"):
            if hasattr(msg.content, "text"):
                messages_text += msg.content.text

    # Verify suggestion includes intent and constraints
    assert "Turn on porch light at 7 PM" in messages_text
    assert "Only on weekdays" in messages_text
    assert "trigger" in messages_text.lower()
    assert "action" in messages_text.lower()


@pytest.mark.asyncio
async def test_suggest_automation_sunset_trigger(mock_hass_client):
    """Test suggest_automation with sunset trigger."""
    from src.homeassistant_mcp.prompts.automation import register_automation_prompts

    mcp = MagicMock()
    prompts = {}

    def capture_prompt(**kwargs):
        def decorator(func):
            prompts[func.__name__] = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    def get_client():
        return mock_hass_client

    mock_hass_client.get_states = AsyncMock(return_value=[])

    register_automation_prompts(mcp, get_client)

    result = await prompts["suggest_automation"](intent="Turn on lights at sunset")

    assert isinstance(result, list)
    assert len(result) > 0

    # Extract text content
    messages_text = ""
    for msg in result:
        if hasattr(msg, "content"):
            if hasattr(msg.content, "text"):
                messages_text += msg.content.text

    # Verify sun trigger is suggested
    assert "sun" in messages_text.lower()
    assert "sunset" in messages_text.lower()


@pytest.mark.asyncio
async def test_suggest_automation_state_trigger(mock_hass_client):
    """Test suggest_automation with state-based intent."""
    from src.homeassistant_mcp.prompts.automation import register_automation_prompts

    mcp = MagicMock()
    prompts = {}

    def capture_prompt(**kwargs):
        def decorator(func):
            prompts[func.__name__] = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    def get_client():
        return mock_hass_client

    mock_hass_client.get_states = AsyncMock(return_value=[])

    register_automation_prompts(mcp, get_client)

    result = await prompts["suggest_automation"](
        intent="When motion sensor detects movement, turn on light"
    )

    assert isinstance(result, list)
    assert len(result) > 0

    # Extract text content
    messages_text = ""
    for msg in result:
        if hasattr(msg, "content"):
            if hasattr(msg.content, "text"):
                messages_text += msg.content.text

    # Verify state trigger is suggested
    assert "state" in messages_text.lower()
    assert "trigger" in messages_text.lower()
