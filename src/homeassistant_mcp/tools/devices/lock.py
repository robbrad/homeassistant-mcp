"""Lock control tool for Home Assistant MCP server."""

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


def register_lock_tool(mcp: Any, get_client: Any) -> None:
    """Register the lock control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool()
    async def lock_control(
        action: Annotated[
            Literal["list", "get", "lock", "unlock"],
            Field(
                description="Action to perform: list all locks, get specific lock, lock, or unlock"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Lock entity ID (required for get, lock, unlock). Example: 'lock.front_door'"
            ),
        ] = None,
        code: Annotated[
            str | None,
            Field(description="Optional code for unlock action (required by some locks)"),
        ] = None,
    ) -> dict:
        """Control smart locks in Home Assistant.

        This tool allows you to list all locks, get details about a specific lock,
        lock and unlock doors with optional code support.

        Actions:
        - list: Get all lock entities with their current states
        - get: Get detailed information about a specific lock including battery level
        - lock: Lock a smart lock
        - unlock: Unlock a smart lock (with optional code parameter)

        Examples:
        - List all locks: lock_control(action="list")
        - Get lock details: lock_control(action="get", entity_id="lock.front_door")
        - Lock a door: lock_control(action="lock", entity_id="lock.front_door")
        - Unlock a door: lock_control(action="unlock", entity_id="lock.front_door")
        - Unlock with code: lock_control(action="unlock", entity_id="lock.front_door", code="1234")

        Note: The list action returns entities from the HA states API. If some
            entities are missing, use states_control(action="list", domain="lock")
            or list_devices(domain="lock") for a more complete view.

        Args:
            action: The action to perform
            entity_id: The lock entity ID (required for get, lock, unlock)
            code: Optional code for unlock action

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if action == "list":
                return await _list_locks(client)

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                return await _get_lock(client, entity_id)

            elif action == "lock":
                if not entity_id:
                    return {"error": "entity_id is required for 'lock' action", "success": False}
                return await _lock_lock(client, entity_id)

            elif action == "unlock":
                if not entity_id:
                    return {"error": "entity_id is required for 'unlock' action", "success": False}
                return await _unlock_lock(client, entity_id, code)

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
            logger.error(f"Unexpected error in lock_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_locks(client: HomeAssistantClient) -> dict:
    """List all lock entities.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing list of locks with their states
    """
    logger.info("Listing all lock entities")

    # Get all states and filter for locks
    all_states = await client.get_states()
    locks = [state for state in all_states if state.get("entity_id", "").startswith("lock.")]

    # Format the response
    lock_list = []
    for lock in locks:
        attributes = lock.get("attributes", {})
        lock_info = {
            "entity_id": lock.get("entity_id"),
            "name": attributes.get("friendly_name", lock.get("entity_id")),
            "state": lock.get("state"),
        }

        # Include battery level if available
        if "battery_level" in attributes:
            lock_info["battery_level"] = attributes["battery_level"]

        lock_list.append(lock_info)

    logger.info(f"Found {len(lock_list)} lock entities")

    return {"success": True, "count": len(lock_list), "locks": lock_list}


async def _get_lock(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific lock.

    Args:
        client: The Home Assistant client
        entity_id: The lock entity ID

    Returns:
        Dictionary containing detailed lock information

    Raises:
        EntityNotFoundError: If the lock entity is not found
    """
    logger.info(f"Getting details for lock: {entity_id}")

    # Validate that this is a lock entity
    if not entity_id.startswith("lock."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a lock entity. Lock entities must start with 'lock.'"
        )

    # Get the entity state
    state = await client.get_state(entity_id)
    attributes = state.get("attributes", {})

    # Format the response with all available information
    lock_info = {
        "entity_id": state.get("entity_id"),
        "name": attributes.get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
    }

    # Include battery level if available
    if "battery_level" in attributes:
        lock_info["battery_level"] = attributes["battery_level"]

    # Include other relevant attributes
    lock_info["attributes"] = attributes

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")

    return {"success": True, "lock": lock_info}


async def _lock_lock(client: HomeAssistantClient, entity_id: str) -> dict:
    """Lock a smart lock.

    Args:
        client: The Home Assistant client
        entity_id: The lock entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the lock entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Locking: {entity_id}")

    # Validate that this is a lock entity
    if not entity_id.startswith("lock."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a lock entity. Lock entities must start with 'lock.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("lock", "lock", service_data)

    logger.info(f"Successfully locked: {entity_id}")

    return {
        "success": True,
        "message": f"Lock '{entity_id}' locked",
        "entity_id": entity_id,
    }


async def _unlock_lock(
    client: HomeAssistantClient, entity_id: str, code: str | None = None
) -> dict:
    """Unlock a smart lock.

    Args:
        client: The Home Assistant client
        entity_id: The lock entity ID
        code: Optional code for unlock action

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the lock entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Unlocking: {entity_id}")

    # Validate that this is a lock entity
    if not entity_id.startswith("lock."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a lock entity. Lock entities must start with 'lock.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    if code:
        service_data["code"] = code

    await client.call_service("lock", "unlock", service_data)

    logger.info(f"Successfully unlocked: {entity_id}")

    return {
        "success": True,
        "message": f"Lock '{entity_id}' unlocked",
        "entity_id": entity_id,
    }
