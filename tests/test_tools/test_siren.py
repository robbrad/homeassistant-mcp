"""Unit tests for the siren control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.devices.siren import (
    _get_siren,
    _list_sirens,
    _toggle_siren,
    _turn_off_siren,
    _turn_on_siren,
)


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)
    return client


@pytest.fixture
def sample_siren_states():
    """Sample siren entity states for testing."""
    return [
        {
            "entity_id": "siren.alarm",
            "state": "off",
            "attributes": {
                "friendly_name": "Alarm Siren",
                "available_tones": ["fire", "ambulance", "police"],
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "siren.doorbell",
            "state": "off",
            "attributes": {
                "friendly_name": "Doorbell Siren",
                "available_tones": ["chime", "ding"],
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "switch.light",
            "state": "on",
            "attributes": {
                "friendly_name": "Light Switch",
            },
        },
    ]


class TestListSirens:
    """Tests for listing sirens."""

    @pytest.mark.asyncio
    async def test_list_sirens_success(self, mock_client, sample_siren_states):
        """Test successfully listing all sirens."""
        mock_client.get_states.return_value = sample_siren_states

        result = await _list_sirens(mock_client)

        assert result["success"] is True
        assert result["count"] == 2  # Only sirens, not the switch
        assert len(result["sirens"]) == 2

        # Verify siren data
        alarm = next(siren for siren in result["sirens"] if siren["entity_id"] == "siren.alarm")
        assert alarm["name"] == "Alarm Siren"
        assert alarm["state"] == "off"
        assert alarm["available_tones"] == ["fire", "ambulance", "police"]

    @pytest.mark.asyncio
    async def test_list_sirens_empty(self, mock_client):
        """Test listing sirens when no sirens exist."""
        mock_client.get_states.return_value = [
            {
                "entity_id": "switch.test",
                "state": "on",
                "attributes": {},
            }
        ]

        result = await _list_sirens(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["sirens"] == []


class TestGetSiren:
    """Tests for getting a specific siren."""

    @pytest.mark.asyncio
    async def test_get_siren_success(self, mock_client):
        """Test successfully getting a specific siren."""
        mock_client.get_state.return_value = {
            "entity_id": "siren.alarm",
            "state": "off",
            "attributes": {
                "friendly_name": "Alarm Siren",
                "available_tones": ["fire", "ambulance", "police"],
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_siren(mock_client, "siren.alarm")

        assert result["success"] is True
        assert result["siren"]["entity_id"] == "siren.alarm"
        assert result["siren"]["name"] == "Alarm Siren"
        assert result["siren"]["state"] == "off"
        assert result["siren"]["last_changed"] == "2024-01-01T12:00:00"

        mock_client.get_state.assert_called_once_with("siren.alarm")

    @pytest.mark.asyncio
    async def test_get_siren_not_found(self, mock_client):
        """Test getting a siren that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'siren.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_siren(mock_client, "siren.nonexistent")

    @pytest.mark.asyncio
    async def test_get_siren_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not a siren."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_siren(mock_client, "switch.light")

        assert "not a siren entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestTurnOnSiren:
    """Tests for turning on sirens."""

    @pytest.mark.asyncio
    async def test_turn_on_siren_success(self, mock_client):
        """Test successfully turning on a siren."""
        mock_client.call_service.return_value = {}

        result = await _turn_on_siren(mock_client, "siren.alarm")

        assert result["success"] is True
        assert result["entity_id"] == "siren.alarm"
        assert "turned on" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "siren", "turn_on", {"entity_id": "siren.alarm"}
        )

    @pytest.mark.asyncio
    async def test_turn_on_siren_with_tone(self, mock_client):
        """Test turning on a siren with a specific tone."""
        mock_client.call_service.return_value = {}

        result = await _turn_on_siren(mock_client, "siren.alarm", tone="fire")

        assert result["success"] is True
        assert result["entity_id"] == "siren.alarm"

        mock_client.call_service.assert_called_once_with(
            "siren", "turn_on", {"entity_id": "siren.alarm", "tone": "fire"}
        )

    @pytest.mark.asyncio
    async def test_turn_on_siren_with_volume(self, mock_client):
        """Test turning on a siren with a specific volume."""
        mock_client.call_service.return_value = {}

        result = await _turn_on_siren(mock_client, "siren.alarm", volume_level=0.8)

        assert result["success"] is True
        assert result["entity_id"] == "siren.alarm"

        mock_client.call_service.assert_called_once_with(
            "siren", "turn_on", {"entity_id": "siren.alarm", "volume_level": 0.8}
        )

    @pytest.mark.asyncio
    async def test_turn_on_siren_with_duration(self, mock_client):
        """Test turning on a siren with a specific duration."""
        mock_client.call_service.return_value = {}

        result = await _turn_on_siren(mock_client, "siren.alarm", duration=30)

        assert result["success"] is True
        assert result["entity_id"] == "siren.alarm"

        mock_client.call_service.assert_called_once_with(
            "siren", "turn_on", {"entity_id": "siren.alarm", "duration": 30}
        )

    @pytest.mark.asyncio
    async def test_turn_on_siren_with_all_options(self, mock_client):
        """Test turning on a siren with all optional parameters."""
        mock_client.call_service.return_value = {}

        result = await _turn_on_siren(
            mock_client, "siren.alarm", tone="fire", volume_level=0.9, duration=60
        )

        assert result["success"] is True
        assert result["entity_id"] == "siren.alarm"

        mock_client.call_service.assert_called_once_with(
            "siren",
            "turn_on",
            {"entity_id": "siren.alarm", "tone": "fire", "volume_level": 0.9, "duration": 60},
        )

    @pytest.mark.asyncio
    async def test_turn_on_siren_invalid_entity_type(self, mock_client):
        """Test turning on an entity that is not a siren."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _turn_on_siren(mock_client, "switch.light")

        assert "not a siren entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_on_siren_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _turn_on_siren(mock_client, "siren.alarm")


class TestTurnOffSiren:
    """Tests for turning off sirens."""

    @pytest.mark.asyncio
    async def test_turn_off_siren_success(self, mock_client):
        """Test successfully turning off a siren."""
        mock_client.call_service.return_value = {}

        result = await _turn_off_siren(mock_client, "siren.alarm")

        assert result["success"] is True
        assert result["entity_id"] == "siren.alarm"
        assert "turned off" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "siren", "turn_off", {"entity_id": "siren.alarm"}
        )

    @pytest.mark.asyncio
    async def test_turn_off_siren_invalid_entity_type(self, mock_client):
        """Test turning off an entity that is not a siren."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _turn_off_siren(mock_client, "switch.light")

        assert "not a siren entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestToggleSiren:
    """Tests for toggling sirens."""

    @pytest.mark.asyncio
    async def test_toggle_siren_success(self, mock_client):
        """Test successfully toggling a siren."""
        mock_client.call_service.return_value = {}

        result = await _toggle_siren(mock_client, "siren.alarm")

        assert result["success"] is True
        assert result["entity_id"] == "siren.alarm"
        assert "toggled" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "siren", "toggle", {"entity_id": "siren.alarm"}
        )

    @pytest.mark.asyncio
    async def test_toggle_siren_invalid_entity_type(self, mock_client):
        """Test toggling an entity that is not a siren."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _toggle_siren(mock_client, "switch.light")

        assert "not a siren entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestSirenControlIntegration:
    """Integration tests for the siren_control tool function."""

    @pytest.mark.asyncio
    async def test_siren_control_list_action(self, mock_client, sample_siren_states):
        """Test the siren_control function with list action."""
        from src.homeassistant_mcp.tools.devices.siren import register_siren_tool

        mock_client.get_states.return_value = sample_siren_states

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
        register_siren_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_siren_control_missing_entity_id(self):
        """Test siren_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.devices.siren import register_siren_tool

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

        register_siren_tool(mock_mcp, lambda: mock_client)

        # Test get without entity_id
        result = await registered_func(action="get")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test turn_on without entity_id
        result = await registered_func(action="turn_on")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test toggle without entity_id
        result = await registered_func(action="toggle")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

    @pytest.mark.asyncio
    async def test_siren_control_error_handling(self):
        """Test siren_control error handling."""
        from src.homeassistant_mcp.tools.devices.siren import register_siren_tool

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

        register_siren_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="siren.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
        assert result["error_type"] == "entity_not_found"
