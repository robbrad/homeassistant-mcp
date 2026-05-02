"""Switch control tool for Home Assistant MCP server."""

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


def register_switch_tool(mcp: Any, get_client: Any) -> None:
    """Register the switch control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool()
    async def switch_control(
        action: Annotated[
            Literal["list", "get", "turn_on", "turn_off", "toggle"],
            Field(
                description="Action to perform: list all switches, get specific switch, turn on, turn off, or toggle"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Switch entity ID (required for get, turn_on, turn_off, toggle). Example: 'switch.living_room'"
            ),
        ] = None,
        entity_ids: Annotated[
            list[str] | None,
            Field(
                description="List of switch entity IDs for bulk operations (optional, used with turn_on/turn_off)"
            ),
        ] = None,
    ) -> dict:
        """Control switches in Home Assistant.

        This tool allows you to list all switches, get details about a specific switch,
        turn switches on or off, toggle switches, and perform bulk operations.

        Actions:
        - list: Get all switch entities with their current states
        - get: Get detailed information about a specific switch
        - turn_on: Turn on a switch (supports single or bulk operation)
        - turn_off: Turn off a switch (supports single or bulk operation)
        - toggle: Toggle a switch state

        Examples:
        - List all switches: switch_control(action="list")
        - Get switch details: switch_control(action="get", entity_id="switch.living_room")
        - Turn on switch: switch_control(action="turn_on", entity_id="switch.living_room")
        - Turn off switch: switch_control(action="turn_off", entity_id="switch.living_room")
        - Toggle switch: switch_control(action="toggle", entity_id="switch.living_room")
        - Bulk turn on: switch_control(action="turn_on", entity_ids=["switch.light1", "switch.light2"])
        - Bulk turn off: switch_control(action="turn_off", entity_ids=["switch.light1", "switch.light2"])

        Args:
            action: The action to perform
            entity_id: The switch entity ID (required for get, turn_on, turn_off, toggle)
            entity_ids: List of switch entity IDs for bulk operations (optional)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if action == "list":
                return await _list_switches(client)

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                return await _get_switch(client, entity_id)

            elif action == "turn_on":
                if entity_ids:
                    return await _bulk_control_switches(client, entity_ids, "turn_on")
                if not entity_id:
                    return {
                        "error": "entity_id or entity_ids is required for 'turn_on' action",
                        "success": False,
                    }
                return await _turn_on_switch(client, entity_id)

            elif action == "turn_off":
                if entity_ids:
                    return await _bulk_control_switches(client, entity_ids, "turn_off")
                if not entity_id:
                    return {
                        "error": "entity_id or entity_ids is required for 'turn_off' action",
                        "success": False,
                    }
                return await _turn_off_switch(client, entity_id)

            elif action == "toggle":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'toggle' action",
                        "success": False,
                    }
                return await _toggle_switch(client, entity_id)

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
            logger.error(f"Unexpected error in switch_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_switches(client: HomeAssistantClient) -> dict:
    """List all switch entities.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing list of switches with their states
    """
    logger.info("Listing all switch entities")

    # Get all states and filter for switches
    all_states = await client.get_states()
    switches = [state for state in all_states if state.get("entity_id", "").startswith("switch.")]

    # Format the response
    switch_list = []
    for switch in switches:
        switch_info = {
            "entity_id": switch.get("entity_id"),
            "name": switch.get("attributes", {}).get("friendly_name", switch.get("entity_id")),
            "state": switch.get("state"),
        }
        switch_list.append(switch_info)

    logger.info(f"Found {len(switch_list)} switch entities")

    return {"success": True, "count": len(switch_list), "switches": switch_list}


async def _get_switch(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific switch.

    Args:
        client: The Home Assistant client
        entity_id: The switch entity ID

    Returns:
        Dictionary containing detailed switch information

    Raises:
        EntityNotFoundError: If the switch entity is not found
    """
    logger.info(f"Getting details for switch: {entity_id}")

    # Validate that this is a switch entity
    if not entity_id.startswith("switch."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a switch entity. Switch entities must start with 'switch.'"
        )

    # Get the entity state
    state = await client.get_state(entity_id)

    # Format the response with all available information
    switch_info = {
        "entity_id": state.get("entity_id"),
        "name": state.get("attributes", {}).get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": state.get("attributes", {}),
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")

    return {"success": True, "switch": switch_info}


async def _turn_on_switch(client: HomeAssistantClient, entity_id: str) -> dict:
    """Turn on a switch.

    Args:
        client: The Home Assistant client
        entity_id: The switch entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the switch entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Turning on switch: {entity_id}")

    # Validate that this is a switch entity
    if not entity_id.startswith("switch."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a switch entity. Switch entities must start with 'switch.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("switch", "turn_on", service_data)

    logger.info(f"Successfully turned on switch: {entity_id}")

    return {
        "success": True,
        "message": f"Switch '{entity_id}' turned on",
        "entity_id": entity_id,
    }


async def _turn_off_switch(client: HomeAssistantClient, entity_id: str) -> dict:
    """Turn off a switch.

    Args:
        client: The Home Assistant client
        entity_id: The switch entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the switch entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Turning off switch: {entity_id}")

    # Validate that this is a switch entity
    if not entity_id.startswith("switch."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a switch entity. Switch entities must start with 'switch.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("switch", "turn_off", service_data)

    logger.info(f"Successfully turned off switch: {entity_id}")

    return {
        "success": True,
        "message": f"Switch '{entity_id}' turned off",
        "entity_id": entity_id,
    }


async def _toggle_switch(client: HomeAssistantClient, entity_id: str) -> dict:
    """Toggle a switch state.

    Args:
        client: The Home Assistant client
        entity_id: The switch entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the switch entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Toggling switch: {entity_id}")

    # Validate that this is a switch entity
    if not entity_id.startswith("switch."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a switch entity. Switch entities must start with 'switch.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("switch", "toggle", service_data)

    logger.info(f"Successfully toggled switch: {entity_id}")

    return {
        "success": True,
        "message": f"Switch '{entity_id}' toggled",
        "entity_id": entity_id,
    }


async def _bulk_control_switches(
    client: HomeAssistantClient, entity_ids: list[str], action: str
) -> dict:
    """Control multiple switches at once.

    Args:
        client: The Home Assistant client
        entity_ids: List of switch entity IDs
        action: The action to perform (turn_on or turn_off)

    Returns:
        Dictionary containing the result of the bulk operation

    Raises:
        EntityNotFoundError: If any switch entity is not valid
        ServiceCallError: If the service call fails
    """
    logger.info(f"Performing bulk {action} on {len(entity_ids)} switches")

    # Validate all entity IDs
    for entity_id in entity_ids:
        if not entity_id.startswith("switch."):
            raise EntityNotFoundError(
                f"Entity '{entity_id}' is not a switch entity. Switch entities must start with 'switch.'"
            )

    # Call the service with all entity IDs
    service_data = {"entity_id": entity_ids}
    await client.call_service("switch", action, service_data)

    logger.info(f"Successfully performed bulk {action} on {len(entity_ids)} switches")

    return {
        "success": True,
        "message": f"Bulk {action} completed for {len(entity_ids)} switches",
        "entity_ids": entity_ids,
        "count": len(entity_ids),
    }
