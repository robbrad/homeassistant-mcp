"""Unit tests for control prompts."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastmcp.prompts import PromptMessage
from homeassistant_mcp.exceptions import ConnectionError, EntityNotFoundError
from homeassistant_mcp.prompts.control import register_control_prompts


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


class TestControlEntityPrompt:
    """Tests for control_entity prompt."""

    @pytest.mark.asyncio
    async def test_control_entity_light_on(self, mock_mcp, mock_client, get_client):
        """Test control_entity with a light that is on."""
        # Register prompts
        register_control_prompts(mock_mcp, get_client)

        # Get the registered prompt
        control_entity = mock_mcp._prompts["control_entity"]

        # Mock entity state
        mock_client.get_state.return_value = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"brightness": 200, "color_temp": 300},
        }

        # Call the prompt
        result = await control_entity("light.living_room")

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], PromptMessage)
        assert result[0].role == "assistant"

        content = result[0].content.text
        assert "light.living_room" in content
        assert "on" in content
        assert "Brightness: 78%" in content  # 200/255 * 100
        assert "turn_on" in content
        assert "turn_off" in content
        assert "toggle" in content

    @pytest.mark.asyncio
    async def test_control_entity_with_action(self, mock_mcp, mock_client, get_client):
        """Test control_entity with specific action parameter."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "switch.fan",
            "state": "off",
            "attributes": {},
        }

        result = await control_entity("switch.fan", action="turn_on")

        assert isinstance(result, list)
        content = result[0].content.text
        assert "Requested Action" in content
        assert "turn_on" in content

    @pytest.mark.asyncio
    async def test_control_entity_sensitive_domain(self, mock_mcp, mock_client, get_client):
        """Test control_entity with sensitive domain (lock)."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "lock.front_door",
            "state": "locked",
            "attributes": {},
        }

        result = await control_entity("lock.front_door")

        assert isinstance(result, list)
        content = result[0].content.text
        # Should contain confirmation language
        assert "⚠️ IMPORTANT" in content
        assert "confirm" in content.lower()

    @pytest.mark.asyncio
    async def test_control_entity_not_found(self, mock_mcp, mock_client, get_client):
        """Test control_entity with non-existent entity."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.side_effect = EntityNotFoundError("Entity not found")

        result = await control_entity("light.nonexistent")

        assert isinstance(result, list)
        content = result[0].content.text
        assert "not found" in content.lower()
        assert "list_devices" in content

    @pytest.mark.asyncio
    async def test_control_entity_connection_error(self, mock_mcp, mock_client, get_client):
        """Test control_entity with connection error."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.side_effect = ConnectionError("Connection failed")

        result = await control_entity("light.living_room")

        assert isinstance(result, list)
        content = result[0].content.text
        assert "cannot connect" in content.lower()
        assert "Home Assistant" in content

    @pytest.mark.asyncio
    async def test_control_entity_climate(self, mock_mcp, mock_client, get_client):
        """Test control_entity with climate entity."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "climate.living_room",
            "state": "heat",
            "attributes": {
                "temperature": 72,
                "target_temp_high": 75,
                "target_temp_low": 68,
            },
        }

        result = await control_entity("climate.living_room")

        assert isinstance(result, list)
        content = result[0].content.text
        assert "climate.living_room" in content
        assert "Current temperature: 72°" in content
        assert "set_temperature" in content
        assert "set_hvac_mode" in content

    @pytest.mark.asyncio
    async def test_control_entity_cover(self, mock_mcp, mock_client, get_client):
        """Test control_entity with cover entity (sensitive domain)."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "cover.garage_door",
            "state": "closed",
            "attributes": {"current_position": 0},
        }

        result = await control_entity("cover.garage_door")

        assert isinstance(result, list)
        content = result[0].content.text
        assert "cover.garage_door" in content
        assert "Position: 0%" in content
        # Cover is sensitive domain
        assert "⚠️ IMPORTANT" in content
        assert "open_cover" in content
        assert "close_cover" in content


class TestControlAreaPrompt:
    """Tests for control_area prompt."""

    @pytest.mark.asyncio
    async def test_control_area_basic(self, mock_mcp, mock_client, get_client):
        """Test control_area with basic area containing multiple entities."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        # Mock entities in area
        mock_client._states_data = [
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

        result = await control_area("Living Room")

        assert isinstance(result, list)
        assert len(result) == 1
        content = result[0].content.text

        # Check basic structure
        assert "Living Room" in content
        assert "Entities in this area:" in content
        assert "Total entities:**" in content or "Total entities: 3" in content

        # Check entities are listed
        assert "Living Room Ceiling" in content
        assert "Living Room Lamp" in content
        assert "Living Room Fan" in content

        # Check bulk action warning (3 entities meets threshold)
        assert "BULK ACTION" in content
        assert "3 entities" in content

    @pytest.mark.asyncio
    async def test_control_area_with_goal(self, mock_mcp, mock_client, get_client):
        """Test control_area with goal parameter."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        mock_client._states_data = [
            {
                "entity_id": "light.bedroom_light",
                "state": "on",
                "attributes": {"friendly_name": "Bedroom Light"},
            }
        ]

        result = await control_area("Bedroom", goal="turn off all lights")

        content = result[0].content.text
        assert "Goal:**" in content or "Goal: turn off all lights" in content
        assert "turn off all lights" in content

    @pytest.mark.asyncio
    async def test_control_area_sensitive_domains(self, mock_mcp, mock_client, get_client):
        """Test control_area with sensitive domain entities."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        mock_client._states_data = [
            {
                "entity_id": "light.garage_light",
                "state": "off",
                "attributes": {"friendly_name": "Garage Light"},
            },
            {
                "entity_id": "lock.garage_door",
                "state": "locked",
                "attributes": {"friendly_name": "Garage Door Lock"},
            },
            {
                "entity_id": "cover.garage_door",
                "state": "closed",
                "attributes": {"friendly_name": "Garage Door"},
            },
        ]

        result = await control_area("Garage")

        content = result[0].content.text
        # Should warn about sensitive devices
        assert "SENSITIVE DEVICES DETECTED" in content
        assert "Garage Door Lock" in content
        assert "Garage Door" in content
        assert "extra caution" in content

    @pytest.mark.asyncio
    async def test_control_area_empty(self, mock_mcp, mock_client, get_client):
        """Test control_area with area that has no entities."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        mock_client._states_data = []

        result = await control_area("Empty Room")

        content = result[0].content.text
        assert "No entities found" in content
        assert "Empty Room" in content

    @pytest.mark.asyncio
    async def test_control_area_connection_error(self, mock_mcp, mock_client, get_client):
        """Test control_area with connection error."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        mock_client.get_states.side_effect = ConnectionError("Connection failed")

        result = await control_area("Living Room")

        content = result[0].content.text
        assert "cannot connect" in content.lower()

    @pytest.mark.asyncio
    async def test_control_area_below_bulk_threshold(self, mock_mcp, mock_client, get_client):
        """Test control_area with fewer entities than bulk threshold."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        # Only 2 entities (below threshold of 3)
        mock_client._states_data = [
            {
                "entity_id": "light.kitchen_light",
                "state": "on",
                "attributes": {"friendly_name": "Kitchen Light"},
            },
            {
                "entity_id": "switch.kitchen_fan",
                "state": "off",
                "attributes": {"friendly_name": "Kitchen Fan"},
            },
        ]

        result = await control_area("Kitchen")

        content = result[0].content.text
        # Should NOT have bulk action warning
        assert "BULK ACTION" not in content
        assert "Total entities:**" in content or "Total entities: 2" in content

    @pytest.mark.asyncio
    async def test_control_area_quiet_hours_detection(self, mock_mcp, mock_client, get_client, monkeypatch):
        """Test control_area detects quiet hours with noisy devices."""
        from datetime import datetime

        # Mock datetime to be during quiet hours (11 PM)
        class MockDateTime:
            @staticmethod
            def now():
                class MockNow:
                    hour = 23
                    minute = 30
                return MockNow()

        monkeypatch.setattr("homeassistant_mcp.prompts.control.datetime", MockDateTime)

        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        # Include noisy devices
        mock_client._states_data = [
            {
                "entity_id": "light.bedroom_light",
                "state": "off",
                "attributes": {"friendly_name": "Bedroom Light"},
            },
            {
                "entity_id": "media_player.bedroom_tv",
                "state": "off",
                "attributes": {"friendly_name": "Bedroom TV"},
            },
        ]

        result = await control_area("Bedroom")

        content = result[0].content.text
        # Should have quiet hours warning
        assert "🌙" in content or "quiet hours" in content.lower()
        assert "23:30" in content
        assert "Noisy devices" in content
        assert "Bedroom TV" in content


class TestControlEntityDomains:
    """Tests for control_entity with various entity domains."""

    @pytest.mark.asyncio
    async def test_control_entity_switch(self, mock_mcp, mock_client, get_client):
        """Test control_entity with switch domain."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "switch.porch_light",
            "state": "on",
            "attributes": {},
        }

        result = await control_entity("switch.porch_light")

        content = result[0].content.text
        assert "switch.porch_light" in content
        assert "turn_on" in content
        assert "turn_off" in content
        assert "toggle" in content

    @pytest.mark.asyncio
    async def test_control_entity_fan(self, mock_mcp, mock_client, get_client):
        """Test control_entity with fan domain."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "fan.ceiling_fan",
            "state": "on",
            "attributes": {"percentage": 50},
        }

        result = await control_entity("fan.ceiling_fan")

        content = result[0].content.text
        assert "fan.ceiling_fan" in content
        assert "set_percentage" in content
        assert "turn_on" in content
        assert "turn_off" in content

    @pytest.mark.asyncio
    async def test_control_entity_media_player(self, mock_mcp, mock_client, get_client):
        """Test control_entity with media_player domain."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "media_player.living_room_tv",
            "state": "playing",
            "attributes": {"volume_level": 0.5},
        }

        result = await control_entity("media_player.living_room_tv")

        content = result[0].content.text
        assert "media_player.living_room_tv" in content
        assert "media_play" in content
        assert "media_pause" in content
        assert "volume_set" in content

    @pytest.mark.asyncio
    async def test_control_entity_vacuum(self, mock_mcp, mock_client, get_client):
        """Test control_entity with vacuum domain."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "vacuum.robot",
            "state": "docked",
            "attributes": {"battery_level": 100},
        }

        result = await control_entity("vacuum.robot")

        content = result[0].content.text
        assert "vacuum.robot" in content
        assert "start" in content
        assert "pause" in content
        assert "return_to_base" in content

    @pytest.mark.asyncio
    async def test_control_entity_alarm_control_panel(self, mock_mcp, mock_client, get_client):
        """Test control_entity with alarm_control_panel (sensitive domain)."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "alarm_control_panel.home",
            "state": "armed_away",
            "attributes": {},
        }

        result = await control_entity("alarm_control_panel.home")

        content = result[0].content.text
        assert "alarm_control_panel.home" in content
        # Should have confirmation warning for sensitive domain
        assert "⚠️ IMPORTANT" in content
        assert "confirm" in content.lower()

    @pytest.mark.asyncio
    async def test_control_entity_camera(self, mock_mcp, mock_client, get_client):
        """Test control_entity with camera (sensitive domain)."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "camera.front_door",
            "state": "idle",
            "attributes": {},
        }

        result = await control_entity("camera.front_door")

        content = result[0].content.text
        assert "camera.front_door" in content
        # Camera is sensitive domain
        assert "⚠️ IMPORTANT" in content

    @pytest.mark.asyncio
    async def test_control_entity_unknown_domain(self, mock_mcp, mock_client, get_client):
        """Test control_entity with unknown/unsupported domain."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "sensor.temperature",
            "state": "72",
            "attributes": {"unit_of_measurement": "°F"},
        }

        result = await control_entity("sensor.temperature")

        content = result[0].content.text
        assert "sensor.temperature" in content
        # Should provide generic actions for unknown domain
        assert "turn_on" in content
        assert "turn_off" in content
        assert "toggle" in content


class TestControlAreaEdgeCases:
    """Tests for control_area edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_control_area_mixed_sensitive_and_normal(self, mock_mcp, mock_client, get_client):
        """Test control_area with mix of sensitive and normal entities."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        mock_client._states_data = [
            {
                "entity_id": "light.entry_light",
                "state": "on",
                "attributes": {"friendly_name": "Entry Light"},
            },
            {
                "entity_id": "lock.front_door",
                "state": "locked",
                "attributes": {"friendly_name": "Front Door Lock"},
            },
            {
                "entity_id": "camera.doorbell",
                "state": "idle",
                "attributes": {"friendly_name": "Doorbell Camera"},
            },
        ]

        result = await control_area("Entry")

        content = result[0].content.text
        # Should list all entities
        assert "Entry Light" in content
        assert "Front Door Lock" in content
        assert "Doorbell Camera" in content

        # Should warn about sensitive devices
        assert "SENSITIVE DEVICES DETECTED" in content
        assert "Front Door Lock" in content
        assert "Doorbell Camera" in content

        # Should have bulk action warning (3 entities)
        assert "BULK ACTION" in content

    @pytest.mark.asyncio
    async def test_control_area_exactly_at_bulk_threshold(self, mock_mcp, mock_client, get_client):
        """Test control_area with exactly 3 entities (at threshold)."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

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
                "entity_id": "light.light3",
                "state": "on",
                "attributes": {"friendly_name": "Light 3"},
            },
        ]

        result = await control_area("Test Area")

        content = result[0].content.text
        # Should have bulk action warning at threshold
        assert "BULK ACTION" in content
        assert "3 entities" in content

    @pytest.mark.asyncio
    async def test_control_area_many_entities(self, mock_mcp, mock_client, get_client):
        """Test control_area with many entities (well above threshold)."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        # Create 10 entities
        entities = []
        for i in range(10):
            entities.append(
                {
                    "entity_id": f"light.light_{i}",
                    "state": "on" if i % 2 == 0 else "off",
                    "attributes": {"friendly_name": f"Light {i}"},
                }
            )

        mock_client._states_data = entities

        result = await control_area("Large Room")

        content = result[0].content.text
        # Should have bulk action warning
        assert "BULK ACTION" in content
        assert "10 entities" in content
        # Should list all entities
        for i in range(10):
            assert f"Light {i}" in content

    @pytest.mark.asyncio
    async def test_control_area_no_friendly_names(self, mock_mcp, mock_client, get_client):
        """Test control_area with entities that have no friendly names."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        mock_client._states_data = [
            {
                "entity_id": "light.unnamed_light",
                "state": "on",
                "attributes": {},  # No friendly_name
            },
            {
                "entity_id": "switch.unnamed_switch",
                "state": "off",
                "attributes": {},  # No friendly_name
            },
        ]

        result = await control_area("Test Area")

        content = result[0].content.text
        # Should fall back to entity_id when no friendly name
        assert "light.unnamed_light" in content
        assert "switch.unnamed_switch" in content
