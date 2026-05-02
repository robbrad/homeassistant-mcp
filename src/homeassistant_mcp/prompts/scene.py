"""Scene creation prompt for guided scene setup.

This module provides a prompt that guides users through creating Home Assistant
scenes. It helps select entities, define their desired states, and provides
safety guidance for scene creation and activation.

The prompt was migrated to FastMCP 2.0+ patterns while preserving its original
functionality and adding safety warnings for scene activation.

For more information on FastMCP prompts, see: https://gofastmcp.com/llms.txt

Example Usage:
    # Create a scene for entire home
    result = await create_scene("Movie Night")

    # Create a scene for specific area
    result = await create_scene("Bedtime", area="Bedroom")
"""

from typing import Any

from fastmcp.prompts import PromptMessage
from mcp.types import TextContent


def register_scene_prompt(mcp: Any, get_client: Any) -> None:
    """Register the scene creation prompt."""

    @mcp.prompt(tags={"control"})
    async def create_scene(name: str, area: str = "") -> list[PromptMessage]:
        """
        Guide through creating a Home Assistant scene.

        This prompt provides a step-by-step conversation flow for creating
        a new scene with entity states.

        Args:
            name: Name for the new scene
            area: Optional area/room to focus on

        Returns:
            A conversation flow guiding through scene creation
        """
        client = get_client()

        messages = []

        # Initial message
        intro_text = f"""I'll help you create a Home Assistant scene called "{name}".
{f'Focusing on area: {area}' if area else ''}

A scene captures the desired state of multiple entities (lights, switches, etc.)
that can be activated with a single command.

**Step 1: Select Entities**
Which entities should be included in this scene? You can include:
- Lights (brightness, color, on/off state)
- Switches (on/off state)
- Climate devices (temperature, mode)
- Covers (position, tilt)
- Media players (volume, source)

Let me show you available entities..."""

        messages.append(
            PromptMessage(role="user", content=TextContent(type="text", text=intro_text))
        )

        # Get available entities
        try:
            # Filter by area if specified
            states = await client.get_states(area=area if area else None, limit=100)

            # Group entities by domain
            entities_by_domain: dict[str, list[dict[str, Any]]] = {}
            for state in states:
                domain = state["entity_id"].split(".")[0]
                if domain not in entities_by_domain:
                    entities_by_domain[domain] = []
                entities_by_domain[domain].append(state)

            # Build entity list
            entity_text_parts = ["**Available Entities:**\n"]
            for domain, entities in sorted(entities_by_domain.items()):
                entity_text_parts.append(f"\n**{domain.title()}s:**")
                for entity in entities[:10]:  # Limit to 10 per domain
                    entity_text_parts.append(f"- {entity['entity_id']}: {entity['state']}")
                if len(entities) > 10:
                    entity_text_parts.append(f"  ... and {len(entities) - 10} more")
            messages.append(
                PromptMessage(
                    role="assistant",
                    content=TextContent(type="text", text="\n".join(entity_text_parts)),
                )
            )
        except Exception:
            # If we can't get entities, continue without them
            pass

        # Step 2: Define states
        states_text = """
**Step 2: Define Entity States**
For each entity you want to include, specify its desired state:

**For Lights:**
- State: on/off
- Brightness: 0-255
- Color: RGB values or color name
- Color temperature: Kelvin value

**For Switches:**
- State: on/off

**For Climate:**
- Temperature: Desired temperature
- HVAC mode: heat/cool/auto/off

**For Covers:**
- Position: 0-100 (0=closed, 100=open)

Please tell me which entities to include and their desired states."""

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=states_text))
        )

        # Step 3: Review
        review_text = """
**Step 3: Review and Create**
Once you've specified all entities and their states, I'll:
1. Format the scene configuration
2. Create the scene using the Home Assistant API
3. Test activating the scene to verify it works

⚠️ **Safety Note:**
- Review all entity states before creating the scene
- Test the scene in a safe environment first
- Ensure no sensitive devices (locks, alarms) are included unless intentional
- Consider the impact of activating this scene at different times

Let me know when you're ready to review and create the scene!"""

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=review_text))
        )

        return messages
