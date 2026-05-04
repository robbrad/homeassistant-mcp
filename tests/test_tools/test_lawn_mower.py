"""Unit tests for the lawn mower control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.devices.lawn_mower import (
    _dock_mower,
    _get_lawn_mower,
    _list_lawn_mowers,
    _pause_mowing,
    _start_mowing,
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
def sample_lawn_mower_states():
    """Sample lawn mower entity states for testing."""
    return [
        {
            "entity_id": "lawn_mower.backyard",
            "state": "mowing",
            "attributes": {
                "friendly_name": "Backyard Lawn Mower",
                "battery_level": 85,
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "lawn_mower.front_yard",
            "state": "docked",
            "attributes": {
                "friendly_name": "Front Yard Lawn Mower",
                "battery_level": 100,
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "vacuum.robot",
            "state": "cleaning",
            "attributes": {
                "friendly_name": "Robot Vacuum",
            },
        },
    ]


class TestListLawnMowers:
    """Tests for listing lawn mowers."""

    @pytest.mark.asyncio
    async def test_list_lawn_mowers_success(self, mock_client, sample_lawn_mower_states):
        """Test successfully listing all lawn mowers."""
        mock_client._states_data = sample_lawn_mower_states

        result = await _list_lawn_mowers(mock_client)

        assert result["success"] is True
        assert result["count"] == 2  # Only lawn mowers, not the vacuum
        assert len(result["lawn_mowers"]) == 2

        # Verify lawn mower data
        backyard = next(
            mower for mower in result["lawn_mowers"] if mower["entity_id"] == "lawn_mower.backyard"
        )
        assert backyard["name"] == "Backyard Lawn Mower"
        assert backyard["state"] == "mowing"
        assert backyard["battery_level"] == 85

    @pytest.mark.asyncio
    async def test_list_lawn_mowers_empty(self, mock_client):
        """Test listing lawn mowers when no lawn mowers exist."""
        mock_client._states_data = [
            {
                "entity_id": "vacuum.test",
                "state": "cleaning",
                "attributes": {},
            }
        ]

        result = await _list_lawn_mowers(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["lawn_mowers"] == []


class TestGetLawnMower:
    """Tests for getting a specific lawn mower."""

    @pytest.mark.asyncio
    async def test_get_lawn_mower_success(self, mock_client):
        """Test successfully getting a specific lawn mower."""
        mock_client.get_state.return_value = {
            "entity_id": "lawn_mower.backyard",
            "state": "mowing",
            "attributes": {
                "friendly_name": "Backyard Lawn Mower",
                "battery_level": 85,
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_lawn_mower(mock_client, "lawn_mower.backyard")

        assert result["success"] is True
        assert result["lawn_mower"]["entity_id"] == "lawn_mower.backyard"
        assert result["lawn_mower"]["name"] == "Backyard Lawn Mower"
        assert result["lawn_mower"]["state"] == "mowing"
        assert result["lawn_mower"]["last_changed"] == "2024-01-01T12:00:00"

        mock_client.get_state.assert_called_once_with("lawn_mower.backyard")

    @pytest.mark.asyncio
    async def test_get_lawn_mower_not_found(self, mock_client):
        """Test getting a lawn mower that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'lawn_mower.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_lawn_mower(mock_client, "lawn_mower.nonexistent")

    @pytest.mark.asyncio
    async def test_get_lawn_mower_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not a lawn mower."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_lawn_mower(mock_client, "vacuum.robot")

        assert "not a lawn mower entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestStartMowing:
    """Tests for starting lawn mowers."""

    @pytest.mark.asyncio
    async def test_start_mowing_success(self, mock_client):
        """Test successfully starting a lawn mower."""
        mock_client.call_service.return_value = {}

        result = await _start_mowing(mock_client, "lawn_mower.backyard")

        assert result["success"] is True
        assert result["entity_id"] == "lawn_mower.backyard"
        assert "started mowing" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "lawn_mower", "start_mowing", {"entity_id": "lawn_mower.backyard"}
        )

    @pytest.mark.asyncio
    async def test_start_mowing_invalid_entity_type(self, mock_client):
        """Test starting an entity that is not a lawn mower."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _start_mowing(mock_client, "vacuum.robot")

        assert "not a lawn mower entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_mowing_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _start_mowing(mock_client, "lawn_mower.backyard")


class TestPauseMowing:
    """Tests for pausing lawn mowers."""

    @pytest.mark.asyncio
    async def test_pause_mowing_success(self, mock_client):
        """Test successfully pausing a lawn mower."""
        mock_client.call_service.return_value = {}

        result = await _pause_mowing(mock_client, "lawn_mower.backyard")

        assert result["success"] is True
        assert result["entity_id"] == "lawn_mower.backyard"
        assert "paused" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "lawn_mower", "pause", {"entity_id": "lawn_mower.backyard"}
        )

    @pytest.mark.asyncio
    async def test_pause_mowing_invalid_entity_type(self, mock_client):
        """Test pausing an entity that is not a lawn mower."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _pause_mowing(mock_client, "vacuum.robot")

        assert "not a lawn mower entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestDockMower:
    """Tests for docking lawn mowers."""

    @pytest.mark.asyncio
    async def test_dock_mower_success(self, mock_client):
        """Test successfully docking a lawn mower."""
        mock_client.call_service.return_value = {}

        result = await _dock_mower(mock_client, "lawn_mower.backyard")

        assert result["success"] is True
        assert result["entity_id"] == "lawn_mower.backyard"
        assert "returning to dock" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "lawn_mower", "dock", {"entity_id": "lawn_mower.backyard"}
        )

    @pytest.mark.asyncio
    async def test_dock_mower_invalid_entity_type(self, mock_client):
        """Test docking an entity that is not a lawn mower."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _dock_mower(mock_client, "vacuum.robot")

        assert "not a lawn mower entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestLawnMowerControlIntegration:
    """Integration tests for the lawn_mower_control tool function."""

    @pytest.mark.asyncio
    async def test_lawn_mower_control_list_action(self, mock_client, sample_lawn_mower_states):
        """Test the lawn_mower_control function with list action."""
        from src.homeassistant_mcp.tools.devices.lawn_mower import register_lawn_mower_tool

        mock_client._states_data = sample_lawn_mower_states

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
        register_lawn_mower_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_lawn_mower_control_missing_entity_id(self):
        """Test lawn_mower_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.devices.lawn_mower import register_lawn_mower_tool

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

        register_lawn_mower_tool(mock_mcp, lambda: mock_client)

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

        # Test dock without entity_id
        result = await registered_func(action="dock")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

    @pytest.mark.asyncio
    async def test_lawn_mower_control_error_handling(self):
        """Test lawn_mower_control error handling."""
        from src.homeassistant_mcp.tools.devices.lawn_mower import register_lawn_mower_tool

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

        register_lawn_mower_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="lawn_mower.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
        assert result["error_type"] == "entity_not_found"
