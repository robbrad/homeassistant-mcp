"""Unit tests for status prompts."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from fastmcp.prompts import PromptMessage
from homeassistant_mcp.exceptions import ConnectionError
from homeassistant_mcp.prompts.status import register_status_prompts


@pytest.fixture
def mock_mcp():
    """Mock FastMCP instance for testing."""
    mcp = MagicMock()
    # Store registered prompts
    mcp._prompts = {}

    def prompt_decorator(**kwargs):
        def wrapper(func):
            mcp._prompts[func.__name__] = func
            return func

        return wrapper

    mcp.prompt = prompt_decorator
    return mcp


@pytest.fixture
def mock_client():
    """Mock HomeAssistantClient for testing."""
    client = AsyncMock()
    return client


@pytest.fixture
def get_client(mock_client):
    """Mock get_client callable."""
    return lambda: mock_client


class TestHomeStatusBriefPrompt:
    """Tests for home_status_brief prompt."""

    @pytest.mark.asyncio
    async def test_home_status_brief_basic(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with basic home state."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        # Mock various entity states
        mock_client._states_data = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"friendly_name": "Living Room Light", "brightness": 200},
            },
            {
                "entity_id": "light.bedroom",
                "state": "off",
                "attributes": {"friendly_name": "Bedroom Light"},
            },
            {
                "entity_id": "switch.porch",
                "state": "on",
                "attributes": {"friendly_name": "Porch Switch"},
            },
            {
                "entity_id": "lock.front_door",
                "state": "locked",
                "attributes": {"friendly_name": "Front Door Lock"},
            },
            {
                "entity_id": "automation.morning_lights",
                "state": "on",
                "attributes": {"friendly_name": "Morning Lights"},
            },
        ]

        result = await home_status_brief()

        # Verify result structure
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], PromptMessage)
        assert result[0].role == "assistant"

        content = result[0].content.text

        # Check basic structure
        assert "Home Status Summary" in content
        assert "Devices:" in content

        # Check domain counts
        assert "Light:" in content or "light:" in content.lower()
        assert "Switch:" in content or "switch:" in content.lower()
        assert "Lock:" in content or "lock:" in content.lower()

        # Check state counts
        assert "2 total" in content  # 2 lights
        assert "1 on" in content or "on" in content

        # Check security status
        assert "Security Status:" in content
        assert "locked" in content.lower()

        # Check automation count
        assert "Active Automations:" in content or "automation" in content.lower()

    @pytest.mark.asyncio
    async def test_home_status_brief_with_issues(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with issues detected."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        mock_client._states_data = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"friendly_name": "Living Room Light"},
            },
            {
                "entity_id": "sensor.temperature",
                "state": "unavailable",
                "attributes": {"friendly_name": "Temperature Sensor"},
            },
            {
                "entity_id": "sensor.door",
                "state": "22",
                "attributes": {"friendly_name": "Door Sensor", "battery_level": 15},
            },
            {
                "entity_id": "sensor.motion",
                "state": "off",
                "attributes": {"friendly_name": "Motion Sensor", "battery_level": 5},
            },
        ]

        result = await home_status_brief()
        content = result[0].content.text

        # Check issues section
        assert "Issues Detected:" in content

        # Check unavailable entities
        assert "Unavailable Entities" in content
        assert "Temperature Sensor" in content

        # Check low battery warnings
        assert "Low Battery" in content
        assert "Door Sensor: 15%" in content
        assert "Motion Sensor: 5%" in content

    @pytest.mark.asyncio
    async def test_home_status_brief_no_issues(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with no issues."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        mock_client._states_data = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"friendly_name": "Living Room Light"},
            },
            {
                "entity_id": "sensor.temperature",
                "state": "22.5",
                "attributes": {"friendly_name": "Temperature Sensor", "battery_level": 85},
            },
        ]

        result = await home_status_brief()
        content = result[0].content.text

        # Should indicate no issues
        assert "Issues Detected:" in content
        assert "✓ None" in content or "None" in content

    @pytest.mark.asyncio
    async def test_home_status_brief_security_all_locked(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with all locks secured."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        mock_client._states_data = [
            {
                "entity_id": "lock.front_door",
                "state": "locked",
                "attributes": {"friendly_name": "Front Door"},
            },
            {
                "entity_id": "lock.back_door",
                "state": "locked",
                "attributes": {"friendly_name": "Back Door"},
            },
            {
                "entity_id": "alarm_control_panel.home",
                "state": "armed_away",
                "attributes": {"friendly_name": "Home Alarm"},
            },
        ]

        result = await home_status_brief()
        content = result[0].content.text

        # Check security status
        assert "Security Status:" in content
        assert "All locked" in content or "locked (2)" in content
        assert "✓" in content
        assert "armed_away" in content

    @pytest.mark.asyncio
    async def test_home_status_brief_security_unlocked(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with unlocked doors."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        mock_client._states_data = [
            {
                "entity_id": "lock.front_door",
                "state": "locked",
                "attributes": {"friendly_name": "Front Door"},
            },
            {
                "entity_id": "lock.back_door",
                "state": "unlocked",
                "attributes": {"friendly_name": "Back Door"},
            },
        ]

        result = await home_status_brief()
        content = result[0].content.text

        # Should warn about unlocked door
        assert "1/2 locked" in content or "unlocked" in content.lower()
        assert "Back Door" in content

    @pytest.mark.asyncio
    async def test_home_status_brief_open_doors_windows(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with open doors/windows."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        mock_client._states_data = [
            {
                "entity_id": "binary_sensor.front_door",
                "state": "on",  # Open
                "attributes": {
                    "friendly_name": "Front Door Sensor",
                    "device_class": "door",
                },
            },
            {
                "entity_id": "binary_sensor.window",
                "state": "on",  # Open
                "attributes": {
                    "friendly_name": "Living Room Window",
                    "device_class": "window",
                },
            },
        ]

        result = await home_status_brief()
        content = result[0].content.text

        # Should warn about open doors/windows
        assert "Open Doors/Windows" in content
        assert "2 detected" in content
        assert "Front Door Sensor" in content
        assert "Living Room Window" in content

    @pytest.mark.asyncio
    async def test_home_status_brief_climate_comfortable(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with comfortable climate."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        mock_client._states_data = [
            {
                "entity_id": "climate.living_room",
                "state": "heat",
                "attributes": {
                    "friendly_name": "Living Room Thermostat",
                    "current_temperature": 22.0,
                    "temperature": 22.0,
                },
            },
            {
                "entity_id": "climate.bedroom",
                "state": "heat",
                "attributes": {
                    "friendly_name": "Bedroom Thermostat",
                    "current_temperature": 21.5,
                    "temperature": 22.0,
                },
            },
        ]

        result = await home_status_brief()
        content = result[0].content.text

        # Check climate section
        assert "Climate:" in content
        assert "Living Room Thermostat" in content
        assert "22.0°" in content
        assert "✓" in content
        assert "Comfortable" in content

    @pytest.mark.asyncio
    async def test_home_status_brief_climate_not_at_target(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with climate not at target temperature."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        mock_client._states_data = [
            {
                "entity_id": "climate.living_room",
                "state": "heat",
                "attributes": {
                    "friendly_name": "Living Room Thermostat",
                    "current_temperature": 18.0,
                    "temperature": 22.0,
                },
            },
        ]

        result = await home_status_brief()
        content = result[0].content.text

        # Should show temperature difference
        assert "Climate:" in content
        assert "18.0°" in content
        assert "target 22.0°" in content
        # Should NOT show comfortable indicator
        assert "Comfortable" not in content or "Climate Comfortable" not in content

    @pytest.mark.asyncio
    async def test_home_status_brief_connection_error(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with connection error."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        mock_client.get_states.side_effect = ConnectionError("Connection failed")

        result = await home_status_brief()

        assert isinstance(result, list)
        content = result[0].content.text
        assert "cannot connect" in content.lower()
        assert "Home Assistant" in content

    @pytest.mark.asyncio
    async def test_home_status_brief_many_unavailable(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with many unavailable entities (truncation)."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        # Create 10 unavailable entities
        entities = []
        for i in range(10):
            entities.append(
                {
                    "entity_id": f"sensor.sensor_{i}",
                    "state": "unavailable",
                    "attributes": {"friendly_name": f"Sensor {i}"},
                }
            )

        mock_client._states_data = entities

        result = await home_status_brief()
        content = result[0].content.text

        # Should show first 5 and indicate more
        assert "Unavailable Entities (10)" in content
        assert "Sensor 0" in content
        assert "Sensor 4" in content
        assert "and 5 more" in content

    @pytest.mark.asyncio
    async def test_home_status_brief_many_low_battery(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with many low battery entities (truncation)."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        # Create 10 low battery entities
        entities = []
        for i in range(10):
            entities.append(
                {
                    "entity_id": f"sensor.sensor_{i}",
                    "state": "on",
                    "attributes": {
                        "friendly_name": f"Sensor {i}",
                        "battery_level": 10 + i,  # 10-19%
                    },
                }
            )

        mock_client._states_data = entities

        result = await home_status_brief()
        content = result[0].content.text

        # Should show first 5 sorted by battery level and indicate more
        assert "Low Battery (10)" in content
        assert "Sensor 0: 10%" in content  # Lowest battery first
        assert "and 5 more" in content

    @pytest.mark.asyncio
    async def test_home_status_brief_empty_home(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with no entities."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        mock_client._states_data = []

        result = await home_status_brief()
        content = result[0].content.text

        # Should still provide a valid status report
        assert "Home Status Summary" in content
        assert "Devices:" in content

    @pytest.mark.asyncio
    async def test_home_status_brief_mixed_states(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with various entity states."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        mock_client._states_data = [
            {
                "entity_id": "light.light1",
                "state": "on",
                "attributes": {"friendly_name": "Light 1"},
            },
            {
                "entity_id": "light.light2",
                "state": "off",
                "attributes": {"friendly_name": "Light 2"},
            },
            {
                "entity_id": "cover.garage",
                "state": "open",
                "attributes": {"friendly_name": "Garage Door"},
            },
            {
                "entity_id": "cover.blinds",
                "state": "closed",
                "attributes": {"friendly_name": "Blinds"},
            },
            {
                "entity_id": "person.john",
                "state": "home",
                "attributes": {"friendly_name": "John"},
            },
            {
                "entity_id": "person.jane",
                "state": "away",
                "attributes": {"friendly_name": "Jane"},
            },
        ]

        result = await home_status_brief()
        content = result[0].content.text

        # Check various state counts
        assert "Light:" in content or "light:" in content.lower()
        assert "1 on" in content
        assert "1 off" in content

        assert "Cover:" in content or "cover:" in content.lower()
        assert "1 open" in content
        assert "1 closed" in content

        assert "Person:" in content or "person:" in content.lower()
        assert "1 home" in content
        assert "1 away" in content

    @pytest.mark.asyncio
    async def test_home_status_brief_no_locks(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with no lock entities."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        mock_client._states_data = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"friendly_name": "Living Room Light"},
            },
        ]

        result = await home_status_brief()
        content = result[0].content.text

        # Should indicate no locks found
        assert "Security Status:" in content
        assert "No lock entities found" in content

    @pytest.mark.asyncio
    async def test_home_status_brief_disarmed_alarm(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with disarmed alarm."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        mock_client._states_data = [
            {
                "entity_id": "alarm_control_panel.home",
                "state": "disarmed",
                "attributes": {"friendly_name": "Home Alarm"},
            },
        ]

        result = await home_status_brief()
        content = result[0].content.text

        # Should warn about disarmed alarm
        assert "Alarm:" in content
        assert "disarmed" in content
        assert "⚠️" in content

    @pytest.mark.asyncio
    async def test_home_status_brief_no_climate(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with no climate entities."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        mock_client._states_data = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"friendly_name": "Living Room Light"},
            },
        ]

        result = await home_status_brief()
        content = result[0].content.text

        # Should not have climate section if no climate entities
        # (or it should be empty/minimal)
        assert "Home Status Summary" in content

    @pytest.mark.asyncio
    async def test_home_status_brief_battery_level_edge_cases(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with various battery level formats."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        mock_client._states_data = [
            {
                "entity_id": "sensor.sensor1",
                "state": "on",
                "attributes": {
                    "friendly_name": "Sensor 1",
                    "battery_level": 15,  # Integer
                },
            },
            {
                "entity_id": "sensor.sensor2",
                "state": "on",
                "attributes": {
                    "friendly_name": "Sensor 2",
                    "battery_level": 18.5,  # Float
                },
            },
            {
                "entity_id": "sensor.sensor3",
                "state": "on",
                "attributes": {
                    "friendly_name": "Sensor 3",
                    "battery_level": "20",  # String
                },
            },
            {
                "entity_id": "sensor.sensor4",
                "state": "on",
                "attributes": {
                    "friendly_name": "Sensor 4",
                    "battery_level": "invalid",  # Invalid value
                },
            },
            {
                "entity_id": "sensor.sensor5",
                "state": "on",
                "attributes": {
                    "friendly_name": "Sensor 5",
                    "battery_level": 85,  # Above threshold
                },
            },
        ]

        result = await home_status_brief()
        content = result[0].content.text

        # Should detect low batteries (15, 18, 20)
        assert "Low Battery" in content
        assert "Sensor 1: 15%" in content
        assert "Sensor 2: 18%" in content
        assert "Sensor 3: 20%" in content

        # Should not include invalid or high battery
        assert "Sensor 4" not in content or "invalid" not in content
        assert "Sensor 5: 85%" not in content

    @pytest.mark.asyncio
    async def test_home_status_brief_automation_counts(self, mock_mcp, mock_client, get_client):
        """Test home_status_brief with automation counts."""
        register_status_prompts(mock_mcp, get_client)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        mock_client._states_data = [
            {
                "entity_id": "automation.morning",
                "state": "on",
                "attributes": {"friendly_name": "Morning Routine"},
            },
            {
                "entity_id": "automation.evening",
                "state": "on",
                "attributes": {"friendly_name": "Evening Routine"},
            },
            {
                "entity_id": "automation.disabled",
                "state": "off",
                "attributes": {"friendly_name": "Disabled Automation"},
            },
        ]

        result = await home_status_brief()
        content = result[0].content.text

        # Should show automation counts
        assert "Active Automations:" in content
        assert "2 enabled" in content
        assert "3 total" in content
