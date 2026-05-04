"""Water heater control tool for Home Assistant MCP server."""

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


def register_water_heater_tool(mcp: Any, get_client: Any) -> None:
    """Register the water heater control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control"},
        timeout=30,
    )
    async def water_heater_control(
        action: Annotated[
            Literal[
                "list",
                "get",
                "turn_on",
                "turn_off",
                "set_temperature",
                "set_operation_mode",
                "set_away_mode",
            ],
            Field(
                description="Action to perform: list all water heaters, get specific water heater, turn on, turn off, set temperature, set operation mode, or set away mode"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Water heater entity ID (required for get, turn_on, turn_off, set_temperature, set_operation_mode, set_away_mode). Example: 'water_heater.tank'"
            ),
        ] = None,
        temperature: Annotated[
            float | None,
            Field(
                description="Target temperature in degrees. Only used with set_temperature action."
            ),
        ] = None,
        operation_mode: Annotated[
            str | None,
            Field(
                description="Operation mode (e.g., 'eco', 'electric', 'gas', 'heat_pump'). Only used with set_operation_mode action."
            ),
        ] = None,
        away_mode: Annotated[
            bool | None,
            Field(description="Enable or disable away mode. Only used with set_away_mode action."),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Control water heaters in Home Assistant.

        This tool allows you to list all water heaters, get details about a specific water heater,
        turn water heaters on/off, set temperature, and control operation modes.

        Actions:
        - list: Get all water heater entities with their current states
        - get: Get detailed information about a specific water heater
        - turn_on: Turn on a water heater
        - turn_off: Turn off a water heater
        - set_temperature: Set target temperature
        - set_operation_mode: Set operation mode (eco, electric, gas, heat_pump, etc.)
        - set_away_mode: Enable or disable away mode

        Examples:
        - List all water heaters: water_heater_control(action="list")
        - Get water heater details: water_heater_control(action="get", entity_id="water_heater.tank")
        - Turn on water heater: water_heater_control(action="turn_on", entity_id="water_heater.tank")
        - Set temperature: water_heater_control(action="set_temperature", entity_id="water_heater.tank", temperature=55.0)
        - Set operation mode: water_heater_control(action="set_operation_mode", entity_id="water_heater.tank", operation_mode="eco")
        - Enable away mode: water_heater_control(action="set_away_mode", entity_id="water_heater.tank", away_mode=True)

        Args:
            action: The action to perform
            entity_id: The water heater entity ID (required for most actions)
            temperature: Target temperature (optional, for set_temperature)
            operation_mode: Operation mode name (optional, for set_operation_mode)
            away_mode: Enable/disable away mode (optional, for set_away_mode)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing water_heater_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_water_heaters(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_water_heater(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "turn_on":
                if not entity_id:
                    return {"error": "entity_id is required for 'turn_on' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _turn_on_water_heater(client, entity_id)
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
                result = await _turn_off_water_heater(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_temperature":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_temperature' action",
                        "success": False,
                    }
                if temperature is None:
                    return {
                        "error": "temperature is required for 'set_temperature' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_temperature(client, entity_id, temperature)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_operation_mode":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_operation_mode' action",
                        "success": False,
                    }
                if not operation_mode:
                    return {
                        "error": "operation_mode is required for 'set_operation_mode' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_operation_mode(client, entity_id, operation_mode)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_away_mode":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_away_mode' action",
                        "success": False,
                    }
                if away_mode is None:
                    return {
                        "error": "away_mode is required for 'set_away_mode' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_away_mode(client, entity_id, away_mode)
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
            logger.error(f"Unexpected error in water_heater_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_water_heaters(client: HomeAssistantClient) -> dict:
    """List all water heater entities.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing list of water heaters with their states
    """
    logger.info("Listing all water heater entities")

    water_heaters = await client.get_states(domain="water_heater")

    water_heater_list = []
    for wh in water_heaters:
        wh_info = {
            "entity_id": wh.get("entity_id"),
            "name": wh.get("attributes", {}).get("friendly_name", wh.get("entity_id")),
            "state": wh.get("state"),
        }

        attrs = wh.get("attributes", {})
        if "temperature" in attrs:
            wh_info["current_temperature"] = attrs["temperature"]
        if "target_temp" in attrs:
            wh_info["target_temperature"] = attrs["target_temp"]
        if "operation_mode" in attrs:
            wh_info["operation_mode"] = attrs["operation_mode"]

        water_heater_list.append(wh_info)

    logger.info(f"Found {len(water_heater_list)} water heater entities")

    return {"success": True, "count": len(water_heater_list), "water_heaters": water_heater_list}


async def _get_water_heater(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific water heater.

    Args:
        client: The Home Assistant client
        entity_id: The water heater entity ID

    Returns:
        Dictionary containing detailed water heater information

    Raises:
        EntityNotFoundError: If the water heater entity is not found
    """
    logger.info(f"Getting details for water heater: {entity_id}")

    if not entity_id.startswith("water_heater."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a water heater entity. Water heater entities must start with 'water_heater.'"
        )

    state = await client.get_state(entity_id)

    water_heater_info = {
        "entity_id": state.get("entity_id"),
        "name": state.get("attributes", {}).get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": state.get("attributes", {}),
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")

    return {"success": True, "water_heater": water_heater_info}


async def _turn_on_water_heater(client: HomeAssistantClient, entity_id: str) -> dict:
    """Turn on a water heater.

    Args:
        client: The Home Assistant client
        entity_id: The water heater entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the water heater entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Turning on water heater: {entity_id}")

    if not entity_id.startswith("water_heater."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a water heater entity. Water heater entities must start with 'water_heater.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("water_heater", "turn_on", service_data)

    logger.info(f"Successfully turned on water heater: {entity_id}")

    return {
        "success": True,
        "message": f"Water heater '{entity_id}' turned on",
        "entity_id": entity_id,
    }


async def _turn_off_water_heater(client: HomeAssistantClient, entity_id: str) -> dict:
    """Turn off a water heater.

    Args:
        client: The Home Assistant client
        entity_id: The water heater entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the water heater entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Turning off water heater: {entity_id}")

    if not entity_id.startswith("water_heater."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a water heater entity. Water heater entities must start with 'water_heater.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("water_heater", "turn_off", service_data)

    logger.info(f"Successfully turned off water heater: {entity_id}")

    return {
        "success": True,
        "message": f"Water heater '{entity_id}' turned off",
        "entity_id": entity_id,
    }


async def _set_temperature(client: HomeAssistantClient, entity_id: str, temperature: float) -> dict:
    """Set the water heater target temperature.

    Args:
        client: The Home Assistant client
        entity_id: The water heater entity ID
        temperature: Target temperature

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the water heater entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Setting water heater {entity_id} temperature to {temperature}")

    if not entity_id.startswith("water_heater."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a water heater entity. Water heater entities must start with 'water_heater.'"
        )

    service_data = {"entity_id": entity_id, "temperature": temperature}
    await client.call_service("water_heater", "set_temperature", service_data)

    logger.info(f"Successfully set water heater {entity_id} temperature to {temperature}")

    return {
        "success": True,
        "message": f"Water heater '{entity_id}' temperature set to {temperature}",
        "entity_id": entity_id,
        "temperature": temperature,
    }


async def _set_operation_mode(
    client: HomeAssistantClient, entity_id: str, operation_mode: str
) -> dict:
    """Set the water heater operation mode.

    Args:
        client: The Home Assistant client
        entity_id: The water heater entity ID
        operation_mode: Operation mode name

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the water heater entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Setting water heater {entity_id} operation mode to {operation_mode}")

    if not entity_id.startswith("water_heater."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a water heater entity. Water heater entities must start with 'water_heater.'"
        )

    service_data = {"entity_id": entity_id, "operation_mode": operation_mode}
    await client.call_service("water_heater", "set_operation_mode", service_data)

    logger.info(f"Successfully set water heater {entity_id} operation mode to {operation_mode}")

    return {
        "success": True,
        "message": f"Water heater '{entity_id}' operation mode set to '{operation_mode}'",
        "entity_id": entity_id,
        "operation_mode": operation_mode,
    }


async def _set_away_mode(client: HomeAssistantClient, entity_id: str, away_mode: bool) -> dict:
    """Set the water heater away mode.

    Args:
        client: The Home Assistant client
        entity_id: The water heater entity ID
        away_mode: Enable or disable away mode

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the water heater entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Setting water heater {entity_id} away mode to {away_mode}")

    if not entity_id.startswith("water_heater."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a water heater entity. Water heater entities must start with 'water_heater.'"
        )

    service_data = {"entity_id": entity_id, "away_mode": "on" if away_mode else "off"}
    await client.call_service("water_heater", "set_away_mode", service_data)

    logger.info(f"Successfully set water heater {entity_id} away mode to {away_mode}")

    return {
        "success": True,
        "message": f"Water heater '{entity_id}' away mode {'enabled' if away_mode else 'disabled'}",
        "entity_id": entity_id,
        "away_mode": away_mode,
    }
