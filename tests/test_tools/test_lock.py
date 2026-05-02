"""Unit tests for the lock control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.devices.lock import (
    _get_lock,
    _list_locks,
    _lock_lock,
    _unlock_lock,
)


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)
    return client


@pytest.fixture
def sample_lock_states():
    """Sample lock entity states for testing."""
    return [
        {
            "entity_id": "lock.front_door",
            "state": "locked",
            "attributes": {
                "friendly_name": "Front Door Lock",
                "battery_level": 85,
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "lock.back_door",
            "state": "unlocked",
            "attributes": {
                "friendly_name": "Back Door Lock",
                "battery_level": 60,
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "lock.garage",
            "state": "locked",
            "attributes": {
                "friendly_name": "Garage Lock",
            },
            "last_changed": "2024-01-01T10:00:00",
            "last_updated": "2024-01-01T10:00:00",
        },
        {
            "entity_id": "switch.porch_light",
            "state": "on",
            "attributes": {
                "friendly_name": "Porch Light",
            },
        },
    ]


class TestListLocks:
    """Tests for listing locks."""

    @pytest.mark.asyncio
    async def test_list_locks_success(self, mock_client, sample_lock_states):
        """Test successfully listing all locks."""
        mock_client.get_states.return_value = sample_lock_states

        result = await _list_locks(mock_client)

        assert result["success"] is True
        assert result["count"] == 3  # Only locks, not the switch
        assert len(result["locks"]) == 3

        # Verify lock data
        front_door = next(
            lock for lock in result["locks"] if lock["entity_id"] == "lock.front_door"
        )
        assert front_door["name"] == "Front Door Lock"
        assert front_door["state"] == "locked"
        assert front_door["battery_level"] == 85

        # Verify back door lock (unlocked)
        back_door = next(lock for lock in result["locks"] if lock["entity_id"] == "lock.back_door")
        assert back_door["state"] == "unlocked"
        assert back_door["battery_level"] == 60

        # Verify garage lock (no battery level)
        garage = next(lock for lock in result["locks"] if lock["entity_id"] == "lock.garage")
        assert garage["state"] == "locked"
        assert "battery_level" not in garage

    @pytest.mark.asyncio
    async def test_list_locks_empty(self, mock_client):
        """Test listing locks when no locks exist."""
        mock_client.get_states.return_value = [
            {
                "entity_id": "switch.test",
                "state": "on",
                "attributes": {},
            }
        ]

        result = await _list_locks(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["locks"] == []


class TestGetLock:
    """Tests for getting a specific lock."""

    @pytest.mark.asyncio
    async def test_get_lock_success(self, mock_client):
        """Test successfully getting a specific lock."""
        mock_client.get_state.return_value = {
            "entity_id": "lock.front_door",
            "state": "locked",
            "attributes": {
                "friendly_name": "Front Door Lock",
                "battery_level": 85,
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_lock(mock_client, "lock.front_door")

        assert result["success"] is True
        assert result["lock"]["entity_id"] == "lock.front_door"
        assert result["lock"]["name"] == "Front Door Lock"
        assert result["lock"]["state"] == "locked"
        assert result["lock"]["battery_level"] == 85
        assert result["lock"]["last_changed"] == "2024-01-01T12:00:00"

        mock_client.get_state.assert_called_once_with("lock.front_door")

    @pytest.mark.asyncio
    async def test_get_lock_without_battery(self, mock_client):
        """Test getting a lock without battery level."""
        mock_client.get_state.return_value = {
            "entity_id": "lock.garage",
            "state": "locked",
            "attributes": {
                "friendly_name": "Garage Lock",
            },
            "last_changed": "2024-01-01T10:00:00",
            "last_updated": "2024-01-01T10:00:00",
        }

        result = await _get_lock(mock_client, "lock.garage")

        assert result["success"] is True
        assert result["lock"]["entity_id"] == "lock.garage"
        assert "battery_level" not in result["lock"]

    @pytest.mark.asyncio
    async def test_get_lock_not_found(self, mock_client):
        """Test getting a lock that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'lock.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_lock(mock_client, "lock.nonexistent")

    @pytest.mark.asyncio
    async def test_get_lock_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not a lock."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_lock(mock_client, "switch.porch_light")

        assert "not a lock entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestLockLock:
    """Tests for locking locks."""

    @pytest.mark.asyncio
    async def test_lock_lock_success(self, mock_client):
        """Test successfully locking a lock."""
        mock_client.call_service.return_value = {}

        result = await _lock_lock(mock_client, "lock.front_door")

        assert result["success"] is True
        assert result["entity_id"] == "lock.front_door"
        assert "locked" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "lock", "lock", {"entity_id": "lock.front_door"}
        )

    @pytest.mark.asyncio
    async def test_lock_lock_invalid_entity_type(self, mock_client):
        """Test locking an entity that is not a lock."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _lock_lock(mock_client, "switch.porch_light")

        assert "not a lock entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_lock_lock_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _lock_lock(mock_client, "lock.front_door")


class TestUnlockLock:
    """Tests for unlocking locks."""

    @pytest.mark.asyncio
    async def test_unlock_lock_success(self, mock_client):
        """Test successfully unlocking a lock without code."""
        mock_client.call_service.return_value = {}

        result = await _unlock_lock(mock_client, "lock.front_door")

        assert result["success"] is True
        assert result["entity_id"] == "lock.front_door"
        assert "unlocked" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "lock", "unlock", {"entity_id": "lock.front_door"}
        )

    @pytest.mark.asyncio
    async def test_unlock_lock_with_code(self, mock_client):
        """Test successfully unlocking a lock with code."""
        mock_client.call_service.return_value = {}

        result = await _unlock_lock(mock_client, "lock.front_door", code="1234")

        assert result["success"] is True
        assert result["entity_id"] == "lock.front_door"
        assert "unlocked" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "lock", "unlock", {"entity_id": "lock.front_door", "code": "1234"}
        )

    @pytest.mark.asyncio
    async def test_unlock_lock_invalid_entity_type(self, mock_client):
        """Test unlocking an entity that is not a lock."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _unlock_lock(mock_client, "switch.porch_light")

        assert "not a lock entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_unlock_lock_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _unlock_lock(mock_client, "lock.front_door")

    @pytest.mark.asyncio
    async def test_unlock_lock_with_code_service_error(self, mock_client):
        """Test handling service call errors with code."""
        mock_client.call_service.side_effect = ServiceCallError("Invalid code")

        with pytest.raises(ServiceCallError):
            await _unlock_lock(mock_client, "lock.front_door", code="9999")


class TestLockControlIntegration:
    """Integration tests for the lock_control tool function."""

    @pytest.mark.asyncio
    async def test_lock_control_list_action(self, mock_client, sample_lock_states):
        """Test the lock_control function with list action."""
        from src.homeassistant_mcp.tools.devices.lock import register_lock_tool

        mock_client.get_states.return_value = sample_lock_states

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
        register_lock_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_lock_control_missing_entity_id(self):
        """Test lock_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.devices.lock import register_lock_tool

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

        register_lock_tool(mock_mcp, lambda: mock_client)

        # Test get without entity_id
        result = await registered_func(action="get")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test lock without entity_id
        result = await registered_func(action="lock")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test unlock without entity_id
        result = await registered_func(action="unlock")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

    @pytest.mark.asyncio
    async def test_lock_control_lock_action(self):
        """Test lock_control with lock action."""
        from src.homeassistant_mcp.tools.devices.lock import register_lock_tool

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

        register_lock_tool(mock_mcp, lambda: mock_client)

        # Test lock action
        result = await registered_func(action="lock", entity_id="lock.front_door")
        assert result["success"] is True
        assert result["entity_id"] == "lock.front_door"

    @pytest.mark.asyncio
    async def test_lock_control_unlock_action(self):
        """Test lock_control with unlock action."""
        from src.homeassistant_mcp.tools.devices.lock import register_lock_tool

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

        register_lock_tool(mock_mcp, lambda: mock_client)

        # Test unlock without code
        result = await registered_func(action="unlock", entity_id="lock.front_door")
        assert result["success"] is True
        assert result["entity_id"] == "lock.front_door"

        # Test unlock with code
        result = await registered_func(action="unlock", entity_id="lock.front_door", code="1234")
        assert result["success"] is True
        assert result["entity_id"] == "lock.front_door"

    @pytest.mark.asyncio
    async def test_lock_control_error_handling(self):
        """Test lock_control error handling."""
        from src.homeassistant_mcp.tools.devices.lock import register_lock_tool

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

        register_lock_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="lock.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
        assert result["error_type"] == "entity_not_found"
