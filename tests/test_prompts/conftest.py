"""Shared pytest fixtures for prompt tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from homeassistant_mcp.exceptions import ConnectionError, EntityNotFoundError


@pytest.fixture
def mock_mcp():
    """Mock FastMCP instance for prompt registration testing."""
    mcp = MagicMock()
    # Store registered prompts
    mcp._prompts = {}
    # Store prompt metadata
    mcp._prompt_metadata = {}

    def prompt_decorator(**kwargs):
        """Mock prompt decorator that captures registered functions and accepts kwargs like tags."""
        tags = kwargs.get("tags", set())

        def wrapper(func):
            mcp._prompts[func.__name__] = func
            mcp._prompt_metadata[func.__name__] = {
                "name": func.__name__,
                "description": func.__doc__ or "",
                "tags": tags,
            }
            return func

        return wrapper

    mcp.prompt = prompt_decorator
    return mcp


@pytest.fixture
def mock_client():
    """Mock HomeAssistantClient for testing.

    The get_states mock respects the _states_data attribute so tests can
    populate data by setting: mock_client._states_data = [entities...]
    """
    client = AsyncMock()

    # Set up default return values
    client.get_state.return_value = {
        "entity_id": "test.entity",
        "state": "on",
        "attributes": {},
    }
    client._states_data = []
    client.call_service.return_value = {}

    async def _filtered_get_states(domain=None, area=None, limit=None):
        states = list(client._states_data)
        if domain:
            states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
        return states

    client.get_states = AsyncMock(side_effect=_filtered_get_states)

    return client


@pytest.fixture
def get_client(mock_client):
    """Mock get_client callable that returns the mock client."""
    return lambda: mock_client


@pytest.fixture
def sample_light_state():
    """Sample light entity state for testing."""
    return {
        "entity_id": "light.living_room",
        "state": "on",
        "attributes": {
            "friendly_name": "Living Room Light",
            "brightness": 200,
            "color_temp": 300,
        },
    }


@pytest.fixture
def sample_lock_state():
    """Sample lock entity state (sensitive domain) for testing."""
    return {
        "entity_id": "lock.front_door",
        "state": "locked",
        "attributes": {
            "friendly_name": "Front Door Lock",
        },
    }


@pytest.fixture
def sample_climate_state():
    """Sample climate entity state for testing."""
    return {
        "entity_id": "climate.living_room",
        "state": "heat",
        "attributes": {
            "friendly_name": "Living Room Thermostat",
            "temperature": 72,
            "current_temperature": 70,
            "hvac_mode": "heat",
        },
    }


@pytest.fixture
def sample_automation_state():
    """Sample automation entity state for testing."""
    return {
        "entity_id": "automation.morning_routine",
        "state": "on",
        "attributes": {
            "friendly_name": "Morning Routine",
            "last_triggered": "2024-01-01T08:00:00",
        },
    }


@pytest.fixture
def sample_area_entities():
    """Sample entities in an area for testing."""
    return [
        {
            "entity_id": "light.living_room_ceiling",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Ceiling"},
        },
        {
            "entity_id": "light.living_room_lamp",
            "state": "off",
            "attributes": {"friendly_name": "Living Room Lamp"},
        },
        {
            "entity_id": "switch.living_room_fan",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Fan"},
        },
    ]


@pytest.fixture
def connection_error_client():
    """Mock client that raises ConnectionError."""
    client = AsyncMock()
    client.get_state.side_effect = ConnectionError("Connection failed")
    client.get_states.side_effect = ConnectionError("Connection failed")
    return client


@pytest.fixture
def entity_not_found_client():
    """Mock client that raises EntityNotFoundError."""
    client = AsyncMock()
    client.get_state.side_effect = EntityNotFoundError("Entity not found")
    return client
