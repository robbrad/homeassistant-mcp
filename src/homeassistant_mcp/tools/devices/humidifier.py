"""Humidifier control tool for Home Assistant MCP server."""

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


def register_humidifier_tool(mcp: Any, get_client: Any) -> None:
    """Register the humidifier control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control"},
        timeout=30,
    )
    async def humidifier_control(
        action: Annotated[
            Literal["list", "get", "turn_on", "turn_off", "set_humidity", "set_mode"],
            Field(
                description="Action to perform: list all humidifiers, get specific humidifier, turn on, turn off, set humidity, or set mode"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Humidifier entity ID (required for get, turn_on, turn_off, set_humidity, set_mode). Example: 'humidifier.bedroom'"
            ),
        ] = None,
        humidity: Annotated[
            int | None,
            Field(
                ge=0,
                le=100,
                description="Target humidity percentage (0-100). Only used with set_humidity action.",
            ),
        ] = None,
        mode: Annotated[
            str | None,
            Field(
                description="Operation mode (e.g., 'normal', 'eco', 'away', 'boost', 'comfort', 'home', 'sleep', 'auto', 'baby'). Only used with set_mode action."
            ),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Control humidifiers in Home Assistant.

        This tool allows you to list all humidifiers, get details about a specific humidifier,
        turn humidifiers on/off, set target humidity, and control operation modes.

        Actions:
        - list: Get all humidifier entities with their current states
        - get: Get detailed information about a specific humidifier
        - turn_on: Turn on a humidifier
        - turn_off: Turn off a humidifier
        - set_humidity: Set target humidity percentage (0-100)
        - set_mode: Set operation mode (normal, eco, away, boost, etc.)

        Examples:
        - List all humidifiers: humidifier_control(action="list")
        - Get humidifier details: humidifier_control(action="get", entity_id="humidifier.bedroom")
        - Turn on humidifier: humidifier_control(action="turn_on", entity_id="humidifier.bedroom")
        - Set humidity: humidifier_control(action="set_humidity", entity_id="humidifier.bedroom", humidity=60)
        - Set mode: humidifier_control(action="set_mode", entity_id="humidifier.bedroom", mode="eco")

        Args:
            action: The action to perform
            entity_id: The humidifier entity ID (required for most actions)
            humidity: Target humidity percentage 0-100 (optional, for set_humidity)
            mode: Operation mode name (optional, for set_mode)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing humidifier_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_humidifiers(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_humidifier(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "turn_on":
                if not entity_id:
                    return {"error": "entity_id is required for 'turn_on' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _turn_on_humidifier(client, entity_id)
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
                result = await _turn_off_humidifier(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_humidity":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_humidity' action",
                        "success": False,
                    }
                if humidity is None:
                    return {
                        "error": "humidity is required for 'set_humidity' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_humidity(client, entity_id, humidity)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_mode":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_mode' action",
                        "success": False,
                    }
                if not mode:
                    return {"error": "mode is required for 'set_mode' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_mode(client, entity_id, mode)
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
            logger.error(f"Unexpected error in humidifier_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_humidifiers(client: HomeAssistantClient) -> dict:
    """List all humidifier entities."""
    logger.info("Listing all humidifier entities")

    humidifiers = await client.get_states(domain="humidifier")

    humidifier_list = []
    for hum in humidifiers:
        hum_info = {
            "entity_id": hum.get("entity_id"),
            "name": hum.get("attributes", {}).get("friendly_name", hum.get("entity_id")),
            "state": hum.get("state"),
        }

        attrs = hum.get("attributes", {})
        if "humidity" in attrs:
            hum_info["current_humidity"] = attrs["humidity"]
        if "mode" in attrs:
            hum_info["mode"] = attrs["mode"]

        humidifier_list.append(hum_info)

    logger.info(f"Found {len(humidifier_list)} humidifier entities")
    return {"success": True, "count": len(humidifier_list), "humidifiers": humidifier_list}


async def _get_humidifier(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific humidifier."""
    logger.info(f"Getting details for humidifier: {entity_id}")

    if not entity_id.startswith("humidifier."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a humidifier entity. Humidifier entities must start with 'humidifier.'"
        )

    state = await client.get_state(entity_id)

    humidifier_info = {
        "entity_id": state.get("entity_id"),
        "name": state.get("attributes", {}).get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": state.get("attributes", {}),
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")
    return {"success": True, "humidifier": humidifier_info}


async def _turn_on_humidifier(client: HomeAssistantClient, entity_id: str) -> dict:
    """Turn on a humidifier."""
    logger.info(f"Turning on humidifier: {entity_id}")

    if not entity_id.startswith("humidifier."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a humidifier entity. Humidifier entities must start with 'humidifier.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("humidifier", "turn_on", service_data)

    logger.info(f"Successfully turned on humidifier: {entity_id}")
    return {
        "success": True,
        "message": f"Humidifier '{entity_id}' turned on",
        "entity_id": entity_id,
    }


async def _turn_off_humidifier(client: HomeAssistantClient, entity_id: str) -> dict:
    """Turn off a humidifier."""
    logger.info(f"Turning off humidifier: {entity_id}")

    if not entity_id.startswith("humidifier."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a humidifier entity. Humidifier entities must start with 'humidifier.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("humidifier", "turn_off", service_data)

    logger.info(f"Successfully turned off humidifier: {entity_id}")
    return {
        "success": True,
        "message": f"Humidifier '{entity_id}' turned off",
        "entity_id": entity_id,
    }


async def _set_humidity(client: HomeAssistantClient, entity_id: str, humidity: int) -> dict:
    """Set the humidifier target humidity."""
    logger.info(f"Setting humidifier {entity_id} humidity to {humidity}%")

    if not entity_id.startswith("humidifier."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a humidifier entity. Humidifier entities must start with 'humidifier.'"
        )

    service_data = {"entity_id": entity_id, "humidity": humidity}
    await client.call_service("humidifier", "set_humidity", service_data)

    logger.info(f"Successfully set humidifier {entity_id} humidity to {humidity}%")
    return {
        "success": True,
        "message": f"Humidifier '{entity_id}' humidity set to {humidity}%",
        "entity_id": entity_id,
        "humidity": humidity,
    }


async def _set_mode(client: HomeAssistantClient, entity_id: str, mode: str) -> dict:
    """Set the humidifier operation mode."""
    logger.info(f"Setting humidifier {entity_id} mode to {mode}")

    if not entity_id.startswith("humidifier."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a humidifier entity. Humidifier entities must start with 'humidifier.'"
        )

    service_data = {"entity_id": entity_id, "mode": mode}
    await client.call_service("humidifier", "set_mode", service_data)

    logger.info(f"Successfully set humidifier {entity_id} mode to {mode}")
    return {
        "success": True,
        "message": f"Humidifier '{entity_id}' mode set to '{mode}'",
        "entity_id": entity_id,
        "mode": mode,
    }
