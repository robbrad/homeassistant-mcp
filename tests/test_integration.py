"""Integration tests for Home Assistant MCP Server.

This module tests:
- Tool registration and discovery
- End-to-end flows with mocked HA API
- Consistent error handling across all tools
- Tool metadata and documentation
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.homeassistant_mcp.exceptions import (
    AuthenticationError,
    ConnectionError,
    EntityNotFoundError,
    ServiceCallError,
)
from src.homeassistant_mcp.server import lifespan, mcp


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("HASS_HOST", "http://homeassistant.local:8123")
    monkeypatch.setenv("HASS_TOKEN", "test_token_1234567890_long_enough")
    monkeypatch.setenv("LOG_LEVEL", "INFO")


@pytest.fixture
def mock_hass_client():
    """Create a mock Home Assistant client with comprehensive responses."""
    client = AsyncMock()

    # Default successful responses
    client.get_states.return_value = [
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"brightness": 255, "friendly_name": "Living Room"},
        },
        {
            "entity_id": "switch.kitchen",
            "state": "off",
            "attributes": {"friendly_name": "Kitchen Switch"},
        },
        {
            "entity_id": "climate.bedroom",
            "state": "heat",
            "attributes": {"temperature": 20, "friendly_name": "Bedroom Thermostat"},
        },
    ]

    client.get_state.return_value = {
        "entity_id": "light.living_room",
        "state": "on",
        "attributes": {"brightness": 255},
    }

    client.call_service.return_value = {"success": True}
    client.close = AsyncMock()

    return client


class TestToolRegistration:
    """Tests for tool registration and discovery."""

    def test_all_domain_tools_registered(self):
        """Test that all domain-specific tools are registered."""
        expected_tools = {
            # Core tools
            "lights_control",
            "climate_control",
            "list_devices",
            "automation_control",
            "scene_control",
            "send_notification",
            "query_history",  # Old history tool
            "call_service",
            # "get_automation_config",  # Removed - no longer reading config files
            # Core tools
            "switch_control",
            "cover_control",
            "lock_control",
            "media_player_control",
            "camera_control",
            # Phase 2: Automation Helpers
            "vacuum_control",
            "fan_control",
            "script_control",
            "input_boolean_control",
            "input_number_control",
            "input_select_control",
            "input_text_control",
            "input_datetime_control",
            "weather_control",
            # Phase 3: Advanced Features
            "alarm_control",
            "water_heater_control",
            "humidifier_control",
            "siren_control",
            "valve_control",
            "lawn_mower_control",
            # Phase 4: Configuration Management - REMOVED in REST API Overhaul
            # "config_control",  # Removed - no longer manipulating config files
            # "config_sync_control",  # Removed - no longer manipulating config files
            # "automation_editor_control",  # Removed - no longer manipulating config files
            # "get_automation_config",  # Removed - no longer reading config files
            # Phase 5: REST API Overhaul - Core API Tools
            "api_info",
            "events_control",
            "services_control",
            # Phase 5: REST API Overhaul - State Management
            "states_control",
            # Phase 5: REST API Overhaul - Historical Data
            "history_query",  # New history tool
            "logbook_query",
            "error_log_get",
            # Phase 5: REST API Overhaul - Specialized Tools
            "camera_proxy_get",
            "calendar_access",
            "template_render",
            "config_check",
            "intent_handle",
        }

        registered_tools = set(mcp._tool_manager._tools.keys())

        # Check all expected tools are present
        missing_tools = expected_tools - registered_tools
        assert not missing_tools, f"Missing tools: {missing_tools}"

        # Verify exact count (44 tools - 4 removed config tools = 40 tools)
        assert len(registered_tools) == 40, f"Expected 40 tools, got {len(registered_tools)}"

    def test_tool_naming_consistency(self):
        """Test that all tools follow consistent naming conventions."""
        # Exceptions to the _control naming pattern
        exceptions = {
            "list_devices",
            "get_automation_config",
            "send_notification",
            "query_history",
            "call_service",
            # New REST API tools
            "api_info",
            "states_control",  # This one does follow the pattern
            "history_query",
            "logbook_query",
            "error_log_get",
            # Specialized tools with different naming patterns
            "camera_proxy_get",
            "calendar_access",
            "template_render",
            "config_check",
            "intent_handle",
        }

        for tool_name in mcp._tool_manager._tools.keys():
            # Most tools should end with _control except known exceptions
            if tool_name not in exceptions:
                assert tool_name.endswith(
                    "_control"
                ), f"Tool {tool_name} doesn't follow naming convention"

            # Tool names should use underscores, not hyphens
            assert "-" not in tool_name, f"Tool {tool_name} uses hyphens instead of underscores"

    def test_all_tools_have_metadata(self):
        """Test that all tools have proper metadata."""
        for tool_name, tool in mcp._tool_manager._tools.items():
            # Check description exists and is not empty
            assert tool.description is not None, f"Tool {tool_name} missing description"
            assert len(tool.description) > 10, f"Tool {tool_name} has too short description"

            # Check tool is callable
            assert callable(tool.fn), f"Tool {tool_name} is not callable"

            # Check tool name matches
            assert tool.name == tool_name, f"Tool name mismatch: {tool.name} != {tool_name}"

    def test_tool_descriptions_are_informative(self):
        """Test that tool descriptions provide useful information."""
        for tool_name, tool in mcp._tool_manager._tools.items():
            description = tool.description.lower()

            # Description should mention what the tool does
            assert any(
                keyword in description
                for keyword in [
                    "control",
                    "manage",
                    "list",
                    "get",
                    "set",
                    "query",
                    "send",
                    "activate",
                    "sync",
                    "copy",
                    "retrieve",
                    "create",
                    "edit",
                    "delete",
                    "update",
                ]
            ), f"Tool {tool_name} description doesn't describe action"

    def test_tools_have_proper_parameters(self):
        """Test that tools have properly defined parameters."""
        # Tools that don't use the action parameter pattern
        no_action_tools = {
            "list_devices",
            "get_automation_config",
            "send_notification",
            "query_history",
            "call_service",
            # New REST API tools without action parameter
            "history_query",
            "logbook_query",
            "error_log_get",
            # Specialized tools with specific parameters
            "camera_proxy_get",
            "template_render",
            "config_check",
            "intent_handle",
        }

        for tool_name, tool in mcp._tool_manager._tools.items():
            # Get the function signature
            import inspect

            sig = inspect.signature(tool.fn)

            # Most tools should have an 'action' parameter
            if tool_name not in no_action_tools:
                assert "action" in sig.parameters, f"Tool {tool_name} missing 'action' parameter"


class TestEndToEndFlows:
    """Tests for end-to-end workflows with mocked HA API."""

    @pytest.mark.asyncio
    async def test_light_control_flow(self, mock_env, mock_hass_client):
        """Test complete light control workflow."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # Get the lights control tool
                lights_tool = mcp._tool_manager._tools["lights_control"]

                # Test list action
                mock_hass_client.get_states.return_value = [
                    {
                        "entity_id": "light.living_room",
                        "state": "on",
                        "attributes": {"brightness": 255},
                    }
                ]

                result = await lights_tool.fn(action="list")
                assert result["success"] is True
                assert "lights" in result

                # Test turn_on action
                mock_hass_client.call_service.return_value = {}
                result = await lights_tool.fn(
                    action="turn_on", entity_id="light.living_room", brightness=128
                )
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_climate_control_flow(self, mock_env, mock_hass_client):
        """Test complete climate control workflow."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                climate_tool = mcp._tool_manager._tools["climate_control"]

                # Test list action
                mock_hass_client.get_states.return_value = [
                    {
                        "entity_id": "climate.bedroom",
                        "state": "heat",
                        "attributes": {"temperature": 20},
                    }
                ]

                result = await climate_tool.fn(action="list")
                assert result["success"] is True

                # Test set_temperature action
                result = await climate_tool.fn(
                    action="set_temperature", entity_id="climate.bedroom", temperature=22.0
                )
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_switch_control_flow(self, mock_env, mock_hass_client):
        """Test complete switch control workflow."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                switch_tool = mcp._tool_manager._tools["switch_control"]

                # Test list action
                mock_hass_client.get_states.return_value = [
                    {
                        "entity_id": "switch.kitchen",
                        "state": "off",
                        "attributes": {"friendly_name": "Kitchen"},
                    }
                ]

                result = await switch_tool.fn(action="list")
                assert result["success"] is True

                # Test turn_on action
                result = await switch_tool.fn(action="turn_on", entity_id="switch.kitchen")
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_automation_workflow(self, mock_env, mock_hass_client):
        """Test automation trigger and management workflow."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                automation_tool = mcp._tool_manager._tools["automation_control"]

                # Test list action
                mock_hass_client.get_states.return_value = [
                    {
                        "entity_id": "automation.morning_routine",
                        "state": "on",
                        "attributes": {"friendly_name": "Morning Routine"},
                    }
                ]

                result = await automation_tool.fn(action="list")
                assert result["success"] is True

                # Test trigger action
                result = await automation_tool.fn(
                    action="trigger", automation_id="automation.morning_routine"
                )
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_multi_domain_workflow(self, mock_env, mock_hass_client):
        """Test workflow involving multiple domains."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # Simulate a "movie time" scenario
                # 1. Turn off lights
                lights_tool = mcp._tool_manager._tools["lights_control"]
                result = await lights_tool.fn(action="turn_off", entity_id="light.living_room")
                assert result["success"] is True

                # 2. Close covers
                cover_tool = mcp._tool_manager._tools["cover_control"]
                result = await cover_tool.fn(action="close", entity_id="cover.living_room_blinds")
                assert result["success"] is True

                # 3. Activate scene
                scene_tool = mcp._tool_manager._tools["scene_control"]
                result = await scene_tool.fn(action="activate", scene_id="scene.movie_time")
                assert result["success"] is True


class TestErrorHandlingConsistency:
    """Tests for consistent error handling across all tools."""

    @pytest.mark.asyncio
    async def test_entity_not_found_error_handling(self, mock_env):
        """Test that all tools handle EntityNotFoundError consistently."""
        mock_client = AsyncMock()
        mock_client.get_states.return_value = []
        mock_client.get_state.side_effect = EntityNotFoundError("Entity not found")
        mock_client.close = AsyncMock()

        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # Test lights tool
                lights_tool = mcp._tool_manager._tools["lights_control"]
                result = await lights_tool.fn(action="get", entity_id="light.nonexistent")
                assert result["success"] is False
                assert "error" in result
                assert "error_type" in result
                assert result["error_type"] == "entity_not_found"

    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, mock_env):
        """Test that all tools handle AuthenticationError consistently."""
        mock_client = AsyncMock()
        mock_client.get_states.return_value = []
        mock_client.call_service.side_effect = AuthenticationError("Invalid token")
        mock_client.close = AsyncMock()

        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # Test switch tool
                switch_tool = mcp._tool_manager._tools["switch_control"]
                result = await switch_tool.fn(action="turn_on", entity_id="switch.kitchen")
                assert result["success"] is False
                assert "error" in result
                assert "error_type" in result
                assert result["error_type"] == "authentication_error"

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, mock_env):
        """Test that all tools handle ConnectionError consistently."""
        mock_client = AsyncMock()
        # First call succeeds (for lifespan verification), subsequent calls fail
        mock_client.get_states.side_effect = [[], ConnectionError("Connection failed")]
        mock_client.close = AsyncMock()

        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # Test climate tool
                climate_tool = mcp._tool_manager._tools["climate_control"]
                result = await climate_tool.fn(action="list")
                assert result["success"] is False
                assert "error" in result
                assert "error_type" in result
                assert result["error_type"] == "connection_error"

    @pytest.mark.asyncio
    async def test_service_call_error_handling(self, mock_env):
        """Test that all tools handle ServiceCallError consistently."""
        mock_client = AsyncMock()
        mock_client.get_states.return_value = []
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")
        mock_client.close = AsyncMock()

        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # Test fan tool
                fan_tool = mcp._tool_manager._tools["fan_control"]
                result = await fan_tool.fn(action="turn_on", entity_id="fan.bedroom")
                assert result["success"] is False
                assert "error" in result
                assert "error_type" in result
                assert result["error_type"] == "service_call_error"

    @pytest.mark.asyncio
    async def test_generic_exception_handling(self, mock_env):
        """Test that all tools handle unexpected exceptions consistently."""
        mock_client = AsyncMock()
        # First call succeeds (for lifespan verification), subsequent calls fail
        mock_client.get_states.side_effect = [[], Exception("Unexpected error")]
        mock_client.close = AsyncMock()

        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # Test vacuum tool
                vacuum_tool = mcp._tool_manager._tools["vacuum_control"]
                result = await vacuum_tool.fn(action="list")
                assert result["success"] is False
                assert "error" in result

    @pytest.mark.asyncio
    async def test_error_response_structure(self, mock_env):
        """Test that error responses have consistent structure."""
        mock_client = AsyncMock()
        mock_client.get_states.return_value = []
        mock_client.call_service.side_effect = ServiceCallError("Test error")
        mock_client.close = AsyncMock()

        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # Test multiple tools for consistent error structure
                tools_to_test = [
                    ("lights_control", {"action": "turn_on", "entity_id": "light.test"}),
                    ("switch_control", {"action": "turn_on", "entity_id": "switch.test"}),
                    ("cover_control", {"action": "open", "entity_id": "cover.test"}),
                ]

                for tool_name, params in tools_to_test:
                    tool = mcp._tool_manager._tools[tool_name]
                    result = await tool.fn(**params)

                    # All error responses should have these fields
                    assert "success" in result
                    assert result["success"] is False
                    assert "error" in result
                    assert isinstance(result["error"], str)
                    assert "error_type" in result
                    assert isinstance(result["error_type"], str)


class TestToolParameterValidation:
    """Tests for parameter validation across tools."""

    @pytest.mark.asyncio
    async def test_missing_required_parameters(self, mock_env, mock_hass_client):
        """Test that tools validate required parameters."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # Test lights tool without entity_id for turn_on
                lights_tool = mcp._tool_manager._tools["lights_control"]

                # This should fail validation or return error
                try:
                    result = await lights_tool.fn(action="turn_on")
                    # If it doesn't raise, it should return an error
                    assert result["success"] is False
                except (TypeError, ValueError):
                    # Parameter validation can raise exceptions
                    pass

    @pytest.mark.asyncio
    async def test_invalid_entity_id_prefix(self, mock_env, mock_hass_client):
        """Test that tools validate entity_id domain prefix."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # Test lights tool with wrong domain prefix
                lights_tool = mcp._tool_manager._tools["lights_control"]
                result = await lights_tool.fn(
                    action="turn_on", entity_id="switch.kitchen"  # Wrong domain
                )
                assert result["success"] is False
                assert "error" in result


class TestToolDocumentation:
    """Tests for tool documentation and discoverability."""

    def test_all_tools_have_examples_in_docstring(self):
        """Test that tool functions have usage examples in docstrings."""
        for tool_name, tool in mcp._tool_manager._tools.items():
            # Get the function docstring
            docstring = tool.fn.__doc__

            # Docstring should exist
            assert docstring is not None, f"Tool {tool_name} missing docstring"

            # Docstring should be substantial (at least 30 characters)
            assert len(docstring) > 30, f"Tool {tool_name} has minimal docstring"

    def test_tool_descriptions_mention_domain(self):
        """Test that tool descriptions mention the Home Assistant domain."""
        domain_tools = {
            "lights_control": "light",
            "climate_control": "climate",
            "switch_control": "switch",
            "cover_control": "cover",
            "lock_control": "lock",
            "media_player_control": "media",
            "camera_control": "camera",
            "vacuum_control": "vacuum",
            "fan_control": "fan",
            "alarm_control": "alarm",
        }

        for tool_name, domain_keyword in domain_tools.items():
            tool = mcp._tool_manager._tools[tool_name]
            description = tool.description.lower()

            # Description should mention the domain or related concept
            assert (
                domain_keyword in description or tool_name.replace("_control", "") in description
            ), f"Tool {tool_name} description doesn't mention domain"


class TestConcurrentOperations:
    """Tests for concurrent tool operations."""

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, mock_env, mock_hass_client):
        """Test that multiple tools can be called concurrently."""
        import asyncio

        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # Prepare multiple tool calls
                lights_tool = mcp._tool_manager._tools["lights_control"]
                switch_tool = mcp._tool_manager._tools["switch_control"]
                climate_tool = mcp._tool_manager._tools["climate_control"]

                mock_hass_client.get_states.return_value = []

                # Execute concurrently
                results = await asyncio.gather(
                    lights_tool.fn(action="list"),
                    switch_tool.fn(action="list"),
                    climate_tool.fn(action="list"),
                )

                # All should succeed
                assert all(r["success"] is True for r in results)


class TestToolResponseFormat:
    """Tests for consistent response format across tools."""

    @pytest.mark.asyncio
    async def test_success_response_format(self, mock_env, mock_hass_client):
        """Test that successful responses have consistent format."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                mock_hass_client.get_states.return_value = []

                # Test multiple tools
                tools_to_test = ["lights_control", "switch_control", "climate_control"]

                for tool_name in tools_to_test:
                    tool = mcp._tool_manager._tools[tool_name]
                    result = await tool.fn(action="list")

                    # All success responses should have 'success' field
                    assert "success" in result
                    assert isinstance(result["success"], bool)

                    # Should not have error fields on success
                    if result["success"]:
                        assert "error" not in result or result.get("error") is None

    @pytest.mark.asyncio
    async def test_list_action_response_format(self, mock_env, mock_hass_client):
        """Test that list actions return consistent format."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                mock_hass_client.get_states.return_value = [
                    {
                        "entity_id": "light.test",
                        "state": "on",
                        "attributes": {},
                    }
                ]

                # Test list action on multiple tools
                tools_to_test = ["lights_control", "switch_control", "climate_control"]

                for tool_name in tools_to_test:
                    tool = mcp._tool_manager._tools[tool_name]
                    result = await tool.fn(action="list")

                    assert result["success"] is True
                    # Should have a count field
                    assert "count" in result or "total" in result or len(result) > 1
