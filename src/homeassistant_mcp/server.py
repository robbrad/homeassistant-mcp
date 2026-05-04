"""FastMCP server for Home Assistant integration.

This module sets up the FastMCP server with lifespan management for proper
initialization and cleanup of the Home Assistant client connection.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from fastmcp.server.transforms.search import BM25SearchTransform

from .config import get_settings
from .hass.client import HomeAssistantClient
from .prompts import register_all_prompts
from .resources import register_all_resources
from .tools import (
    register_alarm_tool,
    register_automation_tool,
    register_camera_tool,
    register_climate_tool,
    register_control_tool,
    register_cover_tool,
    register_devices_tool,
    register_fan_tool,
    register_history_tools,
    register_humidifier_tool,
    register_input_boolean_tool,
    register_input_datetime_tool,
    register_input_number_tool,
    register_input_select_tool,
    register_input_text_tool,
    register_lawn_mower_tool,
    register_lights_tool,
    register_lock_tool,
    register_media_player_tool,
    register_notify_tool,
    register_scene_tool,
    register_script_tool,
    register_siren_tool,
    register_state_tools,
    register_switch_tool,
    register_vacuum_tool,
    register_valve_tool,
    register_water_heater_tool,
    register_weather_tool,
)
from .tools.core import (
    register_api_info_tool,
    register_events_control_tool,
    register_services_control_tool,
)
from .tools.specialized import (
    register_calendar_tool,
    register_camera_proxy_tool,
    register_config_check_tool,
    register_intent_tool,
    register_template_tool,
)

# Global client instance
hass_client: HomeAssistantClient | None = None


def setup_logging() -> None:
    """Configure logging based on settings.

    Sets up the root logger with the configured log level and format.
    Also reduces noise from httpx by setting it to WARNING level.
    """
    settings = get_settings()

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,  # Override any existing configuration
    )

    # Reduce noise from httpx
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {settings.log_level} level")


@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[None]:
    """Manage server lifecycle for initialization and cleanup.

    This context manager:
    1. Loads configuration from environment variables
    2. Sets up logging
    3. Initializes the Home Assistant client
    4. Verifies the connection to Home Assistant
    5. Yields control to the server
    6. Cleans up resources on shutdown

    Args:
        app: The FastMCP application instance

    Raises:
        ValidationError: If configuration is invalid
        ConnectionError: If unable to connect to Home Assistant
        AuthenticationError: If authentication fails
    """
    global hass_client

    logger = logging.getLogger(__name__)

    # Load settings
    logger.info("Loading configuration...")
    settings = get_settings()

    # Setup logging based on settings
    setup_logging()

    # Initialize Home Assistant client
    logger.info(f"Initializing Home Assistant client for {settings.hass_host}")
    hass_client = HomeAssistantClient(
        base_url=settings.hass_host,
        token=settings.hass_token,
        cache_ttl_states=settings.cache_ttl_states,
        cache_ttl_entity=settings.cache_ttl_entity,
    )

    # Verify connection by fetching states
    try:
        logger.info("Verifying connection to Home Assistant...")
        states = await hass_client.get_states()
        logger.info(
            f"Successfully connected to Home Assistant " f"({len(states)} entities available)"
        )
    except Exception as e:
        logger.error(f"Failed to connect to Home Assistant: {e}")
        await hass_client.close()
        raise

    logger.info(f"{settings.server_name} v{settings.server_version} started successfully")

    # Yield control to the server
    yield

    # Cleanup on shutdown
    logger.info("Shutting down server...")
    if hass_client:
        await hass_client.close()
    logger.info("Server shutdown complete")


# Create FastMCP server instance with lifespan and tool search
mcp = FastMCP(
    name="Home Assistant MCP",
    lifespan=lifespan,
    transforms=[
        BM25SearchTransform(
            max_results=10,
            always_visible=[
                "states_control",
                "list_devices",
                "call_service",
                "template_render",
                "error_log_get",
                "discover_tools",
            ],
        ),
    ],
)


def get_client() -> HomeAssistantClient:
    """Get the global Home Assistant client instance.

    Returns:
        The initialized HomeAssistantClient instance

    Raises:
        RuntimeError: If the client has not been initialized
    """
    if hass_client is None:
        raise RuntimeError(
            "Home Assistant client not initialized. " "Server may not have started properly."
        )
    return hass_client


# Register all tools with the MCP server
# Core API tools
register_api_info_tool(mcp, get_client)
register_events_control_tool(mcp, get_client)
register_services_control_tool(mcp, get_client)

# State management tools
register_state_tools(mcp, get_client)

# Historical data tools (new)
register_history_tools(mcp, get_client)

# Specialized tools
register_camera_proxy_tool(mcp, get_client)
register_calendar_tool(mcp, get_client)
register_template_tool(mcp, get_client)
register_config_check_tool(mcp, get_client)
register_intent_tool(mcp, get_client)

# Device control tools
register_lights_tool(mcp, get_client)
register_climate_tool(mcp, get_client)
register_devices_tool(mcp, get_client)
register_automation_tool(mcp, get_client)
register_scene_tool(mcp, get_client)
register_notify_tool(mcp, get_client)
register_control_tool(mcp, get_client)
register_switch_tool(mcp, get_client)
register_cover_tool(mcp, get_client)
register_lock_tool(mcp, get_client)
register_media_player_tool(mcp, get_client)
register_camera_tool(mcp, get_client)
register_vacuum_tool(mcp, get_client)
register_fan_tool(mcp, get_client)
register_script_tool(mcp, get_client)
register_input_boolean_tool(mcp, get_client)
register_input_number_tool(mcp, get_client)
register_input_select_tool(mcp, get_client)
register_input_text_tool(mcp, get_client)
register_input_datetime_tool(mcp, get_client)
register_weather_tool(mcp, get_client)
register_alarm_tool(mcp, get_client)
register_water_heater_tool(mcp, get_client)
register_humidifier_tool(mcp, get_client)
register_siren_tool(mcp, get_client)
register_valve_tool(mcp, get_client)
register_lawn_mower_tool(mcp, get_client)

# Register all MCP resources
register_all_resources(mcp, get_client)

# Register all MCP prompts
register_all_prompts(mcp, get_client)


# Tool catalog for discovery — helps LLMs know what's available via search_tools
_TOOL_CATALOG = """Available tools (use search_tools to find and call them):

DEVICE CONTROL: lights_control, climate_control, switch_control, cover_control,
  lock_control, media_player_control, camera_control, vacuum_control, fan_control,
  alarm_control, water_heater_control, humidifier_control, siren_control,
  valve_control, lawn_mower_control, weather_control

AUTOMATION: automation_control, scene_control, script_control

INPUT HELPERS: input_boolean_control, input_number_control, input_select_control,
  input_text_control, input_datetime_control

API & STATE: api_info, events_control, services_control, states_control

HISTORY: history_query, logbook_query, error_log_get

SPECIALIZED: calendar_access, camera_proxy_get, config_check, intent_handle,
  template_render

GENERAL: list_devices, call_service, send_notification
"""


@mcp.tool(
    annotations={"readOnlyHint": True},
    tags={"discovery"},
    timeout=5,
)
def discover_tools() -> str:
    """List all available Home Assistant MCP tools.

    Returns a catalog of every tool available on this server, organized by
    category. Use search_tools(query="...") to get full details and schemas
    for any tool, then call_tool(name="...", arguments={...}) to execute it.

    Categories: device control, automation, input helpers, API & state,
    history, specialized, and general tools.
    """
    return _TOOL_CATALOG


def main() -> None:
    """Entry point for the homeassistant-mcp command."""
    import sys

    if "--version" in sys.argv:
        from importlib.metadata import version as _get_version

        try:
            print(f"homeassistant-mcp {_get_version('homeassistant-mcp')}")
        except Exception:
            print("homeassistant-mcp (version unknown)")
        return

    # Check if we should run in SSE mode for Inspector
    if "--sse" in sys.argv:
        # Remove --sse from argv so it doesn't interfere
        sys.argv.remove("--sse")
        # Run with SSE transport for web-based Inspector
        mcp.run(transport="sse")
    else:
        # Default to STDIO for Claude Desktop, Cursor, etc.
        mcp.run()


# Entry point for running the server
if __name__ == "__main__":
    main()
