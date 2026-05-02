"""Device troubleshooting prompt for diagnosing issues.

This module provides a prompt that guides users through troubleshooting device
issues. It performs diagnostic checks including current state analysis, recent
history review, error log examination, and provides actionable recommendations
for resolving common device problems.

The prompt was migrated to FastMCP 2.0+ patterns while preserving its original
functionality.

For more information on FastMCP prompts, see: https://gofastmcp.com/llms.txt

Example Usage:
    # Troubleshoot a specific device
    result = await troubleshoot_device("light.living_room")
"""

from datetime import datetime, timedelta
from typing import Any

from fastmcp.prompts import PromptMessage
from mcp.types import TextContent


def register_troubleshooting_prompt(mcp: Any, get_client: Any) -> None:
    """Register the device troubleshooting prompt."""

    @mcp.prompt(tags={"diagnostics"})
    async def troubleshoot_device(entity_id: str) -> list[PromptMessage]:
        """
        Guide through troubleshooting a device issue.

        This prompt provides diagnostic steps for identifying and resolving
        device problems.

        Args:
            entity_id: The entity ID to troubleshoot

        Returns:
            A conversation flow guiding through troubleshooting
        """
        client = get_client()

        messages = []

        # Initial message
        intro_text = f"""I'll help you troubleshoot issues with **{entity_id}**.

Let me gather diagnostic information..."""

        messages.append(
            PromptMessage(role="user", content=TextContent(type="text", text=intro_text))
        )

        # Step 1: Check current state
        try:
            state = await client.get_state(entity_id)

            state_text = f"""
**Step 1: Current State Check**

**Entity:** {entity_id}
**Current State:** {state['state']}
**Last Changed:** {state.get('last_changed', 'Unknown')}
**Last Updated:** {state.get('last_updated', 'Unknown')}

**Attributes:**"""

            for key, value in state.get("attributes", {}).items():
                state_text += f"\n- {key}: {value}"

            # Check if unavailable
            if state["state"] in ["unavailable", "unknown"]:
                state_text += """

⚠️ **Issue Detected:** Entity is unavailable or in unknown state.
This usually indicates:
- Device is offline or disconnected
- Integration is not working properly
- Network connectivity issues
- Device battery is dead (for battery-powered devices)"""

            messages.append(
                PromptMessage(role="assistant", content=TextContent(type="text", text=state_text))
            )

        except Exception as e:
            error_text = f"""
**Step 1: Current State Check**

❌ **Error:** Could not retrieve entity state.
Error message: {str(e)}

This suggests:
- Entity ID may be incorrect
- Entity may have been removed
- Home Assistant API connection issue"""

            messages.append(
                PromptMessage(role="assistant", content=TextContent(type="text", text=error_text))
            )

        # Step 2: Check recent history
        history_text = """
**Step 2: Recent State Changes**

Let me check the entity's recent history to identify patterns..."""

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=history_text))
        )

        try:
            # Get history for last 24 hours
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)

            history = await client.get_history(
                timestamp=start_time.isoformat(),
                end_time=end_time.isoformat(),
                filter_entity_id=[entity_id],
                limit=50,
            )

            if history and len(history) > 0 and len(history[0]) > 0:
                changes = history[0]
                history_summary = f"Found {len(changes)} state changes in the last 24 hours:\n"

                # Show last 5 changes
                for change in changes[-5:]:
                    history_summary += f"\n- {change.get('last_changed', 'Unknown')}: {change.get('state', 'Unknown')}"

                # Analyze patterns
                if len(changes) > 20:
                    history_summary += (
                        "\n\n⚠️ **Pattern:** Frequent state changes detected. This could indicate:"
                    )
                    history_summary += "\n- Flapping/unstable connection"
                    history_summary += "\n- Sensor noise or interference"
                    history_summary += "\n- Automation loop"

                unavailable_count = sum(1 for c in changes if c.get("state") == "unavailable")
                if unavailable_count > 0:
                    history_summary += f"\n\n⚠️ **Pattern:** Entity was unavailable {unavailable_count} times in 24 hours."
                    history_summary += "\n- Check device power/battery"
                    history_summary += "\n- Check network connectivity"
                    history_summary += "\n- Check integration status"

            else:
                history_summary = "No state changes found in the last 24 hours.\nThis could indicate the device is not reporting or is stuck."

            messages.append(
                PromptMessage(
                    role="assistant", content=TextContent(type="text", text=history_summary)
                )
            )

        except Exception:
            messages.append(
                PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text",
                        text="Could not retrieve history data. Continuing with other checks...",
                    ),
                )
            )

        # Step 3: Check error logs
        error_log_text = """
**Step 3: Error Log Check**

Checking Home Assistant error logs for related issues..."""

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=error_log_text))
        )

        try:
            error_log = await client.get_error_log()

            # Search for entity_id in error log
            if entity_id in error_log:
                log_text = "Found errors related to this entity in the logs:\n"
                log_text += "\n(Check the full error log for details)"
            else:
                log_text = "No errors found in the log related to this entity."

            messages.append(
                PromptMessage(role="assistant", content=TextContent(type="text", text=log_text))
            )

        except Exception:
            messages.append(
                PromptMessage(
                    role="assistant",
                    content=TextContent(type="text", text="Could not retrieve error logs."),
                )
            )

        # Step 4: Recommendations
        recommendations_text = """
**Step 4: Recommended Actions**

Based on the diagnostic information:

1. **If device is unavailable:**
   - Check device power/battery
   - Verify network connectivity
   - Restart the device
   - Reload the integration in Home Assistant

2. **If device is responding slowly:**
   - Check network signal strength
   - Reduce polling frequency if applicable
   - Check for interference

3. **If state is incorrect:**
   - Try manually controlling the device
   - Check automation rules that might affect it
   - Verify device firmware is up to date

4. **If issues persist:**
   - Check Home Assistant logs for integration errors
   - Restart Home Assistant
   - Remove and re-add the device
   - Check device manufacturer's support resources

Would you like me to help with any of these steps?"""

        messages.append(
            PromptMessage(
                role="assistant", content=TextContent(type="text", text=recommendations_text)
            )
        )

        return messages
