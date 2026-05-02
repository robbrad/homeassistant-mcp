"""Lawn mower control tool for Home Assistant MCP server."""

import logging
from typing import Annotated, Any, Literal

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


def register_lawn_mower_tool(mcp: Any, get_client: Any) -> None:
    """Register the lawn mower control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool()
    async def lawn_mower_control(
        action: Annotated[
            Literal["list", "get", "start", "pause", "dock"],
            Field(
                description="Action to perform: list all lawn mowers, get specific lawn mower, start mowing, pause, or return to dock"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Lawn mower entity ID (required for get, start, pause, dock). Example: 'lawn_mower.backyard'"
            ),
        ] = None,
    ) -> dict:
        """Control lawn mowers in Home Assistant.

        This tool allows you to list all lawn mowers, get details about a specific lawn mower,
        start mowing, pause mowing, and send the mower back to its dock.

        Actions:
        - list: Get all lawn mower entities with their current states
        - get: Get detailed information about a specific lawn mower
        - start: Start mowing
        - pause: Pause mowing
        - dock: Return to dock/charging station

        Examples:
        - List all lawn mowers: lawn_mower_control(action="list")
        - Get lawn mower details: lawn_mower_control(action="get", entity_id="lawn_mower.backyard")
        - Start mowing: lawn_mower_control(action="start", entity_id="lawn_mower.backyard")
        - Pause mowing: lawn_mower_control(action="pause", entity_id="lawn_mower.backyard")
        - Return to dock: lawn_mower_control(action="dock", entity_id="lawn_mower.backyard")

        Args:
            action: The action to perform
            entity_id: The lawn mower entity ID (required for most actions)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if action == "list":
                return await _list_lawn_mowers(client)

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                return await _get_lawn_mower(client, entity_id)

            elif action == "start":
                if not entity_id:
                    return {"error": "entity_id is required for 'start' action", "success": False}
                return await _start_mowing(client, entity_id)

            elif action == "pause":
                if not entity_id:
                    return {"error": "entity_id is required for 'pause' action", "success": False}
                return await _pause_mowing(client, entity_id)

            elif action == "dock":
                if not entity_id:
                    return {"error": "entity_id is required for 'dock' action", "success": False}
                return await _dock_mower(client, entity_id)

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
            logger.error(f"Unexpected error in lawn_mower_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_lawn_mowers(client: HomeAssistantClient) -> dict:
    """List all lawn mower entities."""
    logger.info("Listing all lawn mower entities")

    all_states = await client.get_states()
    lawn_mowers = [
        state for state in all_states if state.get("entity_id", "").startswith("lawn_mower.")
    ]

    lawn_mower_list = []
    for mower in lawn_mowers:
        mower_info = {
            "entity_id": mower.get("entity_id"),
            "name": mower.get("attributes", {}).get("friendly_name", mower.get("entity_id")),
            "state": mower.get("state"),
        }

        attrs = mower.get("attributes", {})
        if "battery_level" in attrs:
            mower_info["battery_level"] = attrs["battery_level"]

        lawn_mower_list.append(mower_info)

    logger.info(f"Found {len(lawn_mower_list)} lawn mower entities")
    return {"success": True, "count": len(lawn_mower_list), "lawn_mowers": lawn_mower_list}


async def _get_lawn_mower(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific lawn mower."""
    logger.info(f"Getting details for lawn mower: {entity_id}")

    if not entity_id.startswith("lawn_mower."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a lawn mower entity. Lawn mower entities must start with 'lawn_mower.'"
        )

    state = await client.get_state(entity_id)

    lawn_mower_info = {
        "entity_id": state.get("entity_id"),
        "name": state.get("attributes", {}).get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": state.get("attributes", {}),
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")
    return {"success": True, "lawn_mower": lawn_mower_info}


async def _start_mowing(client: HomeAssistantClient, entity_id: str) -> dict:
    """Start mowing."""
    logger.info(f"Starting lawn mower: {entity_id}")

    if not entity_id.startswith("lawn_mower."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a lawn mower entity. Lawn mower entities must start with 'lawn_mower.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("lawn_mower", "start_mowing", service_data)

    logger.info(f"Successfully started lawn mower: {entity_id}")
    return {
        "success": True,
        "message": f"Lawn mower '{entity_id}' started mowing",
        "entity_id": entity_id,
    }


async def _pause_mowing(client: HomeAssistantClient, entity_id: str) -> dict:
    """Pause mowing."""
    logger.info(f"Pausing lawn mower: {entity_id}")

    if not entity_id.startswith("lawn_mower."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a lawn mower entity. Lawn mower entities must start with 'lawn_mower.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("lawn_mower", "pause", service_data)

    logger.info(f"Successfully paused lawn mower: {entity_id}")
    return {
        "success": True,
        "message": f"Lawn mower '{entity_id}' paused",
        "entity_id": entity_id,
    }


async def _dock_mower(client: HomeAssistantClient, entity_id: str) -> dict:
    """Return lawn mower to dock."""
    logger.info(f"Sending lawn mower to dock: {entity_id}")

    if not entity_id.startswith("lawn_mower."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a lawn mower entity. Lawn mower entities must start with 'lawn_mower.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("lawn_mower", "dock", service_data)

    logger.info(f"Successfully sent lawn mower to dock: {entity_id}")
    return {
        "success": True,
        "message": f"Lawn mower '{entity_id}' returning to dock",
        "entity_id": entity_id,
    }
