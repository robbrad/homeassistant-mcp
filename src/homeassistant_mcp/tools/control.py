"""Generic service call tool for Home Assistant MCP server."""

import logging
from typing import Annotated, Any

from fastmcp import Context
from pydantic import Field

from ..exceptions import (
    AuthenticationError,
    ConnectionError,
    HomeAssistantError,
    ServiceCallError,
)
from ..hass.client import HomeAssistantClient

logger = logging.getLogger(__name__)


def register_control_tool(mcp: Any, get_client: Any) -> None:
    """Register the generic control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control", "generic"},
        timeout=30,
    )
    async def call_service(
        domain: Annotated[
            str,
            Field(
                description="Service domain (e.g., 'light', 'switch', 'climate', 'media_player')"
            ),
        ],
        service: Annotated[
            str, Field(description="Service name (e.g., 'turn_on', 'turn_off', 'set_temperature')")
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Target entity ID (optional, some services don't require it). Example: 'light.living_room'"
            ),
        ] = None,
        data: Annotated[
            dict[str, Any] | None,
            Field(description="Additional service data as key-value pairs (optional)"),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Call any Home Assistant service with custom parameters.

        This is a generic tool that allows calling any Home Assistant service across all domains.
        Use this when you need to call a service that doesn't have a dedicated tool, or when
        you need fine-grained control over service parameters.

        Common domains and services:
        - light: turn_on, turn_off, toggle
        - switch: turn_on, turn_off, toggle
        - climate: set_temperature, set_hvac_mode, set_fan_mode
        - media_player: play_media, media_play, media_pause, volume_set
        - cover: open_cover, close_cover, stop_cover
        - lock: lock, unlock
        - vacuum: start, stop, return_to_base
        - script: turn_on (to run scripts)
        - homeassistant: restart, stop

        Examples:
        - Turn on a switch: call_service(domain="switch", service="turn_on", entity_id="switch.fan")
        - Set media player volume: call_service(domain="media_player", service="volume_set",
                                               entity_id="media_player.living_room",
                                               data={"volume_level": 0.5})
        - Open a cover: call_service(domain="cover", service="open_cover", entity_id="cover.garage")
        - Run a script: call_service(domain="script", service="turn_on", entity_id="script.movie_mode")
        - Restart Home Assistant: call_service(domain="homeassistant", service="restart")

        Args:
            domain: The service domain
            service: The service name
            entity_id: The target entity ID (optional)
            data: Additional service data (optional)

        Returns:
            Dictionary containing the result of the service call
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing call_service {domain}.{service}")

            if ctx:
                await ctx.report_progress(progress=50, total=100)
            result = await _call_service(client, domain, service, entity_id, data)
            if ctx:
                await ctx.report_progress(progress=100, total=100)
            return result

        except AuthenticationError as e:
            logger.error(f"Authentication error: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "authentication_error"}
        except ConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "connection_error"}
        except ServiceCallError as e:
            logger.error(f"Service call error: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "service_call_error"}
        except HomeAssistantError as e:
            logger.error(f"Home Assistant error: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "home_assistant_error"}
        except Exception as e:
            logger.error(f"Unexpected error in call_service: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _call_service(
    client: HomeAssistantClient,
    domain: str,
    service: str,
    entity_id: str | None,
    data: dict[str, Any] | None,
) -> dict:
    """Call a Home Assistant service with the provided parameters.

    Args:
        client: The Home Assistant client
        domain: The service domain
        service: The service name
        entity_id: The target entity ID (optional)
        data: Additional service data (optional)

    Returns:
        Dictionary containing the result of the service call

    Raises:
        ServiceCallError: If the service call fails
    """
    logger.info(f"Calling service {domain}.{service}")

    # Build service data
    service_data = data.copy() if data else {}

    # Add entity_id to service data if provided
    if entity_id:
        service_data["entity_id"] = entity_id
        logger.debug(f"Target entity: {entity_id}")

    # Log the service data (excluding sensitive information)
    if service_data:
        safe_data = {
            k: v for k, v in service_data.items() if k not in ["password", "token", "api_key"]
        }
        logger.debug(f"Service data: {safe_data}")

    # Call the service
    await client.call_service(domain, service, service_data)

    logger.info(f"Successfully called service {domain}.{service}")

    return {
        "success": True,
        "message": f"Service '{domain}.{service}' called successfully",
        "domain": domain,
        "service": service,
        "entity_id": entity_id,
        "data": service_data,
    }
