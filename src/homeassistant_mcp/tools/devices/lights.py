"""Lights control tool for Home Assistant MCP server."""

import logging
from typing import Annotated, Any, Literal

from fastmcp import Context
from pydantic import Field

from ...exceptions import (
    AuthenticationError,
    ConnectionError,
    EntityNotFoundError,
    HomeAssistantError,
    ServiceCallError,
)
from ...hass.client import HomeAssistantClient

logger = logging.getLogger(__name__)


def register_lights_tool(mcp: Any, get_client: Any) -> None:
    """Register the lights control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control", "light"},
        timeout=30,
    )
    async def lights_control(
        action: Annotated[
            Literal["list", "get", "turn_on", "turn_off"],
            Field(
                description="Action to perform: list all lights, get specific light, turn on, or turn off"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Light entity ID (required for get, turn_on, turn_off). Example: 'light.living_room'"
            ),
        ] = None,
        brightness: Annotated[
            int | None,
            Field(
                ge=0, le=255, description="Brightness level (0-255). Only used with turn_on action."
            ),
        ] = None,
        color_temp: Annotated[
            int | None,
            Field(
                ge=153,
                le=500,
                description="Color temperature in Mireds (153-500). Only used with turn_on action.",
            ),
        ] = None,
        rgb_color: Annotated[
            tuple[int, int, int] | None,
            Field(
                description="RGB color as (r, g, b) tuple where each value is 0-255. Only used with turn_on action."
            ),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Control lights in Home Assistant.

        This tool allows you to list all lights, get details about a specific light,
        turn lights on with optional brightness and color settings, or turn lights off.

        Actions:
        - list: Get all light entities with their current states
        - get: Get detailed information about a specific light
        - turn_on: Turn on a light with optional brightness, color temperature, or RGB color
        - turn_off: Turn off a light

        Examples:
        - List all lights: lights_control(action="list")
        - Get light details: lights_control(action="get", entity_id="light.living_room")
        - Turn on light: lights_control(action="turn_on", entity_id="light.living_room")
        - Turn on with brightness: lights_control(action="turn_on", entity_id="light.living_room", brightness=128)
        - Turn on with color temp: lights_control(action="turn_on", entity_id="light.living_room", color_temp=300)
        - Turn on with RGB: lights_control(action="turn_on", entity_id="light.living_room", rgb_color=(255, 0, 0))
        - Turn off light: lights_control(action="turn_off", entity_id="light.living_room")

        Note: The list action returns entities from the HA states API. If some
            entities are missing, use states_control(action="list", domain="light")
            or list_devices(domain="light") for a more complete view.

        Args:
            action: The action to perform
            entity_id: The light entity ID (required for get, turn_on, turn_off)
            brightness: Brightness level 0-255 (optional, for turn_on)
            color_temp: Color temperature in Mireds 153-500 (optional, for turn_on)
            rgb_color: RGB color tuple (r, g, b) with values 0-255 (optional, for turn_on)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing lights_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_lights(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_light(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "turn_on":
                if not entity_id:
                    return {"error": "entity_id is required for 'turn_on' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _turn_on_light(client, entity_id, brightness, color_temp, rgb_color)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "turn_off":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'turn_off' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _turn_off_light(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

        except EntityNotFoundError as e:
            logger.warning(f"Entity not found: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "entity_not_found"}
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
            logger.error(f"Unexpected error in lights_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_lights(client: HomeAssistantClient) -> dict:
    """List all light entities.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing list of lights with their states
    """
    logger.info("Listing all light entities")

    # Get all states and filter for lights
    all_states = await client.get_states()
    lights = [state for state in all_states if state.get("entity_id", "").startswith("light.")]

    # Format the response
    light_list = []
    for light in lights:
        light_info = {
            "entity_id": light.get("entity_id"),
            "name": light.get("attributes", {}).get("friendly_name", light.get("entity_id")),
            "state": light.get("state"),
        }

        # Add brightness if available
        if "brightness" in light.get("attributes", {}):
            light_info["brightness"] = light["attributes"]["brightness"]

        # Add color information if available
        if "color_temp" in light.get("attributes", {}):
            light_info["color_temp"] = light["attributes"]["color_temp"]

        if "rgb_color" in light.get("attributes", {}):
            light_info["rgb_color"] = light["attributes"]["rgb_color"]

        light_list.append(light_info)

    logger.info(f"Found {len(light_list)} light entities")

    return {"success": True, "count": len(light_list), "lights": light_list}


async def _get_light(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific light.

    Args:
        client: The Home Assistant client
        entity_id: The light entity ID

    Returns:
        Dictionary containing detailed light information

    Raises:
        EntityNotFoundError: If the light entity is not found
    """
    logger.info(f"Getting details for light: {entity_id}")

    # Validate that this is a light entity
    if not entity_id.startswith("light."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a light entity. Light entities must start with 'light.'"
        )

    # Get the entity state
    state = await client.get_state(entity_id)

    # Format the response with all available information
    light_info = {
        "entity_id": state.get("entity_id"),
        "name": state.get("attributes", {}).get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": state.get("attributes", {}),
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")

    return {"success": True, "light": light_info}


async def _turn_on_light(
    client: HomeAssistantClient,
    entity_id: str,
    brightness: int | None = None,
    color_temp: int | None = None,
    rgb_color: tuple[int, int, int] | None = None,
) -> dict:
    """Turn on a light with optional parameters.

    Args:
        client: The Home Assistant client
        entity_id: The light entity ID
        brightness: Optional brightness level (0-255)
        color_temp: Optional color temperature in Mireds (153-500)
        rgb_color: Optional RGB color tuple (r, g, b) with values 0-255

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the light entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Turning on light: {entity_id}")

    # Validate that this is a light entity
    if not entity_id.startswith("light."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a light entity. Light entities must start with 'light.'"
        )

    # Build service data
    service_data: dict[str, Any] = {"entity_id": entity_id}

    if brightness is not None:
        service_data["brightness"] = brightness
        logger.debug(f"Setting brightness to {brightness}")

    if color_temp is not None:
        service_data["color_temp"] = color_temp
        logger.debug(f"Setting color temperature to {color_temp}")

    if rgb_color is not None:
        # Validate RGB values
        if len(rgb_color) != 3:
            return {
                "error": "rgb_color must be a tuple of exactly 3 values (r, g, b)",
                "success": False,
            }

        for i, value in enumerate(rgb_color):
            if not isinstance(value, int) or value < 0 or value > 255:
                return {
                    "error": f"RGB value at index {i} must be an integer between 0 and 255, got {value}",
                    "success": False,
                }

        service_data["rgb_color"] = list(rgb_color)
        logger.debug(f"Setting RGB color to {rgb_color}")

    # Call the service
    await client.call_service("light", "turn_on", service_data)

    logger.info(f"Successfully turned on light: {entity_id}")

    return {
        "success": True,
        "message": f"Light '{entity_id}' turned on",
        "entity_id": entity_id,
        "parameters": {
            k: v
            for k, v in {
                "brightness": brightness,
                "color_temp": color_temp,
                "rgb_color": rgb_color,
            }.items()
            if v is not None
        },
    }


async def _turn_off_light(client: HomeAssistantClient, entity_id: str) -> dict:
    """Turn off a light.

    Args:
        client: The Home Assistant client
        entity_id: The light entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the light entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Turning off light: {entity_id}")

    # Validate that this is a light entity
    if not entity_id.startswith("light."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a light entity. Light entities must start with 'light.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("light", "turn_off", service_data)

    logger.info(f"Successfully turned off light: {entity_id}")

    return {"success": True, "message": f"Light '{entity_id}' turned off", "entity_id": entity_id}
