"""Unit tests for the lights control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.devices.lights import (
    _get_light,
    _list_lights,
    _turn_off_light,
    _turn_on_light,
)


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)
    return client


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
        {
            "entity_id": "switch.garage",
            "state": "on",
            "attributes": {
                "friendly_name": "Garage Switch",
            },
        },
    ]


class TestListLights:
    """Tests for listing lights."""

    @pytest.mark.asyncio
    async def test_list_lights_success(self, mock_client, sample_light_states):
        """Test successfully listing all lights."""
        mock_client.get_states.return_value = sample_light_states

        result = await _list_lights(mock_client)

        assert result["success"] is True
        assert result["count"] == 3  # Only lights, not the switch
        assert len(result["lights"]) == 3

        # Verify light data
        living_room = next(
            light for light in result["lights"] if light["entity_id"] == "light.living_room"
        )
        assert living_room["name"] == "Living Room Light"
        assert living_room["state"] == "on"
        assert living_room["brightness"] == 255
        assert living_room["color_temp"] == 300

        # Verify kitchen light has RGB color
        kitchen = next(light for light in result["lights"] if light["entity_id"] == "light.kitchen")
        assert kitchen["rgb_color"] == [255, 0, 0]

        # Verify bedroom light (off, no extra attributes)
        bedroom = next(light for light in result["lights"] if light["entity_id"] == "light.bedroom")
        assert bedroom["state"] == "off"
        assert "brightness" not in bedroom

    @pytest.mark.asyncio
    async def test_list_lights_empty(self, mock_client):
        """Test listing lights when no lights exist."""
        mock_client.get_states.return_value = [
            {
                "entity_id": "switch.test",
                "state": "on",
                "attributes": {},
            }
        ]

        result = await _list_lights(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["lights"] == []


class TestGetLight:
    """Tests for getting a specific light."""

    @pytest.mark.asyncio
    async def test_get_light_success(self, mock_client):
        """Test successfully getting a specific light."""
        mock_client.get_state.return_value = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "brightness": 200,
                "color_temp": 350,
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_light(mock_client, "light.living_room")

        assert result["success"] is True
        assert result["light"]["entity_id"] == "light.living_room"
        assert result["light"]["name"] == "Living Room Light"
        assert result["light"]["state"] == "on"
        assert result["light"]["attributes"]["brightness"] == 200
        assert result["light"]["last_changed"] == "2024-01-01T12:00:00"

        mock_client.get_state.assert_called_once_with("light.living_room")

    @pytest.mark.asyncio
    async def test_get_light_not_found(self, mock_client):
        """Test getting a light that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'light.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_light(mock_client, "light.nonexistent")

    @pytest.mark.asyncio
    async def test_get_light_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not a light."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_light(mock_client, "switch.garage")

        assert "not a light entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestTurnOnLight:
    """Tests for turning on lights."""

    @pytest.mark.asyncio
    async def test_turn_on_light_basic(self, mock_client):
        """Test turning on a light without parameters."""
        mock_client.call_service.return_value = {}

        result = await _turn_on_light(mock_client, "light.living_room")

        assert result["success"] is True
        assert result["entity_id"] == "light.living_room"
        assert "turned on" in result["message"]
        assert result["parameters"] == {}

        mock_client.call_service.assert_called_once_with(
            "light", "turn_on", {"entity_id": "light.living_room"}
        )

    @pytest.mark.asyncio
    async def test_turn_on_light_with_brightness(self, mock_client):
        """Test turning on a light with brightness."""
        mock_client.call_service.return_value = {}

        result = await _turn_on_light(mock_client, "light.living_room", brightness=128)

        assert result["success"] is True
        assert result["parameters"]["brightness"] == 128

        mock_client.call_service.assert_called_once_with(
            "light", "turn_on", {"entity_id": "light.living_room", "brightness": 128}
        )

    @pytest.mark.asyncio
    async def test_turn_on_light_with_color_temp(self, mock_client):
        """Test turning on a light with color temperature."""
        mock_client.call_service.return_value = {}

        result = await _turn_on_light(mock_client, "light.living_room", color_temp=300)

        assert result["success"] is True
        assert result["parameters"]["color_temp"] == 300

        mock_client.call_service.assert_called_once_with(
            "light", "turn_on", {"entity_id": "light.living_room", "color_temp": 300}
        )

    @pytest.mark.asyncio
    async def test_turn_on_light_with_rgb_color(self, mock_client):
        """Test turning on a light with RGB color."""
        mock_client.call_service.return_value = {}

        result = await _turn_on_light(mock_client, "light.living_room", rgb_color=(255, 128, 0))

        assert result["success"] is True
        assert result["parameters"]["rgb_color"] == (255, 128, 0)

        mock_client.call_service.assert_called_once_with(
            "light", "turn_on", {"entity_id": "light.living_room", "rgb_color": [255, 128, 0]}
        )

    @pytest.mark.asyncio
    async def test_turn_on_light_with_all_parameters(self, mock_client):
        """Test turning on a light with all parameters."""
        mock_client.call_service.return_value = {}

        result = await _turn_on_light(
            mock_client, "light.living_room", brightness=200, color_temp=350, rgb_color=(255, 0, 0)
        )

        assert result["success"] is True
        assert result["parameters"]["brightness"] == 200
        assert result["parameters"]["color_temp"] == 350
        assert result["parameters"]["rgb_color"] == (255, 0, 0)

        mock_client.call_service.assert_called_once_with(
            "light",
            "turn_on",
            {
                "entity_id": "light.living_room",
                "brightness": 200,
                "color_temp": 350,
                "rgb_color": [255, 0, 0],
            },
        )

    @pytest.mark.asyncio
    async def test_turn_on_light_invalid_rgb_length(self, mock_client):
        """Test turning on a light with invalid RGB tuple length."""
        result = await _turn_on_light(
            mock_client, "light.living_room", rgb_color=(255, 0)  # Only 2 values
        )

        assert result["success"] is False
        assert "exactly 3 values" in result["error"]
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_on_light_invalid_rgb_values(self, mock_client):
        """Test turning on a light with invalid RGB values."""
        result = await _turn_on_light(
            mock_client, "light.living_room", rgb_color=(255, 300, 0)  # 300 is out of range
        )

        assert result["success"] is False
        assert "between 0 and 255" in result["error"]
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_on_light_invalid_entity_type(self, mock_client):
        """Test turning on an entity that is not a light."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _turn_on_light(mock_client, "switch.garage")

        assert "not a light entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_on_light_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _turn_on_light(mock_client, "light.living_room")


class TestTurnOffLight:
    """Tests for turning off lights."""

    @pytest.mark.asyncio
    async def test_turn_off_light_success(self, mock_client):
        """Test successfully turning off a light."""
        mock_client.call_service.return_value = {}

        result = await _turn_off_light(mock_client, "light.living_room")

        assert result["success"] is True
        assert result["entity_id"] == "light.living_room"
        assert "turned off" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "light", "turn_off", {"entity_id": "light.living_room"}
        )

    @pytest.mark.asyncio
    async def test_turn_off_light_invalid_entity_type(self, mock_client):
        """Test turning off an entity that is not a light."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _turn_off_light(mock_client, "switch.garage")

        assert "not a light entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_off_light_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _turn_off_light(mock_client, "light.living_room")


class TestLightsControlIntegration:
    """Integration tests for the lights_control tool function."""

    @pytest.mark.asyncio
    async def test_lights_control_list_action(self, mock_client, sample_light_states):
        """Test the lights_control function with list action."""
        from src.homeassistant_mcp.tools.devices.lights import register_lights_tool

        mock_client.get_states.return_value = sample_light_states

        # Create a mock FastMCP instance
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        # Register the tool
        register_lights_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_lights_control_missing_entity_id(self):
        """Test lights_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.devices.lights import register_lights_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_lights_tool(mock_mcp, lambda: mock_client)

        # Test get without entity_id
        result = await registered_func(action="get")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test turn_on without entity_id
        result = await registered_func(action="turn_on")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test turn_off without entity_id
        result = await registered_func(action="turn_off")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

    @pytest.mark.asyncio
    async def test_lights_control_error_handling(self):
        """Test lights_control error handling."""
        from src.homeassistant_mcp.tools.devices.lights import register_lights_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.get_state.side_effect = EntityNotFoundError("Entity not found")

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_lights_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="light.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
