"""Explain prompts for entity explanation and diagnostics.

This module provides prompts that explain Home Assistant entities, including
their current state, capabilities, location, and available services. These
prompts help users understand what devices they have and how to control them.

The prompts fetch live data from Home Assistant to provide accurate, current
information about entities and their capabilities.

For more information on FastMCP prompts, see: https://gofastmcp.com/llms.txt

Example Usage:
    # Explain what an entity is and what it can do
    result = await explain_entity("light.living_room")
"""

import logging
from collections.abc import Callable

from fastmcp import FastMCP
from fastmcp.prompts import PromptMessage
from mcp.types import TextContent

from ..exceptions import ConnectionError, EntityNotFoundError
from ..hass.client import HomeAssistantClient

logger = logging.getLogger(__name__)

# Domain-specific capability descriptions
DOMAIN_CAPABILITIES = {
    "light": [
        "Can be turned on/off",
        "Supports brightness control (0-100%)",
        "May support color temperature adjustment",
        "May support RGB color control",
    ],
    "switch": [
        "Can be turned on/off",
        "Binary state (on or off)",
    ],
    "climate": [
        "Can control temperature",
        "Supports multiple HVAC modes (heat, cool, auto, off)",
        "May support fan speed control",
        "May support humidity control",
    ],
    "cover": [
        "Can be opened/closed",
        "May support position control (0-100%)",
        "May support tilt control",
    ],
    "lock": [
        "Can be locked/unlocked",
        "Binary state (locked or unlocked)",
    ],
    "media_player": [
        "Can play/pause/stop media",
        "Supports volume control",
        "May support source selection",
        "May support media browsing",
    ],
    "fan": [
        "Can be turned on/off",
        "Supports speed control",
        "May support oscillation",
        "May support direction control",
    ],
    "sensor": [
        "Provides read-only measurements",
        "Cannot be controlled directly",
        "Updates automatically based on device",
    ],
    "binary_sensor": [
        "Provides read-only on/off state",
        "Cannot be controlled directly",
        "Updates automatically based on device",
    ],
    "vacuum": [
        "Can start/stop/pause cleaning",
        "Can return to charging dock",
        "May support room-specific cleaning",
    ],
}

# Domain-specific service listings
DOMAIN_SERVICES = {
    "light": [
        "light.turn_on: Turn on with optional brightness, color",
        "light.turn_off: Turn off",
        "light.toggle: Switch state",
    ],
    "switch": [
        "switch.turn_on: Turn on",
        "switch.turn_off: Turn off",
        "switch.toggle: Switch state",
    ],
    "climate": [
        "climate.set_temperature: Set target temperature",
        "climate.set_hvac_mode: Change mode (heat, cool, auto, off)",
        "climate.set_fan_mode: Change fan speed",
        "climate.set_preset_mode: Apply preset configuration",
    ],
    "cover": [
        "cover.open_cover: Fully open",
        "cover.close_cover: Fully close",
        "cover.stop_cover: Stop movement",
        "cover.set_cover_position: Set position (0-100)",
    ],
    "lock": [
        "lock.lock: Lock the door",
        "lock.unlock: Unlock the door",
    ],
    "media_player": [
        "media_player.media_play: Start playback",
        "media_player.media_pause: Pause playback",
        "media_player.media_stop: Stop playback",
        "media_player.volume_set: Set volume level",
        "media_player.select_source: Change input source",
    ],
    "fan": [
        "fan.turn_on: Turn on",
        "fan.turn_off: Turn off",
        "fan.set_percentage: Set speed percentage (0-100)",
        "fan.oscillate: Enable/disable oscillation",
    ],
    "vacuum": [
        "vacuum.start: Start cleaning",
        "vacuum.pause: Pause cleaning",
        "vacuum.stop: Stop cleaning",
        "vacuum.return_to_base: Return to charging dock",
    ],
}


def register_explain_prompts(mcp: FastMCP, get_client: Callable[[], HomeAssistantClient]) -> None:
    """Register explain prompts for entity explanation and diagnostics.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.prompt(tags={"diagnostics"})
    async def explain_entity(entity_id: str) -> list[PromptMessage]:
        """Explain what an entity is, where it is, and what it can do.

        This prompt provides comprehensive information about a Home Assistant entity,
        including its current state, location, capabilities, and available services.

        Args:
            entity_id: The entity to explain (e.g., light.living_room)

        Returns:
            List of prompt messages explaining the entity
        """
        client = get_client()
        messages = []

        # Validate entity_id is not empty
        if not entity_id or not entity_id.strip():
            messages.append(
                PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text",
                        text="Invalid entity_id: entity_id cannot be empty. "
                        "Please provide a valid entity ID (e.g., light.living_room).",
                    ),
                )
            )
            return messages

        # Validate entity_id format (should contain a dot)
        if "." not in entity_id:
            messages.append(
                PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text",
                        text=f"Invalid entity_id format: '{entity_id}'. "
                        f"Entity IDs should be in the format 'domain.name' (e.g., light.living_room).",
                    ),
                )
            )
            return messages

        # Fetch entity state and attributes
        try:
            state = await client.get_state(entity_id)
        except EntityNotFoundError:
            messages.append(
                PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text",
                        text=f"Entity '{entity_id}' not found. "
                        f"Use the list_devices tool to find available entities.",
                    ),
                )
            )
            return messages
        except ConnectionError:
            messages.append(
                PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text",
                        text="I cannot connect to Home Assistant right now. "
                        "Please check that Home Assistant is running and accessible.",
                    ),
                )
            )
            return messages

        # Extract domain from entity_id
        domain = entity_id.split(".")[0] if "." in entity_id else "unknown"

        # Get attributes
        attributes = state.get("attributes", {})
        friendly_name = attributes.get("friendly_name", entity_id)
        area_name = attributes.get("area_id") or attributes.get("area")
        device_class = attributes.get("device_class", "")

        # Build explanation
        explanation = f"**{friendly_name}** ({entity_id}) is a {domain} entity"

        # Add location if available
        if area_name:
            explanation += f" located in the {area_name}"
        explanation += ".\n\n"

        # Add device class if available
        if device_class:
            explanation += f"**Device Class:** {device_class}\n\n"

        # Current state section
        current_state = state.get("state", "unknown")
        explanation += f"**Current State:** {current_state}\n"

        # Add relevant attributes based on domain
        if domain == "light" and current_state == "on":
            if "brightness" in attributes:
                brightness_pct = int((attributes["brightness"] / 255) * 100)
                explanation += f"- Brightness: {brightness_pct}%\n"
            if "color_temp" in attributes:
                explanation += f"- Color temperature: {attributes['color_temp']} mireds\n"
            if "rgb_color" in attributes:
                rgb = attributes["rgb_color"]
                explanation += f"- RGB color: ({rgb[0]}, {rgb[1]}, {rgb[2]})\n"
        elif domain == "climate":
            if "current_temperature" in attributes:
                explanation += f"- Current temperature: {attributes['current_temperature']}°\n"
            if "temperature" in attributes:
                explanation += f"- Target temperature: {attributes['temperature']}°\n"
            if "hvac_mode" in attributes:
                explanation += f"- HVAC mode: {attributes['hvac_mode']}\n"
            if "fan_mode" in attributes:
                explanation += f"- Fan mode: {attributes['fan_mode']}\n"
        elif domain == "cover":
            if "current_position" in attributes:
                explanation += f"- Position: {attributes['current_position']}%\n"
            if "current_tilt_position" in attributes:
                explanation += f"- Tilt: {attributes['current_tilt_position']}%\n"
        elif domain == "media_player":
            if "volume_level" in attributes:
                volume_pct = int(attributes["volume_level"] * 100)
                explanation += f"- Volume: {volume_pct}%\n"
            if "source" in attributes:
                explanation += f"- Source: {attributes['source']}\n"
            if "media_title" in attributes:
                explanation += f"- Playing: {attributes['media_title']}\n"
        elif domain == "sensor":
            if "unit_of_measurement" in attributes:
                explanation += f"- Unit: {attributes['unit_of_measurement']}\n"
        elif domain == "fan":
            if "percentage" in attributes:
                explanation += f"- Speed: {attributes['percentage']}%\n"
            if "oscillating" in attributes:
                explanation += f"- Oscillating: {attributes['oscillating']}\n"

        # Add last changed time
        if "last_changed" in state:
            explanation += f"- Last changed: {state['last_changed']}\n"

        # Capabilities section
        explanation += "\n**Capabilities:**\n"
        capabilities = DOMAIN_CAPABILITIES.get(domain, [f"Standard {domain} capabilities"])
        for capability in capabilities:
            explanation += f"- {capability}\n"

        # Available services section
        explanation += "\n**Available Services:**\n"
        services = DOMAIN_SERVICES.get(domain, [f"{domain}.turn_on", f"{domain}.turn_off"])
        for service in services:
            explanation += f"- {service}\n"

        # Add helpful context
        explanation += "\n**Usage Tips:**\n"
        if domain in ["sensor", "binary_sensor"]:
            explanation += "- This is a read-only entity that cannot be controlled\n"
            explanation += "- Use it to monitor conditions and trigger automations\n"
        else:
            explanation += (
                f"- Use the control_entity prompt for guidance on controlling this {domain}\n"
            )
            explanation += "- Always verify current state before making changes\n"

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=explanation))
        )

        return messages
