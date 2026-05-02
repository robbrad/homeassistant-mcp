"""Status prompts for home monitoring and status reporting.

This module provides prompts that generate comprehensive status reports about
the current state of a Home Assistant installation. It aggregates data across
all entities to provide insights into device states, issues, security status,
and climate comfort levels.

The prompts analyze entity states to identify potential issues like unavailable
devices, low batteries, and security concerns, presenting them in a structured,
easy-to-understand format.

For more information on FastMCP prompts, see: https://gofastmcp.com/llms.txt

Example Usage:
    # Get a comprehensive home status summary
    result = await home_status_brief()
"""

import logging
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime

from fastmcp import FastMCP
from fastmcp.prompts import PromptMessage
from mcp.types import TextContent

from ..exceptions import ConnectionError
from ..hass.client import HomeAssistantClient

logger = logging.getLogger(__name__)

# Battery level threshold for low battery warnings
LOW_BATTERY_THRESHOLD = 20

# Domains to check for security status
SECURITY_DOMAINS = {"lock", "alarm_control_panel", "binary_sensor"}


def register_status_prompts(mcp: FastMCP, get_client: Callable[[], HomeAssistantClient]) -> None:
    """Register status prompts for home monitoring.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.prompt(tags={"status"})
    async def home_status_brief() -> list[PromptMessage]:
        """Provide a comprehensive summary of current home status.

        This prompt fetches all entity states and provides a structured summary including:
        - Entity counts by domain and state
        - Issues detected (unavailable entities, low batteries)
        - Security status (locks, alarms)
        - Climate comfort levels
        - Active automations

        Returns:
            List of prompt messages containing the home status summary
        """
        client = get_client()
        messages = []

        # Fetch all entity states
        try:
            all_entities = await client.get_states(limit=500)
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

        # Get current time for the report
        current_time = datetime.now()
        time_str = current_time.strftime("%I:%M %p")

        # Initialize counters and tracking
        domain_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        security_status: dict[str, list[tuple[str, str]]] = defaultdict(list)
        climate_status: list[tuple[str, str, str]] = []
        unavailable_entities: list[str] = []
        low_battery_entities: list[tuple[str, int]] = []

        # Process all entities
        for entity in all_entities:
            entity_id = entity.get("entity_id", "")
            state = entity.get("state", "unknown")
            attributes = entity.get("attributes", {})
            friendly_name = attributes.get("friendly_name", entity_id)

            # Extract domain
            domain = entity_id.split(".")[0] if "." in entity_id else "unknown"

            # Count by domain and state
            domain_counts[domain]["total"] += 1
            domain_counts[domain][state] += 1

            # Check for unavailable entities
            if state == "unavailable":
                unavailable_entities.append(friendly_name)

            # Check for low battery
            battery_level = attributes.get("battery_level")
            if battery_level is not None:
                try:
                    battery_int = int(float(battery_level))
                    if battery_int <= LOW_BATTERY_THRESHOLD:
                        low_battery_entities.append((friendly_name, battery_int))
                except (ValueError, TypeError):
                    pass

            # Track security devices
            if domain == "lock":
                security_status["locks"].append((friendly_name, state))
            elif domain == "alarm_control_panel":
                security_status["alarms"].append((friendly_name, state))
            elif domain == "binary_sensor" and attributes.get("device_class") in [
                "door",
                "window",
                "opening",
            ]:
                if state == "on":  # Open
                    security_status["openings"].append((friendly_name, "open"))

            # Track climate devices
            if domain == "climate":
                current_temp = attributes.get("current_temperature")
                target_temp = attributes.get("temperature")
                if current_temp is not None and target_temp is not None:
                    climate_status.append((friendly_name, f"{current_temp}°", f"{target_temp}°"))

        # Build the status report
        report = f"**Home Status Summary** (as of {time_str})\n\n"

        # Device counts section
        report += "**Devices:**\n"
        for domain in sorted(domain_counts.keys()):
            counts = domain_counts[domain]
            total = counts["total"]

            # Format state breakdown
            state_parts = []
            for state_name in ["on", "off", "open", "closed", "home", "away"]:
                if state_name in counts and counts[state_name] > 0:
                    state_parts.append(f"{counts[state_name]} {state_name}")

            if state_parts:
                report += f"- {domain.capitalize()}: {total} total ({', '.join(state_parts)})\n"
            else:
                report += f"- {domain.capitalize()}: {total} total\n"

        # Issues section
        if unavailable_entities or low_battery_entities:
            report += "\n**Issues Detected:**\n"

            if unavailable_entities:
                report += f"⚠️ **Unavailable Entities ({len(unavailable_entities)}):**\n"
                for entity_name in unavailable_entities[:5]:  # Limit to first 5
                    report += f"  - {entity_name}\n"
                if len(unavailable_entities) > 5:
                    report += f"  - ... and {len(unavailable_entities) - 5} more\n"

            if low_battery_entities:
                report += f"⚠️ **Low Battery ({len(low_battery_entities)}):**\n"
                for entity_name, battery_level in sorted(low_battery_entities, key=lambda x: x[1])[
                    :5
                ]:
                    report += f"  - {entity_name}: {battery_level}%\n"
                if len(low_battery_entities) > 5:
                    report += f"  - ... and {len(low_battery_entities) - 5} more\n"
        else:
            report += "\n**Issues Detected:** ✓ None\n"

        # Active automations count
        automation_count = domain_counts.get("automation", {}).get("total", 0)
        automation_on = domain_counts.get("automation", {}).get("on", 0)
        if automation_count > 0:
            report += (
                f"\n**Active Automations:** {automation_on} enabled (of {automation_count} total)\n"
            )

        # Security status section
        report += "\n**Security Status:**"

        all_secure = True

        # Check locks
        if security_status["locks"]:
            locked_count = sum(1 for _, state in security_status["locks"] if state == "locked")
            total_locks = len(security_status["locks"])

            if locked_count == total_locks:
                report += f"\n- Locks: ✓ All locked ({total_locks})"
            else:
                all_secure = False
                report += f"\n- Locks: ⚠️ {locked_count}/{total_locks} locked"
                for name, state in security_status["locks"]:
                    if state != "locked":
                        report += f"\n  - {name}: {state}"
        else:
            report += "\n- Locks: No lock entities found"

        # Check alarms
        if security_status["alarms"]:
            for name, state in security_status["alarms"]:
                if state in ["armed_home", "armed_away", "armed_night"]:
                    report += f"\n- Alarm: ✓ {name} ({state})"
                elif state == "disarmed":
                    all_secure = False
                    report += f"\n- Alarm: ⚠️ {name} (disarmed)"
                else:
                    report += f"\n- Alarm: {name} ({state})"

        # Check open doors/windows
        if security_status["openings"]:
            all_secure = False
            report += f"\n- Open Doors/Windows: ⚠️ {len(security_status['openings'])} detected"
            for name, _ in security_status["openings"][:3]:
                report += f"\n  - {name}"
            if len(security_status["openings"]) > 3:
                report += f"\n  - ... and {len(security_status['openings']) - 3} more"

        if all_secure and security_status["locks"]:
            report += "\n\n✓ **All Secure**"

        # Climate status section
        if climate_status:
            report += "\n\n**Climate:**"
            all_comfortable = True

            for name, current, target in climate_status:
                # Parse temperatures to check comfort
                try:
                    current_val = float(current.rstrip("°"))
                    target_val = float(target.rstrip("°"))
                    diff = abs(current_val - target_val)

                    if diff <= 2:
                        report += f"\n- {name}: {current} (target {target}) ✓"
                    else:
                        all_comfortable = False
                        report += f"\n- {name}: {current} (target {target})"
                except (ValueError, AttributeError):
                    report += f"\n- {name}: {current} (target {target})"

            if all_comfortable:
                report += "\n\n✓ **Climate Comfortable**"

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=report))
        )

        return messages
