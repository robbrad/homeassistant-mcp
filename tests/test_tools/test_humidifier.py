"""Unit tests for the humidifier control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.devices.humidifier import (
    _get_humidifier,
    _list_humidifiers,
    _set_humidity,
    _set_mode,
    _turn_off_humidifier,
    _turn_on_humidifier,
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
def sample_humidifier_states():
    """Sample humidifier entity states for testing."""
    return [
        {
            "entity_id": "humidifier.bedroom",
            "state": "on",
            "attributes": {
                "friendly_name": "Bedroom Humidifier",
                "humidity": 45,
                "mode": "normal",
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "humidifier.living_room",
            "state": "off",
            "attributes": {
                "friendly_name": "Living Room Humidifier",
                "humidity": 50,
                "mode": "eco",
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "fan.ceiling",
            "state": "on",
            "attributes": {
                "friendly_name": "Ceiling Fan",
            },
        },
    ]


class TestListHumidifiers:
    """Tests for listing humidifiers."""

    @pytest.mark.asyncio
    async def test_list_humidifiers_success(self, mock_client, sample_humidifier_states):
        """Test successfully listing all humidifiers."""
        mock_client._states_data = sample_humidifier_states

        result = await _list_humidifiers(mock_client)

        assert result["success"] is True
        assert result["count"] == 2  # Only humidifiers, not the fan
        assert len(result["humidifiers"]) == 2

        # Verify humidifier data
        bedroom = next(
            hum for hum in result["humidifiers"] if hum["entity_id"] == "humidifier.bedroom"
        )
        assert bedroom["name"] == "Bedroom Humidifier"
        assert bedroom["state"] == "on"
        assert bedroom["current_humidity"] == 45
        assert bedroom["mode"] == "normal"

    @pytest.mark.asyncio
    async def test_list_humidifiers_empty(self, mock_client):
        """Test listing humidifiers when no humidifiers exist."""
        mock_client._states_data = [
            {
                "entity_id": "fan.test",
                "state": "on",
                "attributes": {},
            }
        ]

        result = await _list_humidifiers(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["humidifiers"] == []


class TestGetHumidifier:
    """Tests for getting a specific humidifier."""

    @pytest.mark.asyncio
    async def test_get_humidifier_success(self, mock_client):
        """Test successfully getting a specific humidifier."""
        mock_client.get_state.return_value = {
            "entity_id": "humidifier.bedroom",
            "state": "on",
            "attributes": {
                "friendly_name": "Bedroom Humidifier",
                "humidity": 45,
                "mode": "normal",
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_humidifier(mock_client, "humidifier.bedroom")

        assert result["success"] is True
        assert result["humidifier"]["entity_id"] == "humidifier.bedroom"
        assert result["humidifier"]["name"] == "Bedroom Humidifier"
        assert result["humidifier"]["state"] == "on"
        assert result["humidifier"]["last_changed"] == "2024-01-01T12:00:00"

        mock_client.get_state.assert_called_once_with("humidifier.bedroom")

    @pytest.mark.asyncio
    async def test_get_humidifier_not_found(self, mock_client):
        """Test getting a humidifier that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'humidifier.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_humidifier(mock_client, "humidifier.nonexistent")

    @pytest.mark.asyncio
    async def test_get_humidifier_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not a humidifier."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_humidifier(mock_client, "fan.ceiling")

        assert "not a humidifier entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestTurnOnHumidifier:
    """Tests for turning on humidifiers."""

    @pytest.mark.asyncio
    async def test_turn_on_humidifier_success(self, mock_client):
        """Test successfully turning on a humidifier."""
        mock_client.call_service.return_value = {}

        result = await _turn_on_humidifier(mock_client, "humidifier.bedroom")

        assert result["success"] is True
        assert result["entity_id"] == "humidifier.bedroom"
        assert "turned on" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "humidifier", "turn_on", {"entity_id": "humidifier.bedroom"}
        )

    @pytest.mark.asyncio
    async def test_turn_on_humidifier_invalid_entity_type(self, mock_client):
        """Test turning on an entity that is not a humidifier."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _turn_on_humidifier(mock_client, "fan.ceiling")

        assert "not a humidifier entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_on_humidifier_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _turn_on_humidifier(mock_client, "humidifier.bedroom")


class TestTurnOffHumidifier:
    """Tests for turning off humidifiers."""

    @pytest.mark.asyncio
    async def test_turn_off_humidifier_success(self, mock_client):
        """Test successfully turning off a humidifier."""
        mock_client.call_service.return_value = {}

        result = await _turn_off_humidifier(mock_client, "humidifier.bedroom")

        assert result["success"] is True
        assert result["entity_id"] == "humidifier.bedroom"
        assert "turned off" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "humidifier", "turn_off", {"entity_id": "humidifier.bedroom"}
        )

    @pytest.mark.asyncio
    async def test_turn_off_humidifier_invalid_entity_type(self, mock_client):
        """Test turning off an entity that is not a humidifier."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _turn_off_humidifier(mock_client, "fan.ceiling")

        assert "not a humidifier entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestSetHumidity:
    """Tests for setting humidifier humidity."""

    @pytest.mark.asyncio
    async def test_set_humidity_success(self, mock_client):
        """Test successfully setting humidifier humidity."""
        mock_client.call_service.return_value = {}

        result = await _set_humidity(mock_client, "humidifier.bedroom", 60)

        assert result["success"] is True
        assert result["entity_id"] == "humidifier.bedroom"
        assert result["humidity"] == 60
        assert "humidity set to 60%" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "humidifier", "set_humidity", {"entity_id": "humidifier.bedroom", "humidity": 60}
        )

    @pytest.mark.asyncio
    async def test_set_humidity_invalid_entity_type(self, mock_client):
        """Test setting humidity for an entity that is not a humidifier."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _set_humidity(mock_client, "fan.ceiling", 60)

        assert "not a humidifier entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestSetMode:
    """Tests for setting humidifier mode."""

    @pytest.mark.asyncio
    async def test_set_mode_success(self, mock_client):
        """Test successfully setting humidifier mode."""
        mock_client.call_service.return_value = {}

        result = await _set_mode(mock_client, "humidifier.bedroom", "eco")

        assert result["success"] is True
        assert result["entity_id"] == "humidifier.bedroom"
        assert result["mode"] == "eco"
        assert "mode set to 'eco'" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "humidifier", "set_mode", {"entity_id": "humidifier.bedroom", "mode": "eco"}
        )

    @pytest.mark.asyncio
    async def test_set_mode_invalid_entity_type(self, mock_client):
        """Test setting mode for an entity that is not a humidifier."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _set_mode(mock_client, "fan.ceiling", "eco")

        assert "not a humidifier entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestHumidifierControlIntegration:
    """Integration tests for the humidifier_control tool function."""

    @pytest.mark.asyncio
    async def test_humidifier_control_list_action(self, mock_client, sample_humidifier_states):
        """Test the humidifier_control function with list action."""
        from src.homeassistant_mcp.tools.devices.humidifier import register_humidifier_tool

        mock_client._states_data = sample_humidifier_states

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
        register_humidifier_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_humidifier_control_missing_entity_id(self):
        """Test humidifier_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.devices.humidifier import register_humidifier_tool

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

        register_humidifier_tool(mock_mcp, lambda: mock_client)

        # Test get without entity_id
        result = await registered_func(action="get")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test set_humidity without humidity
        result = await registered_func(action="set_humidity", entity_id="humidifier.bedroom")
        assert result["success"] is False
        assert "humidity is required" in result["error"]

        # Test set_mode without mode
        result = await registered_func(action="set_mode", entity_id="humidifier.bedroom")
        assert result["success"] is False
        assert "mode is required" in result["error"]

    @pytest.mark.asyncio
    async def test_humidifier_control_error_handling(self):
        """Test humidifier_control error handling."""
        from src.homeassistant_mcp.tools.devices.humidifier import register_humidifier_tool

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

        register_humidifier_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="humidifier.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
        assert result["error_type"] == "entity_not_found"
