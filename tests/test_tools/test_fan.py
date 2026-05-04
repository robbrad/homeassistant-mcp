"""Unit tests for the fan control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.devices.fan import (
    _get_fan,
    _list_fans,
    _oscillate,
    _set_direction,
    _set_percentage,
    _set_preset_mode,
    _turn_off_fan,
    _turn_on_fan,
)


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)

    # Domain-filtering side_effect for get_states
    async def _filtered_get_states(domain=None, area=None, limit=None):
        states = list(client._states_data)
        if domain:
            states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
        return states

    client._states_data = []
    client.get_states = AsyncMock(side_effect=_filtered_get_states)

    return client


@pytest.fixture
def sample_fan_states():
    """Sample fan entity states for testing."""
    return [
        {
            "entity_id": "fan.bedroom",
            "state": "on",
            "attributes": {
                "friendly_name": "Bedroom Fan",
                "percentage": 75,
                "preset_mode": "auto",
                "oscillating": True,
                "direction": "forward",
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "fan.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Fan",
                "percentage": 50,
                "preset_mode": "sleep",
                "oscillating": False,
                "direction": "reverse",
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "fan.kitchen",
            "state": "off",
            "attributes": {
                "friendly_name": "Kitchen Fan",
                "percentage": 0,
            },
            "last_changed": "2024-01-01T10:00:00",
            "last_updated": "2024-01-01T10:00:00",
        },
        {
            "entity_id": "light.garage",
            "state": "on",
            "attributes": {
                "friendly_name": "Garage Light",
            },
        },
    ]


class TestListFans:
    """Tests for listing fans."""

    @pytest.mark.asyncio
    async def test_list_fans_success(self, mock_client, sample_fan_states):
        """Test successfully listing all fans."""
        mock_client._states_data = sample_fan_states

        result = await _list_fans(mock_client)

        assert result["success"] is True
        assert result["count"] == 3  # Only fans, not the light
        assert len(result["fans"]) == 3

        # Verify bedroom fan data
        bedroom = next(fan for fan in result["fans"] if fan["entity_id"] == "fan.bedroom")
        assert bedroom["name"] == "Bedroom Fan"
        assert bedroom["state"] == "on"
        assert bedroom["percentage"] == 75
        assert bedroom["preset_mode"] == "auto"
        assert bedroom["oscillating"] is True
        assert bedroom["direction"] == "forward"

        # Verify living room fan
        living_room = next(fan for fan in result["fans"] if fan["entity_id"] == "fan.living_room")
        assert living_room["state"] == "on"
        assert living_room["percentage"] == 50
        assert living_room["preset_mode"] == "sleep"
        assert living_room["oscillating"] is False
        assert living_room["direction"] == "reverse"

        # Verify kitchen fan (off state)
        kitchen = next(fan for fan in result["fans"] if fan["entity_id"] == "fan.kitchen")
        assert kitchen["state"] == "off"
        assert kitchen["percentage"] == 0

    @pytest.mark.asyncio
    async def test_list_fans_empty(self, mock_client):
        """Test listing fans when no fans exist."""
        mock_client._states_data = [
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {},
            }
        ]

        result = await _list_fans(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["fans"] == []

    @pytest.mark.asyncio
    async def test_list_fans_without_optional_attributes(self, mock_client):
        """Test listing fans that don't have all optional attributes."""
        mock_client._states_data = [
            {
                "entity_id": "fan.simple",
                "state": "on",
                "attributes": {
                    "friendly_name": "Simple Fan",
                },
            }
        ]

        result = await _list_fans(mock_client)

        assert result["success"] is True
        assert result["count"] == 1
        assert "percentage" not in result["fans"][0]
        assert "preset_mode" not in result["fans"][0]
        assert "oscillating" not in result["fans"][0]
        assert "direction" not in result["fans"][0]


class TestGetFan:
    """Tests for getting a specific fan."""

    @pytest.mark.asyncio
    async def test_get_fan_success(self, mock_client):
        """Test successfully getting a specific fan."""
        mock_client.get_state.return_value = {
            "entity_id": "fan.bedroom",
            "state": "on",
            "attributes": {
                "friendly_name": "Bedroom Fan",
                "percentage": 75,
                "preset_mode": "auto",
                "oscillating": True,
                "direction": "forward",
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_fan(mock_client, "fan.bedroom")

        assert result["success"] is True
        assert result["fan"]["entity_id"] == "fan.bedroom"
        assert result["fan"]["name"] == "Bedroom Fan"
        assert result["fan"]["state"] == "on"
        assert result["fan"]["last_changed"] == "2024-01-01T12:00:00"
        assert result["fan"]["attributes"]["percentage"] == 75
        assert result["fan"]["attributes"]["preset_mode"] == "auto"
        assert result["fan"]["attributes"]["oscillating"] is True
        assert result["fan"]["attributes"]["direction"] == "forward"

        mock_client.get_state.assert_called_once_with("fan.bedroom")

    @pytest.mark.asyncio
    async def test_get_fan_not_found(self, mock_client):
        """Test getting a fan that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'fan.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_fan(mock_client, "fan.nonexistent")

    @pytest.mark.asyncio
    async def test_get_fan_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not a fan."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_fan(mock_client, "light.garage")

        assert "not a fan entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestTurnOnFan:
    """Tests for turning on fans."""

    @pytest.mark.asyncio
    async def test_turn_on_fan_success(self, mock_client):
        """Test successfully turning on a fan."""
        mock_client.call_service.return_value = {}

        result = await _turn_on_fan(mock_client, "fan.bedroom")

        assert result["success"] is True
        assert result["entity_id"] == "fan.bedroom"
        assert "turned on" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "fan", "turn_on", {"entity_id": "fan.bedroom"}
        )

    @pytest.mark.asyncio
    async def test_turn_on_fan_invalid_entity_type(self, mock_client):
        """Test turning on an entity that is not a fan."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _turn_on_fan(mock_client, "light.garage")

        assert "not a fan entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_on_fan_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _turn_on_fan(mock_client, "fan.bedroom")


class TestTurnOffFan:
    """Tests for turning off fans."""

    @pytest.mark.asyncio
    async def test_turn_off_fan_success(self, mock_client):
        """Test successfully turning off a fan."""
        mock_client.call_service.return_value = {}

        result = await _turn_off_fan(mock_client, "fan.bedroom")

        assert result["success"] is True
        assert result["entity_id"] == "fan.bedroom"
        assert "turned off" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "fan", "turn_off", {"entity_id": "fan.bedroom"}
        )

    @pytest.mark.asyncio
    async def test_turn_off_fan_invalid_entity_type(self, mock_client):
        """Test turning off an entity that is not a fan."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _turn_off_fan(mock_client, "switch.fan")

        assert "not a fan entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestSetPercentage:
    """Tests for setting fan speed percentage."""

    @pytest.mark.asyncio
    async def test_set_percentage_success(self, mock_client):
        """Test successfully setting fan speed percentage."""
        mock_client.call_service.return_value = {}

        result = await _set_percentage(mock_client, "fan.bedroom", 75)

        assert result["success"] is True
        assert result["entity_id"] == "fan.bedroom"
        assert result["percentage"] == 75
        assert "speed set to 75%" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "fan", "set_percentage", {"entity_id": "fan.bedroom", "percentage": 75}
        )

    @pytest.mark.asyncio
    async def test_set_percentage_different_levels(self, mock_client):
        """Test setting different percentage levels."""
        mock_client.call_service.return_value = {}

        # Test 0% (off)
        result = await _set_percentage(mock_client, "fan.bedroom", 0)
        assert result["success"] is True
        assert result["percentage"] == 0

        # Test 50% (medium)
        result = await _set_percentage(mock_client, "fan.bedroom", 50)
        assert result["success"] is True
        assert result["percentage"] == 50

        # Test 100% (max)
        result = await _set_percentage(mock_client, "fan.bedroom", 100)
        assert result["success"] is True
        assert result["percentage"] == 100

    @pytest.mark.asyncio
    async def test_set_percentage_invalid_entity_type(self, mock_client):
        """Test setting percentage for an entity that is not a fan."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _set_percentage(mock_client, "cover.garage", 50)

        assert "not a fan entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestSetPresetMode:
    """Tests for setting fan preset mode."""

    @pytest.mark.asyncio
    async def test_set_preset_mode_success(self, mock_client):
        """Test successfully setting preset mode."""
        mock_client.call_service.return_value = {}

        result = await _set_preset_mode(mock_client, "fan.bedroom", "auto")

        assert result["success"] is True
        assert result["entity_id"] == "fan.bedroom"
        assert result["preset_mode"] == "auto"
        assert "preset mode set to 'auto'" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "fan", "set_preset_mode", {"entity_id": "fan.bedroom", "preset_mode": "auto"}
        )

    @pytest.mark.asyncio
    async def test_set_preset_mode_different_presets(self, mock_client):
        """Test setting different preset modes."""
        mock_client.call_service.return_value = {}

        # Test auto preset
        result = await _set_preset_mode(mock_client, "fan.bedroom", "auto")
        assert result["success"] is True
        assert result["preset_mode"] == "auto"

        # Test sleep preset
        result = await _set_preset_mode(mock_client, "fan.bedroom", "sleep")
        assert result["success"] is True
        assert result["preset_mode"] == "sleep"

        # Test smart preset
        result = await _set_preset_mode(mock_client, "fan.bedroom", "smart")
        assert result["success"] is True
        assert result["preset_mode"] == "smart"

    @pytest.mark.asyncio
    async def test_set_preset_mode_invalid_entity_type(self, mock_client):
        """Test setting preset mode for an entity that is not a fan."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _set_preset_mode(mock_client, "light.bedroom", "auto")

        assert "not a fan entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestOscillate:
    """Tests for controlling fan oscillation."""

    @pytest.mark.asyncio
    async def test_oscillate_enable_success(self, mock_client):
        """Test successfully enabling oscillation."""
        mock_client.call_service.return_value = {}

        result = await _oscillate(mock_client, "fan.bedroom", True)

        assert result["success"] is True
        assert result["entity_id"] == "fan.bedroom"
        assert result["oscillating"] is True
        assert "oscillation enabled" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "fan", "oscillate", {"entity_id": "fan.bedroom", "oscillating": True}
        )

    @pytest.mark.asyncio
    async def test_oscillate_disable_success(self, mock_client):
        """Test successfully disabling oscillation."""
        mock_client.call_service.return_value = {}

        result = await _oscillate(mock_client, "fan.bedroom", False)

        assert result["success"] is True
        assert result["entity_id"] == "fan.bedroom"
        assert result["oscillating"] is False
        assert "oscillation disabled" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "fan", "oscillate", {"entity_id": "fan.bedroom", "oscillating": False}
        )

    @pytest.mark.asyncio
    async def test_oscillate_invalid_entity_type(self, mock_client):
        """Test oscillating an entity that is not a fan."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _oscillate(mock_client, "climate.thermostat", True)

        assert "not a fan entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestSetDirection:
    """Tests for setting fan rotation direction."""

    @pytest.mark.asyncio
    async def test_set_direction_forward_success(self, mock_client):
        """Test successfully setting direction to forward."""
        mock_client.call_service.return_value = {}

        result = await _set_direction(mock_client, "fan.bedroom", "forward")

        assert result["success"] is True
        assert result["entity_id"] == "fan.bedroom"
        assert result["direction"] == "forward"
        assert "direction set to 'forward'" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "fan", "set_direction", {"entity_id": "fan.bedroom", "direction": "forward"}
        )

    @pytest.mark.asyncio
    async def test_set_direction_reverse_success(self, mock_client):
        """Test successfully setting direction to reverse."""
        mock_client.call_service.return_value = {}

        result = await _set_direction(mock_client, "fan.bedroom", "reverse")

        assert result["success"] is True
        assert result["entity_id"] == "fan.bedroom"
        assert result["direction"] == "reverse"
        assert "direction set to 'reverse'" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "fan", "set_direction", {"entity_id": "fan.bedroom", "direction": "reverse"}
        )

    @pytest.mark.asyncio
    async def test_set_direction_invalid_entity_type(self, mock_client):
        """Test setting direction for an entity that is not a fan."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _set_direction(mock_client, "media_player.tv", "forward")

        assert "not a fan entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestFanControlIntegration:
    """Integration tests for the fan_control tool function."""

    @pytest.mark.asyncio
    async def test_fan_control_list_action(self, mock_client, sample_fan_states):
        """Test the fan_control function with list action."""
        from src.homeassistant_mcp.tools.devices.fan import register_fan_tool

        mock_client._states_data = sample_fan_states

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
        register_fan_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_fan_control_missing_entity_id(self):
        """Test fan_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.devices.fan import register_fan_tool

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

        register_fan_tool(mock_mcp, lambda: mock_client)

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
    async def test_fan_control_set_percentage_missing_params(self):
        """Test fan_control set_percentage with missing parameters."""
        from src.homeassistant_mcp.tools.devices.fan import register_fan_tool

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

        register_fan_tool(mock_mcp, lambda: mock_client)

        # Test set_percentage without entity_id
        result = await registered_func(action="set_percentage", percentage=75)
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test set_percentage without percentage
        result = await registered_func(action="set_percentage", entity_id="fan.bedroom")
        assert result["success"] is False
        assert "percentage is required" in result["error"]

    @pytest.mark.asyncio
    async def test_fan_control_set_preset_mode_missing_params(self):
        """Test fan_control set_preset_mode with missing parameters."""
        from src.homeassistant_mcp.tools.devices.fan import register_fan_tool

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

        register_fan_tool(mock_mcp, lambda: mock_client)

        # Test set_preset_mode without entity_id
        result = await registered_func(action="set_preset_mode", preset_mode="auto")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test set_preset_mode without preset_mode
        result = await registered_func(action="set_preset_mode", entity_id="fan.bedroom")
        assert result["success"] is False
        assert "preset_mode is required" in result["error"]

    @pytest.mark.asyncio
    async def test_fan_control_oscillate_missing_params(self):
        """Test fan_control oscillate with missing parameters."""
        from src.homeassistant_mcp.tools.devices.fan import register_fan_tool

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

        register_fan_tool(mock_mcp, lambda: mock_client)

        # Test oscillate without entity_id
        result = await registered_func(action="oscillate", oscillating=True)
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test oscillate without oscillating parameter
        result = await registered_func(action="oscillate", entity_id="fan.bedroom")
        assert result["success"] is False
        assert "oscillating is required" in result["error"]

    @pytest.mark.asyncio
    async def test_fan_control_set_direction_missing_params(self):
        """Test fan_control set_direction with missing parameters."""
        from src.homeassistant_mcp.tools.devices.fan import register_fan_tool

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

        register_fan_tool(mock_mcp, lambda: mock_client)

        # Test set_direction without entity_id
        result = await registered_func(action="set_direction", direction="forward")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test set_direction without direction
        result = await registered_func(action="set_direction", entity_id="fan.bedroom")
        assert result["success"] is False
        assert "direction is required" in result["error"]

    @pytest.mark.asyncio
    async def test_fan_control_all_actions(self):
        """Test fan_control with all control actions."""
        from src.homeassistant_mcp.tools.devices.fan import register_fan_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.call_service.return_value = {}

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_fan_tool(mock_mcp, lambda: mock_client)

        # Test turn_on
        result = await registered_func(action="turn_on", entity_id="fan.bedroom")
        assert result["success"] is True
        assert "turned on" in result["message"]

        # Test turn_off
        result = await registered_func(action="turn_off", entity_id="fan.bedroom")
        assert result["success"] is True
        assert "turned off" in result["message"]

        # Test set_percentage
        result = await registered_func(
            action="set_percentage", entity_id="fan.bedroom", percentage=75
        )
        assert result["success"] is True
        assert result["percentage"] == 75

        # Test set_preset_mode
        result = await registered_func(
            action="set_preset_mode", entity_id="fan.bedroom", preset_mode="auto"
        )
        assert result["success"] is True
        assert result["preset_mode"] == "auto"

        # Test oscillate
        result = await registered_func(
            action="oscillate", entity_id="fan.bedroom", oscillating=True
        )
        assert result["success"] is True
        assert result["oscillating"] is True

        # Test set_direction
        result = await registered_func(
            action="set_direction", entity_id="fan.bedroom", direction="forward"
        )
        assert result["success"] is True
        assert result["direction"] == "forward"

    @pytest.mark.asyncio
    async def test_fan_control_error_handling(self):
        """Test fan_control error handling."""
        from src.homeassistant_mcp.tools.devices.fan import register_fan_tool

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

        register_fan_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="fan.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
        assert result["error_type"] == "entity_not_found"
