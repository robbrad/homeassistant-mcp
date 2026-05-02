"""Unit tests for the switch control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.devices.switch import (
    _bulk_control_switches,
    _get_switch,
    _list_switches,
    _toggle_switch,
    _turn_off_switch,
    _turn_on_switch,
)


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)
    return client


@pytest.fixture
def sample_switch_states():
    """Sample switch entity states for testing."""
    return [
        {
            "entity_id": "switch.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Switch",
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "switch.bedroom",
            "state": "off",
            "attributes": {
                "friendly_name": "Bedroom Switch",
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "switch.kitchen",
            "state": "on",
            "attributes": {
                "friendly_name": "Kitchen Switch",
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


class TestListSwitches:
    """Tests for listing switches."""

    @pytest.mark.asyncio
    async def test_list_switches_success(self, mock_client, sample_switch_states):
        """Test successfully listing all switches."""
        mock_client.get_states.return_value = sample_switch_states

        result = await _list_switches(mock_client)

        assert result["success"] is True
        assert result["count"] == 3  # Only switches, not the light
        assert len(result["switches"]) == 3

        # Verify switch data
        living_room = next(
            switch for switch in result["switches"] if switch["entity_id"] == "switch.living_room"
        )
        assert living_room["name"] == "Living Room Switch"
        assert living_room["state"] == "on"

        # Verify bedroom switch (off)
        bedroom = next(
            switch for switch in result["switches"] if switch["entity_id"] == "switch.bedroom"
        )
        assert bedroom["state"] == "off"

    @pytest.mark.asyncio
    async def test_list_switches_empty(self, mock_client):
        """Test listing switches when no switches exist."""
        mock_client.get_states.return_value = [
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {},
            }
        ]

        result = await _list_switches(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["switches"] == []


class TestGetSwitch:
    """Tests for getting a specific switch."""

    @pytest.mark.asyncio
    async def test_get_switch_success(self, mock_client):
        """Test successfully getting a specific switch."""
        mock_client.get_state.return_value = {
            "entity_id": "switch.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Switch",
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_switch(mock_client, "switch.living_room")

        assert result["success"] is True
        assert result["switch"]["entity_id"] == "switch.living_room"
        assert result["switch"]["name"] == "Living Room Switch"
        assert result["switch"]["state"] == "on"
        assert result["switch"]["last_changed"] == "2024-01-01T12:00:00"

        mock_client.get_state.assert_called_once_with("switch.living_room")

    @pytest.mark.asyncio
    async def test_get_switch_not_found(self, mock_client):
        """Test getting a switch that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'switch.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_switch(mock_client, "switch.nonexistent")

    @pytest.mark.asyncio
    async def test_get_switch_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not a switch."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_switch(mock_client, "light.garage")

        assert "not a switch entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestTurnOnSwitch:
    """Tests for turning on switches."""

    @pytest.mark.asyncio
    async def test_turn_on_switch_success(self, mock_client):
        """Test successfully turning on a switch."""
        mock_client.call_service.return_value = {}

        result = await _turn_on_switch(mock_client, "switch.living_room")

        assert result["success"] is True
        assert result["entity_id"] == "switch.living_room"
        assert "turned on" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "switch", "turn_on", {"entity_id": "switch.living_room"}
        )

    @pytest.mark.asyncio
    async def test_turn_on_switch_invalid_entity_type(self, mock_client):
        """Test turning on an entity that is not a switch."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _turn_on_switch(mock_client, "light.garage")

        assert "not a switch entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_on_switch_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _turn_on_switch(mock_client, "switch.living_room")


class TestTurnOffSwitch:
    """Tests for turning off switches."""

    @pytest.mark.asyncio
    async def test_turn_off_switch_success(self, mock_client):
        """Test successfully turning off a switch."""
        mock_client.call_service.return_value = {}

        result = await _turn_off_switch(mock_client, "switch.living_room")

        assert result["success"] is True
        assert result["entity_id"] == "switch.living_room"
        assert "turned off" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "switch", "turn_off", {"entity_id": "switch.living_room"}
        )

    @pytest.mark.asyncio
    async def test_turn_off_switch_invalid_entity_type(self, mock_client):
        """Test turning off an entity that is not a switch."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _turn_off_switch(mock_client, "light.garage")

        assert "not a switch entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_off_switch_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _turn_off_switch(mock_client, "switch.living_room")


class TestToggleSwitch:
    """Tests for toggling switches."""

    @pytest.mark.asyncio
    async def test_toggle_switch_success(self, mock_client):
        """Test successfully toggling a switch."""
        mock_client.call_service.return_value = {}

        result = await _toggle_switch(mock_client, "switch.living_room")

        assert result["success"] is True
        assert result["entity_id"] == "switch.living_room"
        assert "toggled" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "switch", "toggle", {"entity_id": "switch.living_room"}
        )

    @pytest.mark.asyncio
    async def test_toggle_switch_invalid_entity_type(self, mock_client):
        """Test toggling an entity that is not a switch."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _toggle_switch(mock_client, "light.garage")

        assert "not a switch entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_toggle_switch_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _toggle_switch(mock_client, "switch.living_room")


class TestBulkControlSwitches:
    """Tests for bulk switch operations."""

    @pytest.mark.asyncio
    async def test_bulk_turn_on_success(self, mock_client):
        """Test successfully turning on multiple switches."""
        mock_client.call_service.return_value = {}
        entity_ids = ["switch.living_room", "switch.bedroom", "switch.kitchen"]

        result = await _bulk_control_switches(mock_client, entity_ids, "turn_on")

        assert result["success"] is True
        assert result["count"] == 3
        assert result["entity_ids"] == entity_ids
        assert "turn_on" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "switch", "turn_on", {"entity_id": entity_ids}
        )

    @pytest.mark.asyncio
    async def test_bulk_turn_off_success(self, mock_client):
        """Test successfully turning off multiple switches."""
        mock_client.call_service.return_value = {}
        entity_ids = ["switch.living_room", "switch.bedroom"]

        result = await _bulk_control_switches(mock_client, entity_ids, "turn_off")

        assert result["success"] is True
        assert result["count"] == 2
        assert result["entity_ids"] == entity_ids
        assert "turn_off" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "switch", "turn_off", {"entity_id": entity_ids}
        )

    @pytest.mark.asyncio
    async def test_bulk_control_invalid_entity_type(self, mock_client):
        """Test bulk control with invalid entity type."""
        entity_ids = ["switch.living_room", "light.garage"]

        with pytest.raises(EntityNotFoundError) as exc_info:
            await _bulk_control_switches(mock_client, entity_ids, "turn_on")

        assert "not a switch entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_bulk_control_service_error(self, mock_client):
        """Test handling service call errors in bulk operations."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")
        entity_ids = ["switch.living_room", "switch.bedroom"]

        with pytest.raises(ServiceCallError):
            await _bulk_control_switches(mock_client, entity_ids, "turn_on")


class TestSwitchControlIntegration:
    """Integration tests for the switch_control tool function."""

    @pytest.mark.asyncio
    async def test_switch_control_list_action(self, mock_client, sample_switch_states):
        """Test the switch_control function with list action."""
        from src.homeassistant_mcp.tools.devices.switch import register_switch_tool

        mock_client.get_states.return_value = sample_switch_states

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
        register_switch_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_switch_control_missing_entity_id(self):
        """Test switch_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.devices.switch import register_switch_tool

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

        register_switch_tool(mock_mcp, lambda: mock_client)

        # Test get without entity_id
        result = await registered_func(action="get")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test turn_on without entity_id or entity_ids
        result = await registered_func(action="turn_on")
        assert result["success"] is False
        assert "entity_id" in result["error"]

        # Test turn_off without entity_id or entity_ids
        result = await registered_func(action="turn_off")
        assert result["success"] is False
        assert "entity_id" in result["error"]

        # Test toggle without entity_id
        result = await registered_func(action="toggle")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

    @pytest.mark.asyncio
    async def test_switch_control_bulk_operations(self):
        """Test switch_control with bulk operations."""
        from src.homeassistant_mcp.tools.devices.switch import register_switch_tool

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

        register_switch_tool(mock_mcp, lambda: mock_client)

        # Test bulk turn_on
        entity_ids = ["switch.light1", "switch.light2"]
        result = await registered_func(action="turn_on", entity_ids=entity_ids)
        assert result["success"] is True
        assert result["count"] == 2

        # Test bulk turn_off
        result = await registered_func(action="turn_off", entity_ids=entity_ids)
        assert result["success"] is True
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_switch_control_error_handling(self):
        """Test switch_control error handling."""
        from src.homeassistant_mcp.tools.devices.switch import register_switch_tool

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

        register_switch_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="switch.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
        assert result["error_type"] == "entity_not_found"
