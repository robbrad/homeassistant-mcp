"""Automation creation and management prompts for guided automation setup.

This module provides prompts for creating, diagnosing, and suggesting Home Assistant
automations. It guides users through the automation creation process with step-by-step
instructions and provides diagnostic information for troubleshooting existing automations.

The prompts analyze user intent to suggest appropriate triggers, conditions, and actions
based on available entities and common automation patterns.

For more information on FastMCP prompts, see: https://gofastmcp.com/llms.txt

Example Usage:
    # Guide through creating a new automation
    result = await create_automation("Morning Lights", "Turn on lights at sunrise")

    # Diagnose why an automation isn't working
    result = await diagnose_automation("automation.morning_lights")

    # Get automation suggestions based on intent
    result = await suggest_automation("Turn on porch light at sunset")
"""

import logging
from collections.abc import Callable

from fastmcp import FastMCP
from fastmcp.prompts import PromptMessage
from mcp.types import TextContent

from ..exceptions import ConnectionError, EntityNotFoundError
from ..hass.client import HomeAssistantClient

logger = logging.getLogger(__name__)


def register_automation_prompts(
    mcp: FastMCP, get_client: Callable[[], HomeAssistantClient]
) -> None:
    """Register automation prompts for creation, diagnosis, and suggestions.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.prompt(tags={"automation"})
    async def create_automation(name: str, description: str = "") -> list[PromptMessage]:
        """
        Guide through creating a Home Assistant automation.

        This prompt provides a step-by-step conversation flow for creating
        a new automation, including trigger definition, conditions, and actions.

        Args:
            name: Name for the new automation
            description: Optional description of what the automation should do

        Returns:
            List of prompt messages guiding through automation creation
        """
        client = get_client()

        # Build the prompt messages
        messages = []

        # Initial message
        intro_text = f"""I'll help you create a Home Assistant automation called "{name}".
{f'Goal: {description}' if description else ''}

Let's build this automation step by step:

**Step 1: Define the Trigger**
What should trigger this automation? Common trigger types:
- **Time**: Trigger at a specific time or interval
- **State**: Trigger when an entity changes state
- **Event**: Trigger on a Home Assistant event
- **Numeric State**: Trigger when a sensor value crosses a threshold
- **Zone**: Trigger when a device enters/leaves a zone
- **Webhook**: Trigger from an external webhook call

Please describe what should trigger this automation."""

        messages.append(
            PromptMessage(role="user", content=TextContent(type="text", text=intro_text))
        )

        # Get available entities for context
        try:
            states = await client.get_states(limit=50)
            entity_summary = "\n".join(
                [f"- {state['entity_id']}: {state['state']}" for state in states[:20]]
            )

            context_text = f"""
**Available Entities (sample):**
{entity_summary}
{'...' if len(states) > 20 else ''}

You can reference any of these entities in your automation."""

            messages.append(
                PromptMessage(role="assistant", content=TextContent(type="text", text=context_text))
            )
        except Exception as e:
            # If we can't get entities, continue without them
            logger.debug(f"Could not fetch entities for automation context: {e}")

        # Step 2: Conditions
        conditions_text = """
**Step 2: Define Conditions (Optional)**
Conditions determine if the automation should run after being triggered.
Common condition types:
- **State**: Check if an entity is in a specific state
- **Numeric State**: Check if a sensor value is above/below a threshold
- **Time**: Only run during specific times
- **Zone**: Check if a device is in a specific zone
- **Template**: Use a template for complex logic

Do you want to add any conditions? If not, the automation will run every time it's triggered."""

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=conditions_text))
        )

        # Step 3: Actions
        actions_text = """
**Step 3: Define Actions**
What should happen when this automation runs? Common action types:
- **Service Call**: Call a Home Assistant service (turn on lights, send notification, etc.)
- **Delay**: Wait for a specified time
- **Wait**: Wait for a condition to be true
- **Choose**: Conditional actions (if-then-else logic)
- **Repeat**: Repeat actions multiple times or until a condition
- **Scene**: Activate a scene

Please describe what actions this automation should perform."""

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=actions_text))
        )

        # Step 4: Review
        review_text = """
**Step 4: Review and Create**
Once you've defined the trigger, conditions (if any), and actions, I'll help you:
1. Format the automation configuration
2. Create the automation using the Home Assistant API
3. Test that it's working correctly

Let me know when you're ready to review and create the automation!"""

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=review_text))
        )

        return messages

    @mcp.prompt(tags={"automation"})
    async def diagnose_automation(automation_id: str) -> list[PromptMessage]:
        """Investigate why an automation did or didn't run.

        This prompt provides diagnostic information about a specific automation,
        including its configuration, current state, and common troubleshooting steps.

        Args:
            automation_id: The automation to diagnose (e.g., automation.morning_lights)

        Returns:
            List of prompt messages with diagnostic information
        """
        client = get_client()
        messages = []

        # Fetch automation state and configuration
        try:
            state = await client.get_state(automation_id)
        except EntityNotFoundError:
            messages.append(
                PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text",
                        text=f"Automation '{automation_id}' not found. "
                        f"Use the list_devices tool with domain='automation' to find available automations.",
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
        except Exception as e:
            # Catch any other exceptions
            logger.error(f"Error fetching automation state: {e}")
            messages.append(
                PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text",
                        text=f"An error occurred while fetching automation information: {str(e)}",
                    ),
                )
            )
            return messages

        # Extract automation details
        attributes = state.get("attributes", {})
        current_state = state.get("state", "unknown")
        friendly_name = attributes.get("friendly_name", automation_id)
        last_triggered = attributes.get("last_triggered", "Never")

        # Build diagnostic report
        diagnostic = f"**Diagnosing: {friendly_name}** ({automation_id})\n\n"

        # Status section
        diagnostic += "**Current Status:**\n"
        is_enabled = current_state == "on"
        status_icon = "✓" if is_enabled else "✗"
        diagnostic += f"- Enabled: {status_icon} {'Yes' if is_enabled else 'No'}\n"
        diagnostic += f"- Last triggered: {last_triggered}\n"

        if not is_enabled:
            diagnostic += "\n⚠️ **WARNING**: This automation is currently disabled. "
            diagnostic += "It will not run until you enable it.\n"

        # Configuration section
        diagnostic += "\n**Configuration:**\n"

        # Trigger information
        trigger = attributes.get("trigger", [])
        if trigger:
            diagnostic += "\n**Triggers:**\n"
            if isinstance(trigger, list):
                for idx, t in enumerate(trigger, 1):
                    platform = t.get("platform", "unknown")
                    diagnostic += f"{idx}. Type: {platform}\n"
                    # Add platform-specific details
                    if platform == "time":
                        at_time = t.get("at", "")
                        diagnostic += f"   - Time: {at_time}\n"
                    elif platform == "state":
                        entity = t.get("entity_id", "")
                        to_state = t.get("to", "any")
                        diagnostic += f"   - Entity: {entity}\n"
                        diagnostic += f"   - To state: {to_state}\n"
                    elif platform == "numeric_state":
                        entity = t.get("entity_id", "")
                        above = t.get("above", "")
                        below = t.get("below", "")
                        diagnostic += f"   - Entity: {entity}\n"
                        if above:
                            diagnostic += f"   - Above: {above}\n"
                        if below:
                            diagnostic += f"   - Below: {below}\n"
            else:
                diagnostic += f"- {trigger}\n"
        else:
            diagnostic += "- No trigger information available\n"

        # Condition information
        condition = attributes.get("condition", [])
        if condition:
            diagnostic += "\n**Conditions:**\n"
            if isinstance(condition, list):
                for idx, c in enumerate(condition, 1):
                    condition_type = c.get("condition", "unknown")
                    diagnostic += f"{idx}. Type: {condition_type}\n"
            else:
                diagnostic += f"- {condition}\n"
        else:
            diagnostic += "\n**Conditions:** None (runs every time triggered)\n"

        # Action information
        action = attributes.get("action", [])
        if action:
            diagnostic += "\n**Actions:**\n"
            if isinstance(action, list):
                for idx, a in enumerate(action, 1):
                    # Try to extract service call
                    if "service" in a:
                        service = a.get("service", "")
                        target = a.get("target", {})
                        entity_id = target.get("entity_id", a.get("entity_id", ""))
                        diagnostic += f"{idx}. Service: {service}\n"
                        if entity_id:
                            diagnostic += f"   - Target: {entity_id}\n"
                    elif "delay" in a:
                        diagnostic += f"{idx}. Delay: {a.get('delay', '')}\n"
                    else:
                        diagnostic += (
                            f"{idx}. Action type: {list(a.keys())[0] if a else 'unknown'}\n"
                        )
            else:
                diagnostic += f"- {action}\n"
        else:
            diagnostic += "- No action information available\n"

        # Debugging checklist
        diagnostic += "\n**Troubleshooting Checklist:**\n"
        diagnostic += "1. ✓ Automation exists and is accessible\n"
        diagnostic += f"2. {'✓' if is_enabled else '✗'} Automation is enabled\n"
        diagnostic += "3. ❓ Are trigger conditions being met?\n"
        diagnostic += "4. ❓ Are all conditions (if any) satisfied?\n"
        diagnostic += "5. ❓ Are target entities available and responsive?\n"
        diagnostic += "6. ❓ Check Home Assistant logs for errors\n"

        # Common issues
        diagnostic += "\n**Common Issues to Check:**\n"
        diagnostic += "- **Trigger not firing**: Verify trigger conditions are correct\n"
        diagnostic += "- **Conditions blocking**: Check if conditions are too restrictive\n"
        diagnostic += (
            "- **Entity unavailable**: Verify all referenced entities exist and are online\n"
        )
        diagnostic += (
            "- **Service errors**: Check that services are called with correct parameters\n"
        )
        diagnostic += "- **Timing issues**: For time-based triggers, verify timezone settings\n"

        # Next steps
        diagnostic += "\n**Next Steps:**\n"
        if not is_enabled:
            diagnostic += "1. Enable the automation using the automation_control tool\n"
        diagnostic += "- Review the configuration above for any issues\n"
        diagnostic += "- Check Home Assistant logs for error messages\n"
        diagnostic += "- Test trigger conditions manually to verify they work\n"
        diagnostic += "- Use the automation_control tool to trigger it manually for testing\n"

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=diagnostic))
        )

        return messages

    @mcp.prompt(tags={"automation"})
    async def suggest_automation(intent: str, constraints: str = "") -> list[PromptMessage]:
        """Convert user intent into an automation plan.

        This prompt analyzes user intent and provides a complete automation suggestion
        including triggers, conditions, and actions based on available entities.

        Args:
            intent: What the user wants to automate (e.g., "Turn on porch light at sunset")
            constraints: Optional limitations or requirements (e.g., "Only on weekdays")

        Returns:
            List of prompt messages with automation suggestions
        """
        client = get_client()
        messages = []

        # Build suggestion based on intent analysis
        suggestion = "**Automation Suggestion**\n\n"
        suggestion += f"**Your Intent:** {intent}\n"
        if constraints:
            suggestion += f"**Constraints:** {constraints}\n"
        suggestion += "\n"

        # Analyze intent to identify trigger type
        intent_lower = intent.lower()

        # Determine trigger type based on keywords
        trigger_suggestion = ""

        if any(word in intent_lower for word in ["sunset", "sunrise", "dawn", "dusk"]):
            if "sunset" in intent_lower:
                trigger_suggestion = """**Trigger:**
- Type: Sun
- Event: sunset
- Offset: -00:30 (30 minutes before sunset)

This will trigger the automation 30 minutes before sunset, ensuring
devices are ready before it gets dark."""
            else:
                trigger_suggestion = """**Trigger:**
- Type: Sun
- Event: sunrise
- Offset: 00:00 (at sunrise)

This will trigger the automation at sunrise."""

        elif any(word in intent_lower for word in ["time", "at ", "o'clock", "am", "pm"]):
            trigger_suggestion = """**Trigger:**
- Type: Time
- At: [Specify time, e.g., "07:00:00"]

This will trigger the automation at a specific time each day.
You can specify the exact time based on your needs."""

        elif any(word in intent_lower for word in ["when", "if", "becomes", "changes to"]):
            trigger_suggestion = """**Trigger:**
- Type: State
- Entity: [Specify entity, e.g., "binary_sensor.motion_sensor"]
- To: [Specify target state, e.g., "on"]

This will trigger when the specified entity changes to the target state."""

        elif any(word in intent_lower for word in ["temperature", "above", "below", "threshold"]):
            trigger_suggestion = """**Trigger:**
- Type: Numeric State
- Entity: [Specify sensor, e.g., "sensor.temperature"]
- Above/Below: [Specify threshold value]

This will trigger when a sensor value crosses the specified threshold."""

        elif any(
            word in intent_lower for word in ["arrive", "leave", "enter", "exit", "home", "away"]
        ):
            trigger_suggestion = """**Trigger:**
- Type: Zone
- Entity: [Specify device tracker, e.g., "device_tracker.phone"]
- Zone: [Specify zone, e.g., "zone.home"]
- Event: enter or leave

This will trigger when a device enters or leaves a specified zone."""

        else:
            # Default to time-based trigger
            trigger_suggestion = """**Trigger:**
- Type: Time (default suggestion)
- At: [Specify time based on your intent]

Based on your intent, a time-based trigger seems appropriate.
You can also consider state, sun, or numeric state triggers."""

        suggestion += trigger_suggestion + "\n\n"

        # Suggest conditions based on constraints
        if constraints:
            suggestion += "**Conditions (based on constraints):**\n"
            constraints_lower = constraints.lower()

            if any(
                word in constraints_lower
                for word in ["weekday", "monday", "tuesday", "wednesday", "thursday", "friday"]
            ):
                suggestion += """- Type: Time
  - Weekday: [mon, tue, wed, thu, fri]
  - Only run on weekdays\n"""

            if any(word in constraints_lower for word in ["weekend", "saturday", "sunday"]):
                suggestion += """- Type: Time
  - Weekday: [sat, sun]
  - Only run on weekends\n"""

            if any(word in constraints_lower for word in ["after", "before", "between"]):
                suggestion += """- Type: Time
  - After/Before: [Specify time range]
  - Only run during specific hours\n"""

            if any(word in constraints_lower for word in ["home", "away", "present"]):
                suggestion += """- Type: State
  - Entity: [person or device tracker]
  - State: home or not_home
  - Only run when someone is home/away\n"""

            suggestion += "\n"
        else:
            suggestion += """**Conditions (optional):**
No specific conditions suggested. The automation will run every time it's triggered.
Consider adding conditions if you want to restrict when it runs.\n\n"""

        # Suggest actions based on intent
        suggestion += "**Actions:**\n"

        # Try to fetch relevant entities for action suggestions
        try:
            # Determine which entities to fetch based on intent
            domain_filter = None
            if any(word in intent_lower for word in ["light", "lamp", "bulb"]):
                domain_filter = "light"
            elif any(word in intent_lower for word in ["switch", "plug", "outlet"]):
                domain_filter = "switch"
            elif any(
                word in intent_lower
                for word in ["climate", "thermostat", "temperature", "heat", "cool"]
            ):
                domain_filter = "climate"
            elif any(word in intent_lower for word in ["lock", "door"]):
                domain_filter = "lock"
            elif any(word in intent_lower for word in ["cover", "blind", "shade", "curtain"]):
                domain_filter = "cover"

            if domain_filter:
                entities = await client.get_states(domain=domain_filter, limit=10)
                if entities:
                    suggestion += f"\n**Available {domain_filter} entities:**\n"
                    for entity in entities[:5]:
                        entity_id = entity.get("entity_id", "")
                        friendly_name = entity.get("attributes", {}).get("friendly_name", entity_id)
                        suggestion += f"- {friendly_name} ({entity_id})\n"
                    if len(entities) > 5:
                        suggestion += f"... and {len(entities) - 5} more\n"
                    suggestion += "\n"
        except Exception as e:
            logger.debug(f"Could not fetch entities for action suggestions: {e}")

        # Provide action template based on intent
        if any(word in intent_lower for word in ["turn on", "enable", "activate"]):
            suggestion += """1. Service: [domain].turn_on
   - Target: [entity_id from available entities]
   - Optional data: brightness, color, etc.

This will turn on the specified device(s)."""

        elif any(word in intent_lower for word in ["turn off", "disable", "deactivate"]):
            suggestion += """1. Service: [domain].turn_off
   - Target: [entity_id from available entities]

This will turn off the specified device(s)."""

        elif any(word in intent_lower for word in ["set", "adjust", "change"]):
            suggestion += """1. Service: [domain].set_[attribute]
   - Target: [entity_id from available entities]
   - Data: [attribute value, e.g., temperature: 72]

This will set the specified attribute on the device(s)."""

        elif any(word in intent_lower for word in ["notify", "alert", "message"]):
            suggestion += """1. Service: notify.notify
   - Data:
     - message: "[Your notification message]"
     - title: "[Optional title]"

This will send a notification."""

        else:
            suggestion += """1. Service: [Specify service based on your intent]
   - Target: [entity_id]
   - Data: [Optional service parameters]

Define the action you want to perform when this automation triggers."""

        suggestion += "\n\n"

        # Provide complete automation template
        suggestion += "**Complete Automation Configuration:**\n\n"
        suggestion += "```yaml\n"
        suggestion += f"alias: {intent[:50]}\n"
        suggestion += (
            "description: "
            + (constraints if constraints else "Automation based on user intent")
            + "\n"
        )
        suggestion += "trigger:\n"
        suggestion += "  - platform: [trigger_type]\n"
        suggestion += "    # Add trigger-specific parameters\n"

        if constraints:
            suggestion += "condition:\n"
            suggestion += "  - condition: [condition_type]\n"
            suggestion += "    # Add condition-specific parameters\n"

        suggestion += "action:\n"
        suggestion += "  - service: [service_name]\n"
        suggestion += "    target:\n"
        suggestion += "      entity_id: [entity_id]\n"
        suggestion += "    # Add optional service data\n"
        suggestion += "mode: single\n"
        suggestion += "```\n\n"

        # Next steps
        suggestion += "**Next Steps:**\n"
        suggestion += "1. Review the suggested trigger, conditions, and actions\n"
        suggestion += "2. Identify specific entities from your Home Assistant setup\n"
        suggestion += "3. Customize the configuration to match your exact needs\n"
        suggestion += "4. Use the create_automation prompt to build it step-by-step\n"
        suggestion += "5. Test the automation to ensure it works as expected\n"

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=suggestion))
        )

        return messages
