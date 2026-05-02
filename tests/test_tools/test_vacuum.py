"""Unit tests for the vacuum control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.devices.vacuum import (
    _get_vacuum,
    _list_vacuums,
    _locate_vacuum,
    _pause_vacuum,
    _return_to_base,
    _set_fan_speed,
    _start_vacuum,
    _stop_vacuum,
)


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)
    return client


@pytest.fixture
def sample_vacuum_states():
    """Sample vacuum entity states for testing."""
    return [
        {
            "entity_id": "vacuum.living_room",
            "state": "cleaning",
            "attributes": {
                "friendly_name": "Living Room Vacuum",
                "battery_level": 85,
                "fan_speed": "medium",
                "status": "Cleaning",
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "vacuum.bedroom",
            "state": "docked",
            "attributes": {
                "friendly_name": "Bedroom Vacuum",
                "battery_level": 100,
                "fan_speed": "auto",
                "status": "Charging",
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "vacuum.kitchen",
            "state": "paused",
            "attributes": {
                "friendly_name": "Kitchen Vacuum",
                "battery_level": 45,
                "fan_speed": "high",
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


class TestListVacuums:
    """Tests for listing vacuums."""

    @pytest.mark.asyncio
    async def test_list_vacuums_success(self, mock_client, sample_vacuum_states):
        """Test successfully listing all vacuums."""
        mock_client.get_states.return_value = sample_vacuum_states

        result = await _list_vacuums(mock_client)

        assert result["success"] is True
        assert result["count"] == 3  # Only vacuums, not the light
        assert len(result["vacuums"]) == 3

        # Verify vacuum data
        living_room = next(
            vacuum for vacuum in result["vacuums"] if vacuum["entity_id"] == "vacuum.living_room"
        )
        assert living_room["name"] == "Living Room Vacuum"
        assert living_room["state"] == "cleaning"
        assert living_room["battery_level"] == 85
        assert living_room["fan_speed"] == "medium"
        assert living_room["status"] == "Cleaning"

        # Verify bedroom vacuum (docked)
        bedroom = next(
            vacuum for vacuum in result["vacuums"] if vacuum["entity_id"] == "vacuum.bedroom"
        )
        assert bedroom["state"] == "docked"
        assert bedroom["battery_level"] == 100

    @pytest.mark.asyncio
    async def test_list_vacuums_empty(self, mock_client):
        """Test listing vacuums when no vacuums exist."""
        mock_client.get_states.return_value = [
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {},
            }
        ]

        result = await _list_vacuums(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["vacuums"] == []

    @pytest.mark.asyncio
    async def test_list_vacuums_without_optional_attributes(self, mock_client):
        """Test listing vacuums that don't have battery or fan speed."""
        mock_client.get_states.return_value = [
            {
                "entity_id": "vacuum.simple",
                "state": "cleaning",
                "attributes": {
                    "friendly_name": "Simple Vacuum",
                },
            }
        ]

        result = await _list_vacuums(mock_client)

        assert result["success"] is True
        assert result["count"] == 1
        assert "battery_level" not in result["vacuums"][0]
        assert "fan_speed" not in result["vacuums"][0]


class TestGetVacuum:
    """Tests for getting a specific vacuum."""

    @pytest.mark.asyncio
    async def test_get_vacuum_success(self, mock_client):
        """Test successfully getting a specific vacuum."""
        mock_client.get_state.return_value = {
            "entity_id": "vacuum.living_room",
            "state": "cleaning",
            "attributes": {
                "friendly_name": "Living Room Vacuum",
                "battery_level": 85,
                "fan_speed": "medium",
                "status": "Cleaning",
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_vacuum(mock_client, "vacuum.living_room")

        assert result["success"] is True
        assert result["vacuum"]["entity_id"] == "vacuum.living_room"
        assert result["vacuum"]["name"] == "Living Room Vacuum"
        assert result["vacuum"]["state"] == "cleaning"
        assert result["vacuum"]["last_changed"] == "2024-01-01T12:00:00"
        assert result["vacuum"]["attributes"]["battery_level"] == 85

        mock_client.get_state.assert_called_once_with("vacuum.living_room")

    @pytest.mark.asyncio
    async def test_get_vacuum_not_found(self, mock_client):
        """Test getting a vacuum that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'vacuum.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_vacuum(mock_client, "vacuum.nonexistent")

    @pytest.mark.asyncio
    async def test_get_vacuum_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not a vacuum."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_vacuum(mock_client, "light.garage")

        assert "not a vacuum entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestStartVacuum:
    """Tests for starting vacuum cleaning."""

    @pytest.mark.asyncio
    async def test_start_vacuum_success(self, mock_client):
        """Test successfully starting a vacuum."""
        mock_client.call_service.return_value = {}

        result = await _start_vacuum(mock_client, "vacuum.living_room")

        assert result["success"] is True
        assert result["entity_id"] == "vacuum.living_room"
        assert "started cleaning" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "vacuum", "start", {"entity_id": "vacuum.living_room"}
        )

    @pytest.mark.asyncio
    async def test_start_vacuum_invalid_entity_type(self, mock_client):
        """Test starting an entity that is not a vacuum."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _start_vacuum(mock_client, "light.garage")

        assert "not a vacuum entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_vacuum_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _start_vacuum(mock_client, "vacuum.living_room")


class TestPauseVacuum:
    """Tests for pausing vacuum cleaning."""

    @pytest.mark.asyncio
    async def test_pause_vacuum_success(self, mock_client):
        """Test successfully pausing a vacuum."""
        mock_client.call_service.return_value = {}

        result = await _pause_vacuum(mock_client, "vacuum.living_room")

        assert result["success"] is True
        assert result["entity_id"] == "vacuum.living_room"
        assert "paused" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "vacuum", "pause", {"entity_id": "vacuum.living_room"}
        )

    @pytest.mark.asyncio
    async def test_pause_vacuum_invalid_entity_type(self, mock_client):
        """Test pausing an entity that is not a vacuum."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _pause_vacuum(mock_client, "switch.fan")

        assert "not a vacuum entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestStopVacuum:
    """Tests for stopping vacuum cleaning."""

    @pytest.mark.asyncio
    async def test_stop_vacuum_success(self, mock_client):
        """Test successfully stopping a vacuum."""
        mock_client.call_service.return_value = {}

        result = await _stop_vacuum(mock_client, "vacuum.living_room")

        assert result["success"] is True
        assert result["entity_id"] == "vacuum.living_room"
        assert "stopped" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "vacuum", "stop", {"entity_id": "vacuum.living_room"}
        )

    @pytest.mark.asyncio
    async def test_stop_vacuum_invalid_entity_type(self, mock_client):
        """Test stopping an entity that is not a vacuum."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _stop_vacuum(mock_client, "climate.thermostat")

        assert "not a vacuum entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestReturnToBase:
    """Tests for sending vacuum to base."""

    @pytest.mark.asyncio
    async def test_return_to_base_success(self, mock_client):
        """Test successfully sending vacuum to base."""
        mock_client.call_service.return_value = {}

        result = await _return_to_base(mock_client, "vacuum.living_room")

        assert result["success"] is True
        assert result["entity_id"] == "vacuum.living_room"
        assert "returning to base" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "vacuum", "return_to_base", {"entity_id": "vacuum.living_room"}
        )

    @pytest.mark.asyncio
    async def test_return_to_base_invalid_entity_type(self, mock_client):
        """Test return to base for an entity that is not a vacuum."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _return_to_base(mock_client, "fan.ceiling")

        assert "not a vacuum entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestLocateVacuum:
    """Tests for locating vacuum."""

    @pytest.mark.asyncio
    async def test_locate_vacuum_success(self, mock_client):
        """Test successfully locating a vacuum."""
        mock_client.call_service.return_value = {}

        result = await _locate_vacuum(mock_client, "vacuum.living_room")

        assert result["success"] is True
        assert result["entity_id"] == "vacuum.living_room"
        assert "locate triggered" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "vacuum", "locate", {"entity_id": "vacuum.living_room"}
        )

    @pytest.mark.asyncio
    async def test_locate_vacuum_invalid_entity_type(self, mock_client):
        """Test locating an entity that is not a vacuum."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _locate_vacuum(mock_client, "media_player.tv")

        assert "not a vacuum entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestSetFanSpeed:
    """Tests for setting vacuum fan speed."""

    @pytest.mark.asyncio
    async def test_set_fan_speed_success(self, mock_client):
        """Test successfully setting fan speed."""
        mock_client.call_service.return_value = {}

        result = await _set_fan_speed(mock_client, "vacuum.living_room", "high")

        assert result["success"] is True
        assert result["entity_id"] == "vacuum.living_room"
        assert result["fan_speed"] == "high"
        assert "fan speed set to 'high'" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "vacuum", "set_fan_speed", {"entity_id": "vacuum.living_room", "fan_speed": "high"}
        )

    @pytest.mark.asyncio
    async def test_set_fan_speed_different_levels(self, mock_client):
        """Test setting different fan speed levels."""
        mock_client.call_service.return_value = {}

        # Test low
        result = await _set_fan_speed(mock_client, "vacuum.living_room", "low")
        assert result["success"] is True
        assert result["fan_speed"] == "low"

        # Test medium
        result = await _set_fan_speed(mock_client, "vacuum.living_room", "medium")
        assert result["success"] is True
        assert result["fan_speed"] == "medium"

        # Test auto
        result = await _set_fan_speed(mock_client, "vacuum.living_room", "auto")
        assert result["success"] is True
        assert result["fan_speed"] == "auto"

    @pytest.mark.asyncio
    async def test_set_fan_speed_invalid_entity_type(self, mock_client):
        """Test setting fan speed for an entity that is not a vacuum."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _set_fan_speed(mock_client, "cover.garage", "high")

        assert "not a vacuum entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestVacuumControlIntegration:
    """Integration tests for the vacuum_control tool function."""

    @pytest.mark.asyncio
    async def test_vacuum_control_list_action(self, mock_client, sample_vacuum_states):
        """Test the vacuum_control function with list action."""
        from src.homeassistant_mcp.tools.devices.vacuum import register_vacuum_tool

        mock_client.get_states.return_value = sample_vacuum_states

        # Create a mock FastMCP instance
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        # Register the tool
        register_vacuum_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_vacuum_control_missing_entity_id(self):
        """Test vacuum_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.devices.vacuum import register_vacuum_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_vacuum_tool(mock_mcp, lambda: mock_client)

        # Test get without entity_id
        result = await registered_func(action="get")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test start without entity_id
        result = await registered_func(action="start")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test pause without entity_id
        result = await registered_func(action="pause")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test stop without entity_id
        result = await registered_func(action="stop")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test return_to_base without entity_id
        result = await registered_func(action="return_to_base")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test locate without entity_id
        result = await registered_func(action="locate")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

    @pytest.mark.asyncio
    async def test_vacuum_control_set_fan_speed_missing_params(self):
        """Test vacuum_control set_fan_speed with missing parameters."""
        from src.homeassistant_mcp.tools.devices.vacuum import register_vacuum_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_vacuum_tool(mock_mcp, lambda: mock_client)

        # Test set_fan_speed without entity_id
        result = await registered_func(action="set_fan_speed", fan_speed="high")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test set_fan_speed without fan_speed
        result = await registered_func(action="set_fan_speed", entity_id="vacuum.living_room")
        assert result["success"] is False
        assert "fan_speed is required" in result["error"]

    @pytest.mark.asyncio
    async def test_vacuum_control_all_actions(self):
        """Test vacuum_control with all control actions."""
        from src.homeassistant_mcp.tools.devices.vacuum import register_vacuum_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.call_service.return_value = {}

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_vacuum_tool(mock_mcp, lambda: mock_client)

        # Test start
        result = await registered_func(action="start", entity_id="vacuum.living_room")
        assert result["success"] is True
        assert "started cleaning" in result["message"]

        # Test pause
        result = await registered_func(action="pause", entity_id="vacuum.living_room")
        assert result["success"] is True
        assert "paused" in result["message"]

        # Test stop
        result = await registered_func(action="stop", entity_id="vacuum.living_room")
        assert result["success"] is True
        assert "stopped" in result["message"]

        # Test return_to_base
        result = await registered_func(action="return_to_base", entity_id="vacuum.living_room")
        assert result["success"] is True
        assert "returning to base" in result["message"]

        # Test locate
        result = await registered_func(action="locate", entity_id="vacuum.living_room")
        assert result["success"] is True
        assert "locate triggered" in result["message"]

        # Test set_fan_speed
        result = await registered_func(
            action="set_fan_speed", entity_id="vacuum.living_room", fan_speed="high"
        )
        assert result["success"] is True
        assert result["fan_speed"] == "high"

    @pytest.mark.asyncio
    async def test_vacuum_control_error_handling(self):
        """Test vacuum_control error handling."""
        from src.homeassistant_mcp.tools.devices.vacuum import register_vacuum_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.get_state.side_effect = EntityNotFoundError("Entity not found")

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_vacuum_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="vacuum.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
        assert result["error_type"] == "entity_not_found"
