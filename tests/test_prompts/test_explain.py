"""Unit tests for explain prompts."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastmcp.prompts import PromptMessage
from homeassistant_mcp.exceptions import ConnectionError, EntityNotFoundError
from homeassistant_mcp.prompts.explain import register_explain_prompts


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


class TestExplainEntityPrompt:
    """Tests for explain_entity prompt."""

    @pytest.mark.asyncio
    async def test_explain_entity_light(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with a light entity."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "area_id": "living_room",
                "brightness": 200,
                "color_temp": 300,
            },
            "last_changed": "2024-01-15T10:30:00",
        }

        result = await explain_entity("light.living_room")

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], PromptMessage)
        assert result[0].role == "assistant"

        content = result[0].content.text
        # Check entity identification
        assert "Living Room Light" in content
        assert "light.living_room" in content
        assert "light entity" in content

        # Check location
        assert "living_room" in content

        # Check current state
        assert "Current State:**" in content or "Current State: on" in content
        assert "on" in content
        assert "Brightness: 78%" in content  # 200/255 * 100

        # Check capabilities
        assert "Capabilities:**" in content or "Capabilities:" in content
        assert "brightness control" in content

        # Check available services
        assert "Available Services:**" in content or "Available Services:" in content
        assert "light.turn_on" in content
        assert "light.turn_off" in content

    @pytest.mark.asyncio
    async def test_explain_entity_switch(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with a switch entity."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "switch.fan",
            "state": "off",
            "attributes": {
                "friendly_name": "Ceiling Fan",
            },
            "last_changed": "2024-01-15T09:00:00",
        }

        result = await explain_entity("switch.fan")

        content = result[0].content.text
        assert "Ceiling Fan" in content
        assert "switch.fan" in content
        assert "switch entity" in content
        assert "off" in content
        assert "switch.turn_on" in content
        assert "switch.turn_off" in content

    @pytest.mark.asyncio
    async def test_explain_entity_climate(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with a climate entity."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "climate.thermostat",
            "state": "heat",
            "attributes": {
                "friendly_name": "Living Room Thermostat",
                "area_id": "living_room",
                "current_temperature": 71.5,
                "temperature": 72.0,
                "hvac_mode": "heat",
                "fan_mode": "auto",
            },
            "last_changed": "2024-01-15T08:00:00",
        }

        result = await explain_entity("climate.thermostat")

        content = result[0].content.text
        assert "Living Room Thermostat" in content
        assert "climate entity" in content
        assert "Current temperature: 71.5°" in content
        assert "Target temperature: 72.0°" in content
        assert "HVAC mode: heat" in content
        assert "Fan mode: auto" in content
        assert "climate.set_temperature" in content
        assert "climate.set_hvac_mode" in content

    @pytest.mark.asyncio
    async def test_explain_entity_sensor(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with a sensor entity."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "sensor.temperature",
            "state": "25.5",
            "attributes": {
                "friendly_name": "Temperature Sensor",
                "unit_of_measurement": "°C",
                "device_class": "temperature",
            },
            "last_changed": "2024-01-15T10:25:00",
        }

        result = await explain_entity("sensor.temperature")

        content = result[0].content.text
        assert "Temperature Sensor" in content
        assert "sensor entity" in content
        assert "25.5" in content
        assert "Unit: °C" in content
        assert "Device Class:**" in content or "Device Class: temperature" in content
        assert "read-only" in content
        assert "cannot be controlled" in content

    @pytest.mark.asyncio
    async def test_explain_entity_cover(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with a cover entity."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "cover.garage_door",
            "state": "closed",
            "attributes": {
                "friendly_name": "Garage Door",
                "current_position": 0,
                "current_tilt_position": 45,
            },
            "last_changed": "2024-01-15T07:00:00",
        }

        result = await explain_entity("cover.garage_door")

        content = result[0].content.text
        assert "Garage Door" in content
        assert "cover entity" in content
        assert "closed" in content
        assert "Position: 0%" in content
        assert "Tilt: 45%" in content
        assert "cover.open_cover" in content
        assert "cover.close_cover" in content

    @pytest.mark.asyncio
    async def test_explain_entity_media_player(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with a media_player entity."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "media_player.tv",
            "state": "playing",
            "attributes": {
                "friendly_name": "Living Room TV",
                "volume_level": 0.5,
                "source": "HDMI 1",
                "media_title": "The Matrix",
            },
            "last_changed": "2024-01-15T10:00:00",
        }

        result = await explain_entity("media_player.tv")

        content = result[0].content.text
        assert "Living Room TV" in content
        assert "media_player entity" in content
        assert "playing" in content
        assert "Volume: 50%" in content
        assert "Source: HDMI 1" in content
        assert "Playing: The Matrix" in content
        assert "media_player.media_play" in content

    @pytest.mark.asyncio
    async def test_explain_entity_fan(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with a fan entity."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "fan.ceiling_fan",
            "state": "on",
            "attributes": {
                "friendly_name": "Bedroom Fan",
                "percentage": 75,
                "oscillating": True,
            },
            "last_changed": "2024-01-15T09:30:00",
        }

        result = await explain_entity("fan.ceiling_fan")

        content = result[0].content.text
        assert "Bedroom Fan" in content
        assert "fan entity" in content
        assert "on" in content
        assert "Speed: 75%" in content
        assert "Oscillating: True" in content
        assert "fan.set_percentage" in content

    @pytest.mark.asyncio
    async def test_explain_entity_with_area(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with entity that has area information."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "light.bedroom_light",
            "state": "off",
            "attributes": {
                "friendly_name": "Bedroom Light",
                "area_id": "bedroom",
            },
            "last_changed": "2024-01-15T06:00:00",
        }

        result = await explain_entity("light.bedroom_light")

        content = result[0].content.text
        assert "Bedroom Light" in content
        assert "located in the bedroom" in content

    @pytest.mark.asyncio
    async def test_explain_entity_without_area(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with entity that has no area."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "switch.unassigned",
            "state": "off",
            "attributes": {
                "friendly_name": "Unassigned Switch",
            },
            "last_changed": "2024-01-15T10:00:00",
        }

        result = await explain_entity("switch.unassigned")

        content = result[0].content.text
        assert "Unassigned Switch" in content
        assert "switch entity" in content
        # Should not mention location
        assert "located in" not in content

    @pytest.mark.asyncio
    async def test_explain_entity_not_found(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with non-existent entity."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.side_effect = EntityNotFoundError("Entity not found")

        result = await explain_entity("light.nonexistent")

        assert isinstance(result, list)
        content = result[0].content.text
        assert "not found" in content.lower()
        assert "light.nonexistent" in content
        assert "list_devices" in content

    @pytest.mark.asyncio
    async def test_explain_entity_connection_error(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with connection error."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.side_effect = ConnectionError("Connection failed")

        result = await explain_entity("light.living_room")

        assert isinstance(result, list)
        content = result[0].content.text
        assert "cannot connect" in content.lower()
        assert "Home Assistant" in content

    @pytest.mark.asyncio
    async def test_explain_entity_binary_sensor(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with binary_sensor entity."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "binary_sensor.motion",
            "state": "on",
            "attributes": {
                "friendly_name": "Motion Sensor",
                "device_class": "motion",
            },
            "last_changed": "2024-01-15T10:20:00",
        }

        result = await explain_entity("binary_sensor.motion")

        content = result[0].content.text
        assert "Motion Sensor" in content
        assert "binary_sensor entity" in content
        assert "read-only" in content
        assert "cannot be controlled" in content

    @pytest.mark.asyncio
    async def test_explain_entity_lock(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with lock entity."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "lock.front_door",
            "state": "locked",
            "attributes": {
                "friendly_name": "Front Door Lock",
            },
            "last_changed": "2024-01-15T08:00:00",
        }

        result = await explain_entity("lock.front_door")

        content = result[0].content.text
        assert "Front Door Lock" in content
        assert "lock entity" in content
        assert "locked" in content
        assert "lock.lock" in content
        assert "lock.unlock" in content

    @pytest.mark.asyncio
    async def test_explain_entity_vacuum(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with vacuum entity."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "vacuum.robot",
            "state": "docked",
            "attributes": {
                "friendly_name": "Robot Vacuum",
                "battery_level": 100,
            },
            "last_changed": "2024-01-15T09:00:00",
        }

        result = await explain_entity("vacuum.robot")

        content = result[0].content.text
        assert "Robot Vacuum" in content
        assert "vacuum entity" in content
        assert "docked" in content
        assert "vacuum.start" in content
        assert "vacuum.return_to_base" in content

    @pytest.mark.asyncio
    async def test_explain_entity_usage_tips_for_controllable(self, mock_mcp, mock_client, get_client):
        """Test explain_entity includes usage tips for controllable entities."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "light.test",
            "state": "on",
            "attributes": {"friendly_name": "Test Light"},
            "last_changed": "2024-01-15T10:00:00",
        }

        result = await explain_entity("light.test")

        content = result[0].content.text
        assert "Usage Tips:**" in content or "Usage Tips:" in content
        assert "control_entity" in content
        assert "verify current state" in content

    @pytest.mark.asyncio
    async def test_explain_entity_usage_tips_for_sensor(self, mock_mcp, mock_client, get_client):
        """Test explain_entity includes appropriate tips for sensors."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "sensor.temp",
            "state": "22",
            "attributes": {
                "friendly_name": "Temperature",
                "unit_of_measurement": "°C",
            },
            "last_changed": "2024-01-15T10:00:00",
        }

        result = await explain_entity("sensor.temp")

        content = result[0].content.text
        assert "Usage Tips:**" in content or "Usage Tips:" in content
        assert "read-only" in content
        assert "monitor conditions" in content or "trigger automations" in content

    @pytest.mark.asyncio
    async def test_explain_entity_no_friendly_name(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with entity that has no friendly name."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "light.unnamed",
            "state": "off",
            "attributes": {},  # No friendly_name
            "last_changed": "2024-01-15T10:00:00",
        }

        result = await explain_entity("light.unnamed")

        content = result[0].content.text
        # Should use entity_id when no friendly name
        assert "light.unnamed" in content
        assert "light entity" in content

    @pytest.mark.asyncio
    async def test_explain_entity_minimal_attributes(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with entity that has minimal attributes."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "switch.minimal",
            "state": "on",
            "attributes": {},  # No attributes at all
        }

        result = await explain_entity("switch.minimal")

        content = result[0].content.text
        assert "switch.minimal" in content
        assert "switch entity" in content
        assert "on" in content
        # Should still provide capabilities and services
        assert "Capabilities:**" in content or "Capabilities:" in content
        assert "Available Services:**" in content or "Available Services:" in content
