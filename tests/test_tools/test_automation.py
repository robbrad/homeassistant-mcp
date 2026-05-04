"""Unit tests for the automation control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.automation.automation import (
    _list_automations,
    _reload_automations,
    _toggle_automation,
    _trigger_automation,
    _turn_off_automation,
    _turn_on_automation,
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
def sample_automation_states():
    """Sample automation entity states for testing."""
    return [
        {
            "entity_id": "automation.morning_routine",
            "state": "on",
            "attributes": {
                "friendly_name": "Morning Routine",
                "last_triggered": "2024-01-01T08:00:00",
            },
            "last_changed": "2024-01-01T07:00:00",
            "last_updated": "2024-01-01T08:00:00",
        },
        {
            "entity_id": "automation.evening_lights",
            "state": "on",
            "attributes": {
                "friendly_name": "Evening Lights",
                "last_triggered": "2024-01-01T18:00:00",
            },
            "last_changed": "2024-01-01T17:00:00",
            "last_updated": "2024-01-01T18:00:00",
        },
        {
            "entity_id": "automation.security_alert",
            "state": "off",
            "attributes": {
                "friendly_name": "Security Alert",
                "last_triggered": None,
            },
            "last_changed": "2024-01-01T10:00:00",
            "last_updated": "2024-01-01T10:00:00",
        },
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
            },
        },
    ]


class TestListAutomations:
    """Tests for listing automations."""

    @pytest.mark.asyncio
    async def test_list_automations_success(self, mock_client, sample_automation_states):
        """Test successfully listing all automations."""
        mock_client._states_data = sample_automation_states

        result = await _list_automations(mock_client)

        assert result["success"] is True
        assert result["count"] == 3  # Only automations, not the light
        assert len(result["automations"]) == 3

        # Verify automation data
        morning = next(
            auto
            for auto in result["automations"]
            if auto["entity_id"] == "automation.morning_routine"
        )
        assert morning["name"] == "Morning Routine"
        assert morning["state"] == "on"
        assert morning["last_triggered"] == "2024-01-01T08:00:00"

        # Verify automation with no last_triggered
        security = next(
            auto
            for auto in result["automations"]
            if auto["entity_id"] == "automation.security_alert"
        )
        assert security["state"] == "off"
        assert security["last_triggered"] is None

    @pytest.mark.asyncio
    async def test_list_automations_empty(self, mock_client):
        """Test listing automations when no automations exist."""
        mock_client._states_data = [
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {},
            }
        ]

        result = await _list_automations(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["automations"] == []


class TestToggleAutomation:
    """Tests for toggling automations."""

    @pytest.mark.asyncio
    async def test_toggle_automation_on_to_off(self, mock_client):
        """Test toggling an automation from on to off."""
        mock_client.get_state.return_value = {
            "entity_id": "automation.morning_routine",
            "state": "on",
            "attributes": {
                "friendly_name": "Morning Routine",
            },
        }
        mock_client.call_service.return_value = {}

        result = await _toggle_automation(mock_client, "automation.morning_routine")

        assert result["success"] is True
        assert result["entity_id"] == "automation.morning_routine"
        assert result["previous_state"] == "on"
        assert result["new_state"] == "off"
        assert "toggled" in result["message"]

        mock_client.get_state.assert_called_once_with("automation.morning_routine")
        mock_client.call_service.assert_called_once_with(
            "automation", "toggle", {"entity_id": "automation.morning_routine"}
        )

    @pytest.mark.asyncio
    async def test_toggle_automation_off_to_on(self, mock_client):
        """Test toggling an automation from off to on."""
        mock_client.get_state.return_value = {
            "entity_id": "automation.security_alert",
            "state": "off",
            "attributes": {
                "friendly_name": "Security Alert",
            },
        }
        mock_client.call_service.return_value = {}

        result = await _toggle_automation(mock_client, "automation.security_alert")

        assert result["success"] is True
        assert result["previous_state"] == "off"
        assert result["new_state"] == "on"

    @pytest.mark.asyncio
    async def test_toggle_automation_not_found(self, mock_client):
        """Test toggling an automation that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'automation.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _toggle_automation(mock_client, "automation.nonexistent")

    @pytest.mark.asyncio
    async def test_toggle_automation_invalid_entity_type(self, mock_client):
        """Test toggling an entity that is not an automation."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _toggle_automation(mock_client, "light.living_room")

        assert "not an automation entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_toggle_automation_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.get_state.return_value = {
            "entity_id": "automation.morning_routine",
            "state": "on",
            "attributes": {},
        }
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _toggle_automation(mock_client, "automation.morning_routine")


class TestTriggerAutomation:
    """Tests for triggering automations."""

    @pytest.mark.asyncio
    async def test_trigger_automation_success(self, mock_client):
        """Test successfully triggering an automation."""
        mock_client.get_state.return_value = {
            "entity_id": "automation.morning_routine",
            "state": "on",
            "attributes": {
                "friendly_name": "Morning Routine",
            },
        }
        mock_client.call_service.return_value = {}

        result = await _trigger_automation(mock_client, "automation.morning_routine")

        assert result["success"] is True
        assert result["entity_id"] == "automation.morning_routine"
        assert "triggered successfully" in result["message"]

        mock_client.get_state.assert_called_once_with("automation.morning_routine")
        mock_client.call_service.assert_called_once_with(
            "automation", "trigger", {"entity_id": "automation.morning_routine"}
        )

    @pytest.mark.asyncio
    async def test_trigger_automation_disabled(self, mock_client):
        """Test triggering a disabled automation (should still work)."""
        mock_client.get_state.return_value = {
            "entity_id": "automation.security_alert",
            "state": "off",
            "attributes": {
                "friendly_name": "Security Alert",
            },
        }
        mock_client.call_service.return_value = {}

        result = await _trigger_automation(mock_client, "automation.security_alert")

        assert result["success"] is True
        assert result["entity_id"] == "automation.security_alert"

    @pytest.mark.asyncio
    async def test_trigger_automation_not_found(self, mock_client):
        """Test triggering an automation that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'automation.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _trigger_automation(mock_client, "automation.nonexistent")

    @pytest.mark.asyncio
    async def test_trigger_automation_invalid_entity_type(self, mock_client):
        """Test triggering an entity that is not an automation."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _trigger_automation(mock_client, "light.living_room")

        assert "not an automation entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_trigger_automation_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.get_state.return_value = {
            "entity_id": "automation.morning_routine",
            "state": "on",
            "attributes": {},
        }
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _trigger_automation(mock_client, "automation.morning_routine")


class TestAutomationControlIntegration:
    """Integration tests for the automation_control tool function."""

    @pytest.mark.asyncio
    async def test_automation_control_list_action(self, mock_client, sample_automation_states):
        """Test the automation_control function with list action."""
        from src.homeassistant_mcp.tools.automation.automation import register_automation_tool

        mock_client._states_data = sample_automation_states

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
        register_automation_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_automation_control_toggle_action(self, mock_client):
        """Test the automation_control function with toggle action."""
        from src.homeassistant_mcp.tools.automation.automation import register_automation_tool

        mock_client.get_state.return_value = {
            "entity_id": "automation.morning_routine",
            "state": "on",
            "attributes": {},
        }
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

        register_automation_tool(mock_mcp, lambda: mock_client)

        result = await registered_func(action="toggle", automation_id="automation.morning_routine")

        assert result["success"] is True
        assert result["previous_state"] == "on"
        assert result["new_state"] == "off"

    @pytest.mark.asyncio
    async def test_automation_control_trigger_action(self, mock_client):
        """Test the automation_control function with trigger action."""
        from src.homeassistant_mcp.tools.automation.automation import register_automation_tool

        mock_client.get_state.return_value = {
            "entity_id": "automation.morning_routine",
            "state": "on",
            "attributes": {},
        }
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

        register_automation_tool(mock_mcp, lambda: mock_client)

        result = await registered_func(action="trigger", automation_id="automation.morning_routine")

        assert result["success"] is True
        assert "triggered successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_automation_control_missing_automation_id(self):
        """Test automation_control with actions that require automation_id but it's missing."""
        from src.homeassistant_mcp.tools.automation.automation import register_automation_tool

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

        register_automation_tool(mock_mcp, lambda: mock_client)

        # Test toggle without automation_id
        result = await registered_func(action="toggle")
        assert result["success"] is False
        assert "automation_id is required" in result["error"]

        # Test trigger without automation_id
        result = await registered_func(action="trigger")
        assert result["success"] is False
        assert "automation_id is required" in result["error"]

    @pytest.mark.asyncio
    async def test_automation_control_error_handling(self):
        """Test automation_control error handling."""
        from src.homeassistant_mcp.tools.automation.automation import register_automation_tool

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

        register_automation_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="toggle", automation_id="automation.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]

    @pytest.mark.asyncio
    async def test_automation_control_unexpected_error(self):
        """Test automation_control handling of unexpected errors."""
        from src.homeassistant_mcp.tools.automation.automation import register_automation_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.get_states.side_effect = Exception("Unexpected error")

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_automation_tool(mock_mcp, lambda: mock_client)

        # Test with unexpected error
        result = await registered_func(action="list")
        assert result["success"] is False
        assert "unexpected error" in result["error"].lower()


class TestTurnOnAutomation:
    """Tests for turning on automations."""

    @pytest.mark.asyncio
    async def test_turn_on_automation_success(self, mock_client):
        """Test successfully turning on an automation."""
        mock_client.get_state.return_value = {
            "entity_id": "automation.morning_routine",
            "state": "off",
            "attributes": {
                "friendly_name": "Morning Routine",
            },
        }
        mock_client.call_service.return_value = {}

        result = await _turn_on_automation(mock_client, "automation.morning_routine")

        assert result["success"] is True
        assert result["entity_id"] == "automation.morning_routine"
        assert result["state"] == "on"
        assert "turned on" in result["message"]

        mock_client.get_state.assert_called_once_with("automation.morning_routine")
        mock_client.call_service.assert_called_once_with(
            "automation", "turn_on", {"entity_id": "automation.morning_routine"}
        )

    @pytest.mark.asyncio
    async def test_turn_on_automation_not_found(self, mock_client):
        """Test turning on an automation that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'automation.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _turn_on_automation(mock_client, "automation.nonexistent")

    @pytest.mark.asyncio
    async def test_turn_on_automation_invalid_entity_type(self, mock_client):
        """Test turning on an entity that is not an automation."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _turn_on_automation(mock_client, "light.living_room")

        assert "not an automation entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()
        mock_client.call_service.assert_not_called()


class TestTurnOffAutomation:
    """Tests for turning off automations."""

    @pytest.mark.asyncio
    async def test_turn_off_automation_success(self, mock_client):
        """Test successfully turning off an automation."""
        mock_client.get_state.return_value = {
            "entity_id": "automation.morning_routine",
            "state": "on",
            "attributes": {
                "friendly_name": "Morning Routine",
            },
        }
        mock_client.call_service.return_value = {}

        result = await _turn_off_automation(mock_client, "automation.morning_routine")

        assert result["success"] is True
        assert result["entity_id"] == "automation.morning_routine"
        assert result["state"] == "off"
        assert "turned off" in result["message"]

        mock_client.get_state.assert_called_once_with("automation.morning_routine")
        mock_client.call_service.assert_called_once_with(
            "automation", "turn_off", {"entity_id": "automation.morning_routine"}
        )

    @pytest.mark.asyncio
    async def test_turn_off_automation_not_found(self, mock_client):
        """Test turning off an automation that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'automation.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _turn_off_automation(mock_client, "automation.nonexistent")

    @pytest.mark.asyncio
    async def test_turn_off_automation_invalid_entity_type(self, mock_client):
        """Test turning off an entity that is not an automation."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _turn_off_automation(mock_client, "light.living_room")

        assert "not an automation entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()
        mock_client.call_service.assert_not_called()


class TestReloadAutomations:
    """Tests for reloading automation configurations."""

    @pytest.mark.asyncio
    async def test_reload_automations_success(self, mock_client):
        """Test successfully reloading automation configurations."""
        mock_client.call_service.return_value = {}

        result = await _reload_automations(mock_client)

        assert result["success"] is True
        assert "reloaded successfully" in result["message"]

        mock_client.call_service.assert_called_once_with("automation", "reload", {})

    @pytest.mark.asyncio
    async def test_reload_automations_service_error(self, mock_client):
        """Test handling service call errors during reload."""
        mock_client.call_service.side_effect = ServiceCallError("Reload failed")

        with pytest.raises(ServiceCallError):
            await _reload_automations(mock_client)
