"""Fan control tool for Home Assistant MCP server."""

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


def register_fan_tool(mcp: Any, get_client: Any) -> None:
    """Register the fan control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control", "fan"},
        timeout=30,
    )
    async def fan_control(
        action: Annotated[
            Literal[
                "list",
                "get",
                "turn_on",
                "turn_off",
                "set_percentage",
                "set_preset_mode",
                "oscillate",
                "set_direction",
            ],
            Field(
                description="Action to perform: list all fans, get specific fan, turn on, turn off, set percentage, set preset mode, oscillate, or set direction"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Fan entity ID (required for get, turn_on, turn_off, set_percentage, set_preset_mode, oscillate, set_direction). Example: 'fan.bedroom'"
            ),
        ] = None,
        percentage: Annotated[
            int | None,
            Field(
                ge=0,
                le=100,
                description="Fan speed percentage (0-100). Only used with set_percentage action.",
            ),
        ] = None,
        preset_mode: Annotated[
            str | None,
            Field(
                description="Preset mode name (e.g., 'auto', 'smart', 'sleep'). Only used with set_preset_mode action."
            ),
        ] = None,
        oscillating: Annotated[
            bool | None,
            Field(description="Enable or disable oscillation. Only used with oscillate action."),
        ] = None,
        direction: Annotated[
            Literal["forward", "reverse"] | None,
            Field(description="Fan rotation direction. Only used with set_direction action."),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Control fans in Home Assistant.

        This tool allows you to list all fans, get details about a specific fan,
        turn fans on/off, control speed, set preset modes, control oscillation, and set direction.

        Actions:
        - list: Get all fan entities with their current states
        - get: Get detailed information about a specific fan
        - turn_on: Turn on a fan
        - turn_off: Turn off a fan
        - set_percentage: Set fan speed percentage (0-100)
        - set_preset_mode: Set a preset mode (e.g., 'auto', 'smart', 'sleep')
        - oscillate: Enable or disable oscillation
        - set_direction: Set rotation direction (forward/reverse)

        Examples:
        - List all fans: fan_control(action="list")
        - Get fan details: fan_control(action="get", entity_id="fan.bedroom")
        - Turn on fan: fan_control(action="turn_on", entity_id="fan.bedroom")
        - Turn off fan: fan_control(action="turn_off", entity_id="fan.bedroom")
        - Set speed: fan_control(action="set_percentage", entity_id="fan.bedroom", percentage=75)
        - Set preset: fan_control(action="set_preset_mode", entity_id="fan.bedroom", preset_mode="auto")
        - Enable oscillation: fan_control(action="oscillate", entity_id="fan.bedroom", oscillating=True)
        - Set direction: fan_control(action="set_direction", entity_id="fan.bedroom", direction="reverse")

        Args:
            action: The action to perform
            entity_id: The fan entity ID (required for most actions)
            percentage: Fan speed percentage 0-100 (optional, for set_percentage)
            preset_mode: Preset mode name (optional, for set_preset_mode)
            oscillating: Enable/disable oscillation (optional, for oscillate)
            direction: Rotation direction (optional, for set_direction)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing fan_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_fans(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_fan(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "turn_on":
                if not entity_id:
                    return {"error": "entity_id is required for 'turn_on' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _turn_on_fan(client, entity_id)
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
                result = await _turn_off_fan(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_percentage":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_percentage' action",
                        "success": False,
                    }
                if percentage is None:
                    return {
                        "error": "percentage is required for 'set_percentage' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_percentage(client, entity_id, percentage)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_preset_mode":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_preset_mode' action",
                        "success": False,
                    }
                if not preset_mode:
                    return {
                        "error": "preset_mode is required for 'set_preset_mode' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_preset_mode(client, entity_id, preset_mode)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "oscillate":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'oscillate' action",
                        "success": False,
                    }
                if oscillating is None:
                    return {
                        "error": "oscillating is required for 'oscillate' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _oscillate(client, entity_id, oscillating)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_direction":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_direction' action",
                        "success": False,
                    }
                if not direction:
                    return {
                        "error": "direction is required for 'set_direction' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_direction(client, entity_id, direction)
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
            logger.error(f"Unexpected error in fan_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_fans(client: HomeAssistantClient) -> dict:
    """List all fan entities.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing list of fans with their states
    """
    logger.info("Listing all fan entities")

    # Get all states and filter for fans
    all_states = await client.get_states()
    fans = [state for state in all_states if state.get("entity_id", "").startswith("fan.")]

    # Format the response
    fan_list = []
    for fan in fans:
        fan_info = {
            "entity_id": fan.get("entity_id"),
            "name": fan.get("attributes", {}).get("friendly_name", fan.get("entity_id")),
            "state": fan.get("state"),
        }

        attrs = fan.get("attributes", {})

        # Add speed information if available
        if "percentage" in attrs:
            fan_info["percentage"] = attrs["percentage"]

        # Add preset mode if available
        if "preset_mode" in attrs:
            fan_info["preset_mode"] = attrs["preset_mode"]

        # Add oscillation status if available
        if "oscillating" in attrs:
            fan_info["oscillating"] = attrs["oscillating"]

        # Add direction if available
        if "direction" in attrs:
            fan_info["direction"] = attrs["direction"]

        fan_list.append(fan_info)

    logger.info(f"Found {len(fan_list)} fan entities")

    return {"success": True, "count": len(fan_list), "fans": fan_list}


async def _get_fan(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific fan.

    Args:
        client: The Home Assistant client
        entity_id: The fan entity ID

    Returns:
        Dictionary containing detailed fan information

    Raises:
        EntityNotFoundError: If the fan entity is not found
    """
    logger.info(f"Getting details for fan: {entity_id}")

    # Validate that this is a fan entity
    if not entity_id.startswith("fan."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a fan entity. Fan entities must start with 'fan.'"
        )

    # Get the entity state
    state = await client.get_state(entity_id)

    # Format the response with all available information
    fan_info = {
        "entity_id": state.get("entity_id"),
        "name": state.get("attributes", {}).get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": state.get("attributes", {}),
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")

    return {"success": True, "fan": fan_info}


async def _turn_on_fan(client: HomeAssistantClient, entity_id: str) -> dict:
    """Turn on a fan.

    Args:
        client: The Home Assistant client
        entity_id: The fan entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the fan entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Turning on fan: {entity_id}")

    # Validate that this is a fan entity
    if not entity_id.startswith("fan."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a fan entity. Fan entities must start with 'fan.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("fan", "turn_on", service_data)

    logger.info(f"Successfully turned on fan: {entity_id}")

    return {"success": True, "message": f"Fan '{entity_id}' turned on", "entity_id": entity_id}


async def _turn_off_fan(client: HomeAssistantClient, entity_id: str) -> dict:
    """Turn off a fan.

    Args:
        client: The Home Assistant client
        entity_id: The fan entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the fan entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Turning off fan: {entity_id}")

    # Validate that this is a fan entity
    if not entity_id.startswith("fan."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a fan entity. Fan entities must start with 'fan.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("fan", "turn_off", service_data)

    logger.info(f"Successfully turned off fan: {entity_id}")

    return {"success": True, "message": f"Fan '{entity_id}' turned off", "entity_id": entity_id}


async def _set_percentage(client: HomeAssistantClient, entity_id: str, percentage: int) -> dict:
    """Set the fan speed percentage.

    Args:
        client: The Home Assistant client
        entity_id: The fan entity ID
        percentage: Speed percentage (0-100)

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the fan entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Setting fan {entity_id} speed to {percentage}%")

    # Validate that this is a fan entity
    if not entity_id.startswith("fan."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a fan entity. Fan entities must start with 'fan.'"
        )

    # Build service data
    service_data = {"entity_id": entity_id, "percentage": percentage}

    # Call the service
    await client.call_service("fan", "set_percentage", service_data)

    logger.info(f"Successfully set fan {entity_id} speed to {percentage}%")

    return {
        "success": True,
        "message": f"Fan '{entity_id}' speed set to {percentage}%",
        "entity_id": entity_id,
        "percentage": percentage,
    }


async def _set_preset_mode(client: HomeAssistantClient, entity_id: str, preset_mode: str) -> dict:
    """Set the fan preset mode.

    Args:
        client: The Home Assistant client
        entity_id: The fan entity ID
        preset_mode: Preset mode name

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the fan entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Setting fan {entity_id} preset mode to {preset_mode}")

    # Validate that this is a fan entity
    if not entity_id.startswith("fan."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a fan entity. Fan entities must start with 'fan.'"
        )

    # Build service data
    service_data = {"entity_id": entity_id, "preset_mode": preset_mode}

    # Call the service
    await client.call_service("fan", "set_preset_mode", service_data)

    logger.info(f"Successfully set fan {entity_id} preset mode to {preset_mode}")

    return {
        "success": True,
        "message": f"Fan '{entity_id}' preset mode set to '{preset_mode}'",
        "entity_id": entity_id,
        "preset_mode": preset_mode,
    }


async def _oscillate(client: HomeAssistantClient, entity_id: str, oscillating: bool) -> dict:
    """Control fan oscillation.

    Args:
        client: The Home Assistant client
        entity_id: The fan entity ID
        oscillating: Enable or disable oscillation

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the fan entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Setting fan {entity_id} oscillation to {oscillating}")

    # Validate that this is a fan entity
    if not entity_id.startswith("fan."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a fan entity. Fan entities must start with 'fan.'"
        )

    # Build service data
    service_data = {"entity_id": entity_id, "oscillating": oscillating}

    # Call the service
    await client.call_service("fan", "oscillate", service_data)

    logger.info(f"Successfully set fan {entity_id} oscillation to {oscillating}")

    return {
        "success": True,
        "message": f"Fan '{entity_id}' oscillation {'enabled' if oscillating else 'disabled'}",
        "entity_id": entity_id,
        "oscillating": oscillating,
    }


async def _set_direction(
    client: HomeAssistantClient, entity_id: str, direction: Literal["forward", "reverse"]
) -> dict:
    """Set the fan rotation direction.

    Args:
        client: The Home Assistant client
        entity_id: The fan entity ID
        direction: Rotation direction (forward or reverse)

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the fan entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Setting fan {entity_id} direction to {direction}")

    # Validate that this is a fan entity
    if not entity_id.startswith("fan."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a fan entity. Fan entities must start with 'fan.'"
        )

    # Build service data
    service_data = {"entity_id": entity_id, "direction": direction}

    # Call the service
    await client.call_service("fan", "set_direction", service_data)

    logger.info(f"Successfully set fan {entity_id} direction to {direction}")

    return {
        "success": True,
        "message": f"Fan '{entity_id}' direction set to '{direction}'",
        "entity_id": entity_id,
        "direction": direction,
    }
