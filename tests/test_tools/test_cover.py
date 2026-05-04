"""Unit tests for the cover control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.devices.cover import (
    _close_cover,
    _get_cover,
    _list_covers,
    _open_cover,
    _set_cover_position,
    _set_cover_tilt,
    _stop_cover,
    _toggle_cover,
)


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)
    return client


@pytest.fixture
def sample_cover_states():
    """Sample cover entity states for testing."""
    return [
        {
            "entity_id": "cover.living_room_blinds",
            "state": "open",
            "attributes": {
                "friendly_name": "Living Room Blinds",
                "current_position": 100,
                "current_tilt_position": 50,
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "cover.bedroom_blinds",
            "state": "closed",
            "attributes": {
                "friendly_name": "Bedroom Blinds",
                "current_position": 0,
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "cover.garage_door",
            "state": "open",
            "attributes": {
                "friendly_name": "Garage Door",
            },
            "last_changed": "2024-01-01T10:00:00",
            "last_updated": "2024-01-01T10:00:00",
        },
        {
            "entity_id": "light.hallway",
            "state": "on",
            "attributes": {
                "friendly_name": "Hallway Light",
            },
        },
    ]


class TestListCovers:
    """Tests for listing covers."""

    @pytest.mark.asyncio
    async def test_list_covers_success(self, mock_client, sample_cover_states):
        """Test successfully listing all covers."""
        mock_client.get_states.return_value = sample_cover_states

        result = await _list_covers(mock_client)

        assert result["success"] is True
        assert result["count"] == 3  # Only covers, not the light
        assert len(result["covers"]) == 3

        # Verify cover data with position and tilt
        living_room = next(
            cover for cover in result["covers"] if cover["entity_id"] == "cover.living_room_blinds"
        )
        assert living_room["name"] == "Living Room Blinds"
        assert living_room["state"] == "open"
        assert living_room["current_position"] == 100
        assert living_room["current_tilt_position"] == 50

        # Verify bedroom cover (no tilt)
        bedroom = next(
            cover for cover in result["covers"] if cover["entity_id"] == "cover.bedroom_blinds"
        )
        assert bedroom["state"] == "closed"
        assert bedroom["current_position"] == 0
        assert "current_tilt_position" not in bedroom

        # Verify garage door (no position or tilt)
        garage = next(
            cover for cover in result["covers"] if cover["entity_id"] == "cover.garage_door"
        )
        assert garage["state"] == "open"
        assert "current_position" not in garage
        assert "current_tilt_position" not in garage

    @pytest.mark.asyncio
    async def test_list_covers_empty(self, mock_client):
        """Test listing covers when no covers exist."""
        mock_client.get_states.return_value = [
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {},
            }
        ]

        result = await _list_covers(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["covers"] == []


class TestGetCover:
    """Tests for getting a specific cover."""

    @pytest.mark.asyncio
    async def test_get_cover_success(self, mock_client):
        """Test successfully getting a specific cover."""
        mock_client.get_state.return_value = {
            "entity_id": "cover.living_room_blinds",
            "state": "open",
            "attributes": {
                "friendly_name": "Living Room Blinds",
                "current_position": 75,
                "current_tilt_position": 50,
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_cover(mock_client, "cover.living_room_blinds")

        assert result["success"] is True
        assert result["cover"]["entity_id"] == "cover.living_room_blinds"
        assert result["cover"]["name"] == "Living Room Blinds"
        assert result["cover"]["state"] == "open"
        assert result["cover"]["current_position"] == 75
        assert result["cover"]["current_tilt_position"] == 50
        assert result["cover"]["last_changed"] == "2024-01-01T12:00:00"

        mock_client.get_state.assert_called_once_with("cover.living_room_blinds")

    @pytest.mark.asyncio
    async def test_get_cover_without_position(self, mock_client):
        """Test getting a cover without position support."""
        mock_client.get_state.return_value = {
            "entity_id": "cover.garage_door",
            "state": "closed",
            "attributes": {
                "friendly_name": "Garage Door",
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_cover(mock_client, "cover.garage_door")

        assert result["success"] is True
        assert result["cover"]["entity_id"] == "cover.garage_door"
        assert "current_position" not in result["cover"]
        assert "current_tilt_position" not in result["cover"]

    @pytest.mark.asyncio
    async def test_get_cover_not_found(self, mock_client):
        """Test getting a cover that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'cover.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_cover(mock_client, "cover.nonexistent")

    @pytest.mark.asyncio
    async def test_get_cover_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not a cover."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_cover(mock_client, "light.hallway")

        assert "not a cover entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestOpenCover:
    """Tests for opening covers."""

    @pytest.mark.asyncio
    async def test_open_cover_success(self, mock_client):
        """Test successfully opening a cover."""
        mock_client.call_service.return_value = {}

        result = await _open_cover(mock_client, "cover.living_room_blinds")

        assert result["success"] is True
        assert result["entity_id"] == "cover.living_room_blinds"
        assert "opened" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "cover", "open_cover", {"entity_id": "cover.living_room_blinds"}
        )

    @pytest.mark.asyncio
    async def test_open_cover_invalid_entity_type(self, mock_client):
        """Test opening an entity that is not a cover."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _open_cover(mock_client, "light.hallway")

        assert "not a cover entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_open_cover_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _open_cover(mock_client, "cover.living_room_blinds")


class TestCloseCover:
    """Tests for closing covers."""

    @pytest.mark.asyncio
    async def test_close_cover_success(self, mock_client):
        """Test successfully closing a cover."""
        mock_client.call_service.return_value = {}

        result = await _close_cover(mock_client, "cover.bedroom_blinds")

        assert result["success"] is True
        assert result["entity_id"] == "cover.bedroom_blinds"
        assert "closed" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "cover", "close_cover", {"entity_id": "cover.bedroom_blinds"}
        )

    @pytest.mark.asyncio
    async def test_close_cover_invalid_entity_type(self, mock_client):
        """Test closing an entity that is not a cover."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _close_cover(mock_client, "switch.fan")

        assert "not a cover entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_close_cover_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _close_cover(mock_client, "cover.bedroom_blinds")


class TestStopCover:
    """Tests for stopping covers."""

    @pytest.mark.asyncio
    async def test_stop_cover_success(self, mock_client):
        """Test successfully stopping a cover."""
        mock_client.call_service.return_value = {}

        result = await _stop_cover(mock_client, "cover.living_room_blinds")

        assert result["success"] is True
        assert result["entity_id"] == "cover.living_room_blinds"
        assert "stopped" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "cover", "stop_cover", {"entity_id": "cover.living_room_blinds"}
        )

    @pytest.mark.asyncio
    async def test_stop_cover_invalid_entity_type(self, mock_client):
        """Test stopping an entity that is not a cover."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _stop_cover(mock_client, "fan.ceiling")

        assert "not a cover entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_cover_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _stop_cover(mock_client, "cover.living_room_blinds")


class TestToggleCover:
    """Tests for toggling covers."""

    @pytest.mark.asyncio
    async def test_toggle_cover_success(self, mock_client):
        """Test successfully toggling a cover."""
        mock_client.call_service.return_value = {}

        result = await _toggle_cover(mock_client, "cover.garage_door")

        assert result["success"] is True
        assert result["entity_id"] == "cover.garage_door"
        assert "toggled" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "cover", "toggle", {"entity_id": "cover.garage_door"}
        )

    @pytest.mark.asyncio
    async def test_toggle_cover_invalid_entity_type(self, mock_client):
        """Test toggling an entity that is not a cover."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _toggle_cover(mock_client, "lock.front_door")

        assert "not a cover entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_toggle_cover_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _toggle_cover(mock_client, "cover.garage_door")


class TestSetCoverPosition:
    """Tests for setting cover position."""

    @pytest.mark.asyncio
    async def test_set_cover_position_success(self, mock_client):
        """Test successfully setting cover position."""
        mock_client.call_service.return_value = {}

        result = await _set_cover_position(mock_client, "cover.living_room_blinds", 50)

        assert result["success"] is True
        assert result["entity_id"] == "cover.living_room_blinds"
        assert result["position"] == 50
        assert "position set to 50" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "cover", "set_cover_position", {"entity_id": "cover.living_room_blinds", "position": 50}
        )

    @pytest.mark.asyncio
    async def test_set_cover_position_fully_open(self, mock_client):
        """Test setting cover to fully open position."""
        mock_client.call_service.return_value = {}

        result = await _set_cover_position(mock_client, "cover.bedroom_blinds", 100)

        assert result["success"] is True
        assert result["position"] == 100

        mock_client.call_service.assert_called_once_with(
            "cover", "set_cover_position", {"entity_id": "cover.bedroom_blinds", "position": 100}
        )

    @pytest.mark.asyncio
    async def test_set_cover_position_fully_closed(self, mock_client):
        """Test setting cover to fully closed position."""
        mock_client.call_service.return_value = {}

        result = await _set_cover_position(mock_client, "cover.bedroom_blinds", 0)

        assert result["success"] is True
        assert result["position"] == 0

        mock_client.call_service.assert_called_once_with(
            "cover", "set_cover_position", {"entity_id": "cover.bedroom_blinds", "position": 0}
        )

    @pytest.mark.asyncio
    async def test_set_cover_position_invalid_entity_type(self, mock_client):
        """Test setting position for an entity that is not a cover."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _set_cover_position(mock_client, "light.hallway", 50)

        assert "not a cover entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_cover_position_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _set_cover_position(mock_client, "cover.living_room_blinds", 50)


class TestSetCoverTilt:
    """Tests for setting cover tilt."""

    @pytest.mark.asyncio
    async def test_set_cover_tilt_success(self, mock_client):
        """Test successfully setting cover tilt."""
        mock_client.call_service.return_value = {}

        result = await _set_cover_tilt(mock_client, "cover.living_room_blinds", 75)

        assert result["success"] is True
        assert result["entity_id"] == "cover.living_room_blinds"
        assert result["tilt"] == 75
        assert "tilt set to 75" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "cover",
            "set_cover_tilt_position",
            {"entity_id": "cover.living_room_blinds", "tilt_position": 75},
        )

    @pytest.mark.asyncio
    async def test_set_cover_tilt_minimum(self, mock_client):
        """Test setting cover tilt to minimum."""
        mock_client.call_service.return_value = {}

        result = await _set_cover_tilt(mock_client, "cover.bedroom_blinds", 0)

        assert result["success"] is True
        assert result["tilt"] == 0

        mock_client.call_service.assert_called_once_with(
            "cover",
            "set_cover_tilt_position",
            {"entity_id": "cover.bedroom_blinds", "tilt_position": 0},
        )

    @pytest.mark.asyncio
    async def test_set_cover_tilt_maximum(self, mock_client):
        """Test setting cover tilt to maximum."""
        mock_client.call_service.return_value = {}

        result = await _set_cover_tilt(mock_client, "cover.bedroom_blinds", 100)

        assert result["success"] is True
        assert result["tilt"] == 100

        mock_client.call_service.assert_called_once_with(
            "cover",
            "set_cover_tilt_position",
            {"entity_id": "cover.bedroom_blinds", "tilt_position": 100},
        )

    @pytest.mark.asyncio
    async def test_set_cover_tilt_invalid_entity_type(self, mock_client):
        """Test setting tilt for an entity that is not a cover."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _set_cover_tilt(mock_client, "switch.fan", 50)

        assert "not a cover entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_cover_tilt_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _set_cover_tilt(mock_client, "cover.living_room_blinds", 75)


class TestCoverControlIntegration:
    """Integration tests for the cover_control tool function."""

    @pytest.mark.asyncio
    async def test_cover_control_list_action(self, mock_client, sample_cover_states):
        """Test the cover_control function with list action."""
        from src.homeassistant_mcp.tools.devices.cover import register_cover_tool

        mock_client.get_states.return_value = sample_cover_states

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
        register_cover_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_cover_control_missing_entity_id(self):
        """Test cover_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.devices.cover import register_cover_tool

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

        register_cover_tool(mock_mcp, lambda: mock_client)

        # Test get without entity_id
        result = await registered_func(action="get")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test open without entity_id
        result = await registered_func(action="open")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test close without entity_id
        result = await registered_func(action="close")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test stop without entity_id
        result = await registered_func(action="stop")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test toggle without entity_id
        result = await registered_func(action="toggle")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

    @pytest.mark.asyncio
    async def test_cover_control_missing_position_parameter(self):
        """Test cover_control set_position without position parameter."""
        from src.homeassistant_mcp.tools.devices.cover import register_cover_tool

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

        register_cover_tool(mock_mcp, lambda: mock_client)

        # Test set_position without position
        result = await registered_func(action="set_position", entity_id="cover.test")
        assert result["success"] is False
        assert "position parameter is required" in result["error"]

    @pytest.mark.asyncio
    async def test_cover_control_missing_tilt_parameter(self):
        """Test cover_control set_tilt without tilt parameter."""
        from src.homeassistant_mcp.tools.devices.cover import register_cover_tool

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

        register_cover_tool(mock_mcp, lambda: mock_client)

        # Test set_tilt without tilt
        result = await registered_func(action="set_tilt", entity_id="cover.test")
        assert result["success"] is False
        assert "tilt parameter is required" in result["error"]

    @pytest.mark.asyncio
    async def test_cover_control_error_handling(self):
        """Test cover_control error handling."""
        from src.homeassistant_mcp.tools.devices.cover import register_cover_tool

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

        register_cover_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="cover.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
        assert result["error_type"] == "entity_not_found"
