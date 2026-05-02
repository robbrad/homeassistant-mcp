"""Device listing tool for Home Assistant MCP server."""

import logging
from collections import defaultdict
from typing import Annotated, Any, Literal

from pydantic import Field

from ..exceptions import (
    AuthenticationError,
    ConnectionError,
    HomeAssistantError,
    ServiceCallError,
)
from ..hass.client import HomeAssistantClient

logger = logging.getLogger(__name__)


# All Home Assistant entity domains as documented
VALID_DOMAINS = [
    "air_quality",
    "alarm_control_panel",
    "assist_satellite",
    "binary_sensor",
    "button",
    "calendar",
    "camera",
    "climate",
    "conversation",
    "cover",
    "date",
    "datetime",
    "device_tracker",
    "event",
    "fan",
    "geo_location",
    "humidifier",
    "image",
    "image_processing",
    "lawn_mower",
    "light",
    "lock",
    "media_player",
    "notify",
    "number",
    "remote",
    "scene",
    "select",
    "sensor",
    "siren",
    "stt",
    "switch",
    "tag",
    "text",
    "time",
    "todo",
    "tts",
    "update",
    "vacuum",
    "valve",
    "wake_word",
    "water_heater",
    "weather",
]


def register_devices_tool(mcp: Any, get_client: Any) -> None:
    """Register the device listing tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool()
    async def list_devices(
        domain: Annotated[
            Literal[
                "air_quality",
                "alarm_control_panel",
                "assist_satellite",
                "binary_sensor",
                "button",
                "calendar",
                "camera",
                "climate",
                "conversation",
                "cover",
                "date",
                "datetime",
                "device_tracker",
                "event",
                "fan",
                "geo_location",
                "humidifier",
                "image",
                "image_processing",
                "lawn_mower",
                "light",
                "lock",
                "media_player",
                "notify",
                "number",
                "remote",
                "scene",
                "select",
                "sensor",
                "siren",
                "stt",
                "switch",
                "tag",
                "text",
                "time",
                "todo",
                "tts",
                "update",
                "vacuum",
                "valve",
                "wake_word",
                "water_heater",
                "weather",
            ]
            | None,
            Field(
                description="Filter devices by domain (e.g., 'light', 'switch', 'sensor'). If not specified, returns all devices."
            ),
        ] = None,
        area: Annotated[
            str | None,
            Field(description="Filter devices by area name (e.g., 'Living Room', 'Kitchen')"),
        ] = None,
        floor: Annotated[
            str | None,
            Field(description="Filter devices by floor name (e.g., 'Ground Floor', 'First Floor')"),
        ] = None,
    ) -> dict:
        """List all available Home Assistant devices with optional filtering.

        This tool allows you to discover and list devices across all Home Assistant
        entity domains. You can filter by domain (e.g., lights, switches, sensors),
        area (e.g., Living Room), or floor (e.g., Ground Floor).

        The response includes:
        - Devices grouped by domain
        - Statistics (total count, active count, state distribution)
        - Sample devices for each domain

        Examples:
        - List all devices: list_devices()
        - List all lights: list_devices(domain="light")
        - List devices in living room: list_devices(area="Living Room")
        - List devices on ground floor: list_devices(floor="Ground Floor")
        - List lights in kitchen: list_devices(domain="light", area="Kitchen")

        Args:
            domain: Optional domain filter (e.g., 'light', 'switch', 'sensor')
            area: Optional area filter (e.g., 'Living Room', 'Kitchen')
            floor: Optional floor filter (e.g., 'Ground Floor', 'First Floor')

        Returns:
            Dictionary containing:
                - success: Boolean indicating success
                - total_devices: Total number of devices matching filters
                - domains: Dictionary of domains with their devices and statistics
                - filters_applied: Dictionary showing which filters were used
        """
        client: HomeAssistantClient = get_client()

        try:
            return await _list_and_filter_devices(client, domain, area, floor)

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
            logger.error(f"Unexpected error in list_devices: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_and_filter_devices(
    client: HomeAssistantClient,
    domain: str | None = None,
    area: str | None = None,
    floor: str | None = None,
) -> dict:
    """List and filter devices based on provided criteria.

    Args:
        client: The Home Assistant client
        domain: Optional domain filter
        area: Optional area filter
        floor: Optional floor filter

    Returns:
        Dictionary containing filtered devices grouped by domain with statistics
    """
    logger.info(f"Listing devices with filters: domain={domain}, area={area}, floor={floor}")

    # Get all entity states
    all_states = await client.get_states()

    # Filter devices based on criteria
    filtered_devices = []
    for state in all_states:
        entity_id = state.get("entity_id", "")

        # Skip if no entity_id
        if not entity_id:
            continue

        # Extract domain from entity_id
        entity_domain = entity_id.split(".")[0] if "." in entity_id else ""

        # Apply domain filter
        if domain and entity_domain != domain:
            continue

        # Apply area filter
        if area:
            entity_area = state.get("attributes", {}).get("area_id") or state.get(
                "attributes", {}
            ).get("area_name")
            if not entity_area or entity_area.lower() != area.lower():
                continue

        # Apply floor filter
        if floor:
            entity_floor = state.get("attributes", {}).get("floor_id") or state.get(
                "attributes", {}
            ).get("floor_name")
            if not entity_floor or entity_floor.lower() != floor.lower():
                continue

        filtered_devices.append(state)

    logger.info(f"Found {len(filtered_devices)} devices matching filters")

    # Group devices by domain
    devices_by_domain = defaultdict(list)
    for device in filtered_devices:
        entity_id = device.get("entity_id", "")
        entity_domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
        devices_by_domain[entity_domain].append(device)

    # Build response with statistics and samples
    domains_data = {}
    for domain_name, devices in devices_by_domain.items():
        # Calculate statistics
        total_count = len(devices)

        # Count active devices (state != 'unavailable' and state != 'unknown')
        active_count = sum(1 for d in devices if d.get("state") not in ["unavailable", "unknown"])

        # Count state distribution
        state_counts: dict[str, int] = defaultdict(int)
        for device in devices:
            state = device.get("state", "unknown")
            state_counts[state] += 1

        # Get sample devices (up to 5 when filtered, 3 when showing all)
        max_samples = 5 if domain else 3
        sample_devices = []
        for device in devices[:max_samples]:
            sample_devices.append(
                {
                    "entity_id": device.get("entity_id"),
                    "name": device.get("attributes", {}).get(
                        "friendly_name", device.get("entity_id")
                    ),
                    "state": device.get("state"),
                    "area": device.get("attributes", {}).get("area_name")
                    or device.get("attributes", {}).get("area_id"),
                    "floor": device.get("attributes", {}).get("floor_name")
                    or device.get("attributes", {}).get("floor_id"),
                }
            )

        domains_data[domain_name] = {
            "total": total_count,
            "active": active_count,
            "states": dict(state_counts),
            "sample_devices": sample_devices,
        }

    # Build filters applied info
    filters_applied = {}
    if domain:
        filters_applied["domain"] = domain
    if area:
        filters_applied["area"] = area
    if floor:
        filters_applied["floor"] = floor

    logger.info(f"Returning {len(domains_data)} domains with {len(filtered_devices)} total devices")

    return {
        "success": True,
        "total_devices": len(filtered_devices),
        "domain_count": len(domains_data),
        "domains": domains_data,
        "filters_applied": filters_applied if filters_applied else None,
    }
