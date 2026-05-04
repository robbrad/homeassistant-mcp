"""Valve control tool for Home Assistant MCP server."""

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


def register_valve_tool(mcp: Any, get_client: Any) -> None:
    """Register the valve control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control"},
        timeout=30,
    )
    async def valve_control(
        action: Annotated[
            Literal["list", "get", "open", "close", "stop", "toggle", "set_position"],
            Field(
                description="Action to perform: list all valves, get specific valve, open, close, stop, toggle, or set position"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Valve entity ID (required for get, open, close, stop, toggle, set_position). Example: 'valve.water_main'"
            ),
        ] = None,
        position: Annotated[
            int | None,
            Field(
                ge=0,
                le=100,
                description="Valve position percentage (0-100). Only used with set_position action.",
            ),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Control valves in Home Assistant.

        This tool allows you to list all valves, get details about a specific valve,
        open/close valves, stop valve movement, toggle valves, and set valve position.

        Actions:
        - list: Get all valve entities with their current states
        - get: Get detailed information about a specific valve
        - open: Fully open a valve
        - close: Fully close a valve
        - stop: Stop valve movement
        - toggle: Toggle valve state
        - set_position: Set valve position (0-100)

        Examples:
        - List all valves: valve_control(action="list")
        - Get valve details: valve_control(action="get", entity_id="valve.water_main")
        - Open valve: valve_control(action="open", entity_id="valve.water_main")
        - Close valve: valve_control(action="close", entity_id="valve.water_main")
        - Stop valve: valve_control(action="stop", entity_id="valve.water_main")
        - Toggle valve: valve_control(action="toggle", entity_id="valve.water_main")
        - Set position: valve_control(action="set_position", entity_id="valve.water_main", position=50)

        Args:
            action: The action to perform
            entity_id: The valve entity ID (required for most actions)
            position: Valve position 0-100 (optional, for set_position)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing valve_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_valves(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_valve(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "open":
                if not entity_id:
                    return {"error": "entity_id is required for 'open' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _open_valve(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "close":
                if not entity_id:
                    return {"error": "entity_id is required for 'close' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _close_valve(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "stop":
                if not entity_id:
                    return {"error": "entity_id is required for 'stop' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _stop_valve(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "toggle":
                if not entity_id:
                    return {"error": "entity_id is required for 'toggle' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _toggle_valve(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_position":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_position' action",
                        "success": False,
                    }
                if position is None:
                    return {
                        "error": "position is required for 'set_position' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_valve_position(client, entity_id, position)
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
            logger.error(f"Unexpected error in valve_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_valves(client: HomeAssistantClient) -> dict:
    """List all valve entities."""
    logger.info("Listing all valve entities")

    valves = await client.get_states(domain="valve")

    valve_list = []
    for valve in valves:
        valve_info = {
            "entity_id": valve.get("entity_id"),
            "name": valve.get("attributes", {}).get("friendly_name", valve.get("entity_id")),
            "state": valve.get("state"),
        }

        attrs = valve.get("attributes", {})
        if "current_position" in attrs:
            valve_info["current_position"] = attrs["current_position"]

        valve_list.append(valve_info)

    logger.info(f"Found {len(valve_list)} valve entities")
    return {"success": True, "count": len(valve_list), "valves": valve_list}


async def _get_valve(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific valve."""
    logger.info(f"Getting details for valve: {entity_id}")

    if not entity_id.startswith("valve."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a valve entity. Valve entities must start with 'valve.'"
        )

    state = await client.get_state(entity_id)

    valve_info = {
        "entity_id": state.get("entity_id"),
        "name": state.get("attributes", {}).get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": state.get("attributes", {}),
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")
    return {"success": True, "valve": valve_info}


async def _open_valve(client: HomeAssistantClient, entity_id: str) -> dict:
    """Open a valve."""
    logger.info(f"Opening valve: {entity_id}")

    if not entity_id.startswith("valve."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a valve entity. Valve entities must start with 'valve.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("valve", "open_valve", service_data)

    logger.info(f"Successfully opened valve: {entity_id}")
    return {"success": True, "message": f"Valve '{entity_id}' opened", "entity_id": entity_id}


async def _close_valve(client: HomeAssistantClient, entity_id: str) -> dict:
    """Close a valve."""
    logger.info(f"Closing valve: {entity_id}")

    if not entity_id.startswith("valve."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a valve entity. Valve entities must start with 'valve.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("valve", "close_valve", service_data)

    logger.info(f"Successfully closed valve: {entity_id}")
    return {"success": True, "message": f"Valve '{entity_id}' closed", "entity_id": entity_id}


async def _stop_valve(client: HomeAssistantClient, entity_id: str) -> dict:
    """Stop a valve."""
    logger.info(f"Stopping valve: {entity_id}")

    if not entity_id.startswith("valve."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a valve entity. Valve entities must start with 'valve.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("valve", "stop_valve", service_data)

    logger.info(f"Successfully stopped valve: {entity_id}")
    return {"success": True, "message": f"Valve '{entity_id}' stopped", "entity_id": entity_id}


async def _toggle_valve(client: HomeAssistantClient, entity_id: str) -> dict:
    """Toggle a valve state."""
    logger.info(f"Toggling valve: {entity_id}")

    if not entity_id.startswith("valve."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a valve entity. Valve entities must start with 'valve.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("valve", "toggle", service_data)

    logger.info(f"Successfully toggled valve: {entity_id}")
    return {"success": True, "message": f"Valve '{entity_id}' toggled", "entity_id": entity_id}


async def _set_valve_position(client: HomeAssistantClient, entity_id: str, position: int) -> dict:
    """Set the valve position."""
    logger.info(f"Setting valve {entity_id} position to {position}%")

    if not entity_id.startswith("valve."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a valve entity. Valve entities must start with 'valve.'"
        )

    service_data = {"entity_id": entity_id, "position": position}
    await client.call_service("valve", "set_valve_position", service_data)

    logger.info(f"Successfully set valve {entity_id} position to {position}%")
    return {
        "success": True,
        "message": f"Valve '{entity_id}' position set to {position}%",
        "entity_id": entity_id,
        "position": position,
    }
