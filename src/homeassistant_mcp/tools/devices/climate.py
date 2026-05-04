"""Climate control tool for Home Assistant MCP server."""

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


def register_climate_tool(mcp: Any, get_client: Any) -> None:
    """Register the climate control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"device", "control", "climate"},
        timeout=30,
    )
    async def climate_control(
        action: Annotated[
            Literal["list", "get", "set_hvac_mode", "set_temperature", "set_fan_mode"],
            Field(
                description="Action to perform: list all climate devices, get specific device, set HVAC mode, set temperature, or set fan mode"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Climate entity ID (required for get, set_hvac_mode, set_temperature, set_fan_mode). Example: 'climate.living_room'"
            ),
        ] = None,
        hvac_mode: Annotated[
            Literal["off", "heat", "cool", "auto", "dry", "fan_only"] | None,
            Field(description="HVAC mode to set. Only used with set_hvac_mode action."),
        ] = None,
        temperature: Annotated[
            float | None,
            Field(
                description="Target temperature for single-setpoint devices. Only used with set_temperature action."
            ),
        ] = None,
        target_temp_high: Annotated[
            float | None,
            Field(
                description="High target temperature for dual-setpoint devices. Must be used with target_temp_low."
            ),
        ] = None,
        target_temp_low: Annotated[
            float | None,
            Field(
                description="Low target temperature for dual-setpoint devices. Must be used with target_temp_high."
            ),
        ] = None,
        fan_mode: Annotated[
            Literal["auto", "low", "medium", "high"] | None,
            Field(description="Fan mode to set. Only used with set_fan_mode action."),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Control climate devices (thermostats, HVAC) in Home Assistant.

        This tool allows you to list all climate devices, get details about a specific device,
        set HVAC modes, adjust temperatures, and control fan modes.

        Actions:
        - list: Get all climate entities with their current states
        - get: Get detailed information about a specific climate device
        - set_hvac_mode: Change the HVAC mode (off, heat, cool, auto, dry, fan_only)
        - set_temperature: Set target temperature (single or dual setpoint)
        - set_fan_mode: Change the fan mode (auto, low, medium, high)

        Examples:
        - List all climate devices: climate_control(action="list")
        - Get device details: climate_control(action="get", entity_id="climate.living_room")
        - Set HVAC mode: climate_control(action="set_hvac_mode", entity_id="climate.living_room", hvac_mode="heat")
        - Set temperature: climate_control(action="set_temperature", entity_id="climate.living_room", temperature=72.0)
        - Set temp range: climate_control(action="set_temperature", entity_id="climate.living_room", target_temp_high=75.0, target_temp_low=68.0)
        - Set fan mode: climate_control(action="set_fan_mode", entity_id="climate.living_room", fan_mode="auto")

        Note: The list action returns entities from the HA states API. If some
            entities are missing, use states_control(action="list", domain="climate")
            or list_devices(domain="climate") for a more complete view.

        Args:
            action: The action to perform
            entity_id: The climate entity ID (required for get, set_hvac_mode, set_temperature, set_fan_mode)
            hvac_mode: HVAC mode to set (for set_hvac_mode)
            temperature: Target temperature for single-setpoint devices (for set_temperature)
            target_temp_high: High target temperature for dual-setpoint devices (for set_temperature)
            target_temp_low: Low target temperature for dual-setpoint devices (for set_temperature)
            fan_mode: Fan mode to set (for set_fan_mode)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing climate_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_climate_devices(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _get_climate_device(client, entity_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_hvac_mode":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_hvac_mode' action",
                        "success": False,
                    }
                if not hvac_mode:
                    return {
                        "error": "hvac_mode is required for 'set_hvac_mode' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_hvac_mode(client, entity_id, hvac_mode)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "set_temperature":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_temperature' action",
                        "success": False,
                    }
                return await _set_temperature(
                    client, entity_id, temperature, target_temp_high, target_temp_low
                )

            elif action == "set_fan_mode":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_fan_mode' action",
                        "success": False,
                    }
                if not fan_mode:
                    return {
                        "error": "fan_mode is required for 'set_fan_mode' action",
                        "success": False,
                    }
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _set_fan_mode(client, entity_id, fan_mode)
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
            logger.error(f"Unexpected error in climate_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_climate_devices(client: HomeAssistantClient) -> dict:
    """List all climate entities.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing list of climate devices with their states
    """
    logger.info("Listing all climate entities")

    # Get all climate device states
    climate_devices = await client.get_states(domain="climate")

    # Format the response
    device_list = []
    for device in climate_devices:
        device_info = {
            "entity_id": device.get("entity_id"),
            "name": device.get("attributes", {}).get("friendly_name", device.get("entity_id")),
            "state": device.get("state"),
        }

        # Add temperature information if available
        attrs = device.get("attributes", {})
        if "current_temperature" in attrs:
            device_info["current_temperature"] = attrs["current_temperature"]

        if "temperature" in attrs:
            device_info["target_temperature"] = attrs["temperature"]

        if "target_temp_high" in attrs:
            device_info["target_temp_high"] = attrs["target_temp_high"]

        if "target_temp_low" in attrs:
            device_info["target_temp_low"] = attrs["target_temp_low"]

        # Add mode information
        if "hvac_mode" in attrs:
            device_info["hvac_mode"] = attrs["hvac_mode"]

        if "fan_mode" in attrs:
            device_info["fan_mode"] = attrs["fan_mode"]

        device_list.append(device_info)

    logger.info(f"Found {len(device_list)} climate entities")

    return {"success": True, "count": len(device_list), "climate_devices": device_list}


async def _get_climate_device(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific climate device.

    Args:
        client: The Home Assistant client
        entity_id: The climate entity ID

    Returns:
        Dictionary containing detailed climate device information

    Raises:
        EntityNotFoundError: If the climate entity is not found
    """
    logger.info(f"Getting details for climate device: {entity_id}")

    # Validate that this is a climate entity
    if not entity_id.startswith("climate."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a climate entity. Climate entities must start with 'climate.'"
        )

    # Get the entity state
    state = await client.get_state(entity_id)

    # Format the response with all available information
    device_info = {
        "entity_id": state.get("entity_id"),
        "name": state.get("attributes", {}).get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": state.get("attributes", {}),
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")

    return {"success": True, "climate_device": device_info}


async def _set_hvac_mode(
    client: HomeAssistantClient,
    entity_id: str,
    hvac_mode: str,
) -> dict:
    """Set the HVAC mode for a climate device.

    Args:
        client: The Home Assistant client
        entity_id: The climate entity ID
        hvac_mode: The HVAC mode to set

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the climate entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Setting HVAC mode for {entity_id} to {hvac_mode}")

    # Validate that this is a climate entity
    if not entity_id.startswith("climate."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a climate entity. Climate entities must start with 'climate.'"
        )

    # Build service data
    service_data = {"entity_id": entity_id, "hvac_mode": hvac_mode}

    # Call the service
    await client.call_service("climate", "set_hvac_mode", service_data)

    logger.info(f"Successfully set HVAC mode for {entity_id} to {hvac_mode}")

    return {
        "success": True,
        "message": f"HVAC mode for '{entity_id}' set to '{hvac_mode}'",
        "entity_id": entity_id,
        "hvac_mode": hvac_mode,
    }


async def _set_temperature(
    client: HomeAssistantClient,
    entity_id: str,
    temperature: float | None = None,
    target_temp_high: float | None = None,
    target_temp_low: float | None = None,
) -> dict:
    """Set the target temperature for a climate device.

    Args:
        client: The Home Assistant client
        entity_id: The climate entity ID
        temperature: Target temperature for single-setpoint devices
        target_temp_high: High target temperature for dual-setpoint devices
        target_temp_low: Low target temperature for dual-setpoint devices

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the climate entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Setting temperature for {entity_id}")

    # Validate that this is a climate entity
    if not entity_id.startswith("climate."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a climate entity. Climate entities must start with 'climate.'"
        )

    # Validate temperature parameters
    has_single = temperature is not None
    has_high = target_temp_high is not None
    has_low = target_temp_low is not None

    # Check for invalid combinations
    if has_high and not has_low:
        return {
            "error": "target_temp_low is required when target_temp_high is provided",
            "success": False,
        }

    if has_low and not has_high:
        return {
            "error": "target_temp_high is required when target_temp_low is provided",
            "success": False,
        }

    if not has_single and not (has_high and has_low):
        return {
            "error": "Either 'temperature' or both 'target_temp_high' and 'target_temp_low' must be provided",
            "success": False,
        }

    if has_single and (has_high or has_low):
        return {
            "error": "Cannot specify both 'temperature' and temperature range (target_temp_high/target_temp_low)",
            "success": False,
        }

    # Build service data
    service_data: dict[str, Any] = {"entity_id": entity_id}

    if has_single:
        service_data["temperature"] = temperature
        logger.debug(f"Setting temperature to {temperature}")
    else:
        service_data["target_temp_high"] = target_temp_high
        service_data["target_temp_low"] = target_temp_low
        logger.debug(f"Setting temperature range: {target_temp_low} - {target_temp_high}")

    # Call the service
    await client.call_service("climate", "set_temperature", service_data)

    logger.info(f"Successfully set temperature for {entity_id}")

    result = {
        "success": True,
        "message": f"Temperature for '{entity_id}' updated",
        "entity_id": entity_id,
    }

    if has_single:
        result["temperature"] = temperature
    else:
        result["target_temp_high"] = target_temp_high
        result["target_temp_low"] = target_temp_low

    return result


async def _set_fan_mode(
    client: HomeAssistantClient,
    entity_id: str,
    fan_mode: str,
) -> dict:
    """Set the fan mode for a climate device.

    Args:
        client: The Home Assistant client
        entity_id: The climate entity ID
        fan_mode: The fan mode to set

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the climate entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Setting fan mode for {entity_id} to {fan_mode}")

    # Validate that this is a climate entity
    if not entity_id.startswith("climate."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a climate entity. Climate entities must start with 'climate.'"
        )

    # Build service data
    service_data = {"entity_id": entity_id, "fan_mode": fan_mode}

    # Call the service
    await client.call_service("climate", "set_fan_mode", service_data)

    logger.info(f"Successfully set fan mode for {entity_id} to {fan_mode}")

    return {
        "success": True,
        "message": f"Fan mode for '{entity_id}' set to '{fan_mode}'",
        "entity_id": entity_id,
        "fan_mode": fan_mode,
    }
