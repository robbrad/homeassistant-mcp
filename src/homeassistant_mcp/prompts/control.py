"""Control prompts for entity and area control guidance.

This module provides prompts that guide safe control of Home Assistant entities
and areas. It implements safety-first design with confirmation requirements for
sensitive domains, quiet hours warnings, and bulk action thresholds.

The prompts use FastMCP 2.0+ patterns with type-safe parameter validation and
structured guidance that encodes best practices directly in the prompt text.

For more information on FastMCP prompts, see: https://gofastmcp.com/llms.txt

Example Usage:
    # Control a single entity
    result = await control_entity("light.living_room", action="turn_on")

    # Control all entities in an area
    result = await control_area("Living Room", goal="turn off all lights")
"""

import logging
from collections.abc import Callable
from datetime import datetime

from fastmcp import FastMCP
from fastmcp.prompts import PromptMessage
from mcp.types import TextContent

from ..exceptions import ConnectionError, EntityNotFoundError
from ..hass.client import HomeAssistantClient
from .models import SENSITIVE_DOMAINS, SafetyConfig
from .safety_templates import (
    BULK_ACTION_TEMPLATE,
    CONFIRMATION_TEMPLATE,
    QUIET_HOURS_TEMPLATE,
    READ_STATE_FIRST_TEMPLATE,
)

logger = logging.getLogger(__name__)

# Noisy domains that should trigger quiet hours warnings
NOISY_DOMAINS = {
    "media_player",
    "siren",
    "tts",
    "notify",  # Some notifications can be audible
}

# Domain-specific action guidance
DOMAIN_ACTIONS = {
    "light": [
        "turn_on: Turn the light on (with optional brightness, color)",
        "turn_off: Turn the light off",
        "toggle: Switch between on and off",
    ],
    "switch": [
        "turn_on: Turn the switch on",
        "turn_off: Turn the switch off",
        "toggle: Switch between on and off",
    ],
    "climate": [
        "set_temperature: Set target temperature",
        "set_hvac_mode: Change mode (heat, cool, auto, off)",
        "set_fan_mode: Change fan speed",
    ],
    "cover": [
        "open_cover: Fully open the cover",
        "close_cover: Fully close the cover",
        "stop_cover: Stop movement",
        "set_cover_position: Set position (0-100)",
    ],
    "lock": [
        "lock: Lock the door",
        "unlock: Unlock the door (requires confirmation)",
    ],
    "media_player": [
        "media_play: Start playback",
        "media_pause: Pause playback",
        "media_stop: Stop playback",
        "volume_set: Set volume level",
    ],
    "fan": [
        "turn_on: Turn the fan on",
        "turn_off: Turn the fan off",
        "set_percentage: Set speed percentage (0-100)",
    ],
    "vacuum": [
        "start: Start cleaning",
        "pause: Pause cleaning",
        "stop: Stop cleaning",
        "return_to_base: Return to charging dock",
    ],
}


def register_control_prompts(mcp: FastMCP, get_client: Callable[[], HomeAssistantClient]) -> None:
    """Register control prompts for entity and area control.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.prompt(tags={"control"})
    async def control_entity(entity_id: str, action: str = "") -> list[PromptMessage]:
        """Guide safe control of a Home Assistant entity.

        This prompt provides structured guidance for controlling a specific entity,
        including current state verification, available actions, and safety checks
        for sensitive domains.

        Args:
            entity_id: The entity to control (e.g., light.living_room)
            action: Optional specific action to perform

        Returns:
            List of prompt messages for controlling the entity safely
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

        # Fetch entity state
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
        domain = entity_id.split(".")[0] if "." in entity_id else ""

        # Build current state description
        current_state = state.get("state", "unknown")
        attributes = state.get("attributes", {})

        # Format attributes for display
        # We show domain-specific attributes that are most relevant to users
        # This helps them understand the current state before making changes
        attr_lines = []
        if domain == "light" and current_state == "on":
            # For lights, show brightness and color information when on
            if "brightness" in attributes:
                brightness_pct = int((attributes["brightness"] / 255) * 100)
                attr_lines.append(f"- Brightness: {brightness_pct}%")
            if "color_temp" in attributes:
                attr_lines.append(f"- Color temperature: {attributes['color_temp']} mireds")
        elif domain == "climate":
            # For climate devices, show temperature information
            if "temperature" in attributes:
                attr_lines.append(f"- Current temperature: {attributes['temperature']}°")
            if "target_temp_high" in attributes:
                attr_lines.append(f"- Target high: {attributes['target_temp_high']}°")
            if "target_temp_low" in attributes:
                attr_lines.append(f"- Target low: {attributes['target_temp_low']}°")
        elif domain == "cover":
            # For covers, show position information
            if "current_position" in attributes:
                attr_lines.append(f"- Position: {attributes['current_position']}%")

        attributes_text = "\n".join(attr_lines) if attr_lines else "No additional attributes"

        # Build read-state-first guidance
        # This is a core safety principle: always show current state before suggesting actions
        # It prevents redundant actions and gives users context for decision-making
        state_info = READ_STATE_FIRST_TEMPLATE.format(
            entity_id=entity_id, state=current_state, attributes=attributes_text
        )

        # Check if entity is in sensitive domain
        # Sensitive domains (locks, alarms, garage doors, cameras) require extra caution
        # and explicit user confirmation before any control actions
        is_sensitive = domain in SENSITIVE_DOMAINS

        # Build main guidance message
        intro = f"I'll help you control {entity_id} safely.\n\n"
        intro += state_info

        # Add available actions for this domain
        actions_text = "\n\n**Available Actions:**\n"
        domain_actions = DOMAIN_ACTIONS.get(domain, [])
        if domain_actions:
            actions_text += "\n".join(f"- {action}" for action in domain_actions)
        else:
            # Generic actions for unknown domains
            actions_text += "- turn_on: Turn the entity on\n"
            actions_text += "- turn_off: Turn the entity off\n"
            actions_text += "- toggle: Switch between on and off"

        intro += actions_text

        # Add action-specific guidance if action parameter provided
        if action:
            intro += f"\n\n**Requested Action:** {action}"

        # Add safety warning for sensitive domains
        # For sensitive domains, we require explicit confirmation before any actions
        # This prevents accidental or unauthorized control of security-critical devices
        if is_sensitive:
            safety_warning = CONFIRMATION_TEMPLATE.format(
                domain=domain, current_state=current_state
            )
            intro += f"\n\n{safety_warning}"
        else:
            intro += "\n\nBefore making changes, I've verified the current state. What would you like to do?"

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=intro))
        )

        return messages

    @mcp.prompt(tags={"control"})
    async def control_area(area_id: str, goal: str = "") -> list[PromptMessage]:
        """Guide control of multiple entities in an area.

        This prompt provides structured guidance for controlling all entities in a specific
        area, including listing affected entities, bulk action confirmation, and safety
        checks for sensitive domains and quiet hours.

        Args:
            area_id: The area to control (e.g., "Living Room", "Bedroom")
            goal: Optional desired outcome (e.g., "turn off all lights")

        Returns:
            List of prompt messages for controlling the area safely
        """
        client = get_client()
        messages = []
        safety_config = SafetyConfig()

        # Fetch all entities in the area
        try:
            entities = await client.get_states(area=area_id, limit=500)
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

        # Check if area has any entities
        if not entities:
            messages.append(
                PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text",
                        text=f"No entities found in area '{area_id}'. "
                        f"Please check the area name or use the list_devices tool to find available areas.",
                    ),
                )
            )
            return messages

        # Build intro message
        intro = f"I'll help you control devices in the {area_id}.\n\n"

        # Add goal if provided
        if goal:
            intro += f"**Goal:** {goal}\n\n"

        # List all entities with their current states
        intro += "**Entities in this area:**\n"
        entity_list = []
        sensitive_entities = []
        noisy_entities = []

        for entity in entities:
            entity_id = entity.get("entity_id", "")
            state = entity.get("state", "unknown")
            friendly_name = entity.get("attributes", {}).get("friendly_name", entity_id)
            domain = entity_id.split(".")[0] if "." in entity_id else ""

            # Format entity line
            entity_line = f"- {friendly_name} ({entity_id}): {state}"
            entity_list.append(entity_line)

            # Track sensitive domains
            # We need to warn users if any sensitive devices will be affected
            # This ensures they're aware of security implications
            if domain in SENSITIVE_DOMAINS:
                sensitive_entities.append(friendly_name)

            # Track noisy domains for quiet hours check
            # Noisy devices (media players, sirens, etc.) should trigger warnings
            # during quiet hours to avoid disturbing sleep
            if domain in NOISY_DOMAINS:
                noisy_entities.append(friendly_name)

        intro += "\n".join(entity_list)
        intro += f"\n\n**Total entities:** {len(entities)}"

        # Add bulk action warning if threshold met
        # Bulk actions (affecting 3+ entities by default) require confirmation
        # This prevents accidental mass changes and gives users a chance to review
        if len(entities) >= safety_config.min_bulk_threshold:
            bulk_warning = BULK_ACTION_TEMPLATE.format(
                count=len(entities), entity_list="\n".join(entity_list)
            )
            intro += f"\n\n{bulk_warning}"

        # Add sensitive domain warnings
        # If any sensitive devices are in the area, we must warn the user
        # and require explicit confirmation before proceeding
        if sensitive_entities:
            intro += "\n\n⚠️ **SENSITIVE DEVICES DETECTED:**\n"
            intro += "The following devices require extra caution:\n"
            for entity_name in sensitive_entities:
                intro += f"- {entity_name}\n"
            intro += "\nPlease verify you want to control these devices and confirm your action."

        # Check for quiet hours if noisy devices present
        # Quiet hours (10 PM - 7 AM by default) are when we should avoid noisy actions
        # This prevents disturbing sleep or quiet time unless explicitly requested
        if noisy_entities:
            current_time = datetime.now()
            current_hour = current_time.hour
            current_minute = current_time.minute

            # Parse quiet hours from config
            quiet_start_hour = int(safety_config.quiet_hours_start.split(":")[0])
            quiet_end_hour = int(safety_config.quiet_hours_end.split(":")[0])

            # Check if current time is in quiet hours
            # Handle overnight quiet hours (e.g., 22:00 to 07:00)
            # This requires special logic since the period crosses midnight
            is_quiet_hours = False
            if quiet_start_hour > quiet_end_hour:
                # Overnight period (e.g., 22:00 to 07:00)
                is_quiet_hours = current_hour >= quiet_start_hour or current_hour < quiet_end_hour
            else:
                # Same day period (e.g., 13:00 to 15:00)
                is_quiet_hours = quiet_start_hour <= current_hour < quiet_end_hour

            if is_quiet_hours:
                current_time_str = f"{current_hour:02d}:{current_minute:02d}"
                quiet_warning = QUIET_HOURS_TEMPLATE.format(current_time=current_time_str)
                intro += f"\n\n{quiet_warning}"
                intro += "\n**Noisy devices in this area:**\n"
                for entity_name in noisy_entities:
                    intro += f"- {entity_name}\n"

        # Add final guidance
        intro += "\n\n**Before proceeding:**\n"
        intro += "1. Review the list of affected entities above\n"
        intro += "2. Verify this matches your intent\n"
        intro += "3. Confirm you want to proceed with this action\n"

        if not goal:
            intro += "\nWhat would you like to do with these devices?"

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=intro))
        )

        return messages
