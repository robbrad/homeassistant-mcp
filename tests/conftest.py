"""Shared pytest fixtures for Home Assistant MCP Server tests."""

# Import reset_settings from the config.py module
# We need to be explicit because there's also a config/ package
import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from src.homeassistant_mcp.hass.client import HomeAssistantClient

config_file = Path(__file__).parent.parent / "src" / "homeassistant_mcp" / "config.py"
spec = importlib.util.spec_from_file_location("config_module", config_file)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
reset_settings = config_module.reset_settings


@pytest.fixture(autouse=True)
def reset_settings_after_test():
    """Automatically reset settings singleton after each test."""
    yield
    reset_settings()


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up standard mock environment variables for testing."""
    monkeypatch.setenv("HASS_HOST", "http://homeassistant.local:8123")
    monkeypatch.setenv("HASS_TOKEN", "test_token_1234567890_long_enough")
    monkeypatch.setenv("SERVER_NAME", "Home Assistant MCP")
    monkeypatch.setenv("SERVER_VERSION", "2.0.0")
    monkeypatch.setenv("CACHE_TTL_STATES", "30")
    monkeypatch.setenv("CACHE_TTL_ENTITY", "10")
    monkeypatch.setenv("LOG_LEVEL", "INFO")


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx AsyncClient with common methods."""
    client = AsyncMock(spec=httpx.AsyncClient)

    # Set up default successful responses
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_response.text = ""

    client.get.return_value = mock_response
    client.post.return_value = mock_response
    client.aclose = AsyncMock()

    return client


@pytest.fixture
def mock_hass_client():
    """Create a mock Home Assistant client with common methods."""
    client = AsyncMock(spec=HomeAssistantClient)

    # Set up default return values
    client.get_states.return_value = []
    client.get_state.return_value = {
        "entity_id": "test.entity",
        "state": "on",
        "attributes": {},
    }
    client.call_service.return_value = {}
    client.close = AsyncMock()

    return client


@pytest.fixture
def sample_entity_states():
    """Sample entity states covering multiple domains for testing."""
    return [
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "brightness": 255,
                "color_temp": 300,
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "light.bedroom",
            "state": "off",
            "attributes": {
                "friendly_name": "Bedroom Light",
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "climate.living_room",
            "state": "heat",
            "attributes": {
                "friendly_name": "Living Room Thermostat",
                "temperature": 22,
                "current_temperature": 20,
                "hvac_mode": "heat",
                "fan_mode": "auto",
            },
            "last_changed": "2024-01-01T10:00:00",
            "last_updated": "2024-01-01T10:00:00",
        },
        {
            "entity_id": "switch.kitchen",
            "state": "on",
            "attributes": {
                "friendly_name": "Kitchen Switch",
            },
            "last_changed": "2024-01-01T09:00:00",
            "last_updated": "2024-01-01T09:00:00",
        },
        {
            "entity_id": "automation.morning_routine",
            "state": "on",
            "attributes": {
                "friendly_name": "Morning Routine",
                "last_triggered": "2024-01-01T08:00:00",
            },
            "last_changed": "2024-01-01T08:00:00",
            "last_updated": "2024-01-01T08:00:00",
        },
        {
            "entity_id": "scene.movie_time",
            "state": "scening",
            "attributes": {
                "friendly_name": "Movie Time",
            },
            "last_changed": "2024-01-01T07:00:00",
            "last_updated": "2024-01-01T07:00:00",
        },
    ]


@pytest.fixture
def sample_light_states():
    """Sample light entity states for testing."""
    return [
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "brightness": 255,
                "color_temp": 300,
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "light.bedroom",
            "state": "off",
            "attributes": {
                "friendly_name": "Bedroom Light",
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "light.kitchen",
            "state": "on",
            "attributes": {
                "friendly_name": "Kitchen Light",
                "brightness": 128,
                "rgb_color": [255, 0, 0],
            },
            "last_changed": "2024-01-01T10:00:00",
            "last_updated": "2024-01-01T10:00:00",
        },
    ]


@pytest.fixture
def sample_climate_states():
    """Sample climate entity states for testing."""
    return [
        {
            "entity_id": "climate.living_room",
            "state": "heat",
            "attributes": {
                "friendly_name": "Living Room Thermostat",
                "temperature": 22,
                "current_temperature": 20,
                "hvac_mode": "heat",
                "fan_mode": "auto",
                "hvac_modes": ["off", "heat", "cool", "auto"],
                "fan_modes": ["auto", "low", "medium", "high"],
            },
            "last_changed": "2024-01-01T10:00:00",
            "last_updated": "2024-01-01T10:00:00",
        },
        {
            "entity_id": "climate.bedroom",
            "state": "cool",
            "attributes": {
                "friendly_name": "Bedroom Thermostat",
                "temperature": 20,
                "current_temperature": 22,
                "hvac_mode": "cool",
                "fan_mode": "low",
                "hvac_modes": ["off", "heat", "cool", "auto"],
                "fan_modes": ["auto", "low", "medium", "high"],
            },
            "last_changed": "2024-01-01T09:00:00",
            "last_updated": "2024-01-01T09:00:00",
        },
    ]


@pytest.fixture
def sample_automation_states():
    """Sample automation entity states for testing."""
    return [
        {
            "entity_id": "automation.morning_routine",
            "state": "on",
            "attributes": {
                "friendly_name": "Morning Routine",
                "last_triggered": "2024-01-01T08:00:00",
            },
            "last_changed": "2024-01-01T08:00:00",
            "last_updated": "2024-01-01T08:00:00",
        },
        {
            "entity_id": "automation.evening_routine",
            "state": "off",
            "attributes": {
                "friendly_name": "Evening Routine",
                "last_triggered": "2024-01-01T20:00:00",
            },
            "last_changed": "2024-01-01T20:00:00",
            "last_updated": "2024-01-01T20:00:00",
        },
    ]


@pytest.fixture
def sample_scene_states():
    """Sample scene entity states for testing."""
    return [
        {
            "entity_id": "scene.movie_time",
            "state": "scening",
            "attributes": {
                "friendly_name": "Movie Time",
            },
            "last_changed": "2024-01-01T07:00:00",
            "last_updated": "2024-01-01T07:00:00",
        },
        {
            "entity_id": "scene.bedtime",
            "state": "scening",
            "attributes": {
                "friendly_name": "Bedtime",
            },
            "last_changed": "2024-01-01T22:00:00",
            "last_updated": "2024-01-01T22:00:00",
        },
    ]


def get_mcp_tools_dict(mcp_instance):
    """Get a dict of {name: tool} from a FastMCP instance, compatible with v2 and v3.

    Bypasses search transforms to return the full tool catalog.
    """
    if hasattr(mcp_instance, "_tool_manager"):
        return dict(mcp_instance._tool_manager._tools)
    # In FastMCP 3.x, use get_tool to access individual tools
    # list_tools may be filtered by search transforms, so we need the provider
    import asyncio
    if hasattr(mcp_instance, "local_provider"):
        tools = asyncio.get_event_loop().run_until_complete(
            mcp_instance.local_provider.list_tools()
        )
    else:
        tools = asyncio.get_event_loop().run_until_complete(mcp_instance.list_tools())
    return {t.name: t for t in tools}


def get_mcp_prompts_dict(mcp_instance):
    """Get a dict of {name: prompt} from a FastMCP instance, compatible with v2 and v3."""
    if hasattr(mcp_instance, "_prompt_manager"):
        return dict(mcp_instance._prompt_manager._prompts)
    import asyncio
    if hasattr(mcp_instance, "local_provider"):
        prompts = asyncio.get_event_loop().run_until_complete(
            mcp_instance.local_provider.list_prompts()
        )
    else:
        prompts = asyncio.get_event_loop().run_until_complete(mcp_instance.list_prompts())
    return {p.name: p for p in prompts}


def get_mcp_resources_dict(mcp_instance):
    """Get a dict of {uri: resource} from a FastMCP instance, compatible with v2 and v3."""
    if hasattr(mcp_instance, "_resource_manager"):
        return dict(mcp_instance._resource_manager._resources)
    import asyncio
    if hasattr(mcp_instance, "local_provider"):
        resources = asyncio.get_event_loop().run_until_complete(
            mcp_instance.local_provider.list_resources()
        )
    else:
        resources = asyncio.get_event_loop().run_until_complete(mcp_instance.list_resources())
    return {str(r.uri): r for r in resources}


async def get_mcp_tools_dict_async(mcp_instance):
    """Async version of get_mcp_tools_dict."""
    if hasattr(mcp_instance, "_tool_manager"):
        return dict(mcp_instance._tool_manager._tools)
    if hasattr(mcp_instance, "local_provider"):
        tools = await mcp_instance.local_provider.list_tools()
    else:
        tools = await mcp_instance.list_tools()
    return {t.name: t for t in tools}


async def get_mcp_prompts_dict_async(mcp_instance):
    """Async version of get_mcp_prompts_dict."""
    if hasattr(mcp_instance, "_prompt_manager"):
        return dict(mcp_instance._prompt_manager._prompts)
    if hasattr(mcp_instance, "local_provider"):
        prompts = await mcp_instance.local_provider.list_prompts()
    else:
        prompts = await mcp_instance.list_prompts()
    return {p.name: p for p in prompts}


@pytest.fixture
def mock_fastmcp():
    """Create a mock FastMCP instance for tool registration testing."""
    from unittest.mock import MagicMock

    mock_mcp = MagicMock()
    registered_tools = {}

    def mock_tool(**kwargs):
        """Mock tool decorator that captures registered functions."""

        def decorator(func):
            registered_tools[func.__name__] = func
            return func

        return decorator

    mock_mcp.tool = mock_tool
    mock_mcp._registered_tools = registered_tools

    return mock_mcp


@pytest.fixture
def mock_mcp_with_prompts():
    """Create a mock FastMCP instance for prompt registration testing."""
    from unittest.mock import MagicMock

    mock_mcp = MagicMock()
    registered_prompts = {}
    prompt_metadata = {}

    def mock_prompt(**kwargs):
        """Mock prompt decorator that accepts tags and other kwargs."""
        tags = kwargs.get("tags", set())
        
        def decorator(func):
            registered_prompts[func.__name__] = func
            prompt_metadata[func.__name__] = {
                "name": func.__name__,
                "description": func.__doc__ or "",
                "tags": tags,
            }
            return func

        return decorator

    mock_mcp.prompt = mock_prompt
    mock_mcp._registered_prompts = registered_prompts
    mock_mcp._prompt_metadata = prompt_metadata

    return mock_mcp
