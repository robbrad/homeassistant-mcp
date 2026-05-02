"""Energy optimization prompt for analyzing and reducing energy usage.

This module provides a prompt that analyzes device energy usage and suggests
ways to reduce consumption. It identifies high-power devices, categorizes them
by type, and provides actionable recommendations for energy savings through
scheduling, automation, and device management.

The prompt was migrated to FastMCP 2.0+ patterns while preserving its original
functionality.

For more information on FastMCP prompts, see: https://gofastmcp.com/llms.txt

Example Usage:
    # Analyze energy usage for entire home
    result = await optimize_energy()

    # Analyze energy usage for specific area
    result = await optimize_energy(area="Living Room")
"""

from typing import Any

from fastmcp.prompts import PromptMessage
from mcp.types import TextContent


def register_energy_prompt(mcp: Any, get_client: Any) -> None:
    """Register the energy optimization prompt."""

    @mcp.prompt(tags={"status"})
    async def optimize_energy(area: str = "") -> list[PromptMessage]:
        """
        Analyze energy usage and suggest optimizations.

        This prompt provides analysis of device energy usage and suggests
        ways to reduce consumption.

        Args:
            area: Optional area/room to focus on

        Returns:
            A conversation flow guiding through energy optimization
        """
        client = get_client()

        messages = []

        # Initial message
        intro_text = f"""I'll help you optimize energy usage{f' in {area}' if area else ''}.

Let me analyze your devices and identify optimization opportunities..."""

        messages.append(
            PromptMessage(role="user", content=TextContent(type="text", text=intro_text))
        )

        # Step 1: Identify high-power devices
        try:
            states = await client.get_states(area=area if area else None, limit=200)

            # Categorize devices by type
            lights = [s for s in states if s["entity_id"].startswith("light.")]
            climate = [s for s in states if s["entity_id"].startswith("climate.")]
            switches = [s for s in states if s["entity_id"].startswith("switch.")]
            media_players = [s for s in states if s["entity_id"].startswith("media_player.")]

            analysis_text = f"""
**Step 1: Device Analysis**

Found {len(states)} devices{f' in {area}' if area else ''}:
- {len(lights)} lights
- {len(climate)} climate devices
- {len(switches)} switches
- {len(media_players)} media players

**High-Power Device Categories:**

**Climate Devices ({len(climate)}):**"""

            for device in climate[:5]:
                state_info = device["state"]
                temp = device.get("attributes", {}).get("temperature", "N/A")
                mode = device.get("attributes", {}).get("hvac_mode", "N/A")
                analysis_text += (
                    f"\n- {device['entity_id']}: {state_info} (Mode: {mode}, Temp: {temp})"
                )

            if len(climate) > 5:
                analysis_text += f"\n  ... and {len(climate) - 5} more"

            # Count lights that are on
            lights_on = [light for light in lights if light["state"] == "on"]
            analysis_text += f"""

**Lights ({len(lights_on)} currently on):**"""

            for light in lights_on[:10]:
                brightness = light.get("attributes", {}).get("brightness", "N/A")
                analysis_text += f"\n- {light['entity_id']}: on (Brightness: {brightness})"

            if len(lights_on) > 10:
                analysis_text += f"\n  ... and {len(lights_on) - 10} more"

            # Count switches that are on
            switches_on = [s for s in switches if s["state"] == "on"]
            if switches_on:
                analysis_text += f"""

**Active Switches ({len(switches_on)}):**"""
                for switch in switches_on[:5]:
                    analysis_text += f"\n- {switch['entity_id']}: on"
                if len(switches_on) > 5:
                    analysis_text += f"\n  ... and {len(switches_on) - 5} more"

            messages.append(
                PromptMessage(
                    role="assistant", content=TextContent(type="text", text=analysis_text)
                )
            )

        except Exception as e:
            messages.append(
                PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text", text=f"Could not retrieve device states: {str(e)}"
                    ),
                )
            )

        # Step 2: Optimization suggestions
        suggestions_text = """
**Step 2: Energy Optimization Opportunities**

Based on the device analysis, here are optimization suggestions:

**Climate Control:**
- Consider reducing heating/cooling setpoints by 1-2°F when away
- Use "eco" or "away" modes when not home
- Ensure proper insulation to reduce HVAC runtime
- Schedule temperature adjustments based on occupancy

**Lighting:**
- Replace high-brightness lights with lower settings where possible
- Use motion sensors to auto-off lights in unoccupied rooms
- Consider LED bulbs if not already using them
- Create "away" scenes that turn off unnecessary lights

**Standby Power:**
- Identify devices that can be turned off when not in use
- Use smart plugs to eliminate phantom power draw
- Create automations to turn off devices at night

**Automation Ideas:**
- "Good Night" automation: Turn off all non-essential devices
- "Away Mode": Reduce climate settings and turn off lights
- "Sunrise/Sunset" automation: Adjust lighting based on natural light
- Motion-based lighting: Only turn on lights when needed"""

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=suggestions_text))
        )

        # Step 3: Implementation
        implementation_text = """
**Step 3: Implementation Plan**

I can help you implement these optimizations:

1. **Create energy-saving scenes:**
   - "Away Mode" scene with reduced settings
   - "Sleep Mode" scene for nighttime
   - "Eco Mode" scene for maximum savings

2. **Set up automations:**
   - Auto-adjust climate based on time of day
   - Auto-off lights after no motion detected
   - Reduce power usage during peak hours

3. **Monitor usage:**
   - Track energy consumption over time
   - Identify devices with highest usage
   - Measure savings from optimizations

Which optimization would you like to implement first?"""

        messages.append(
            PromptMessage(
                role="assistant", content=TextContent(type="text", text=implementation_text)
            )
        )

        return messages
