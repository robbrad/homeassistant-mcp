"""Alarm control panel tool for Home Assistant MCP server."""

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


def register_alarm_tool(mcp: Any, get_client: Any) -> None:
    """Register the alarm control panel tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control", "security"},
        timeout=30,
    )
    async def alarm_control(
        action: Annotated[
            Literal["list", "get", "arm_away", "arm_home", "arm_night", "disarm", "trigger"],
            Field(
                description="Action to perform: list all alarms, get specific alarm, arm in different modes, disarm, or trigger"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Alarm control panel entity ID (required for get, arm_away, arm_home, arm_night, disarm, trigger). Example: 'alarm_control_panel.home'"
            ),
        ] = None,
        code: Annotated[
            str | None,
            Field(
                description="Security code (required for disarm action, may be required for arming depending on configuration)"
            ),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Control alarm systems in Home Assistant.

        This tool allows you to list all alarm control panels, get details about a specific alarm,
        arm the alarm in different modes (away, home, night), disarm the alarm, and trigger the alarm.

        Actions:
        - list: Get all alarm control panel entities with their armed state
        - get: Get detailed information about a specific alarm control panel
        - arm_away: Arm the alarm in away mode (full protection)
        - arm_home: Arm the alarm in home mode (perimeter protection)
        - arm_night: Arm the alarm in night mode (sleep protection)
        - disarm: Disarm the alarm (requires code)
        - trigger: Manually trigger the alarm

        Examples:
        - List all alarms: alarm_control(action="list")
        - Get alarm details: alarm_control(action="get", entity_id="alarm_control_panel.home")
        - Arm away: alarm_control(action="arm_away", entity_id="alarm_control_panel.home")
        - Arm home: alarm_control(action="arm_home", entity_id="alarm_control_panel.home")
        - Arm night: alarm_control(action="arm_night", entity_id="alarm_control_panel.home")
        - Disarm: alarm_control(action="disarm", entity_id="alarm_control_panel.home", code="1234")
        - Trigger: alarm_control(action="trigger", entity_id="alarm_control_panel.home")

        Args:
            action: The action to perform
            entity_id: The alarm control panel entity ID (required for all actions except list)
            code: Security code (required for disarm, may be required for arming)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing alarm_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_alarms(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_alarm(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "arm_away":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'arm_away' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _arm_alarm(client, entity_id, "arm_away", code)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "arm_home":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'arm_home' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _arm_alarm(client, entity_id, "arm_home", code)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "arm_night":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'arm_night' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _arm_alarm(client, entity_id, "arm_night", code)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "disarm":
                if not entity_id:
                    return {"error": "entity_id is required for 'disarm' action", "success": False}
                if not code:
                    return {"error": "code is required for 'disarm' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _disarm_alarm(client, entity_id, code)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "trigger":
                if not entity_id:
                    return {"error": "entity_id is required for 'trigger' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _trigger_alarm(client, entity_id)
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
            logger.error(f"Unexpected error in alarm_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_alarms(client: HomeAssistantClient) -> dict:
    """List all alarm control panel entities.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing list of alarm control panels with their states
    """
    logger.info("Listing all alarm control panel entities")

    # Get all states and filter for alarm control panels
    all_states = await client.get_states()
    alarms = [
        state
        for state in all_states
        if state.get("entity_id", "").startswith("alarm_control_panel.")
    ]

    # Format the response
    alarm_list = []
    for alarm in alarms:
        attributes = alarm.get("attributes", {})
        alarm_info = {
            "entity_id": alarm.get("entity_id"),
            "name": attributes.get("friendly_name", alarm.get("entity_id")),
            "state": alarm.get("state"),
        }

        # Include code format if available
        if "code_format" in attributes:
            alarm_info["code_format"] = attributes["code_format"]

        # Include supported features
        if "supported_features" in attributes:
            alarm_info["supported_features"] = attributes["supported_features"]

        alarm_list.append(alarm_info)

    logger.info(f"Found {len(alarm_list)} alarm control panel entities")

    return {"success": True, "count": len(alarm_list), "alarms": alarm_list}


async def _get_alarm(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific alarm control panel.

    Args:
        client: The Home Assistant client
        entity_id: The alarm control panel entity ID

    Returns:
        Dictionary containing detailed alarm information

    Raises:
        EntityNotFoundError: If the alarm entity is not found
    """
    logger.info(f"Getting details for alarm control panel: {entity_id}")

    # Validate that this is an alarm control panel entity
    if not entity_id.startswith("alarm_control_panel."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an alarm control panel entity. "
            f"Alarm control panel entities must start with 'alarm_control_panel.'"
        )

    # Get the entity state
    state = await client.get_state(entity_id)
    attributes = state.get("attributes", {})

    # Format the response with all available information
    alarm_info = {
        "entity_id": state.get("entity_id"),
        "name": attributes.get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
    }

    # Include code format if available
    if "code_format" in attributes:
        alarm_info["code_format"] = attributes["code_format"]

    # Include supported features
    if "supported_features" in attributes:
        alarm_info["supported_features"] = attributes["supported_features"]

    # Include other relevant attributes
    alarm_info["attributes"] = attributes

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")

    return {"success": True, "alarm": alarm_info}


async def _arm_alarm(
    client: HomeAssistantClient, entity_id: str, mode: str, code: str | None = None
) -> dict:
    """Arm an alarm control panel in a specific mode.

    Args:
        client: The Home Assistant client
        entity_id: The alarm control panel entity ID
        mode: The arming mode (arm_away, arm_home, arm_night)
        code: Optional security code

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the alarm entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Arming alarm {entity_id} in mode: {mode}")

    # Validate that this is an alarm control panel entity
    if not entity_id.startswith("alarm_control_panel."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an alarm control panel entity. "
            f"Alarm control panel entities must start with 'alarm_control_panel.'"
        )

    # Build service data
    service_data = {"entity_id": entity_id}
    if code:
        service_data["code"] = code

    # Call the appropriate service
    await client.call_service("alarm_control_panel", mode, service_data)

    logger.info(f"Successfully armed alarm {entity_id} in mode: {mode}")

    return {
        "success": True,
        "message": f"Alarm '{entity_id}' armed in {mode.replace('arm_', '')} mode",
        "entity_id": entity_id,
        "mode": mode.replace("arm_", ""),
    }


async def _disarm_alarm(client: HomeAssistantClient, entity_id: str, code: str) -> dict:
    """Disarm an alarm control panel.

    Args:
        client: The Home Assistant client
        entity_id: The alarm control panel entity ID
        code: Security code (required)

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the alarm entity is not found
        ServiceCallError: If the service call fails (including invalid code)
    """
    logger.info(f"Disarming alarm: {entity_id}")

    # Validate that this is an alarm control panel entity
    if not entity_id.startswith("alarm_control_panel."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an alarm control panel entity. "
            f"Alarm control panel entities must start with 'alarm_control_panel.'"
        )

    # Call the service with code
    service_data = {"entity_id": entity_id, "code": code}
    await client.call_service("alarm_control_panel", "disarm", service_data)

    logger.info(f"Successfully disarmed alarm: {entity_id}")

    return {
        "success": True,
        "message": f"Alarm '{entity_id}' disarmed",
        "entity_id": entity_id,
    }


async def _trigger_alarm(client: HomeAssistantClient, entity_id: str) -> dict:
    """Manually trigger an alarm control panel.

    Args:
        client: The Home Assistant client
        entity_id: The alarm control panel entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the alarm entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Triggering alarm: {entity_id}")

    # Validate that this is an alarm control panel entity
    if not entity_id.startswith("alarm_control_panel."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not an alarm control panel entity. "
            f"Alarm control panel entities must start with 'alarm_control_panel.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("alarm_control_panel", "alarm_trigger", service_data)

    logger.info(f"Successfully triggered alarm: {entity_id}")

    return {
        "success": True,
        "message": f"Alarm '{entity_id}' triggered",
        "entity_id": entity_id,
    }
