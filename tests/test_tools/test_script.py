"""Unit tests for the script control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.automation.script import (
    _execute_script,
    _get_script,
    _list_scripts,
    _reload_scripts,
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
def sample_script_states():
    """Sample script entity states for testing."""
    return [
        {
            "entity_id": "script.morning_routine",
            "state": "off",
            "attributes": {
                "friendly_name": "Morning Routine",
                "description": "Turn on lights and start coffee maker",
                "last_triggered": "2024-01-01T08:00:00",
            },
            "last_changed": "2024-01-01T08:00:00",
            "last_updated": "2024-01-01T08:00:00",
        },
        {
            "entity_id": "script.evening_routine",
            "state": "off",
            "attributes": {
                "friendly_name": "Evening Routine",
                "description": "Close blinds and dim lights",
                "last_triggered": "2024-01-01T20:00:00",
            },
            "last_changed": "2024-01-01T20:00:00",
            "last_updated": "2024-01-01T20:00:00",
        },
        {
            "entity_id": "script.set_lights",
            "state": "off",
            "attributes": {
                "friendly_name": "Set Lights",
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


class TestListScripts:
    """Tests for listing scripts."""

    @pytest.mark.asyncio
    async def test_list_scripts_success(self, mock_client, sample_script_states):
        """Test successfully listing all scripts."""
        mock_client._states_data = sample_script_states

        result = await _list_scripts(mock_client)

        assert result["success"] is True
        assert result["count"] == 3  # Only scripts, not the light
        assert len(result["scripts"]) == 3

        # Verify script data
        morning = next(
            script
            for script in result["scripts"]
            if script["entity_id"] == "script.morning_routine"
        )
        assert morning["name"] == "Morning Routine"
        assert morning["state"] == "off"
        assert morning["description"] == "Turn on lights and start coffee maker"
        assert morning["last_triggered"] == "2024-01-01T08:00:00"

        # Verify script without description
        set_lights = next(
            script for script in result["scripts"] if script["entity_id"] == "script.set_lights"
        )
        assert "description" not in set_lights

    @pytest.mark.asyncio
    async def test_list_scripts_empty(self, mock_client):
        """Test listing scripts when no scripts exist."""
        mock_client._states_data = [
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {},
            }
        ]

        result = await _list_scripts(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["scripts"] == []


class TestGetScript:
    """Tests for getting a specific script."""

    @pytest.mark.asyncio
    async def test_get_script_success(self, mock_client):
        """Test successfully getting a specific script."""
        mock_client.get_state.return_value = {
            "entity_id": "script.morning_routine",
            "state": "off",
            "attributes": {
                "friendly_name": "Morning Routine",
                "description": "Turn on lights and start coffee maker",
                "last_triggered": "2024-01-01T08:00:00",
            },
            "last_changed": "2024-01-01T08:00:00",
            "last_updated": "2024-01-01T08:00:00",
        }

        result = await _get_script(mock_client, "script.morning_routine")

        assert result["success"] is True
        assert result["script"]["entity_id"] == "script.morning_routine"
        assert result["script"]["name"] == "Morning Routine"
        assert result["script"]["state"] == "off"
        assert result["script"]["last_changed"] == "2024-01-01T08:00:00"
        assert (
            result["script"]["attributes"]["description"] == "Turn on lights and start coffee maker"
        )

        mock_client.get_state.assert_called_once_with("script.morning_routine")

    @pytest.mark.asyncio
    async def test_get_script_not_found(self, mock_client):
        """Test getting a script that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'script.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_script(mock_client, "script.nonexistent")

    @pytest.mark.asyncio
    async def test_get_script_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not a script."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_script(mock_client, "light.garage")

        assert "not a script entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestExecuteScript:
    """Tests for executing scripts."""

    @pytest.mark.asyncio
    async def test_execute_script_success(self, mock_client):
        """Test successfully executing a script."""
        mock_client.call_service.return_value = {}

        result = await _execute_script(mock_client, "script.morning_routine")

        assert result["success"] is True
        assert result["entity_id"] == "script.morning_routine"
        assert "executed successfully" in result["message"]
        assert "variables" not in result

        mock_client.call_service.assert_called_once_with(
            "script", "turn_on", {"entity_id": "script.morning_routine"}
        )

    @pytest.mark.asyncio
    async def test_execute_script_with_variables(self, mock_client):
        """Test executing a script with variables."""
        mock_client.call_service.return_value = {}
        variables = {"brightness": 100, "color": "blue"}

        result = await _execute_script(mock_client, "script.set_lights", variables)

        assert result["success"] is True
        assert result["entity_id"] == "script.set_lights"
        assert "executed successfully" in result["message"]
        assert result["variables"] == variables

        mock_client.call_service.assert_called_once_with(
            "script",
            "turn_on",
            {"entity_id": "script.set_lights", "brightness": 100, "color": "blue"},
        )

    @pytest.mark.asyncio
    async def test_execute_script_invalid_entity_type(self, mock_client):
        """Test executing an entity that is not a script."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _execute_script(mock_client, "light.garage")

        assert "not a script entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_script_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _execute_script(mock_client, "script.morning_routine")


class TestReloadScripts:
    """Tests for reloading scripts."""

    @pytest.mark.asyncio
    async def test_reload_scripts_success(self, mock_client):
        """Test successfully reloading all scripts."""
        mock_client.call_service.return_value = {}

        result = await _reload_scripts(mock_client)

        assert result["success"] is True
        assert "reloaded successfully" in result["message"]

        mock_client.call_service.assert_called_once_with("script", "reload", {})

    @pytest.mark.asyncio
    async def test_reload_scripts_service_error(self, mock_client):
        """Test handling service call errors during reload."""
        mock_client.call_service.side_effect = ServiceCallError("Reload failed")

        with pytest.raises(ServiceCallError):
            await _reload_scripts(mock_client)


class TestScriptControlIntegration:
    """Integration tests for the script_control tool function."""

    @pytest.mark.asyncio
    async def test_script_control_list_action(self, mock_client, sample_script_states):
        """Test the script_control function with list action."""
        from src.homeassistant_mcp.tools.automation.script import register_script_tool

        mock_client._states_data = sample_script_states

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
        register_script_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_script_control_get_action(self, mock_client):
        """Test the script_control function with get action."""
        from src.homeassistant_mcp.tools.automation.script import register_script_tool

        mock_client.get_state.return_value = {
            "entity_id": "script.morning_routine",
            "state": "off",
            "attributes": {"friendly_name": "Morning Routine"},
            "last_changed": "2024-01-01T08:00:00",
            "last_updated": "2024-01-01T08:00:00",
        }

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_script_tool(mock_mcp, lambda: mock_client)

        result = await registered_func(action="get", entity_id="script.morning_routine")

        assert result["success"] is True
        assert result["script"]["entity_id"] == "script.morning_routine"

    @pytest.mark.asyncio
    async def test_script_control_execute_action(self, mock_client):
        """Test the script_control function with execute action."""
        from src.homeassistant_mcp.tools.automation.script import register_script_tool

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

        register_script_tool(mock_mcp, lambda: mock_client)

        result = await registered_func(action="execute", entity_id="script.morning_routine")

        assert result["success"] is True
        assert result["entity_id"] == "script.morning_routine"

    @pytest.mark.asyncio
    async def test_script_control_execute_with_variables(self, mock_client):
        """Test the script_control function with execute action and variables."""
        from src.homeassistant_mcp.tools.automation.script import register_script_tool

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

        register_script_tool(mock_mcp, lambda: mock_client)

        variables = {"brightness": 100, "color": "blue"}
        result = await registered_func(
            action="execute", entity_id="script.set_lights", variables=variables
        )

        assert result["success"] is True
        assert result["entity_id"] == "script.set_lights"
        assert result["variables"] == variables

    @pytest.mark.asyncio
    async def test_script_control_reload_action(self, mock_client):
        """Test the script_control function with reload action."""
        from src.homeassistant_mcp.tools.automation.script import register_script_tool

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

        register_script_tool(mock_mcp, lambda: mock_client)

        result = await registered_func(action="reload")

        assert result["success"] is True
        assert "reloaded successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_script_control_missing_entity_id(self):
        """Test script_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.automation.script import register_script_tool

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

        register_script_tool(mock_mcp, lambda: mock_client)

        # Test get without entity_id
        result = await registered_func(action="get")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test execute without entity_id
        result = await registered_func(action="execute")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

    @pytest.mark.asyncio
    async def test_script_control_error_handling(self):
        """Test script_control error handling."""
        from src.homeassistant_mcp.tools.automation.script import register_script_tool

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

        register_script_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="script.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
        assert result["error_type"] == "entity_not_found"

    @pytest.mark.asyncio
    async def test_script_control_service_call_error(self):
        """Test script_control with ServiceCallError."""
        from src.homeassistant_mcp.tools.automation.script import register_script_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_script_tool(mock_mcp, lambda: mock_client)

        # Test with ServiceCallError
        result = await registered_func(action="execute", entity_id="script.morning_routine")
        assert result["success"] is False
        assert "Service call failed" in result["error"]
        assert result["error_type"] == "service_call_error"
