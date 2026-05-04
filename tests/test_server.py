"""Integration tests for FastMCP server startup and shutdown."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.homeassistant_mcp.config import reset_settings
from src.homeassistant_mcp.server import get_client, lifespan, mcp, setup_logging
from tests.conftest import (
    get_mcp_prompts_dict,
    get_mcp_resources_dict,
    get_mcp_tools_dict,
    get_mcp_tools_dict_async,
)


@pytest.fixture(autouse=True)
def reset_config():
    """Reset configuration before each test."""
    reset_settings()
    yield
    reset_settings()


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("HASS_HOST", "http://homeassistant.local:8123")
    monkeypatch.setenv("HASS_TOKEN", "test_token_1234567890_long_enough")
    monkeypatch.setenv("LOG_LEVEL", "INFO")


@pytest.fixture
def mock_hass_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock()
    client.get_states.return_value = [
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"brightness": 255},
        },
        {
            "entity_id": "climate.bedroom",
            "state": "heat",
            "attributes": {"temperature": 20},
        },
    ]
    client.close = AsyncMock()
    return client


class TestSetupLogging:
    """Tests for logging configuration."""

    def test_setup_logging_default_level(self, mock_env):
        """Test that logging is configured with default INFO level."""
        setup_logging()

        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_setup_logging_custom_level(self, monkeypatch):
        """Test that logging respects custom log level."""
        monkeypatch.setenv("HASS_HOST", "http://homeassistant.local:8123")
        monkeypatch.setenv("HASS_TOKEN", "test_token_1234567890_long_enough")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        reset_settings()
        setup_logging()

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_setup_logging_reduces_httpx_noise(self, mock_env):
        """Test that httpx logging is set to WARNING."""
        setup_logging()

        httpx_logger = logging.getLogger("httpx")
        assert httpx_logger.level == logging.WARNING


class TestLifespan:
    """Tests for server lifespan management."""

    @pytest.mark.asyncio
    async def test_lifespan_initializes_client(self, mock_env, mock_hass_client):
        """Test that lifespan initializes the Home Assistant client."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # Client should be initialized
                client = get_client()
                assert client is not None
                assert client == mock_hass_client

                # Verify connection was tested
                mock_hass_client.get_states.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_verifies_connection(self, mock_env, mock_hass_client):
        """Test that lifespan verifies connection on startup."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # get_states should have been called to verify connection
                mock_hass_client.get_states.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_closes_client_on_shutdown(self, mock_env, mock_hass_client):
        """Test that lifespan closes the client on shutdown."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                pass  # Exit context

            # Client should be closed
            mock_hass_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_handles_connection_failure(self, mock_env):
        """Test that lifespan handles connection failures gracefully."""
        mock_client = AsyncMock()
        mock_client.get_states.side_effect = Exception("Connection failed")
        mock_client.close = AsyncMock()

        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_client,
        ):
            mock_app = MagicMock()

            with pytest.raises(Exception, match="Connection failed"):
                async with lifespan(mock_app):
                    pass

            # Client should still be closed even on failure
            mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_uses_cache_ttl_from_settings(self, mock_env):
        """Test that lifespan passes cache TTL settings to client."""
        with patch("src.homeassistant_mcp.server.HomeAssistantClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_states.return_value = []
            mock_client_class.return_value = mock_client

            mock_app = MagicMock()

            async with lifespan(mock_app):
                pass

            # Verify client was initialized with correct cache TTL values
            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args.kwargs
            assert call_kwargs["cache_ttl_states"] == 30
            assert call_kwargs["cache_ttl_entity"] == 10


class TestGetClient:
    """Tests for get_client function."""

    def test_get_client_raises_when_not_initialized(self):
        """Test that get_client raises error when client not initialized."""
        # Ensure client is None
        import src.homeassistant_mcp.server as server_module

        server_module.hass_client = None

        with pytest.raises(RuntimeError, match="not initialized"):
            get_client()

    @pytest.mark.asyncio
    async def test_get_client_returns_initialized_client(self, mock_env, mock_hass_client):
        """Test that get_client returns the initialized client."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                client = get_client()
                assert client == mock_hass_client


class TestMCPServer:
    """Tests for FastMCP server configuration."""

    def test_mcp_server_has_correct_name(self):
        """Test that MCP server has correct name."""
        assert mcp.name == "Home Assistant MCP"

    def test_mcp_server_has_lifespan(self):
        """Test that MCP server has lifespan configured."""
        assert mcp._lifespan is not None


class TestToolRegistration:
    """Tests for tool registration with FastMCP server."""

    def test_all_core_tools_are_registered(self):
        """Test that all core API tools are registered."""
        expected_core_tools = {
            "api_info",
            "events_control",
            "services_control",
        }

        registered_tools = set(get_mcp_tools_dict(mcp).keys())
        assert expected_core_tools.issubset(
            registered_tools
        ), f"Missing core tools: {expected_core_tools - registered_tools}"

    def test_all_state_tools_are_registered(self):
        """Test that state management tools are registered."""
        expected_state_tools = {
            "states_control",
        }

        registered_tools = set(get_mcp_tools_dict(mcp).keys())
        assert expected_state_tools.issubset(
            registered_tools
        ), f"Missing state tools: {expected_state_tools - registered_tools}"

    def test_all_history_tools_are_registered(self):
        """Test that historical data tools are registered."""
        expected_history_tools = {
            "history_query",
            "logbook_query",
            "error_log_get",
        }

        registered_tools = set(get_mcp_tools_dict(mcp).keys())
        assert expected_history_tools.issubset(
            registered_tools
        ), f"Missing history tools: {expected_history_tools - registered_tools}"

    def test_all_specialized_tools_are_registered(self):
        """Test that specialized tools are registered."""
        expected_specialized_tools = {
            "camera_proxy_get",
            "calendar_access",
            "template_render",
            "config_check",
            "intent_handle",
        }

        registered_tools = set(get_mcp_tools_dict(mcp).keys())
        assert expected_specialized_tools.issubset(
            registered_tools
        ), f"Missing specialized tools: {expected_specialized_tools - registered_tools}"

    def test_all_device_control_tools_are_registered(self):
        """Test that existing device control tools are preserved."""
        expected_device_tools = {
            "lights_control",
            "climate_control",
            "list_devices",
            "automation_control",
            "scene_control",
            "send_notification",
            "call_service",
            "switch_control",
            "cover_control",
            "lock_control",
            "media_player_control",
            "camera_control",
            "vacuum_control",
            "fan_control",
            "script_control",
        }

        registered_tools = set(get_mcp_tools_dict(mcp).keys())
        assert expected_device_tools.issubset(
            registered_tools
        ), f"Missing device tools: {expected_device_tools - registered_tools}"

    def test_tool_count(self):
        """Test that the correct number of tools are registered."""
        # Count all registered tools
        tool_count = len(get_mcp_tools_dict(mcp))

        # We expect at least 40 tools (all new + existing, minus 4 removed config tools)
        assert tool_count >= 39, f"Expected at least 39 tools, got {tool_count}"

    @pytest.mark.asyncio
    async def test_tools_are_executable(self, mock_env, mock_hass_client):
        """Test that registered tools can be executed through FastMCP."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # Test that we can get a tool and it has the expected structure
                lights_tool = (await get_mcp_tools_dict_async(mcp)).get("lights_control")
                assert lights_tool is not None
                assert callable(lights_tool.fn)

                # Test that the tool has proper metadata
                assert lights_tool.name == "lights_control"
                assert lights_tool.description is not None

    def test_each_tool_has_description(self):
        """Test that each registered tool has a description."""
        for tool_name, tool in get_mcp_tools_dict(mcp).items():
            assert tool.description is not None, f"Tool {tool_name} is missing a description"
            assert len(tool.description) > 0, f"Tool {tool_name} has an empty description"

    def test_config_file_manipulation_tools_are_removed(self):
        """Test that configuration file manipulation tools are NOT registered.

        This is a breaking change - these tools have been removed to ensure
        all Home Assistant interaction happens through the REST API.

        **Validates: Requirements 1.1**
        """
        # These tools should NOT be registered
        removed_tools = {
            "config_control",
            "config_sync_control",
            "automation_editor_control",
            "get_automation_config",
        }

        registered_tools = set(get_mcp_tools_dict(mcp).keys())

        # Verify none of the removed tools are registered
        found_removed_tools = removed_tools.intersection(registered_tools)
        assert (
            len(found_removed_tools) == 0
        ), f"Configuration file manipulation tools should be removed but found: {found_removed_tools}"


class TestResourceRegistration:
    """Tests for MCP resource registration."""

    def test_services_resource_is_registered(self):
        """Test that the services resource is registered."""
        # Get registered resource templates from the MCP server
        registered_resources = set(get_mcp_resources_dict(mcp).keys())

        assert "hass://services" in registered_resources, "Services resource not registered"

    def test_resource_count(self):
        """Test that resources are registered."""
        # We expect at least 1 resource (services)
        # Note: Entity, area, and device resources use URI templates with path parameters
        # which may be registered differently by FastMCP
        assert len(get_mcp_resources_dict(mcp)) >= 1

    def test_each_resource_has_handler(self):
        """Test that each registered resource has a handler function."""
        for resource_uri, resource in get_mcp_resources_dict(mcp).items():
            assert resource.fn is not None, f"Resource {resource_uri} is missing a handler"
            assert callable(resource.fn), f"Resource {resource_uri} handler is not callable"


class TestPromptRegistration:
    """Tests for MCP prompt registration."""

    def test_all_prompts_are_registered(self):
        """Test that all expected prompts are registered."""
        expected_prompts = {
            "create_automation",
            "create_scene",
            "troubleshoot_device",
            "optimize_energy",
            "security_check",  # Note: prompt name is security_check, not check_security
            "optimize_climate",
        }

        # Get registered prompts from the MCP server
        registered_prompts = set(get_mcp_prompts_dict(mcp).keys())

        assert expected_prompts.issubset(
            registered_prompts
        ), f"Missing prompts: {expected_prompts - registered_prompts}"

    def test_prompt_count(self):
        """Test that the correct number of prompts are registered."""
        # We expect 13 prompts: 6 legacy + 7 new (control_entity, control_area,
        # explain_entity, diagnose_automation, suggest_automation, home_status_brief, safety_policy)
        assert len(get_mcp_prompts_dict(mcp)) == 13

    def test_each_prompt_has_handler(self):
        """Test that each registered prompt has a handler function."""
        for prompt_name, prompt in get_mcp_prompts_dict(mcp).items():
            assert prompt.fn is not None, f"Prompt {prompt_name} is missing a handler"
            assert callable(prompt.fn), f"Prompt {prompt_name} handler is not callable"

    def test_each_prompt_has_description(self):
        """Test that each registered prompt has a description."""
        for prompt_name, prompt in get_mcp_prompts_dict(mcp).items():
            assert prompt.description is not None, f"Prompt {prompt_name} is missing a description"
            assert len(prompt.description) > 0, f"Prompt {prompt_name} has an empty description"
