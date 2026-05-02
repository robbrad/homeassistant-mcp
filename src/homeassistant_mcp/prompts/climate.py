"""Climate optimization prompt for analyzing and optimizing HVAC settings.

This module provides a prompt that analyzes climate device settings and provides
optimization recommendations for comfort and energy efficiency. It reviews current
HVAC settings, considers weather context, and suggests temperature schedules,
mode optimizations, and automation opportunities.

The prompt was migrated to FastMCP 2.0+ patterns while preserving its original
functionality and adding safety guidance for climate control actions.

For more information on FastMCP prompts, see: https://gofastmcp.com/llms.txt

Example Usage:
    # Optimize climate settings for entire home
    result = await optimize_climate()

    # Optimize climate settings for specific area
    result = await optimize_climate(area="Living Room")
"""

from typing import Any

from fastmcp.prompts import PromptMessage
from mcp.types import TextContent


def register_climate_prompt(mcp: Any, get_client: Any) -> None:
    """Register the climate optimization prompt."""

    @mcp.prompt(tags={"diagnostics"})
    async def optimize_climate(area: str = "") -> list[PromptMessage]:
        """
        Analyze climate settings and suggest optimizations.

        This prompt reviews climate device settings and provides
        optimization recommendations for comfort and efficiency.

        Args:
            area: Optional area/room to focus on

        Returns:
            A conversation flow guiding through climate optimization
        """
        client = get_client()

        messages = []

        # Initial message
        intro_text = f"""I'll help you optimize climate settings{f' in {area}' if area else ''}.

Let me analyze your climate devices and current settings..."""

        messages.append(
            PromptMessage(role="user", content=TextContent(type="text", text=intro_text))
        )

        # Step 1: Analyze current climate settings
        try:
            states = await client.get_states(
                area=area if area else None, domain="climate", limit=100
            )

            if not states:
                # Try without domain filter
                all_states = await client.get_states(area=area if area else None, limit=200)
                states = [s for s in all_states if s["entity_id"].startswith("climate.")]

            if states:
                analysis_text = f"""
**Step 1: Current Climate Settings**

Found {len(states)} climate device(s){f' in {area}' if area else ''}:

"""

                for device in states:
                    attrs = device.get("attributes", {})
                    analysis_text += f"""
**{device['entity_id']}**
- State: {device['state']}
- Current Temperature: {attrs.get('current_temperature', 'N/A')}°
- Target Temperature: {attrs.get('temperature', 'N/A')}°
- HVAC Mode: {attrs.get('hvac_mode', 'N/A')}
- Fan Mode: {attrs.get('fan_mode', 'N/A')}
- Preset: {attrs.get('preset_mode', 'N/A')}
"""

                messages.append(
                    PromptMessage(
                        role="assistant", content=TextContent(type="text", text=analysis_text)
                    )
                )

            else:
                messages.append(
                    PromptMessage(
                        role="assistant",
                        content=TextContent(
                            type="text",
                            text=f"No climate devices found{f' in {area}' if area else ''}.",
                        ),
                    )
                )

        except Exception as e:
            messages.append(
                PromptMessage(
                    role="assistant",
                    content=TextContent(
                        type="text", text=f"Could not retrieve climate device states: {str(e)}"
                    ),
                )
            )

        # Step 2: Get weather context (if available)
        weather_text = """
**Step 2: Weather Context**

Let me check the weather to provide context-aware recommendations..."""

        messages.append(
            PromptMessage(role="assistant", content=TextContent(type="text", text=weather_text))
        )

        try:
            all_states = await client.get_states(limit=500)
            weather_entities = [s for s in all_states if s["entity_id"].startswith("weather.")]

            if weather_entities:
                weather = weather_entities[0]
                attrs = weather.get("attributes", {})

                weather_info = f"""
**Current Weather:**
- Condition: {weather['state']}
- Temperature: {attrs.get('temperature', 'N/A')}°
- Humidity: {attrs.get('humidity', 'N/A')}%
- Forecast: {attrs.get('forecast', 'Not available')}

This weather information helps optimize your climate settings."""

                messages.append(
                    PromptMessage(
                        role="assistant", content=TextContent(type="text", text=weather_info)
                    )
                )
            else:
                messages.append(
                    PromptMessage(
                        role="assistant",
                        content=TextContent(
                            type="text",
                            text="No weather entities found. Continuing with general recommendations...",
                        ),
                    )
                )

        except Exception:
            pass

        # Step 3: Optimization recommendations
        recommendations_text = """
**Step 3: Climate Optimization Recommendations**

**Temperature Settings:**

**Heating Season:**
- Occupied: 68-70°F (20-21°C)
- Away: 62-65°F (17-18°C)
- Sleep: 65-68°F (18-20°C)
- Each degree lower saves ~3% on heating costs

**Cooling Season:**
- Occupied: 75-78°F (24-26°C)
- Away: 80-85°F (27-29°C)
- Sleep: 72-75°F (22-24°C)
- Each degree higher saves ~3% on cooling costs

**HVAC Mode Optimization:**

1. **Auto Mode:**
   - Best for maintaining consistent temperature
   - System switches between heating/cooling as needed
   - Use when temperature varies throughout the day

2. **Heat/Cool Only:**
   - More efficient when you know what's needed
   - Prevents unnecessary mode switching
   - Use during stable weather

3. **Fan Mode:**
   - "Auto": Fan runs only when heating/cooling (most efficient)
   - "On": Continuous circulation (better air quality, higher energy use)
   - "Circulate": Periodic circulation (balanced approach)

**Preset Modes:**

- **Eco/Away:** Use when leaving home for extended periods
- **Sleep:** Optimized for nighttime comfort and efficiency
- **Boost:** Quick temperature adjustment (use sparingly)
- **Comfort:** Standard occupied settings

**Scheduling Recommendations:**

**Weekday Schedule:**
- 6:00 AM: Wake up temperature (comfort mode)
- 8:00 AM: Away temperature (eco mode)
- 5:00 PM: Return home (comfort mode)
- 10:00 PM: Sleep temperature (sleep mode)

**Weekend Schedule:**
- Adjust wake time to match your routine
- Maintain comfort settings during the day
- Use eco mode only when actually away

**Advanced Optimizations:**

1. **Zone Control:**
   - Close vents in unused rooms
   - Use separate thermostats for different areas
   - Focus heating/cooling on occupied spaces

2. **Humidity Management:**
   - Maintain 30-50% humidity for comfort
   - Use dehumidifier in summer if needed
   - Humidifier in winter for better heat retention

3. **Smart Automations:**
   - Adjust based on occupancy sensors
   - Integrate with weather forecasts
   - Pre-cool/pre-heat before arrival
   - Reduce settings when windows are open

4. **Maintenance:**
   - Change filters monthly
   - Clean vents and registers
   - Schedule annual HVAC service
   - Check for air leaks and insulation

**Safety Considerations:**

⚠️ **Before making climate changes:**
- Verify current settings to avoid drastic temperature swings
- Consider occupants' comfort and health needs
- Avoid extreme temperature changes (>5°F at once)
- Ensure proper ventilation when adjusting settings
- Monitor for unusual HVAC behavior after changes"""

        messages.append(
            PromptMessage(
                role="assistant", content=TextContent(type="text", text=recommendations_text)
            )
        )

        # Step 4: Implementation
        implementation_text = """
**Step 4: Implementation Options**

I can help you implement these optimizations:

1. **Create Climate Schedules:**
   - Set up automations for different times of day
   - Adjust based on weekday vs weekend
   - Integrate with presence detection

2. **Create Climate Scenes:**
   - "Home" scene with comfort settings
   - "Away" scene with eco settings
   - "Sleep" scene with nighttime settings
   - "Boost" scene for quick adjustments

3. **Set Up Smart Automations:**
   - Auto-adjust when leaving/arriving home
   - Reduce settings when windows open
   - Pre-condition before scheduled arrival
   - Seasonal mode switching

4. **Monitor and Optimize:**
   - Track temperature patterns
   - Measure energy usage
   - Fine-tune settings based on comfort
   - Adjust for seasonal changes

Which optimization would you like to implement first?"""

        messages.append(
            PromptMessage(
                role="assistant", content=TextContent(type="text", text=implementation_text)
            )
        )

        return messages
