"""Unit tests for the valve control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.devices.valve import (
    _close_valve,
    _get_valve,
    _list_valves,
    _open_valve,
    _set_valve_position,
    _stop_valve,
    _toggle_valve,
)


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)
    return client


@pytest.fixture
def sample_valve_states():
    """Sample valve entity states for testing."""
    return [
        {
            "entity_id": "valve.water_main",
            "state": "open",
            "attributes": {
                "friendly_name": "Water Main Valve",
                "current_position": 100,
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "valve.irrigation",
            "state": "closed",
            "attributes": {
                "friendly_name": "Irrigation Valve",
                "current_position": 0,
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "cover.garage",
            "state": "open",
            "attributes": {
                "friendly_name": "Garage Door",
            },
        },
    ]


class TestListValves:
    """Tests for listing valves."""

    @pytest.mark.asyncio
    async def test_list_valves_success(self, mock_client, sample_valve_states):
        """Test successfully listing all valves."""
        mock_client.get_states.return_value = sample_valve_states

        result = await _list_valves(mock_client)

        assert result["success"] is True
        assert result["count"] == 2  # Only valves, not the cover
        assert len(result["valves"]) == 2

        # Verify valve data
        water_main = next(
            valve for valve in result["valves"] if valve["entity_id"] == "valve.water_main"
        )
        assert water_main["name"] == "Water Main Valve"
        assert water_main["state"] == "open"
        assert water_main["current_position"] == 100

    @pytest.mark.asyncio
    async def test_list_valves_empty(self, mock_client):
        """Test listing valves when no valves exist."""
        mock_client.get_states.return_value = [
            {
                "entity_id": "cover.test",
                "state": "open",
                "attributes": {},
            }
        ]

        result = await _list_valves(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["valves"] == []


class TestGetValve:
    """Tests for getting a specific valve."""

    @pytest.mark.asyncio
    async def test_get_valve_success(self, mock_client):
        """Test successfully getting a specific valve."""
        mock_client.get_state.return_value = {
            "entity_id": "valve.water_main",
            "state": "open",
            "attributes": {
                "friendly_name": "Water Main Valve",
                "current_position": 100,
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_valve(mock_client, "valve.water_main")

        assert result["success"] is True
        assert result["valve"]["entity_id"] == "valve.water_main"
        assert result["valve"]["name"] == "Water Main Valve"
        assert result["valve"]["state"] == "open"
        assert result["valve"]["last_changed"] == "2024-01-01T12:00:00"

        mock_client.get_state.assert_called_once_with("valve.water_main")

    @pytest.mark.asyncio
    async def test_get_valve_not_found(self, mock_client):
        """Test getting a valve that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'valve.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_valve(mock_client, "valve.nonexistent")

    @pytest.mark.asyncio
    async def test_get_valve_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not a valve."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_valve(mock_client, "cover.garage")

        assert "not a valve entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestOpenValve:
    """Tests for opening valves."""

    @pytest.mark.asyncio
    async def test_open_valve_success(self, mock_client):
        """Test successfully opening a valve."""
        mock_client.call_service.return_value = {}

        result = await _open_valve(mock_client, "valve.water_main")

        assert result["success"] is True
        assert result["entity_id"] == "valve.water_main"
        assert "opened" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "valve", "open_valve", {"entity_id": "valve.water_main"}
        )

    @pytest.mark.asyncio
    async def test_open_valve_invalid_entity_type(self, mock_client):
        """Test opening an entity that is not a valve."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _open_valve(mock_client, "cover.garage")

        assert "not a valve entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_open_valve_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _open_valve(mock_client, "valve.water_main")


class TestCloseValve:
    """Tests for closing valves."""

    @pytest.mark.asyncio
    async def test_close_valve_success(self, mock_client):
        """Test successfully closing a valve."""
        mock_client.call_service.return_value = {}

        result = await _close_valve(mock_client, "valve.water_main")

        assert result["success"] is True
        assert result["entity_id"] == "valve.water_main"
        assert "closed" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "valve", "close_valve", {"entity_id": "valve.water_main"}
        )

    @pytest.mark.asyncio
    async def test_close_valve_invalid_entity_type(self, mock_client):
        """Test closing an entity that is not a valve."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _close_valve(mock_client, "cover.garage")

        assert "not a valve entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestStopValve:
    """Tests for stopping valves."""

    @pytest.mark.asyncio
    async def test_stop_valve_success(self, mock_client):
        """Test successfully stopping a valve."""
        mock_client.call_service.return_value = {}

        result = await _stop_valve(mock_client, "valve.water_main")

        assert result["success"] is True
        assert result["entity_id"] == "valve.water_main"
        assert "stopped" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "valve", "stop_valve", {"entity_id": "valve.water_main"}
        )

    @pytest.mark.asyncio
    async def test_stop_valve_invalid_entity_type(self, mock_client):
        """Test stopping an entity that is not a valve."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _stop_valve(mock_client, "cover.garage")

        assert "not a valve entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestToggleValve:
    """Tests for toggling valves."""

    @pytest.mark.asyncio
    async def test_toggle_valve_success(self, mock_client):
        """Test successfully toggling a valve."""
        mock_client.call_service.return_value = {}

        result = await _toggle_valve(mock_client, "valve.water_main")

        assert result["success"] is True
        assert result["entity_id"] == "valve.water_main"
        assert "toggled" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "valve", "toggle", {"entity_id": "valve.water_main"}
        )

    @pytest.mark.asyncio
    async def test_toggle_valve_invalid_entity_type(self, mock_client):
        """Test toggling an entity that is not a valve."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _toggle_valve(mock_client, "cover.garage")

        assert "not a valve entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestSetValvePosition:
    """Tests for setting valve position."""

    @pytest.mark.asyncio
    async def test_set_valve_position_success(self, mock_client):
        """Test successfully setting valve position."""
        mock_client.call_service.return_value = {}

        result = await _set_valve_position(mock_client, "valve.water_main", 50)

        assert result["success"] is True
        assert result["entity_id"] == "valve.water_main"
        assert result["position"] == 50
        assert "position set to 50%" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "valve", "set_valve_position", {"entity_id": "valve.water_main", "position": 50}
        )

    @pytest.mark.asyncio
    async def test_set_valve_position_invalid_entity_type(self, mock_client):
        """Test setting position for an entity that is not a valve."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _set_valve_position(mock_client, "cover.garage", 50)

        assert "not a valve entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestValveControlIntegration:
    """Integration tests for the valve_control tool function."""

    @pytest.mark.asyncio
    async def test_valve_control_list_action(self, mock_client, sample_valve_states):
        """Test the valve_control function with list action."""
        from src.homeassistant_mcp.tools.devices.valve import register_valve_tool

        mock_client.get_states.return_value = sample_valve_states

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
        register_valve_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_valve_control_missing_entity_id(self):
        """Test valve_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.devices.valve import register_valve_tool

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

        register_valve_tool(mock_mcp, lambda: mock_client)

        # Test get without entity_id
        result = await registered_func(action="get")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test open without entity_id
        result = await registered_func(action="open")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test set_position without position
        result = await registered_func(action="set_position", entity_id="valve.water_main")
        assert result["success"] is False
        assert "position is required" in result["error"]

    @pytest.mark.asyncio
    async def test_valve_control_error_handling(self):
        """Test valve_control error handling."""
        from src.homeassistant_mcp.tools.devices.valve import register_valve_tool

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

        register_valve_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="valve.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
        assert result["error_type"] == "entity_not_found"
