# Home Assistant MCP Server - Examples

This directory contains configuration files and usage examples for the Home Assistant MCP Server.

## 📁 Files in This Directory

- **[EXAMPLES.md](EXAMPLES.md)** - Comprehensive usage examples, natural language commands, and advanced scenarios
- **[claude_desktop_config.json](claude_desktop_config.json)** - Example configuration for Claude Desktop
- **[cursor_config.json](cursor_config.json)** - Example configuration for Cursor

## 📖 Quick Links

- [Configuration Examples](EXAMPLES.md#configuration-examples) - How to configure different MCP clients
- [Natural Language Commands](EXAMPLES.md#natural-language-commands) - Examples of commands to use with AI assistants
- [Tool Usage Examples](EXAMPLES.md#tool-usage-examples) - Direct tool usage examples
- [Advanced Scenarios](EXAMPLES.md#advanced-scenarios) - Complex multi-step automation examples

## Table of Contents

- [Basic Examples](#basic-examples)
- [Advanced Scenarios](#advanced-scenarios)
- [Natural Language Commands](#natural-language-commands)
- [Automation Examples](#automation-examples)
- [Integration Examples](#integration-examples)

## Basic Examples

### Controlling Lights

```python
# Turn on a light
lights_control(action="turn_on", entity_id="light.living_room")

# Turn on with 50% brightness
lights_control(action="turn_on", entity_id="light.living_room", brightness=128)

# Set warm white color temperature
lights_control(action="turn_on", entity_id="light.bedroom", color_temp=400)

# Set RGB color to red
lights_control(action="turn_on", entity_id="light.kitchen", rgb_color=(255, 0, 0))

# Turn off a light
lights_control(action="turn_off", entity_id="light.living_room")

# List all lights
lights_control(action="list")
```

### Climate Control

```python
# Set thermostat to heat mode
climate_control(action="set_hvac_mode", entity_id="climate.living_room", hvac_mode="heat")

# Set temperature to 72°F
climate_control(action="set_temperature", entity_id="climate.living_room", temperature=72.0)

# Set temperature range for dual-setpoint thermostat
climate_control(
    action="set_temperature",
    entity_id="climate.bedroom",
    target_temp_high=75.0,
    target_temp_low=68.0
)

# Set fan mode
climate_control(action="set_fan_mode", entity_id="climate.living_room", fan_mode="auto")

# List all climate devices
climate_control(action="list")
```

### Device Discovery

```python
# List all devices
list_devices()

# List all lights
list_devices(domain="light")

# List all devices in the living room
list_devices(area="Living Room")

# List all sensors on the ground floor
list_devices(domain="sensor", floor="Ground Floor")

# List lights in the kitchen
list_devices(domain="light", area="Kitchen")
```

## Advanced Scenarios

### Morning Routine

```python
# 1. Turn on bedroom lights gradually
lights_control(action="turn_on", entity_id="light.bedroom", brightness=50)

# 2. Set thermostat to comfortable temperature
climate_control(action="set_temperature", entity_id="climate.bedroom", temperature=70.0)

# 3. Turn on coffee maker (using generic control)
call_service(domain="switch", service="turn_on", entity_id="switch.coffee_maker")

# 4. Send notification
send_notification(message="Good morning! Your routine has started.", title="Morning Routine")
```

### Movie Night

```python
# 1. Dim living room lights
lights_control(action="turn_on", entity_id="light.living_room", brightness=30)

# 2. Turn off kitchen lights
lights_control(action="turn_off", entity_id="light.kitchen")

# 3. Set ambient lighting
lights_control(action="turn_on", entity_id="light.tv_backlight", rgb_color=(100, 50, 200))

# 4. Adjust thermostat
climate_control(action="set_temperature", entity_id="climate.living_room", temperature=68.0)

# 5. Or use a predefined scene
scene_control(action="activate", scene_id="scene.movie_mode")
```

### Energy Saving Mode

```python
# 1. List all lights that are on
all_lights = lights_control(action="list")
on_lights = [light for light in all_lights["lights"] if light["state"] == "on"]

# 2. Dim all lights to 30%
for light in on_lights:
    lights_control(action="turn_on", entity_id=light["entity_id"], brightness=77)

# 3. Set thermostats to eco mode
climate_devices = climate_control(action="list")
for device in climate_devices["climate_devices"]:
    climate_control(action="set_hvac_mode", entity_id=device["entity_id"], hvac_mode="auto")

# 4. Send confirmation
send_notification(message="Energy saving mode activated", title="Home Automation")
```

## Natural Language Commands

These are examples of natural language commands you can use with AI assistants:

### Lighting Commands

- "Turn on the living room lights"
- "Dim the bedroom lights to 30%"
- "Set the kitchen lights to warm white"
- "Make the hallway lights blue"
- "Turn off all lights in the house"
- "What lights are currently on?"

### Climate Commands

- "Set the thermostat to 72 degrees"
- "Turn on the AC in the bedroom"
- "What's the current temperature in the living room?"
- "Set the heat to 68 degrees"
- "Turn off the HVAC"
- "Set the fan to auto mode"

### Scene Commands

- "Activate movie mode"
- "Turn on the morning routine"
- "Set up the dinner scene"
- "What scenes are available?"

### Device Discovery Commands

- "Show me all devices in the kitchen"
- "List all sensors in the house"
- "What lights are in the living room?"
- "Show me all devices on the ground floor"

## Automation Examples

### Presence-Based Lighting

```python
# When someone arrives home
def on_arrival():
    # Turn on entry lights
    lights_control(action="turn_on", entity_id="light.entry", brightness=255)
    
    # Turn on living room lights
    lights_control(action="turn_on", entity_id="light.living_room", brightness=180)
    
    # Send welcome notification
    send_notification(message="Welcome home!", title="Home Automation")
```

### Bedtime Routine

```python
def bedtime_routine():
    # Turn off all lights except bedroom
    all_lights = lights_control(action="list")
    for light in all_lights["lights"]:
        if "bedroom" not in light["entity_id"]:
            lights_control(action="turn_off", entity_id=light["entity_id"])
    
    # Dim bedroom lights
    lights_control(action="turn_on", entity_id="light.bedroom", brightness=50)
    
    # Set thermostat for sleeping
    climate_control(action="set_temperature", entity_id="climate.bedroom", temperature=68.0)
    
    # Lock doors
    call_service(domain="lock", service="lock", entity_id="lock.front_door")
```

## Integration Examples

### Claude Desktop Integration

Once configured in Claude Desktop, you can have natural conversations like:

**User:** "Can you turn on the living room lights and set them to 50% brightness?"

**Claude:** I'll turn on the living room lights and set them to 50% brightness for you.

*[Calls lights_control tool]*

The living room lights are now on at 50% brightness (brightness level 128).

---

**User:** "What's the temperature in the bedroom and can you make it warmer?"

**Claude:** Let me check the bedroom temperature and adjust it for you.

*[Calls climate_control to get state and set temperature]*

The bedroom is currently at 68°F. I've set the thermostat to 72°F to make it warmer.

### Cursor Integration

In Cursor, you can use the MCP server to help with home automation scripts:

**User:** "Write a script to turn off all lights when I leave home"

**Cursor:** Here's a script that will turn off all lights:

```python
def lights_off_on_departure():
    # Get all lights
    lights = lights_control(action="list")
    
    # Turn off each light
    for light in lights["lights"]:
        lights_control(action="turn_off", entity_id=light["entity_id"])
    
    # Send confirmation
    send_notification(message="All lights turned off", title="Departure Routine")
```

## Tips and Best Practices

1. **Use Specific Entity IDs**: Always use the full entity ID (e.g., `light.living_room`) for reliability

2. **Check States First**: Before making changes, check current states to avoid unnecessary calls

3. **Use Scenes**: For complex multi-device setups, create scenes in Home Assistant and activate them

4. **Test Incrementally**: Test each command individually before combining into complex routines

5. **Use Natural Language**: With AI assistants, use natural language - they'll translate to the appropriate tool calls

## More Examples

For more comprehensive examples, see:
- **[EXAMPLES.md](EXAMPLES.md)** - Full documentation with all examples
- [Home Assistant Automation Documentation](https://www.home-assistant.io/docs/automation/)
- [Home Assistant Scene Documentation](https://www.home-assistant.io/integrations/scene/)
