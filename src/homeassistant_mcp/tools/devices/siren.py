"""Siren control tool for Home Assistant MCP server."""

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


def register_siren_tool(mcp: Any, get_client: Any) -> None:
    """Register the siren control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control", "security"},
        timeout=30,
    )
    async def siren_control(
        action: Annotated[
            Literal["list", "get", "turn_on", "turn_off", "toggle"],
            Field(
                description="Action to perform: list all sirens, get specific siren, turn on, turn off, or toggle"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Siren entity ID (required for get, turn_on, turn_off, toggle). Example: 'siren.alarm'"
            ),
        ] = None,
        tone: Annotated[
            str | None,
            Field(
                description="Tone/sound to play (e.g., 'fire', 'ambulance', 'police'). Only used with turn_on action."
            ),
        ] = None,
        volume_level: Annotated[
            float | None,
            Field(
                ge=0.0, le=1.0, description="Volume level (0.0-1.0). Only used with turn_on action."
            ),
        ] = None,
        duration: Annotated[
            int | None,
            Field(
                description="Duration in seconds to play the siren. Only used with turn_on action."
            ),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Control sirens in Home Assistant.

        This tool allows you to list all sirens, get details about a specific siren,
        turn sirens on/off with optional tone, volume, and duration settings.

        Actions:
        - list: Get all siren entities with their current states
        - get: Get detailed information about a specific siren
        - turn_on: Turn on a siren with optional tone, volume, and duration
        - turn_off: Turn off a siren
        - toggle: Toggle a siren state

        Examples:
        - List all sirens: siren_control(action="list")
        - Get siren details: siren_control(action="get", entity_id="siren.alarm")
        - Turn on siren: siren_control(action="turn_on", entity_id="siren.alarm")
        - Turn on with tone: siren_control(action="turn_on", entity_id="siren.alarm", tone="fire")
        - Turn on with volume: siren_control(action="turn_on", entity_id="siren.alarm", volume_level=0.8)
        - Turn on with duration: siren_control(action="turn_on", entity_id="siren.alarm", duration=30)
        - Turn off siren: siren_control(action="turn_off", entity_id="siren.alarm")
        - Toggle siren: siren_control(action="toggle", entity_id="siren.alarm")

        Args:
            action: The action to perform
            entity_id: The siren entity ID (required for most actions)
            tone: Tone/sound to play (optional, for turn_on)
            volume_level: Volume level 0.0-1.0 (optional, for turn_on)
            duration: Duration in seconds (optional, for turn_on)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing siren_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_sirens(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_siren(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "turn_on":
                if not entity_id:
                    return {"error": "entity_id is required for 'turn_on' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _turn_on_siren(client, entity_id, tone, volume_level, duration)
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
                result = await _turn_off_siren(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "toggle":
                if not entity_id:
                    return {"error": "entity_id is required for 'toggle' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _toggle_siren(client, entity_id)
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
            logger.error(f"Unexpected error in siren_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_sirens(client: HomeAssistantClient) -> dict:
    """List all siren entities."""
    logger.info("Listing all siren entities")

    all_states = await client.get_states()
    sirens = [state for state in all_states if state.get("entity_id", "").startswith("siren.")]

    siren_list = []
    for siren in sirens:
        siren_info = {
            "entity_id": siren.get("entity_id"),
            "name": siren.get("attributes", {}).get("friendly_name", siren.get("entity_id")),
            "state": siren.get("state"),
        }

        attrs = siren.get("attributes", {})
        if "available_tones" in attrs:
            siren_info["available_tones"] = attrs["available_tones"]

        siren_list.append(siren_info)

    logger.info(f"Found {len(siren_list)} siren entities")
    return {"success": True, "count": len(siren_list), "sirens": siren_list}


async def _get_siren(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific siren."""
    logger.info(f"Getting details for siren: {entity_id}")

    if not entity_id.startswith("siren."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a siren entity. Siren entities must start with 'siren.'"
        )

    state = await client.get_state(entity_id)

    siren_info = {
        "entity_id": state.get("entity_id"),
        "name": state.get("attributes", {}).get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": state.get("attributes", {}),
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")
    return {"success": True, "siren": siren_info}


async def _turn_on_siren(
    client: HomeAssistantClient,
    entity_id: str,
    tone: str | None = None,
    volume_level: float | None = None,
    duration: int | None = None,
) -> dict:
    """Turn on a siren."""
    logger.info(f"Turning on siren: {entity_id}")

    if not entity_id.startswith("siren."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a siren entity. Siren entities must start with 'siren.'"
        )

    service_data: dict[str, Any] = {"entity_id": entity_id}
    if tone is not None:
        service_data["tone"] = tone
    if volume_level is not None:
        service_data["volume_level"] = volume_level
    if duration is not None:
        service_data["duration"] = duration

    await client.call_service("siren", "turn_on", service_data)

    logger.info(f"Successfully turned on siren: {entity_id}")
    return {"success": True, "message": f"Siren '{entity_id}' turned on", "entity_id": entity_id}


async def _turn_off_siren(client: HomeAssistantClient, entity_id: str) -> dict:
    """Turn off a siren."""
    logger.info(f"Turning off siren: {entity_id}")

    if not entity_id.startswith("siren."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a siren entity. Siren entities must start with 'siren.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("siren", "turn_off", service_data)

    logger.info(f"Successfully turned off siren: {entity_id}")
    return {"success": True, "message": f"Siren '{entity_id}' turned off", "entity_id": entity_id}


async def _toggle_siren(client: HomeAssistantClient, entity_id: str) -> dict:
    """Toggle a siren state."""
    logger.info(f"Toggling siren: {entity_id}")

    if not entity_id.startswith("siren."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a siren entity. Siren entities must start with 'siren.'"
        )

    service_data = {"entity_id": entity_id}
    await client.call_service("siren", "toggle", service_data)

    logger.info(f"Successfully toggled siren: {entity_id}")
    return {"success": True, "message": f"Siren '{entity_id}' toggled", "entity_id": entity_id}
