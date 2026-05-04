"""Cover/blind control tool for Home Assistant MCP server."""

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


def register_cover_tool(mcp: Any, get_client: Any) -> None:
    """Register the cover control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control", "cover"},
        timeout=30,
    )
    async def cover_control(
        action: Annotated[
            Literal["list", "get", "open", "close", "stop", "toggle", "set_position", "set_tilt"],
            Field(
                description="Action to perform: list all covers, get specific cover, open, close, stop, toggle, set position, or set tilt"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Cover entity ID (required for get, open, close, stop, toggle, set_position, set_tilt). Example: 'cover.living_room_blinds'"
            ),
        ] = None,
        position: Annotated[
            int | None,
            Field(
                description="Position to set (0-100, where 0 is closed and 100 is fully open). Used with set_position action.",
                ge=0,
                le=100,
            ),
        ] = None,
        tilt: Annotated[
            int | None,
            Field(
                description="Tilt angle to set (0-100). Used with set_tilt action.",
                ge=0,
                le=100,
            ),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Control covers, blinds, and garage doors in Home Assistant.

        This tool allows you to list all covers, get details about a specific cover,
        open/close covers, stop movement, toggle state, and control position and tilt.

        Actions:
        - list: Get all cover entities with their current states and positions
        - get: Get detailed information about a specific cover
        - open: Fully open a cover
        - close: Fully close a cover
        - stop: Stop cover movement
        - toggle: Toggle between open and closed states
        - set_position: Set cover position (0-100, where 0 is closed and 100 is fully open)
        - set_tilt: Set tilt angle (0-100)

        Examples:
        - List all covers: cover_control(action="list")
        - Get cover details: cover_control(action="get", entity_id="cover.living_room_blinds")
        - Open cover: cover_control(action="open", entity_id="cover.garage_door")
        - Close cover: cover_control(action="close", entity_id="cover.bedroom_blinds")
        - Stop cover: cover_control(action="stop", entity_id="cover.living_room_blinds")
        - Toggle cover: cover_control(action="toggle", entity_id="cover.garage_door")
        - Set position: cover_control(action="set_position", entity_id="cover.bedroom_blinds", position=50)
        - Set tilt: cover_control(action="set_tilt", entity_id="cover.living_room_blinds", tilt=75)

        Note: The list action returns entities from the HA states API. If some
            entities are missing, use states_control(action="list", domain="cover")
            or list_devices(domain="cover") for a more complete view.

        Args:
            action: The action to perform
            entity_id: The cover entity ID (required for most actions)
            position: Position to set (0-100, used with set_position)
            tilt: Tilt angle to set (0-100, used with set_tilt)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing cover_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_covers(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_cover(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "open":
                if not entity_id:
                    return {"error": "entity_id is required for 'open' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _open_cover(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "close":
                if not entity_id:
                    return {"error": "entity_id is required for 'close' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _close_cover(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "stop":
                if not entity_id:
                    return {"error": "entity_id is required for 'stop' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _stop_cover(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "toggle":
                if not entity_id:
                    return {"error": "entity_id is required for 'toggle' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _toggle_cover(client, entity_id)
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
                        "error": "position parameter is required for 'set_position' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_cover_position(client, entity_id, position)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_tilt":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_tilt' action",
                        "success": False,
                    }
                if tilt is None:
                    return {
                        "error": "tilt parameter is required for 'set_tilt' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_cover_tilt(client, entity_id, tilt)
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
            logger.error(f"Unexpected error in cover_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_covers(client: HomeAssistantClient) -> dict:
    """List all cover entities.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing list of covers with their states
    """
    logger.info("Listing all cover entities")

    # Get all states and filter for covers
    all_states = await client.get_states()
    covers = [state for state in all_states if state.get("entity_id", "").startswith("cover.")]

    # Format the response
    cover_list = []
    for cover in covers:
        attributes = cover.get("attributes", {})
        cover_info = {
            "entity_id": cover.get("entity_id"),
            "name": attributes.get("friendly_name", cover.get("entity_id")),
            "state": cover.get("state"),
        }

        # Include position if available
        if "current_position" in attributes:
            cover_info["current_position"] = attributes["current_position"]

        # Include tilt if available
        if "current_tilt_position" in attributes:
            cover_info["current_tilt_position"] = attributes["current_tilt_position"]

        cover_list.append(cover_info)

    logger.info(f"Found {len(cover_list)} cover entities")

    return {"success": True, "count": len(cover_list), "covers": cover_list}


async def _get_cover(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific cover.

    Args:
        client: The Home Assistant client
        entity_id: The cover entity ID

    Returns:
        Dictionary containing detailed cover information

    Raises:
        EntityNotFoundError: If the cover entity is not found
    """
    logger.info(f"Getting details for cover: {entity_id}")

    # Validate that this is a cover entity
    if not entity_id.startswith("cover."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a cover entity. Cover entities must start with 'cover.'"
        )

    # Get the entity state
    state = await client.get_state(entity_id)
    attributes = state.get("attributes", {})

    # Format the response with all available information
    cover_info = {
        "entity_id": state.get("entity_id"),
        "name": attributes.get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
    }

    # Include position if available
    if "current_position" in attributes:
        cover_info["current_position"] = attributes["current_position"]

    # Include tilt if available
    if "current_tilt_position" in attributes:
        cover_info["current_tilt_position"] = attributes["current_tilt_position"]

    # Include other relevant attributes
    cover_info["attributes"] = attributes

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")

    return {"success": True, "cover": cover_info}


async def _open_cover(client: HomeAssistantClient, entity_id: str) -> dict:
    """Open a cover.

    Args:
        client: The Home Assistant client
        entity_id: The cover entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the cover entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Opening cover: {entity_id}")

    # Validate that this is a cover entity
    if not entity_id.startswith("cover."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a cover entity. Cover entities must start with 'cover.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("cover", "open_cover", service_data)

    logger.info(f"Successfully opened cover: {entity_id}")

    return {
        "success": True,
        "message": f"Cover '{entity_id}' opened",
        "entity_id": entity_id,
    }


async def _close_cover(client: HomeAssistantClient, entity_id: str) -> dict:
    """Close a cover.

    Args:
        client: The Home Assistant client
        entity_id: The cover entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the cover entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Closing cover: {entity_id}")

    # Validate that this is a cover entity
    if not entity_id.startswith("cover."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a cover entity. Cover entities must start with 'cover.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("cover", "close_cover", service_data)

    logger.info(f"Successfully closed cover: {entity_id}")

    return {
        "success": True,
        "message": f"Cover '{entity_id}' closed",
        "entity_id": entity_id,
    }


async def _stop_cover(client: HomeAssistantClient, entity_id: str) -> dict:
    """Stop a cover's movement.

    Args:
        client: The Home Assistant client
        entity_id: The cover entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the cover entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Stopping cover: {entity_id}")

    # Validate that this is a cover entity
    if not entity_id.startswith("cover."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a cover entity. Cover entities must start with 'cover.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("cover", "stop_cover", service_data)

    logger.info(f"Successfully stopped cover: {entity_id}")

    return {
        "success": True,
        "message": f"Cover '{entity_id}' stopped",
        "entity_id": entity_id,
    }


async def _toggle_cover(client: HomeAssistantClient, entity_id: str) -> dict:
    """Toggle a cover's state.

    Args:
        client: The Home Assistant client
        entity_id: The cover entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the cover entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Toggling cover: {entity_id}")

    # Validate that this is a cover entity
    if not entity_id.startswith("cover."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a cover entity. Cover entities must start with 'cover.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("cover", "toggle", service_data)

    logger.info(f"Successfully toggled cover: {entity_id}")

    return {
        "success": True,
        "message": f"Cover '{entity_id}' toggled",
        "entity_id": entity_id,
    }


async def _set_cover_position(client: HomeAssistantClient, entity_id: str, position: int) -> dict:
    """Set a cover's position.

    Args:
        client: The Home Assistant client
        entity_id: The cover entity ID
        position: Position to set (0-100, where 0 is closed and 100 is fully open)

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the cover entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Setting cover position: {entity_id} to {position}")

    # Validate that this is a cover entity
    if not entity_id.startswith("cover."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a cover entity. Cover entities must start with 'cover.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id, "position": position}
    await client.call_service("cover", "set_cover_position", service_data)

    logger.info(f"Successfully set cover position: {entity_id} to {position}")

    return {
        "success": True,
        "message": f"Cover '{entity_id}' position set to {position}",
        "entity_id": entity_id,
        "position": position,
    }


async def _set_cover_tilt(client: HomeAssistantClient, entity_id: str, tilt: int) -> dict:
    """Set a cover's tilt angle.

    Args:
        client: The Home Assistant client
        entity_id: The cover entity ID
        tilt: Tilt angle to set (0-100)

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the cover entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Setting cover tilt: {entity_id} to {tilt}")

    # Validate that this is a cover entity
    if not entity_id.startswith("cover."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a cover entity. Cover entities must start with 'cover.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id, "tilt_position": tilt}
    await client.call_service("cover", "set_cover_tilt_position", service_data)

    logger.info(f"Successfully set cover tilt: {entity_id} to {tilt}")

    return {
        "success": True,
        "message": f"Cover '{entity_id}' tilt set to {tilt}",
        "entity_id": entity_id,
        "tilt": tilt,
    }
