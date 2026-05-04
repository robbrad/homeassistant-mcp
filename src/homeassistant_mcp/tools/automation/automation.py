"""Automation management tool for Home Assistant MCP server."""

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


def register_automation_tool(mcp: Any, get_client: Any) -> None:
    """Register the automation control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"automation", "control"},
        timeout=30,
    )
    async def automation_control(
        action: Annotated[
            Literal["list", "toggle", "trigger", "turn_on", "turn_off", "reload"],
            Field(
                description="Action to perform: list all automations, toggle automation on/off, trigger automation, turn on, turn off, or reload automations"
            ),
        ],
        automation_id: Annotated[
            str | None,
            Field(
                description="Automation entity ID (required for toggle, trigger, turn_on, turn_off). Example: 'automation.morning_routine'"
            ),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Manage Home Assistant automations.

        This tool allows you to list all automations, toggle automations on/off,
        manually trigger automations, turn them on/off, and reload automation configuration.

        Tip: If the list action returns fewer automations than expected, use
            states_control(action="list", domain="automation") for a complete list
            of all automation entities regardless of how they were created.

        Actions:
        - list: Get all automation entities with their current states and last triggered time
        - toggle: Enable or disable an automation
        - trigger: Manually execute an automation
        - turn_on: Enable an automation
        - turn_off: Disable an automation
        - reload: Reload all automation configurations from YAML files

        Examples:
        - List all automations: automation_control(action="list")
        - Toggle automation: automation_control(action="toggle", automation_id="automation.morning_routine")
        - Trigger automation: automation_control(action="trigger", automation_id="automation.morning_routine")
        - Turn on automation: automation_control(action="turn_on", automation_id="automation.morning_routine")
        - Turn off automation: automation_control(action="turn_off", automation_id="automation.morning_routine")
        - Reload automations: automation_control(action="reload")

        Args:
            action: The action to perform
            automation_id: The automation entity ID (required for toggle, trigger, turn_on, turn_off)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing automation_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_automations(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "toggle":
                if not automation_id:
                    return {
                        "error": "automation_id is required for 'toggle' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _toggle_automation(client, automation_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "trigger":
                if not automation_id:
                    return {
                        "error": "automation_id is required for 'trigger' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _trigger_automation(client, automation_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "turn_on":
                if not automation_id:
                    return {
                        "error": "automation_id is required for 'turn_on' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _turn_on_automation(client, automation_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "turn_off":
                if not automation_id:
                    return {
                        "error": "automation_id is required for 'turn_off' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _turn_off_automation(client, automation_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "reload":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _reload_automations(client)
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
            logger.error(f"Unexpected error in automation_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_automations(client: HomeAssistantClient) -> dict:
    """List all automation entities.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing list of automations with their states
    """
    logger.info("Listing all automation entities")

    # Get all states and filter for automations
    all_states = await client.get_states()
    automations = [
        state for state in all_states if state.get("entity_id", "").startswith("automation.")
    ]

    # Format the response
    automation_list = []
    for automation in automations:
        automation_info = {
            "entity_id": automation.get("entity_id"),
            "name": automation.get("attributes", {}).get(
                "friendly_name", automation.get("entity_id")
            ),
            "state": automation.get("state"),
            "last_triggered": automation.get("attributes", {}).get("last_triggered"),
        }

        automation_list.append(automation_info)

    logger.info(f"Found {len(automation_list)} automation entities")

    return {"success": True, "count": len(automation_list), "automations": automation_list}


async def _toggle_automation(client: HomeAssistantClient, automation_id: str) -> dict:
    """Toggle an automation on or off.

    Args:
        client: The Home Assistant client
        automation_id: The automation entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the automation entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Toggling automation: {automation_id}")

    # Validate that this is an automation entity
    if not automation_id.startswith("automation."):
        raise EntityNotFoundError(
            f"Entity '{automation_id}' is not an automation entity. Automation entities must start with 'automation.'"
        )

    # Get current state to determine the action
    state = await client.get_state(automation_id)
    current_state = state.get("state")

    # Call the toggle service
    service_data = {"entity_id": automation_id}
    await client.call_service("automation", "toggle", service_data)

    # Determine new state (opposite of current)
    new_state = "off" if current_state == "on" else "on"

    logger.info(
        f"Successfully toggled automation: {automation_id} from {current_state} to {new_state}"
    )

    return {
        "success": True,
        "message": f"Automation '{automation_id}' toggled from {current_state} to {new_state}",
        "entity_id": automation_id,
        "previous_state": current_state,
        "new_state": new_state,
    }


async def _trigger_automation(client: HomeAssistantClient, automation_id: str) -> dict:
    """Manually trigger an automation.

    Args:
        client: The Home Assistant client
        automation_id: The automation entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the automation entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Triggering automation: {automation_id}")

    # Validate that this is an automation entity
    if not automation_id.startswith("automation."):
        raise EntityNotFoundError(
            f"Entity '{automation_id}' is not an automation entity. Automation entities must start with 'automation.'"
        )

    # Verify the automation exists
    await client.get_state(automation_id)

    # Call the trigger service
    service_data = {"entity_id": automation_id}
    await client.call_service("automation", "trigger", service_data)

    logger.info(f"Successfully triggered automation: {automation_id}")

    return {
        "success": True,
        "message": f"Automation '{automation_id}' triggered successfully",
        "entity_id": automation_id,
    }


async def _turn_on_automation(client: HomeAssistantClient, automation_id: str) -> dict:
    """Turn on (enable) an automation.

    Args:
        client: The Home Assistant client
        automation_id: The automation entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the automation entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Turning on automation: {automation_id}")

    # Validate that this is an automation entity
    if not automation_id.startswith("automation."):
        raise EntityNotFoundError(
            f"Entity '{automation_id}' is not an automation entity. Automation entities must start with 'automation.'"
        )

    # Verify the automation exists
    await client.get_state(automation_id)

    # Call the turn_on service
    service_data = {"entity_id": automation_id}
    await client.call_service("automation", "turn_on", service_data)

    logger.info(f"Successfully turned on automation: {automation_id}")

    return {
        "success": True,
        "message": f"Automation '{automation_id}' turned on (enabled)",
        "entity_id": automation_id,
        "state": "on",
    }


async def _turn_off_automation(client: HomeAssistantClient, automation_id: str) -> dict:
    """Turn off (disable) an automation.

    Args:
        client: The Home Assistant client
        automation_id: The automation entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the automation entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Turning off automation: {automation_id}")

    # Validate that this is an automation entity
    if not automation_id.startswith("automation."):
        raise EntityNotFoundError(
            f"Entity '{automation_id}' is not an automation entity. Automation entities must start with 'automation.'"
        )

    # Verify the automation exists
    await client.get_state(automation_id)

    # Call the turn_off service
    service_data = {"entity_id": automation_id}
    await client.call_service("automation", "turn_off", service_data)

    logger.info(f"Successfully turned off automation: {automation_id}")

    return {
        "success": True,
        "message": f"Automation '{automation_id}' turned off (disabled)",
        "entity_id": automation_id,
        "state": "off",
    }


async def _reload_automations(client: HomeAssistantClient) -> dict:
    """Reload all automation configurations from YAML files.

    This is useful after editing automation configuration files to apply changes
    without restarting Home Assistant.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing the result of the operation

    Raises:
        ServiceCallError: If the service call fails
    """
    logger.info("Reloading automation configurations")

    # Call the reload service (no entity_id needed)
    await client.call_service("automation", "reload", {})

    logger.info("Successfully reloaded automation configurations")

    return {
        "success": True,
        "message": "All automation configurations reloaded successfully",
    }
