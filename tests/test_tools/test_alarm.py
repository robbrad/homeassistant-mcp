"""Unit tests for the alarm control panel tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.exceptions import (
    AuthenticationError,
    ConnectionError,
    EntityNotFoundError,
    ServiceCallError,
)
from src.homeassistant_mcp.hass.client import HomeAssistantClient
from src.homeassistant_mcp.tools.devices.alarm import (
    _arm_alarm,
    _disarm_alarm,
    _get_alarm,
    _list_alarms,
    _trigger_alarm,
)


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)
    return client


@pytest.fixture
def sample_alarm_states():
    """Sample alarm control panel entity states for testing."""
    return [
        {
            "entity_id": "alarm_control_panel.home",
            "state": "disarmed",
            "attributes": {
                "friendly_name": "Home Alarm",
                "code_format": "number",
                "supported_features": 15,
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "alarm_control_panel.garage",
            "state": "armed_away",
            "attributes": {
                "friendly_name": "Garage Alarm",
                "code_format": "number",
                "supported_features": 7,
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "alarm_control_panel.office",
            "state": "armed_home",
            "attributes": {
                "friendly_name": "Office Alarm",
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


class TestListAlarms:
    """Tests for listing alarm control panels."""

    @pytest.mark.asyncio
    async def test_list_alarms_success(self, mock_client, sample_alarm_states):
        """Test successfully listing all alarm control panels."""
        mock_client.get_states.return_value = sample_alarm_states

        result = await _list_alarms(mock_client)

        assert result["success"] is True
        assert result["count"] == 3  # Only alarms, not the light
        assert len(result["alarms"]) == 3

        # Verify alarm data
        home_alarm = next(
            alarm for alarm in result["alarms"] if alarm["entity_id"] == "alarm_control_panel.home"
        )
        assert home_alarm["name"] == "Home Alarm"
        assert home_alarm["state"] == "disarmed"
        assert home_alarm["code_format"] == "number"
        assert home_alarm["supported_features"] == 15

        # Verify garage alarm (armed_away)
        garage_alarm = next(
            alarm
            for alarm in result["alarms"]
            if alarm["entity_id"] == "alarm_control_panel.garage"
        )
        assert garage_alarm["state"] == "armed_away"

        # Verify office alarm (no code_format)
        office_alarm = next(
            alarm
            for alarm in result["alarms"]
            if alarm["entity_id"] == "alarm_control_panel.office"
        )
        assert "code_format" not in office_alarm

    @pytest.mark.asyncio
    async def test_list_alarms_empty(self, mock_client):
        """Test listing alarms when no alarms exist."""
        mock_client.get_states.return_value = [
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {},
            }
        ]

        result = await _list_alarms(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["alarms"] == []


class TestGetAlarm:
    """Tests for getting a specific alarm control panel."""

    @pytest.mark.asyncio
    async def test_get_alarm_success(self, mock_client):
        """Test successfully getting a specific alarm control panel."""
        mock_client.get_state.return_value = {
            "entity_id": "alarm_control_panel.home",
            "state": "disarmed",
            "attributes": {
                "friendly_name": "Home Alarm",
                "code_format": "number",
                "supported_features": 15,
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_alarm(mock_client, "alarm_control_panel.home")

        assert result["success"] is True
        assert result["alarm"]["entity_id"] == "alarm_control_panel.home"
        assert result["alarm"]["name"] == "Home Alarm"
        assert result["alarm"]["state"] == "disarmed"
        assert result["alarm"]["code_format"] == "number"
        assert result["alarm"]["last_changed"] == "2024-01-01T12:00:00"

        mock_client.get_state.assert_called_once_with("alarm_control_panel.home")

    @pytest.mark.asyncio
    async def test_get_alarm_not_found(self, mock_client):
        """Test getting an alarm that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'alarm_control_panel.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_alarm(mock_client, "alarm_control_panel.nonexistent")

    @pytest.mark.asyncio
    async def test_get_alarm_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not an alarm control panel."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_alarm(mock_client, "light.garage")

        assert "not an alarm control panel entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestArmAlarm:
    """Tests for arming alarm control panels."""

    @pytest.mark.asyncio
    async def test_arm_away_success(self, mock_client):
        """Test successfully arming an alarm in away mode."""
        mock_client.call_service.return_value = {}

        result = await _arm_alarm(mock_client, "alarm_control_panel.home", "arm_away")

        assert result["success"] is True
        assert result["entity_id"] == "alarm_control_panel.home"
        assert result["mode"] == "away"
        assert "armed" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "alarm_control_panel", "arm_away", {"entity_id": "alarm_control_panel.home"}
        )

    @pytest.mark.asyncio
    async def test_arm_away_with_code(self, mock_client):
        """Test arming an alarm in away mode with a code."""
        mock_client.call_service.return_value = {}

        result = await _arm_alarm(mock_client, "alarm_control_panel.home", "arm_away", code="1234")

        assert result["success"] is True
        assert result["entity_id"] == "alarm_control_panel.home"
        assert result["mode"] == "away"

        mock_client.call_service.assert_called_once_with(
            "alarm_control_panel",
            "arm_away",
            {"entity_id": "alarm_control_panel.home", "code": "1234"},
        )

    @pytest.mark.asyncio
    async def test_arm_home_success(self, mock_client):
        """Test successfully arming an alarm in home mode."""
        mock_client.call_service.return_value = {}

        result = await _arm_alarm(mock_client, "alarm_control_panel.home", "arm_home")

        assert result["success"] is True
        assert result["entity_id"] == "alarm_control_panel.home"
        assert result["mode"] == "home"

        mock_client.call_service.assert_called_once_with(
            "alarm_control_panel", "arm_home", {"entity_id": "alarm_control_panel.home"}
        )

    @pytest.mark.asyncio
    async def test_arm_night_success(self, mock_client):
        """Test successfully arming an alarm in night mode."""
        mock_client.call_service.return_value = {}

        result = await _arm_alarm(mock_client, "alarm_control_panel.home", "arm_night")

        assert result["success"] is True
        assert result["entity_id"] == "alarm_control_panel.home"
        assert result["mode"] == "night"

        mock_client.call_service.assert_called_once_with(
            "alarm_control_panel", "arm_night", {"entity_id": "alarm_control_panel.home"}
        )

    @pytest.mark.asyncio
    async def test_arm_alarm_invalid_entity_type(self, mock_client):
        """Test arming an entity that is not an alarm control panel."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _arm_alarm(mock_client, "light.garage", "arm_away")

        assert "not an alarm control panel entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_arm_alarm_service_error(self, mock_client):
        """Test handling service call errors when arming."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _arm_alarm(mock_client, "alarm_control_panel.home", "arm_away")


class TestDisarmAlarm:
    """Tests for disarming alarm control panels."""

    @pytest.mark.asyncio
    async def test_disarm_alarm_success(self, mock_client):
        """Test successfully disarming an alarm."""
        mock_client.call_service.return_value = {}

        result = await _disarm_alarm(mock_client, "alarm_control_panel.home", "1234")

        assert result["success"] is True
        assert result["entity_id"] == "alarm_control_panel.home"
        assert "disarmed" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "alarm_control_panel",
            "disarm",
            {"entity_id": "alarm_control_panel.home", "code": "1234"},
        )

    @pytest.mark.asyncio
    async def test_disarm_alarm_invalid_entity_type(self, mock_client):
        """Test disarming an entity that is not an alarm control panel."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _disarm_alarm(mock_client, "light.garage", "1234")

        assert "not an alarm control panel entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_disarm_alarm_service_error(self, mock_client):
        """Test handling service call errors when disarming (e.g., invalid code)."""
        mock_client.call_service.side_effect = ServiceCallError("Invalid code")

        with pytest.raises(ServiceCallError):
            await _disarm_alarm(mock_client, "alarm_control_panel.home", "9999")

    @pytest.mark.asyncio
    async def test_disarm_alarm_authentication_error(self, mock_client):
        """Test handling authentication errors when disarming."""
        mock_client.call_service.side_effect = AuthenticationError("Authentication failed")

        with pytest.raises(AuthenticationError):
            await _disarm_alarm(mock_client, "alarm_control_panel.home", "1234")


class TestTriggerAlarm:
    """Tests for triggering alarm control panels."""

    @pytest.mark.asyncio
    async def test_trigger_alarm_success(self, mock_client):
        """Test successfully triggering an alarm."""
        mock_client.call_service.return_value = {}

        result = await _trigger_alarm(mock_client, "alarm_control_panel.home")

        assert result["success"] is True
        assert result["entity_id"] == "alarm_control_panel.home"
        assert "triggered" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "alarm_control_panel", "alarm_trigger", {"entity_id": "alarm_control_panel.home"}
        )

    @pytest.mark.asyncio
    async def test_trigger_alarm_invalid_entity_type(self, mock_client):
        """Test triggering an entity that is not an alarm control panel."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _trigger_alarm(mock_client, "light.garage")

        assert "not an alarm control panel entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_trigger_alarm_service_error(self, mock_client):
        """Test handling service call errors when triggering."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _trigger_alarm(mock_client, "alarm_control_panel.home")


class TestAlarmControlIntegration:
    """Integration tests for the alarm_control tool function."""

    @pytest.mark.asyncio
    async def test_alarm_control_list_action(self, mock_client, sample_alarm_states):
        """Test the alarm_control function with list action."""
        from src.homeassistant_mcp.tools.devices.alarm import register_alarm_tool

        mock_client.get_states.return_value = sample_alarm_states

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
        register_alarm_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_alarm_control_missing_entity_id(self):
        """Test alarm_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.devices.alarm import register_alarm_tool

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

        register_alarm_tool(mock_mcp, lambda: mock_client)

        # Test get without entity_id
        result = await registered_func(action="get")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test arm_away without entity_id
        result = await registered_func(action="arm_away")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test arm_home without entity_id
        result = await registered_func(action="arm_home")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test arm_night without entity_id
        result = await registered_func(action="arm_night")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test disarm without entity_id
        result = await registered_func(action="disarm")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test trigger without entity_id
        result = await registered_func(action="trigger")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

    @pytest.mark.asyncio
    async def test_alarm_control_disarm_missing_code(self):
        """Test alarm_control disarm action without required code."""
        from src.homeassistant_mcp.tools.devices.alarm import register_alarm_tool

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

        register_alarm_tool(mock_mcp, lambda: mock_client)

        # Test disarm without code
        result = await registered_func(action="disarm", entity_id="alarm_control_panel.home")
        assert result["success"] is False
        assert "code is required" in result["error"]

    @pytest.mark.asyncio
    async def test_alarm_control_arm_modes(self):
        """Test alarm_control with different arming modes."""
        from src.homeassistant_mcp.tools.devices.alarm import register_alarm_tool

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

        register_alarm_tool(mock_mcp, lambda: mock_client)

        # Test arm_away
        result = await registered_func(action="arm_away", entity_id="alarm_control_panel.home")
        assert result["success"] is True
        assert result["mode"] == "away"

        # Test arm_home
        result = await registered_func(action="arm_home", entity_id="alarm_control_panel.home")
        assert result["success"] is True
        assert result["mode"] == "home"

        # Test arm_night
        result = await registered_func(action="arm_night", entity_id="alarm_control_panel.home")
        assert result["success"] is True
        assert result["mode"] == "night"

    @pytest.mark.asyncio
    async def test_alarm_control_disarm_with_code(self):
        """Test alarm_control disarm action with code."""
        from src.homeassistant_mcp.tools.devices.alarm import register_alarm_tool

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

        register_alarm_tool(mock_mcp, lambda: mock_client)

        # Test disarm with code
        result = await registered_func(
            action="disarm", entity_id="alarm_control_panel.home", code="1234"
        )
        assert result["success"] is True
        assert "disarmed" in result["message"]

    @pytest.mark.asyncio
    async def test_alarm_control_error_handling(self):
        """Test alarm_control error handling."""
        from src.homeassistant_mcp.tools.devices.alarm import register_alarm_tool

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

        register_alarm_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="alarm_control_panel.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
        assert result["error_type"] == "entity_not_found"

    @pytest.mark.asyncio
    async def test_alarm_control_authentication_error(self):
        """Test alarm_control with authentication error."""
        from src.homeassistant_mcp.tools.devices.alarm import register_alarm_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.call_service.side_effect = AuthenticationError("Invalid credentials")

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_alarm_tool(mock_mcp, lambda: mock_client)

        # Test with AuthenticationError
        result = await registered_func(
            action="disarm", entity_id="alarm_control_panel.home", code="wrong"
        )
        assert result["success"] is False
        assert "Invalid credentials" in result["error"]
        assert result["error_type"] == "authentication_error"

    @pytest.mark.asyncio
    async def test_alarm_control_connection_error(self):
        """Test alarm_control with connection error."""
        from src.homeassistant_mcp.tools.devices.alarm import register_alarm_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.get_states.side_effect = ConnectionError("Connection failed")

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_alarm_tool(mock_mcp, lambda: mock_client)

        # Test with ConnectionError
        result = await registered_func(action="list")
        assert result["success"] is False
        assert "Connection failed" in result["error"]
        assert result["error_type"] == "connection_error"

    @pytest.mark.asyncio
    async def test_alarm_control_service_call_error(self):
        """Test alarm_control with service call error."""
        from src.homeassistant_mcp.tools.devices.alarm import register_alarm_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.call_service.side_effect = ServiceCallError("Service unavailable")

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_alarm_tool(mock_mcp, lambda: mock_client)

        # Test with ServiceCallError
        result = await registered_func(action="trigger", entity_id="alarm_control_panel.home")
        assert result["success"] is False
        assert "Service unavailable" in result["error"]
        assert result["error_type"] == "service_call_error"
