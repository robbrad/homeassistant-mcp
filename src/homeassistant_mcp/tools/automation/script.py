"""Script execution tool for Home Assistant MCP server."""

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


def register_script_tool(mcp: Any, get_client: Any) -> None:
    """Register the script control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool()
    async def script_control(
        action: Annotated[
            Literal["list", "get", "execute", "reload"],
            Field(
                description="Action to perform: list all scripts, get specific script details, execute a script, or reload all scripts"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Script entity ID (required for get and execute). Example: 'script.morning_routine'"
            ),
        ] = None,
        variables: Annotated[
            dict | None,
            Field(
                description="Optional variables to pass to the script during execution. Example: {'brightness': 100, 'color': 'blue'}"
            ),
        ] = None,
    ) -> dict:
        """Execute and manage Home Assistant scripts.

        This tool allows you to list all scripts, get details about a specific script,
        execute scripts with optional variables, and reload all scripts from configuration.

        Actions:
        - list: Get all script entities with their descriptions
        - get: Get detailed information about a specific script including configuration and last execution time
        - execute: Run a script with optional variables
        - reload: Reload all scripts from configuration files

        Examples:
        - List all scripts: script_control(action="list")
        - Get script details: script_control(action="get", entity_id="script.morning_routine")
        - Execute script: script_control(action="execute", entity_id="script.morning_routine")
        - Execute with variables: script_control(action="execute", entity_id="script.set_lights", variables={"brightness": 100})
        - Reload scripts: script_control(action="reload")

        Args:
            action: The action to perform
            entity_id: The script entity ID (required for get and execute)
            variables: Optional variables to pass to the script (only used with execute)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if action == "list":
                return await _list_scripts(client)

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                return await _get_script(client, entity_id)

            elif action == "execute":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'execute' action",
                        "success": False,
                    }
                return await _execute_script(client, entity_id, variables)

            elif action == "reload":
                return await _reload_scripts(client)

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
            logger.error(f"Unexpected error in script_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_scripts(client: HomeAssistantClient) -> dict:
    """List all script entities.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing list of scripts with their descriptions
    """
    logger.info("Listing all script entities")

    # Get all states and filter for scripts
    all_states = await client.get_states()
    scripts = [state for state in all_states if state.get("entity_id", "").startswith("script.")]

    # Format the response
    script_list = []
    for script in scripts:
        script_info = {
            "entity_id": script.get("entity_id"),
            "name": script.get("attributes", {}).get("friendly_name", script.get("entity_id")),
            "state": script.get("state"),
        }

        attrs = script.get("attributes", {})

        # Add description if available
        if "description" in attrs:
            script_info["description"] = attrs["description"]

        # Add last triggered time if available
        if "last_triggered" in attrs:
            script_info["last_triggered"] = attrs["last_triggered"]

        script_list.append(script_info)

    logger.info(f"Found {len(script_list)} script entities")

    return {"success": True, "count": len(script_list), "scripts": script_list}


async def _get_script(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific script.

    Args:
        client: The Home Assistant client
        entity_id: The script entity ID

    Returns:
        Dictionary containing detailed script information

    Raises:
        EntityNotFoundError: If the script entity is not found
    """
    logger.info(f"Getting details for script: {entity_id}")

    # Validate that this is a script entity
    if not entity_id.startswith("script."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a script entity. Script entities must start with 'script.'"
        )

    # Get the entity state
    state = await client.get_state(entity_id)

    # Format the response with all available information
    script_info = {
        "entity_id": state.get("entity_id"),
        "name": state.get("attributes", {}).get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": state.get("attributes", {}),
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")

    return {"success": True, "script": script_info}


async def _execute_script(
    client: HomeAssistantClient, entity_id: str, variables: dict | None = None
) -> dict:
    """Execute a script with optional variables.

    Args:
        client: The Home Assistant client
        entity_id: The script entity ID
        variables: Optional variables to pass to the script

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the script entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Executing script: {entity_id}")

    # Validate that this is a script entity
    if not entity_id.startswith("script."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a script entity. Script entities must start with 'script.'"
        )

    # Build service data
    service_data = {"entity_id": entity_id}

    # Add variables if provided
    if variables:
        service_data.update(variables)
        logger.info(f"Executing script {entity_id} with variables: {variables}")

    # Call the service - scripts are executed using the turn_on service
    await client.call_service("script", "turn_on", service_data)

    logger.info(f"Successfully executed script: {entity_id}")

    result = {
        "success": True,
        "message": f"Script '{entity_id}' executed successfully",
        "entity_id": entity_id,
    }

    if variables:
        result["variables"] = variables

    return result


async def _reload_scripts(client: HomeAssistantClient) -> dict:
    """Reload all scripts from configuration.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing the result of the operation

    Raises:
        ServiceCallError: If the service call fails
    """
    logger.info("Reloading all scripts")

    # Call the reload service
    await client.call_service("script", "reload", {})

    logger.info("Successfully reloaded all scripts")

    return {
        "success": True,
        "message": "All scripts reloaded successfully",
    }
