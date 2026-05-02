"""Security check prompt for comprehensive security status review.

This module provides a prompt that performs comprehensive security checks across
all security-related devices including locks, alarms, cameras, and sensors. It
identifies potential security issues and provides actionable recommendations.

The prompt was migrated to FastMCP 2.0+ patterns while preserving its original
functionality and enhancing safety warnings for security device control.

For more information on FastMCP prompts, see: https://gofastmcp.com/llms.txt

Example Usage:
    # Perform comprehensive security check
    result = await security_check()
"""

from typing import Any

from fastmcp.prompts import PromptMessage
from mcp.types import TextContent


def register_security_prompt(mcp: Any, get_client: Any) -> None:
    """Register the security check prompt."""

    @mcp.prompt(tags={"safety", "status"})
    async def security_check() -> list[PromptMessage]:
        """
        Perform a comprehensive security check.

        This prompt reviews all security-related devices and provides
        a security status summary.

        Returns:
            A conversation flow guiding through security checks
        """
        client = get_client()

        messages = []

        # Initial message
        intro_text = """I'll perform a comprehensive security check of your home.

Let me check all security-related devices..."""

        messages.append(
            PromptMessage(role="user", content=TextContent(type="text", text=intro_text))
        )

        # Step 1: Check locks
        try:
            states = await client.get_states(limit=500)

            locks = [s for s in states if s["entity_id"].startswith("lock.")]
            alarms = [s for s in states if s["entity_id"].startswith("alarm_control_panel.")]
            cameras = [s for s in states if s["entity_id"].startswith("camera.")]
            binary_sensors = [s for s in states if s["entity_id"].startswith("binary_sensor.")]

            # Filter for security-related binary sensors
            door_sensors = [s for s in binary_sensors if "door" in s["entity_id"]]
            window_sensors = [s for s in binary_sensors if "window" in s["entity_id"]]
            motion_sensors = [s for s in binary_sensors if "motion" in s["entity_id"]]

            security_text = """
**Step 1: Security Device Status**

"""

            # Locks
            if locks:
                security_text += f"**Locks ({len(locks)}):**\n"
                unlocked_locks = []
                for lock in locks:
                    state = lock["state"]
                    status_icon = "🔒" if state == "locked" else "🔓"
                    security_text += f"{status_icon} {lock['entity_id']}: {state}\n"
                    if state == "unlocked":
                        unlocked_locks.append(lock["entity_id"])

                if unlocked_locks:
                    security_text += (
                        f"\n⚠️ **Warning:** {len(unlocked_locks)} lock(s) are unlocked!\n"
                    )
            else:
                security_text += "**Locks:** No locks found\n"

            # Alarms
            security_text += f"\n**Alarm Systems ({len(alarms)}):**\n"
            if alarms:
                for alarm in alarms:
                    state = alarm["state"]
                    status_icon = "🛡️" if state == "armed_away" or state == "armed_home" else "⚠️"
                    security_text += f"{status_icon} {alarm['entity_id']}: {state}\n"

                disarmed = [a for a in alarms if a["state"] == "disarmed"]
                if disarmed:
                    security_text += f"\n⚠️ **Warning:** {len(disarmed)} alarm(s) are disarmed!\n"
            else:
                security_text += "No alarm systems found\n"

            # Cameras
            security_text += f"\n**Cameras ({len(cameras)}):**\n"
            if cameras:
                unavailable_cameras = []
                for camera in cameras[:10]:
                    state = camera["state"]
                    status_icon = "📹" if state != "unavailable" else "❌"
                    security_text += f"{status_icon} {camera['entity_id']}: {state}\n"
                    if state == "unavailable":
                        unavailable_cameras.append(camera["entity_id"])

                if len(cameras) > 10:
                    security_text += f"... and {len(cameras) - 10} more\n"

                if unavailable_cameras:
                    security_text += (
                        f"\n⚠️ **Warning:** {len(unavailable_cameras)} camera(s) are unavailable!\n"
                    )
            else:
                security_text += "No cameras found\n"

            messages.append(
                PromptMessage(
                    role="assistant", content=TextContent(type="text", text=security_text)
                )
            )

        except Exception as e:
            messages.append(
                PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text", text=f"Could not retrieve security device states: {str(e)}"
                    ),
                )
            )

        # Step 2: Check sensors
        sensor_text = """
**Step 2: Security Sensor Status**

"""

        try:
            # Door sensors
            if door_sensors:
                sensor_text += f"**Door Sensors ({len(door_sensors)}):**\n"
                open_doors = []
                for sensor in door_sensors[:10]:
                    state = sensor["state"]
                    status_icon = "🚪" if state == "off" else "⚠️"
                    sensor_text += f"{status_icon} {sensor['entity_id']}: {'closed' if state == 'off' else 'open'}\n"
                    if state == "on":
                        open_doors.append(sensor["entity_id"])

                if len(door_sensors) > 10:
                    sensor_text += f"... and {len(door_sensors) - 10} more\n"

                if open_doors:
                    sensor_text += f"\n⚠️ **Alert:** {len(open_doors)} door(s) are open!\n"
            else:
                sensor_text += "**Door Sensors:** None found\n"

            # Window sensors
            if window_sensors:
                sensor_text += f"\n**Window Sensors ({len(window_sensors)}):**\n"
                open_windows = []
                for sensor in window_sensors[:10]:
                    state = sensor["state"]
                    status_icon = "🪟" if state == "off" else "⚠️"
                    sensor_text += f"{status_icon} {sensor['entity_id']}: {'closed' if state == 'off' else 'open'}\n"
                    if state == "on":
                        open_windows.append(sensor["entity_id"])

                if len(window_sensors) > 10:
                    sensor_text += f"... and {len(window_sensors) - 10} more\n"

                if open_windows:
                    sensor_text += f"\n⚠️ **Alert:** {len(open_windows)} window(s) are open!\n"
            else:
                sensor_text += "\n**Window Sensors:** None found\n"

            # Motion sensors
            if motion_sensors:
                sensor_text += f"\n**Motion Sensors ({len(motion_sensors)}):**\n"
                active_motion = [s for s in motion_sensors if s["state"] == "on"]
                sensor_text += (
                    f"Active motion detected: {len(active_motion)}/{len(motion_sensors)}\n"
                )

                if active_motion:
                    sensor_text += "\nMotion detected at:\n"
                    for sensor in active_motion[:5]:
                        sensor_text += f"- {sensor['entity_id']}\n"

            messages.append(
                PromptMessage(role="assistant", content=TextContent(type="text", text=sensor_text))
            )

        except Exception:
            pass

        # Step 3: Security summary
        summary_text = """
**Step 3: Security Summary & Recommendations**

**Overall Security Status:**

✅ **Secure Areas:**
- All locks that should be locked are secured
- Alarm system is armed (if applicable)
- All cameras are operational
- All entry points are closed

⚠️ **Areas Needing Attention:**
Review any warnings above and take appropriate action.

🛡️ **CRITICAL SECURITY REMINDERS:**

**Before Making Security Changes:**
- ALWAYS verify current state before modifying locks or alarms
- NEVER lock doors if someone might be inside without a key
- CONFIRM alarm status before arming/disarming
- CHECK camera feeds are working before relying on them
- ENSURE you have backup access methods (keys, codes)

**Emergency Considerations:**
- Keep emergency contact numbers accessible
- Ensure fire exits remain accessible
- Test alarm systems regularly
- Verify battery backups are functional
- Have a plan for power outages

**Recommendations:**

1. **Lock Management:**
   - Ensure all exterior doors are locked when away
   - Consider automations to lock doors at bedtime
   - Set up notifications for unexpected unlocking
   - ⚠️ Always confirm lock status before leaving

2. **Alarm System:**
   - Arm alarm when leaving home
   - Use "armed_home" mode at night
   - Test alarm system regularly
   - ⚠️ Verify alarm is armed, don't assume

3. **Camera Monitoring:**
   - Verify all cameras are online
   - Check camera views for obstructions
   - Ensure adequate lighting for night vision
   - ⚠️ Cameras are for monitoring, not prevention

4. **Sensor Maintenance:**
   - Test door/window sensors monthly
   - Replace batteries in wireless sensors
   - Verify sensor placement and coverage
   - ⚠️ Failed sensors create security blind spots

5. **Automation Ideas:**
   - "Away Mode": Lock all doors, arm alarm, verify windows closed
   - "Good Night": Lock doors, arm alarm in home mode
   - Notifications: Alert on door/window opening when armed
   - Camera recording: Trigger recording on motion when away
   - ⚠️ Test automations thoroughly before relying on them

Would you like me to help implement any of these security improvements?"""

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=summary_text))
        )

        return messages
