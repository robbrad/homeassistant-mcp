"""Vacuum control tool for Home Assistant MCP server."""

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


def register_vacuum_tool(mcp: Any, get_client: Any) -> None:
    """Register the vacuum control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control"},
        timeout=30,
    )
    async def vacuum_control(
        action: Annotated[
            Literal[
                "list", "get", "start", "pause", "stop", "return_to_base", "locate", "set_fan_speed"
            ],
            Field(
                description="Action to perform: list all vacuums, get specific vacuum, start, pause, stop, return to base, locate, or set fan speed"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Vacuum entity ID (required for get, start, pause, stop, return_to_base, locate, set_fan_speed). Example: 'vacuum.living_room'"
            ),
        ] = None,
        fan_speed: Annotated[
            str | None,
            Field(
                description="Fan speed level (optional, for set_fan_speed action). Example: 'low', 'medium', 'high', 'auto'"
            ),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Control robot vacuums in Home Assistant.

        This tool allows you to list all vacuums, get details about a specific vacuum,
        and control vacuum operations including cleaning, pausing, and returning to base.

        Actions:
        - list: Get all vacuum entities with their current state, battery, and cleaning status
        - get: Get detailed information about a specific vacuum
        - start: Start cleaning
        - pause: Pause cleaning
        - stop: Stop cleaning
        - return_to_base: Send vacuum to charging dock
        - locate: Trigger vacuum's locate function (usually plays a sound)
        - set_fan_speed: Set suction power level

        Examples:
        - List all vacuums: vacuum_control(action="list")
        - Get vacuum details: vacuum_control(action="get", entity_id="vacuum.living_room")
        - Start cleaning: vacuum_control(action="start", entity_id="vacuum.living_room")
        - Pause cleaning: vacuum_control(action="pause", entity_id="vacuum.living_room")
        - Stop cleaning: vacuum_control(action="stop", entity_id="vacuum.living_room")
        - Return to base: vacuum_control(action="return_to_base", entity_id="vacuum.living_room")
        - Locate vacuum: vacuum_control(action="locate", entity_id="vacuum.living_room")
        - Set fan speed: vacuum_control(action="set_fan_speed", entity_id="vacuum.living_room", fan_speed="high")

        Args:
            action: The action to perform
            entity_id: The vacuum entity ID (required for most actions)
            fan_speed: Fan speed level (required for set_fan_speed action)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing vacuum_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_vacuums(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_vacuum(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "start":
                if not entity_id:
                    return {"error": "entity_id is required for 'start' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _start_vacuum(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "pause":
                if not entity_id:
                    return {"error": "entity_id is required for 'pause' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _pause_vacuum(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "stop":
                if not entity_id:
                    return {"error": "entity_id is required for 'stop' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _stop_vacuum(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "return_to_base":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'return_to_base' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _return_to_base(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "locate":
                if not entity_id:
                    return {"error": "entity_id is required for 'locate' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _locate_vacuum(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_fan_speed":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_fan_speed' action",
                        "success": False,
                    }
                if not fan_speed:
                    return {
                        "error": "fan_speed is required for 'set_fan_speed' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_fan_speed(client, entity_id, fan_speed)
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
            logger.error(f"Unexpected error in vacuum_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_vacuums(client: HomeAssistantClient) -> dict:
    """List all vacuum entities.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing list of vacuums with their states
    """
    logger.info("Listing all vacuum entities")

    # Get all states and filter for vacuums
    all_states = await client.get_states()
    vacuums = [state for state in all_states if state.get("entity_id", "").startswith("vacuum.")]

    # Format the response
    vacuum_list = []
    for vacuum in vacuums:
        vacuum_info = {
            "entity_id": vacuum.get("entity_id"),
            "name": vacuum.get("attributes", {}).get("friendly_name", vacuum.get("entity_id")),
            "state": vacuum.get("state"),
        }

        # Add battery level if available
        if "battery_level" in vacuum.get("attributes", {}):
            vacuum_info["battery_level"] = vacuum["attributes"]["battery_level"]

        # Add fan speed if available
        if "fan_speed" in vacuum.get("attributes", {}):
            vacuum_info["fan_speed"] = vacuum["attributes"]["fan_speed"]

        # Add status if available
        if "status" in vacuum.get("attributes", {}):
            vacuum_info["status"] = vacuum["attributes"]["status"]

        vacuum_list.append(vacuum_info)

    logger.info(f"Found {len(vacuum_list)} vacuum entities")

    return {"success": True, "count": len(vacuum_list), "vacuums": vacuum_list}


async def _get_vacuum(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific vacuum.

    Args:
        client: The Home Assistant client
        entity_id: The vacuum entity ID

    Returns:
        Dictionary containing detailed vacuum information

    Raises:
        EntityNotFoundError: If the vacuum entity is not found
    """
    logger.info(f"Getting details for vacuum: {entity_id}")

    # Validate that this is a vacuum entity
    if not entity_id.startswith("vacuum."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a vacuum entity. Vacuum entities must start with 'vacuum.'"
        )

    # Get the entity state
    state = await client.get_state(entity_id)

    # Format the response with all available information
    vacuum_info = {
        "entity_id": state.get("entity_id"),
        "name": state.get("attributes", {}).get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": state.get("attributes", {}),
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")

    return {"success": True, "vacuum": vacuum_info}


async def _start_vacuum(client: HomeAssistantClient, entity_id: str) -> dict:
    """Start vacuum cleaning.

    Args:
        client: The Home Assistant client
        entity_id: The vacuum entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the vacuum entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Starting vacuum: {entity_id}")

    # Validate that this is a vacuum entity
    if not entity_id.startswith("vacuum."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a vacuum entity. Vacuum entities must start with 'vacuum.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("vacuum", "start", service_data)

    logger.info(f"Successfully started vacuum: {entity_id}")

    return {
        "success": True,
        "message": f"Vacuum '{entity_id}' started cleaning",
        "entity_id": entity_id,
    }


async def _pause_vacuum(client: HomeAssistantClient, entity_id: str) -> dict:
    """Pause vacuum cleaning.

    Args:
        client: The Home Assistant client
        entity_id: The vacuum entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the vacuum entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Pausing vacuum: {entity_id}")

    # Validate that this is a vacuum entity
    if not entity_id.startswith("vacuum."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a vacuum entity. Vacuum entities must start with 'vacuum.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("vacuum", "pause", service_data)

    logger.info(f"Successfully paused vacuum: {entity_id}")

    return {
        "success": True,
        "message": f"Vacuum '{entity_id}' paused",
        "entity_id": entity_id,
    }


async def _stop_vacuum(client: HomeAssistantClient, entity_id: str) -> dict:
    """Stop vacuum cleaning.

    Args:
        client: The Home Assistant client
        entity_id: The vacuum entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the vacuum entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Stopping vacuum: {entity_id}")

    # Validate that this is a vacuum entity
    if not entity_id.startswith("vacuum."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a vacuum entity. Vacuum entities must start with 'vacuum.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("vacuum", "stop", service_data)

    logger.info(f"Successfully stopped vacuum: {entity_id}")

    return {
        "success": True,
        "message": f"Vacuum '{entity_id}' stopped",
        "entity_id": entity_id,
    }


async def _return_to_base(client: HomeAssistantClient, entity_id: str) -> dict:
    """Send vacuum to charging dock.

    Args:
        client: The Home Assistant client
        entity_id: The vacuum entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the vacuum entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Sending vacuum to base: {entity_id}")

    # Validate that this is a vacuum entity
    if not entity_id.startswith("vacuum."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a vacuum entity. Vacuum entities must start with 'vacuum.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("vacuum", "return_to_base", service_data)

    logger.info(f"Successfully sent vacuum to base: {entity_id}")

    return {
        "success": True,
        "message": f"Vacuum '{entity_id}' returning to base",
        "entity_id": entity_id,
    }


async def _locate_vacuum(client: HomeAssistantClient, entity_id: str) -> dict:
    """Trigger vacuum's locate function.

    Args:
        client: The Home Assistant client
        entity_id: The vacuum entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the vacuum entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Locating vacuum: {entity_id}")

    # Validate that this is a vacuum entity
    if not entity_id.startswith("vacuum."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a vacuum entity. Vacuum entities must start with 'vacuum.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("vacuum", "locate", service_data)

    logger.info(f"Successfully triggered locate for vacuum: {entity_id}")

    return {
        "success": True,
        "message": f"Vacuum '{entity_id}' locate triggered",
        "entity_id": entity_id,
    }


async def _set_fan_speed(client: HomeAssistantClient, entity_id: str, fan_speed: str) -> dict:
    """Set vacuum fan speed.

    Args:
        client: The Home Assistant client
        entity_id: The vacuum entity ID
        fan_speed: The fan speed level

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the vacuum entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Setting fan speed for vacuum {entity_id} to {fan_speed}")

    # Validate that this is a vacuum entity
    if not entity_id.startswith("vacuum."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a vacuum entity. Vacuum entities must start with 'vacuum.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id, "fan_speed": fan_speed}
    await client.call_service("vacuum", "set_fan_speed", service_data)

    logger.info(f"Successfully set fan speed for vacuum: {entity_id}")

    return {
        "success": True,
        "message": f"Vacuum '{entity_id}' fan speed set to '{fan_speed}'",
        "entity_id": entity_id,
        "fan_speed": fan_speed,
    }
