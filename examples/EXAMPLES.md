# Home Assistant MCP - Usage Examples

This document provides comprehensive examples of using the Home Assistant MCP server with various AI assistants and for different smart home scenarios.

## Table of Contents

- [Configuration Examples](#configuration-examples)
- [Natural Language Commands](#natural-language-commands)
- [Tool Usage Examples](#tool-usage-examples)
- [Advanced Scenarios](#advanced-scenarios)

---

## Configuration Examples

### Claude Desktop Configuration

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Using uvx (Recommended):**

```json
{
  "mcpServers": {
    "homeassistant": {
      "name": "Home Assistant",
      "command": "uvx",
      "args": ["homeassistant-mcp"],
      "env": {
        "HASS_HOST": "http://homeassistant.local:8123",
        "HASS_TOKEN": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
      }
    }
  }
}
```

**Using pip install:**

```json
{
  "mcpServers": {
    "homeassistant": {
      "name": "Home Assistant",
      "command": "homeassistant-mcp",
      "env": {
        "HASS_HOST": "http://homeassistant.local:8123",
        "HASS_TOKEN": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
      }
    }
  }
}
```

**With Custom Settings:**

```json
{
  "mcpServers": {
    "homeassistant": {
      "name": "Home Assistant",
      "command": "uvx",
      "args": ["homeassistant-mcp"],
      "env": {
        "HASS_HOST": "https://my-home.duckdns.org",
        "HASS_TOKEN": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "LOG_LEVEL": "DEBUG",
        "CACHE_TTL_STATES": "60",
        "CACHE_TTL_ENTITY": "20"
      }
    }
  }
}
```

### Cursor Configuration

**Location:** `.cursor/config/config.json` in your project or global config

**Configuration:**

```json
{
  "mcpServers": {
    "homeassistant": {
      "name": "Home Assistant",
      "command": "uvx",
      "args": ["homeassistant-mcp"],
      "env": {
        "HASS_HOST": "http://homeassistant.local:8123",
        "HASS_TOKEN": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
      }
    }
  }
}
```

### Other MCP Clients

For any MCP-compatible client that supports stdio transport:

**Command:**
```bash
homeassistant-mcp
```

**Environment Variables:**
```bash
export HASS_HOST="http://homeassistant.local:8123"
export HASS_TOKEN="your_token_here"
homeassistant-mcp
```

---

## Natural Language Commands

Once configured, you can use natural language to control your smart home. Here are examples organized by category:

### Lighting Control

**Basic Operations:**
- "Turn on the living room lights"
- "Turn off all bedroom lights"
- "Toggle the kitchen light"
- "Turn on the porch light"

**Brightness Control:**
- "Set the living room lights to 50% brightness"
- "Dim the bedroom lights to 25%"
- "Make the kitchen lights brighter" (AI will interpret and set appropriate level)
- "Set the office light to full brightness"

**Color Temperature:**
- "Set the bedroom lights to warm white"
- "Make the living room lights cooler"
- "Set the reading lamp to 3000K"
- "Change the kitchen lights to daylight white"

**RGB Colors:**
- "Make the bedroom lights red"
- "Set the living room lights to blue"
- "Change the kitchen lights to purple"
- "Make the office lights green"

**Complex Commands:**
- "Turn on the living room lights at 75% brightness with warm white"
- "Set all bedroom lights to 50% brightness and blue color"
- "Dim the kitchen lights to 30% and make them orange"

### Climate Control

**Temperature Control:**
- "Set the thermostat to 72 degrees"
- "Make it warmer in the living room"
- "Set the bedroom temperature to 68°F"
- "Increase the temperature by 2 degrees"

**HVAC Modes:**
- "Turn on the heat"
- "Switch to cooling mode"
- "Set the thermostat to auto mode"
- "Turn off the AC"

**Fan Control:**
- "Set the fan to low"
- "Turn the fan to high speed"
- "Set the fan to auto mode"

**Temperature Ranges (for dual-setpoint thermostats):**
- "Set the temperature range to 68-75 degrees"
- "Keep the temperature between 70 and 74"

**Status Queries:**
- "What's the current temperature in the living room?"
- "What mode is the thermostat in?"
- "Is the AC running?"

### Device Discovery

**Listing Devices:**
- "List all lights in the house"
- "Show me all sensors"
- "What switches do I have?"
- "List all devices in the living room"

**Filtering by Domain:**
- "Show me all climate devices"
- "List all motion sensors"
- "What cameras do I have?"
- "Show all media players"

**Filtering by Location:**
- "What devices are in the kitchen?"
- "List all sensors in the bedroom"
- "Show me everything on the ground floor"
- "What's in the garage?"

**Device Information:**
- "Tell me about the living room light"
- "What's the status of the front door sensor?"
- "Is the garage door open?"

### Scenes and Automation

**Scene Activation:**
- "Activate the movie scene"
- "Turn on the good morning scene"
- "Activate bedtime mode"
- "Set the romantic scene"

**Scene Discovery:**
- "What scenes do I have?"
- "List all available scenes"
- "Show me my scenes"

**Automation Control:**
- "Turn on the morning routine"
- "Disable the night mode automation"
- "Trigger the security check"
- "Enable the vacation mode automation"

**Automation Status:**
- "List all automations"
- "Is the morning routine enabled?"
- "When did the security check last run?"

### Notifications

**Simple Notifications:**
- "Send a notification that dinner is ready"
- "Notify everyone that I'm home"
- "Send an alert that the laundry is done"

**Notifications with Titles:**
- "Send a notification titled 'Security Alert' saying 'Front door opened'"
- "Notify with title 'Weather Update' that it's going to rain"

**Targeted Notifications:**
- "Send a notification to my phone that the garage is open"
- "Notify the family room display that dinner is ready"

### History and Status

**Historical Queries:**
- "What was the temperature in the living room yesterday?"
- "Show me the history of the front door sensor"
- "When was the last time the motion sensor was triggered?"

**Current Status:**
- "What's the status of all lights?"
- "Are any windows open?"
- "What's the current state of the house?"

### Switch Control

**Basic Operations:**
- "Turn on the coffee maker"
- "Turn off the fan"
- "Toggle the Christmas lights"
- "Turn on all outdoor switches"

**Bulk Operations:**
- "Turn off all switches in the living room"
- "Turn on all outdoor lights"
- "Toggle all bedroom switches"

**Status Queries:**
- "Are any switches on in the kitchen?"
- "What's the status of the coffee maker?"
- "List all switches that are currently on"

### Media Player Control

**Playback Control:**
- "Play music in the living room"
- "Pause the TV"
- "Stop the bedroom speaker"
- "Skip to the next track"
- "Go back to the previous song"

**Volume Control:**
- "Set the volume to 50%"
- "Turn up the volume in the living room"
- "Turn down the volume"
- "Mute the TV"
- "Unmute the speakers"

**Source Selection:**
- "Switch to HDMI 1 on the TV"
- "Change the input to Bluetooth"
- "Select Spotify on the living room speaker"

**Media Playback:**
- "Play my favorite playlist on Spotify"
- "Play the radio station on TuneIn"
- "Stream this YouTube video to the TV"

### Cover Control (Blinds, Shades, Garage Doors)

**Basic Operations:**
- "Open the garage door"
- "Close the bedroom blinds"
- "Stop the living room blinds"
- "Toggle the garage door"

**Position Control:**
- "Set the bedroom blinds to 50%"
- "Open the living room shades halfway"
- "Close the blinds to 25%"

**Tilt Control:**
- "Tilt the blinds to 45 degrees"
- "Adjust the slats to let in more light"
- "Set the blind tilt to 75%"

**Status Queries:**
- "Is the garage door open?"
- "What position are the bedroom blinds at?"
- "Are any covers open?"

### Lock Control

**Basic Operations:**
- "Lock the front door"
- "Unlock the back door"
- "Lock all doors"

**With Code:**
- "Unlock the front door with code 1234"
- "Lock the garage door with my code"

**Status Queries:**
- "Is the front door locked?"
- "Are all doors locked?"
- "What's the battery level of the front door lock?"

### Camera Control

**Snapshots:**
- "Take a snapshot from the front door camera"
- "Get a picture from the driveway camera"
- "Save a snapshot from the backyard camera to /tmp/snapshot.jpg"

**Motion Detection:**
- "Enable motion detection on the front door camera"
- "Disable motion detection on all cameras"
- "Turn off motion alerts for the garage camera"

**Streaming:**
- "Get the stream URL for the living room camera"
- "Show me the feed from the front door camera"

**Status Queries:**
- "List all cameras"
- "Is motion detection enabled on the front door camera?"
- "What cameras are available?"

### Vacuum Control

**Basic Operations:**
- "Start the vacuum"
- "Pause the vacuum cleaner"
- "Stop the robot vacuum"
- "Send the vacuum back to base"
- "Make the vacuum beep so I can find it"

**Fan Speed:**
- "Set the vacuum to max suction"
- "Change the vacuum fan speed to quiet"
- "Set the vacuum to turbo mode"

**Status Queries:**
- "Where is the vacuum?"
- "What's the battery level of the vacuum?"
- "Is the vacuum cleaning?"
- "When did the vacuum last clean?"

### Fan Control

**Basic Operations:**
- "Turn on the bedroom fan"
- "Turn off the ceiling fan"
- "Toggle the living room fan"

**Speed Control:**
- "Set the fan speed to 75%"
- "Turn the fan to low speed"
- "Set the ceiling fan to maximum"

**Oscillation:**
- "Turn on oscillation for the bedroom fan"
- "Stop the fan from oscillating"
- "Make the fan rotate"

**Direction:**
- "Set the fan to forward direction"
- "Reverse the ceiling fan direction"
- "Change the fan to winter mode"

**Preset Modes:**
- "Set the fan to sleep mode"
- "Change the fan to turbo mode"
- "Use the natural breeze preset"

### Script Execution

**Running Scripts:**
- "Run the morning routine script"
- "Execute the bedtime script"
- "Trigger the party mode script"

**With Variables:**
- "Run the notification script with message 'Dinner is ready'"
- "Execute the light scene script with brightness 75"

**Script Management:**
- "List all available scripts"
- "Reload all scripts"
- "When did the morning routine last run?"

### Input Helpers

**Input Boolean:**
- "Turn on the guest mode"
- "Disable vacation mode"
- "Toggle the sleep mode"

**Input Number:**
- "Set the temperature offset to 2.5"
- "Increase the brightness level by 1"
- "Decrease the volume level"
- "Set the timer duration to 30"

**Input Select:**
- "Select 'Home' for the house mode"
- "Change the theme to 'Dark'"
- "Set the alarm mode to 'Armed Away'"

**Input Text:**
- "Set the welcome message to 'Hello, World!'"
- "Update the notification text"
- "Change the display name"

**Input DateTime:**
- "Set the alarm time to 7:00 AM"
- "Change the wake up time to tomorrow at 6:30"
- "Update the event date to next Friday"

### Weather Information

**Current Conditions:**
- "What's the weather like?"
- "What's the temperature outside?"
- "What's the current humidity?"
- "Is it raining?"

**Forecasts:**
- "What's the weather forecast for today?"
- "Show me the hourly forecast"
- "What's the weather going to be like this week?"
- "Will it rain tomorrow?"

**Detailed Information:**
- "What's the wind speed?"
- "What's the atmospheric pressure?"
- "What's the UV index?"

### Alarm Control Panel

**Arming:**
- "Arm the alarm in away mode"
- "Set the alarm to home mode"
- "Arm the alarm for night"

**Disarming:**
- "Disarm the alarm with code 1234"
- "Turn off the alarm system"

**Status:**
- "Is the alarm armed?"
- "What mode is the alarm in?"
- "Check the alarm status"

**Trigger:**
- "Trigger the alarm"
- "Sound the alarm"

### Water Heater Control

**Temperature:**
- "Set the water heater to 120°F"
- "Increase the water heater temperature"
- "What's the water heater temperature?"

**Modes:**
- "Set the water heater to eco mode"
- "Turn on the water heater boost mode"
- "Set the water heater to electric mode"

### Humidifier Control

**Basic Operations:**
- "Turn on the humidifier"
- "Turn off the bedroom humidifier"
- "Toggle the humidifier"

**Humidity Control:**
- "Set the humidifier to 60%"
- "Increase the humidity level"
- "Set the target humidity to 55%"

**Modes:**
- "Set the humidifier to auto mode"
- "Change the humidifier to sleep mode"
- "Set the humidifier to boost mode"

### Siren Control

**Basic Operations:**
- "Turn on the siren"
- "Turn off the alarm siren"
- "Sound the siren"

**With Options:**
- "Turn on the siren with high volume"
- "Sound the siren with the emergency tone"
- "Activate the siren for 30 seconds"

### Valve Control

**Basic Operations:**
- "Open the water valve"
- "Close the irrigation valve"
- "Toggle the gas valve"

**Position Control:**
- "Set the valve to 50% open"
- "Open the valve halfway"
- "Close the valve to 25%"

### Lawn Mower Control

**Basic Operations:**
- "Start the lawn mower"
- "Pause the mower"
- "Stop the lawn mower"
- "Send the mower back to dock"

**Status:**
- "Where is the lawn mower?"
- "What's the battery level of the mower?"
- "Is the mower cutting?"

---

## Tool Usage Examples

These examples show how to use the tools directly (useful for developers or advanced users).

### Lights Control Tool

**List all lights:**
```python
lights_control(action="list")
```

**Response:**
```json
{
  "lights": [
    {
      "entity_id": "light.living_room",
      "state": "on",
      "attributes": {
        "brightness": 255,
        "color_temp": 370,
        "friendly_name": "Living Room Light"
      }
    },
    {
      "entity_id": "light.bedroom",
      "state": "off",
      "attributes": {
        "friendly_name": "Bedroom Light"
      }
    }
  ]
}
```

**Get specific light:**
```python
lights_control(action="get", entity_id="light.living_room")
```

**Turn on with brightness:**
```python
lights_control(
    action="turn_on",
    entity_id="light.living_room",
    brightness=128  # 50% brightness (0-255 scale)
)
```

**Turn on with color temperature:**
```python
lights_control(
    action="turn_on",
    entity_id="light.bedroom",
    color_temp=370  # Warm white (153-500 Mireds)
)
```

**Turn on with RGB color:**
```python
lights_control(
    action="turn_on",
    entity_id="light.kitchen",
    rgb_color=(255, 0, 0)  # Red
)
```

**Turn on with all parameters:**
```python
lights_control(
    action="turn_on",
    entity_id="light.office",
    brightness=200,
    color_temp=300,
    rgb_color=(255, 200, 100)
)
```

**Turn off:**
```python
lights_control(action="turn_off", entity_id="light.living_room")
```

### Climate Control Tool

**List all climate devices:**
```python
climate_control(action="list")
```

**Get specific device:**
```python
climate_control(action="get", entity_id="climate.living_room")
```

**Set HVAC mode:**
```python
climate_control(
    action="set_hvac_mode",
    entity_id="climate.living_room",
    hvac_mode="heat"  # Options: off, heat, cool, auto, dry, fan_only
)
```

**Set temperature (single setpoint):**
```python
climate_control(
    action="set_temperature",
    entity_id="climate.living_room",
    temperature=72.0
)
```

**Set temperature range (dual setpoint):**
```python
climate_control(
    action="set_temperature",
    entity_id="climate.bedroom",
    target_temp_high=75.0,
    target_temp_low=68.0
)
```

**Set fan mode:**
```python
climate_control(
    action="set_fan_mode",
    entity_id="climate.living_room",
    fan_mode="low"  # Options: auto, low, medium, high
)
```

### Device Listing Tool

**List all devices:**
```python
list_devices()
```

**Filter by domain:**
```python
list_devices(domain="light")
list_devices(domain="sensor")
list_devices(domain="switch")
```

**Filter by area:**
```python
list_devices(area="Living Room")
list_devices(area="Kitchen")
```

**Filter by floor:**
```python
list_devices(floor="Ground Floor")
list_devices(floor="Upstairs")
```

**Multiple filters:**
```python
list_devices(domain="sensor", area="Bedroom")
list_devices(domain="light", floor="Ground Floor")
```

### Automation Control Tool

**List all automations:**
```python
automation_control(action="list")
```

**Response:**
```json
{
  "automations": [
    {
      "entity_id": "automation.morning_routine",
      "state": "on",
      "attributes": {
        "friendly_name": "Morning Routine",
        "last_triggered": "2024-01-15T07:00:00"
      }
    }
  ]
}
```

**Trigger an automation:**
```python
automation_control(
    action="trigger",
    automation_id="automation.morning_routine"
)
```

**Toggle an automation (enable/disable):**
```python
automation_control(
    action="toggle",
    automation_id="automation.night_mode"
)
```

### Scene Control Tool

**List all scenes:**
```python
scene_control(action="list")
```

**Activate a scene:**
```python
scene_control(
    action="activate",
    scene_id="scene.movie_mode"
)
```

### Notification Tool

**Simple notification:**
```python
send_notification(message="Dinner is ready!")
```

**Notification with title:**
```python
send_notification(
    message="The temperature is 75°F",
    title="Living Room Update"
)
```

**Targeted notification:**
```python
send_notification(
    message="The door is open",
    title="Security Alert",
    target="mobile_app_iphone"
)
```

### History Query Tool

**Get recent history:**
```python
query_history(entity_id="sensor.living_room_temperature")
```

**Get history for specific time range:**
```python
query_history(
    entity_id="sensor.living_room_temperature",
    start_time="2024-01-15T00:00:00",
    end_time="2024-01-15T23:59:59"
)
```

### Switch Control Tool

**List all switches:**
```python
switch_control(action="list")
```

**Response:**
```json
{
  "success": true,
  "count": 3,
  "switches": [
    {
      "entity_id": "switch.coffee_maker",
      "state": "off",
      "attributes": {
        "friendly_name": "Coffee Maker"
      }
    }
  ]
}
```

**Turn on a switch:**
```python
switch_control(
    action="turn_on",
    entity_id="switch.coffee_maker"
)
```

**Turn off a switch:**
```python
switch_control(
    action="turn_off",
    entity_id="switch.fan"
)
```

**Toggle a switch:**
```python
switch_control(
    action="toggle",
    entity_id="switch.christmas_lights"
)
```

**Get specific switch:**
```python
switch_control(
    action="get",
    entity_id="switch.coffee_maker"
)
```

### Media Player Control Tool

**List all media players:**
```python
media_player_control(action="list")
```

**Response:**
```json
{
  "success": true,
  "count": 2,
  "media_players": [
    {
      "entity_id": "media_player.living_room",
      "state": "playing",
      "attributes": {
        "volume_level": 0.5,
        "media_title": "Favorite Song",
        "media_artist": "Artist Name",
        "source": "Spotify",
        "source_list": ["Spotify", "Bluetooth", "HDMI 1"]
      }
    }
  ]
}
```

**Playback control:**
```python
# Play
media_player_control(
    action="play",
    entity_id="media_player.living_room"
)

# Pause
media_player_control(
    action="pause",
    entity_id="media_player.living_room"
)

# Stop
media_player_control(
    action="stop",
    entity_id="media_player.living_room"
)

# Toggle play/pause
media_player_control(
    action="toggle",
    entity_id="media_player.living_room"
)

# Next track
media_player_control(
    action="next_track",
    entity_id="media_player.living_room"
)

# Previous track
media_player_control(
    action="previous_track",
    entity_id="media_player.living_room"
)
```

**Volume control:**
```python
# Set volume (0.0 to 1.0)
media_player_control(
    action="set_volume",
    entity_id="media_player.living_room",
    volume_level=0.7
)

# Volume up
media_player_control(
    action="volume_up",
    entity_id="media_player.living_room"
)

# Volume down
media_player_control(
    action="volume_down",
    entity_id="media_player.living_room"
)

# Mute
media_player_control(
    action="mute",
    entity_id="media_player.living_room"
)

# Unmute
media_player_control(
    action="unmute",
    entity_id="media_player.living_room"
)
```

**Source selection:**
```python
media_player_control(
    action="select_source",
    entity_id="media_player.living_room",
    source="HDMI 1"
)
```

**Play media:**
```python
media_player_control(
    action="play_media",
    entity_id="media_player.living_room",
    media_content_id="spotify:playlist:37i9dQZF1DXcBWIGoYBM5M",
    media_content_type="playlist"
)
```

### Cover Control Tool

**List all covers:**
```python
cover_control(action="list")
```

**Response:**
```json
{
  "success": true,
  "count": 2,
  "covers": [
    {
      "entity_id": "cover.garage_door",
      "state": "closed",
      "attributes": {
        "current_position": 0,
        "friendly_name": "Garage Door"
      }
    },
    {
      "entity_id": "cover.bedroom_blinds",
      "state": "open",
      "attributes": {
        "current_position": 100,
        "current_tilt_position": 50,
        "friendly_name": "Bedroom Blinds"
      }
    }
  ]
}
```

**Basic operations:**
```python
# Open
cover_control(
    action="open",
    entity_id="cover.garage_door"
)

# Close
cover_control(
    action="close",
    entity_id="cover.bedroom_blinds"
)

# Stop
cover_control(
    action="stop",
    entity_id="cover.living_room_blinds"
)

# Toggle
cover_control(
    action="toggle",
    entity_id="cover.garage_door"
)
```

**Position control:**
```python
# Set position (0-100)
cover_control(
    action="set_position",
    entity_id="cover.bedroom_blinds",
    position=50
)
```

**Tilt control:**
```python
# Set tilt (0-100)
cover_control(
    action="set_tilt",
    entity_id="cover.bedroom_blinds",
    tilt=75
)
```

### Lock Control Tool

**List all locks:**
```python
lock_control(action="list")
```

**Response:**
```json
{
  "success": true,
  "count": 2,
  "locks": [
    {
      "entity_id": "lock.front_door",
      "state": "locked",
      "attributes": {
        "battery_level": 85,
        "friendly_name": "Front Door Lock"
      }
    }
  ]
}
```

**Lock operations:**
```python
# Lock
lock_control(
    action="lock",
    entity_id="lock.front_door"
)

# Unlock
lock_control(
    action="unlock",
    entity_id="lock.front_door"
)

# Unlock with code
lock_control(
    action="unlock",
    entity_id="lock.front_door",
    code="1234"
)
```

**Get lock details:**
```python
lock_control(
    action="get",
    entity_id="lock.front_door"
)
```

### Camera Control Tool

**List all cameras:**
```python
camera_control(action="list")
```

**Response:**
```json
{
  "success": true,
  "count": 3,
  "cameras": [
    {
      "entity_id": "camera.front_door",
      "state": "idle",
      "attributes": {
        "motion_detection": true,
        "friendly_name": "Front Door Camera"
      }
    }
  ]
}
```

**Take snapshot:**
```python
# Save to file
camera_control(
    action="snapshot",
    entity_id="camera.front_door",
    output_path="/tmp/front_door.jpg"
)

# Get base64 data
camera_control(
    action="snapshot",
    entity_id="camera.front_door"
)
```

**Motion detection:**
```python
# Enable
camera_control(
    action="enable_motion_detection",
    entity_id="camera.front_door"
)

# Disable
camera_control(
    action="disable_motion_detection",
    entity_id="camera.front_door"
)
```

**Get stream URL:**
```python
camera_control(
    action="get_stream_url",
    entity_id="camera.front_door"
)
```

### Vacuum Control Tool

**List all vacuums:**
```python
vacuum_control(action="list")
```

**Response:**
```json
{
  "success": true,
  "count": 1,
  "vacuums": [
    {
      "entity_id": "vacuum.robot_vacuum",
      "state": "docked",
      "attributes": {
        "battery_level": 100,
        "status": "Charging",
        "fan_speed": "standard",
        "friendly_name": "Robot Vacuum"
      }
    }
  ]
}
```

**Control operations:**
```python
# Start cleaning
vacuum_control(
    action="start",
    entity_id="vacuum.robot_vacuum"
)

# Pause
vacuum_control(
    action="pause",
    entity_id="vacuum.robot_vacuum"
)

# Stop
vacuum_control(
    action="stop",
    entity_id="vacuum.robot_vacuum"
)

# Return to base
vacuum_control(
    action="return_to_base",
    entity_id="vacuum.robot_vacuum"
)

# Locate (beep)
vacuum_control(
    action="locate",
    entity_id="vacuum.robot_vacuum"
)
```

**Set fan speed:**
```python
vacuum_control(
    action="set_fan_speed",
    entity_id="vacuum.robot_vacuum",
    fan_speed="max"
)
```

### Fan Control Tool

**List all fans:**
```python
fan_control(action="list")
```

**Response:**
```json
{
  "success": true,
  "count": 2,
  "fans": [
    {
      "entity_id": "fan.bedroom_fan",
      "state": "on",
      "attributes": {
        "percentage": 66,
        "preset_mode": "auto",
        "oscillating": true,
        "direction": "forward",
        "friendly_name": "Bedroom Fan"
      }
    }
  ]
}
```

**Basic operations:**
```python
# Turn on
fan_control(
    action="turn_on",
    entity_id="fan.bedroom_fan"
)

# Turn off
fan_control(
    action="turn_off",
    entity_id="fan.bedroom_fan"
)
```

**Speed control:**
```python
# Set percentage (0-100)
fan_control(
    action="set_percentage",
    entity_id="fan.bedroom_fan",
    percentage=75
)
```

**Preset modes:**
```python
fan_control(
    action="set_preset_mode",
    entity_id="fan.bedroom_fan",
    preset_mode="sleep"
)
```

**Oscillation:**
```python
# Enable oscillation
fan_control(
    action="oscillate",
    entity_id="fan.bedroom_fan",
    oscillating=True
)

# Disable oscillation
fan_control(
    action="oscillate",
    entity_id="fan.bedroom_fan",
    oscillating=False
)
```

**Direction:**
```python
fan_control(
    action="set_direction",
    entity_id="fan.bedroom_fan",
    direction="reverse"
)
```

### Script Control Tool

**List all scripts:**
```python
script_control(action="list")
```

**Response:**
```json
{
  "success": true,
  "count": 3,
  "scripts": [
    {
      "entity_id": "script.morning_routine",
      "state": "off",
      "attributes": {
        "friendly_name": "Morning Routine",
        "last_triggered": "2024-01-15T07:00:00"
      }
    }
  ]
}
```

**Execute script:**
```python
# Simple execution
script_control(
    action="execute",
    entity_id="script.morning_routine"
)

# With variables
script_control(
    action="execute",
    entity_id="script.notification",
    variables={
        "message": "Dinner is ready",
        "title": "Kitchen Alert"
    }
)
```

**Get script details:**
```python
script_control(
    action="get",
    entity_id="script.morning_routine"
)
```

**Reload scripts:**
```python
script_control(action="reload")
```

### Input Helper Tools

**Input Boolean:**
```python
# List
input_boolean_control(action="list")

# Turn on
input_boolean_control(
    action="turn_on",
    entity_id="input_boolean.guest_mode"
)

# Turn off
input_boolean_control(
    action="turn_off",
    entity_id="input_boolean.vacation_mode"
)

# Toggle
input_boolean_control(
    action="toggle",
    entity_id="input_boolean.sleep_mode"
)
```

**Input Number:**
```python
# List
input_number_control(action="list")

# Set value
input_number_control(
    action="set_value",
    entity_id="input_number.temperature_offset",
    value=2.5
)

# Increment
input_number_control(
    action="increment",
    entity_id="input_number.brightness_level"
)

# Decrement
input_number_control(
    action="decrement",
    entity_id="input_number.volume_level"
)
```

**Input Select:**
```python
# List
input_select_control(action="list")

# Select option
input_select_control(
    action="select_option",
    entity_id="input_select.house_mode",
    option="Home"
)
```

**Input Text:**
```python
# List
input_text_control(action="list")

# Set value
input_text_control(
    action="set_value",
    entity_id="input_text.welcome_message",
    value="Hello, World!"
)
```

**Input DateTime:**
```python
# List
input_datetime_control(action="list")

# Set datetime
input_datetime_control(
    action="set_datetime",
    entity_id="input_datetime.alarm_time",
    datetime="2024-01-15T07:00:00"
)
```

### Weather Tool

**List all weather entities:**
```python
weather_control(action="list")
```

**Response:**
```json
{
  "success": true,
  "count": 1,
  "weather_entities": [
    {
      "entity_id": "weather.home",
      "state": "sunny",
      "attributes": {
        "temperature": 72,
        "humidity": 45,
        "pressure": 1013,
        "wind_speed": 5,
        "friendly_name": "Home Weather"
      }
    }
  ]
}
```

**Get current conditions:**
```python
weather_control(
    action="get",
    entity_id="weather.home"
)
```

**Get forecast:**
```python
# Daily forecast
weather_control(
    action="get_forecast",
    entity_id="weather.home",
    forecast_type="daily"
)

# Hourly forecast
weather_control(
    action="get_forecast",
    entity_id="weather.home",
    forecast_type="hourly"
)
```

### Alarm Control Panel Tool

**List all alarm panels:**
```python
alarm_control(action="list")
```

**Response:**
```json
{
  "success": true,
  "count": 1,
  "alarm_panels": [
    {
      "entity_id": "alarm_control_panel.home",
      "state": "disarmed",
      "attributes": {
        "code_arm_required": false,
        "friendly_name": "Home Alarm"
      }
    }
  ]
}
```

**Arm the alarm:**
```python
# Arm away
alarm_control(
    action="arm_away",
    entity_id="alarm_control_panel.home"
)

# Arm home
alarm_control(
    action="arm_home",
    entity_id="alarm_control_panel.home"
)

# Arm night
alarm_control(
    action="arm_night",
    entity_id="alarm_control_panel.home"
)
```

**Disarm:**
```python
alarm_control(
    action="disarm",
    entity_id="alarm_control_panel.home",
    code="1234"
)
```

**Trigger:**
```python
alarm_control(
    action="trigger",
    entity_id="alarm_control_panel.home"
)
```

### Specialized Domain Tools

**Water Heater:**
```python
# List
water_heater_control(action="list")

# Set temperature
water_heater_control(
    action="set_temperature",
    entity_id="water_heater.main",
    temperature=120
)

# Set operation mode
water_heater_control(
    action="set_operation_mode",
    entity_id="water_heater.main",
    operation_mode="eco"
)
```

**Humidifier:**
```python
# List
humidifier_control(action="list")

# Turn on
humidifier_control(
    action="turn_on",
    entity_id="humidifier.bedroom"
)

# Set humidity
humidifier_control(
    action="set_humidity",
    entity_id="humidifier.bedroom",
    humidity=60
)

# Set mode
humidifier_control(
    action="set_mode",
    entity_id="humidifier.bedroom",
    mode="auto"
)
```

**Siren:**
```python
# List
siren_control(action="list")

# Turn on
siren_control(
    action="turn_on",
    entity_id="siren.alarm"
)

# Turn on with options
siren_control(
    action="turn_on",
    entity_id="siren.alarm",
    tone="emergency",
    volume_level=0.8,
    duration=30
)

# Turn off
siren_control(
    action="turn_off",
    entity_id="siren.alarm"
)
```

**Valve:**
```python
# List
valve_control(action="list")

# Open
valve_control(
    action="open",
    entity_id="valve.water_main"
)

# Close
valve_control(
    action="close",
    entity_id="valve.irrigation"
)

# Set position
valve_control(
    action="set_position",
    entity_id="valve.water_main",
    position=50
)
```

**Lawn Mower:**
```python
# List
lawn_mower_control(action="list")

# Start
lawn_mower_control(
    action="start",
    entity_id="lawn_mower.robot_mower"
)

# Pause
lawn_mower_control(
    action="pause",
    entity_id="lawn_mower.robot_mower"
)

# Return to dock
lawn_mower_control(
    action="dock",
    entity_id="lawn_mower.robot_mower"
)
```

### Generic Control Tool

**Call any service:**
```python
call_service(
    domain="switch",
    service="turn_on",
    entity_id="switch.coffee_maker"
)
```

**With service data:**
```python
call_service(
    domain="notify",
    service="mobile_app",
    data={
        "message": "Hello from Home Assistant",
        "title": "Notification"
    }
)
```

### Automation Configuration Tool

**Get automation configuration:**
```python
get_automation_config(automation_id="automation.morning_routine")
```

**Response:**
```json
{
  "automation_id": "automation.morning_routine",
  "config": {
    "alias": "Morning Routine",
    "trigger": [
      {
        "platform": "time",
        "at": "07:00:00"
      }
    ],
    "action": [
      {
        "service": "light.turn_on",
        "target": {
          "entity_id": "light.bedroom"
        }
      }
    ]
  }
}
```

### Configuration Management Tools

**Note:** Configuration management tools require the `HA_CONFIG_PATH` environment variable to be set to your Home Assistant configuration directory.

#### Config Control Tool

**List configuration files:**
```python
config_control(action="list_files")
```

**Response:**
```json
{
  "success": true,
  "files": [
    "configuration.yaml",
    "automations.yaml",
    "scripts.yaml",
    "scenes.yaml",
    "groups.yaml"
  ]
}
```

**Read configuration file:**
```python
config_control(
    action="read_file",
    filename="automations.yaml"
)
```

**Response:**
```json
{
  "success": true,
  "filename": "automations.yaml",
  "content": "- id: '1234567890'\n  alias: Morning Routine\n  trigger:\n  - platform: time\n    at: '07:00:00'\n  action:\n  - service: light.turn_on\n    target:\n      entity_id: light.bedroom"
}
```

**Write configuration file:**
```python
# Automatically creates backup before writing
config_control(
    action="write_file",
    filename="scripts.yaml",
    content="""
test_script:
  alias: Test Script
  sequence:
    - service: light.turn_on
      target:
        entity_id: light.living_room
"""
)
```

**Response:**
```json
{
  "success": true,
  "message": "File written successfully",
  "backup_created": "scripts.yaml.backup.20240115_143022"
}
```

**Create backup:**
```python
config_control(
    action="backup_file",
    filename="automations.yaml"
)
```

**Response:**
```json
{
  "success": true,
  "backup_file": "automations.yaml.backup.20240115_143022"
}
```

**Restore from backup:**
```python
config_control(
    action="restore_file",
    filename="automations.yaml",
    backup_timestamp="20240115_143022"
)
```

**Validate configuration:**
```python
config_control(action="validate_config")
```

**Response:**
```json
{
  "success": true,
  "valid": true,
  "errors": []
}
```

**Reload configuration:**
```python
config_control(action="reload_config")
```

#### Config Sync Tool

**Copy configuration to Home Assistant:**
```python
config_sync_control(
    action="copy_to_target",
    source_path="/path/to/my/config",
    files=["automations.yaml", "scripts.yaml"],
    confirm=True
)
```

**Response:**
```json
{
  "success": true,
  "files_copied": 2,
  "backups_created": 2,
  "summary": {
    "copied": ["automations.yaml", "scripts.yaml"],
    "backed_up": [
      "automations.yaml.backup.20240115_143022",
      "scripts.yaml.backup.20240115_143022"
    ],
    "errors": []
  }
}
```

**Copy configuration from Home Assistant:**
```python
config_sync_control(
    action="copy_from_target",
    destination_path="/path/to/backup",
    files=["automations.yaml", "scripts.yaml"]
)
```

**Show differences:**
```python
config_sync_control(
    action="diff",
    source_path="/path/to/my/config",
    filename="automations.yaml"
)
```

**Response:**
```json
{
  "success": true,
  "has_differences": true,
  "diff": "--- source\n+++ target\n@@ -1,3 +1,4 @@\n - id: '1234567890'\n   alias: Morning Routine\n+  description: 'Wake up routine'\n   trigger:"
}
```

**List backups:**
```python
config_sync_control(action="list_backups")
```

**Response:**
```json
{
  "success": true,
  "backups": [
    {
      "filename": "automations.yaml.backup.20240115_143022",
      "original": "automations.yaml",
      "timestamp": "2024-01-15T14:30:22",
      "size": 2048
    },
    {
      "filename": "scripts.yaml.backup.20240115_120000",
      "original": "scripts.yaml",
      "timestamp": "2024-01-15T12:00:00",
      "size": 1024
    }
  ]
}
```

#### Automation Editor Tool

**List all automations:**
```python
automation_editor_control(action="list")
```

**Response:**
```json
{
  "success": true,
  "count": 3,
  "automations": [
    {
      "id": "1234567890",
      "alias": "Morning Routine",
      "description": "Wake up routine",
      "enabled": true
    },
    {
      "id": "0987654321",
      "alias": "Night Mode",
      "description": "Bedtime routine",
      "enabled": true
    }
  ]
}
```

**Get automation details:**
```python
automation_editor_control(
    action="get",
    automation_id="1234567890"
)
```

**Response:**
```json
{
  "success": true,
  "automation": {
    "id": "1234567890",
    "alias": "Morning Routine",
    "description": "Wake up routine",
    "trigger": [
      {
        "platform": "time",
        "at": "07:00:00"
      }
    ],
    "condition": [],
    "action": [
      {
        "service": "light.turn_on",
        "target": {
          "entity_id": "light.bedroom"
        },
        "data": {
          "brightness": 128
        }
      }
    ],
    "mode": "single"
  }
}
```

**Create new automation:**
```python
automation_editor_control(
    action="create",
    automation_config={
        "alias": "Test Automation",
        "description": "A test automation",
        "trigger": [
            {
                "platform": "state",
                "entity_id": "binary_sensor.motion",
                "to": "on"
            }
        ],
        "action": [
            {
                "service": "light.turn_on",
                "target": {
                    "entity_id": "light.hallway"
                }
            }
        ]
    }
)
```

**Response:**
```json
{
  "success": true,
  "message": "Automation created successfully",
  "automation_id": "1234567891",
  "backup_created": "automations.yaml.backup.20240115_143022"
}
```

**Update existing automation:**
```python
automation_editor_control(
    action="update",
    automation_id="1234567890",
    automation_config={
        "alias": "Morning Routine Updated",
        "description": "Updated wake up routine",
        "trigger": [
            {
                "platform": "time",
                "at": "06:30:00"  # Changed time
            }
        ],
        "action": [
            {
                "service": "light.turn_on",
                "target": {
                    "entity_id": "light.bedroom"
                },
                "data": {
                    "brightness": 200  # Increased brightness
                }
            }
        ]
    }
)
```

**Delete automation:**
```python
automation_editor_control(
    action="delete",
    automation_id="1234567890"
)
```

**Response:**
```json
{
  "success": true,
  "message": "Automation deleted successfully",
  "backup_created": "automations.yaml.backup.20240115_143022"
}
```

**Enable/Disable automation:**
```python
# Disable
automation_editor_control(
    action="disable",
    automation_id="1234567890"
)

# Enable
automation_editor_control(
    action="enable",
    automation_id="1234567890"
)
```

---

## Advanced Scenarios

### Multi-Step Workflows

These examples demonstrate complex workflows that combine multiple tools and domains to achieve sophisticated automation goals.

#### Complete Home Automation Workflow

**Scenario:** Create a comprehensive "Good Night" routine that secures the home, adjusts climate, and prepares for sleep.

**Steps:**
1. **Security Check** - Verify all doors and windows
2. **Lighting** - Turn off all lights except bedroom (dim to 20%)
3. **Climate** - Set thermostats to night mode (68°F)
4. **Covers** - Close all blinds and shades
5. **Locks** - Lock all doors
6. **Alarm** - Arm in night mode
7. **Media** - Turn off all media players
8. **Notification** - Confirm routine completion

**Implementation:**
```python
async def good_night_routine():
    results = {
        "security_check": None,
        "lighting": None,
        "climate": None,
        "covers": None,
        "locks": None,
        "alarm": None,
        "media": None,
        "notification": None
    }
    
    # Step 1: Security Check
    print("Checking security...")
    doors = list_devices(domain="binary_sensor")
    open_doors = [d for d in doors.get("devices", []) 
                  if "door" in d["entity_id"].lower() and d["state"] == "on"]
    
    if open_doors:
        results["security_check"] = f"Warning: {len(open_doors)} doors open"
        send_notification(
            message=f"{len(open_doors)} doors are still open",
            title="Security Warning"
        )
    else:
        results["security_check"] = "All doors closed"
    
    # Step 2: Lighting
    print("Adjusting lights...")
    lights = lights_control(action="list")
    for light in lights.get("lights", []):
        if "bedroom" in light["entity_id"]:
            lights_control(
                action="turn_on",
                entity_id=light["entity_id"],
                brightness=51  # 20%
            )
        else:
            lights_control(action="turn_off", entity_id=light["entity_id"])
    results["lighting"] = "Lights adjusted"
    
    # Step 3: Climate
    print("Setting climate...")
    climates = climate_control(action="list")
    for climate in climates.get("climate_devices", []):
        climate_control(
            action="set_temperature",
            entity_id=climate["entity_id"],
            temperature=68.0
        )
    results["climate"] = "Climate set to 68°F"
    
    # Step 4: Covers
    print("Closing covers...")
    covers = cover_control(action="list")
    for cover in covers.get("covers", []):
        cover_control(action="close", entity_id=cover["entity_id"])
    results["covers"] = "All covers closed"
    
    # Step 5: Locks
    print("Locking doors...")
    locks = lock_control(action="list")
    for lock in locks.get("locks", []):
        lock_control(action="lock", entity_id=lock["entity_id"])
    results["locks"] = "All doors locked"
    
    # Step 6: Alarm
    print("Arming alarm...")
    alarm_control(
        action="arm_night",
        entity_id="alarm_control_panel.home"
    )
    results["alarm"] = "Alarm armed (night mode)"
    
    # Step 7: Media
    print("Turning off media...")
    media_players = media_player_control(action="list")
    for player in media_players.get("media_players", []):
        media_player_control(action="stop", entity_id=player["entity_id"])
    results["media"] = "All media stopped"
    
    # Step 8: Notification
    summary = "\n".join([f"{k}: {v}" for k, v in results.items()])
    send_notification(
        message=f"Good night routine complete\n{summary}",
        title="Good Night"
    )
    results["notification"] = "Notification sent"
    
    return results
```

#### Weather-Responsive Automation

**Scenario:** Automatically adjust home settings based on weather forecast.

**Implementation:**
```python
def weather_responsive_automation():
    # Get weather forecast
    forecast = weather_control(
        action="get_forecast",
        entity_id="weather.home",
        forecast_type="daily"
    )
    
    today = forecast.get("forecast", [{}])[0]
    condition = today.get("condition")
    temp_high = today.get("temperature")
    precipitation = today.get("precipitation_probability", 0)
    
    actions_taken = []
    
    # Hot day - close blinds, increase AC
    if temp_high > 85:
        print("Hot day detected - closing blinds and cooling")
        
        # Close south-facing blinds
        covers = cover_control(action="list")
        for cover in covers.get("covers", []):
            if "south" in cover["entity_id"].lower():
                cover_control(action="close", entity_id=cover["entity_id"])
        
        # Set AC to cool mode
        climates = climate_control(action="list")
        for climate in climates.get("climate_devices", []):
            climate_control(
                action="set_hvac_mode",
                entity_id=climate["entity_id"],
                hvac_mode="cool"
            )
            climate_control(
                action="set_temperature",
                entity_id=climate["entity_id"],
                temperature=72.0
            )
        
        actions_taken.append("Closed blinds and set AC to 72°F")
    
    # Rain expected - close outdoor covers
    if precipitation > 50:
        print("Rain expected - securing outdoor areas")
        
        covers = cover_control(action="list")
        for cover in covers.get("covers", []):
            if "outdoor" in cover["entity_id"].lower() or "patio" in cover["entity_id"].lower():
                cover_control(action="close", entity_id=cover["entity_id"])
        
        # Turn on outdoor lights for visibility
        lights = lights_control(action="list")
        for light in lights.get("lights", []):
            if "outdoor" in light["entity_id"].lower():
                lights_control(
                    action="turn_on",
                    entity_id=light["entity_id"],
                    brightness=255
                )
        
        actions_taken.append("Closed outdoor covers and turned on outdoor lights")
    
    # Cold day - set heat mode
    if temp_high < 50:
        print("Cold day detected - setting heat mode")
        
        climates = climate_control(action="list")
        for climate in climates.get("climate_devices", []):
            climate_control(
                action="set_hvac_mode",
                entity_id=climate["entity_id"],
                hvac_mode="heat"
            )
            climate_control(
                action="set_temperature",
                entity_id=climate["entity_id"],
                temperature=70.0
            )
        
        actions_taken.append("Set heating to 70°F")
    
    # Send summary
    if actions_taken:
        send_notification(
            message=f"Weather: {condition}, High: {temp_high}°F\n" + 
                   "\n".join(actions_taken),
            title="Weather Automation"
        )
    
    return actions_taken
```

#### Presence-Based Automation

**Scenario:** Adjust home settings based on who is home.

**Implementation:**
```python
def presence_based_automation():
    # Check who is home (using input_select for demo)
    presence = input_select_control(
        action="get",
        entity_id="input_select.home_mode"
    )
    
    mode = presence.get("state")
    
    if mode == "Home":
        print("Someone is home - normal mode")
        
        # Normal temperature
        climates = climate_control(action="list")
        for climate in climates.get("climate_devices", []):
            climate_control(
                action="set_temperature",
                entity_id=climate["entity_id"],
                temperature=72.0
            )
        
        # Disarm alarm
        alarm_control(
            action="disarm",
            entity_id="alarm_control_panel.home",
            code="1234"
        )
        
        # Normal lighting
        scene_control(action="activate", scene_id="scene.home")
        
    elif mode == "Away":
        print("Nobody home - away mode")
        
        # Energy saving temperature
        climates = climate_control(action="list")
        for climate in climates.get("climate_devices", []):
            climate_control(
                action="set_temperature",
                entity_id=climate["entity_id"],
                temperature=68.0
            )
        
        # Turn off most lights
        lights = lights_control(action="list")
        for light in lights.get("lights", []):
            if "outdoor" not in light["entity_id"].lower():
                lights_control(action="turn_off", entity_id=light["entity_id"])
        
        # Arm alarm
        alarm_control(
            action="arm_away",
            entity_id="alarm_control_panel.home"
        )
        
        # Start vacuum
        vacuum_control(action="start", entity_id="vacuum.robot_vacuum")
        
    elif mode == "Sleep":
        print("Sleep mode")
        
        # Night temperature
        climates = climate_control(action="list")
        for climate in climates.get("climate_devices", []):
            climate_control(
                action="set_temperature",
                entity_id=climate["entity_id"],
                temperature=68.0
            )
        
        # Turn off all lights except bedroom (dim)
        lights = lights_control(action="list")
        for light in lights.get("lights", []):
            if "bedroom" in light["entity_id"].lower():
                lights_control(
                    action="turn_on",
                    entity_id=light["entity_id"],
                    brightness=25
                )
            else:
                lights_control(action="turn_off", entity_id=light["entity_id"])
        
        # Arm alarm in night mode
        alarm_control(
            action="arm_night",
            entity_id="alarm_control_panel.home"
        )
```

### Morning Routine

**Natural Language:**
"Execute my morning routine: turn on the bedroom lights to 50%, set the thermostat to 72°F, and open the blinds"

**AI will execute:**
1. `lights_control(action="turn_on", entity_id="light.bedroom", brightness=128)`
2. `climate_control(action="set_temperature", entity_id="climate.bedroom", temperature=72.0)`
3. `call_service(domain="cover", service="open_cover", entity_id="cover.bedroom_blinds")`

### Movie Time

**Natural Language:**
"Set up movie mode: dim the living room lights to 10%, turn off the kitchen lights, and activate the movie scene"

**AI will execute:**
1. `lights_control(action="turn_on", entity_id="light.living_room", brightness=25)`
2. `lights_control(action="turn_off", entity_id="light.kitchen")`
3. `scene_control(action="activate", scene_id="scene.movie_mode")`

### Bedtime Routine

**Natural Language:**
"Prepare for bed: turn off all downstairs lights, lock the doors, set the bedroom lights to 20% warm white, and set the thermostat to 68°F"

**AI will execute:**
1. `lights_control(action="turn_off", entity_id="light.living_room")`
2. `lights_control(action="turn_off", entity_id="light.kitchen")`
3. `call_service(domain="lock", service="lock", entity_id="lock.front_door")`
4. `call_service(domain="lock", service="lock", entity_id="lock.back_door")`
5. `lights_control(action="turn_on", entity_id="light.bedroom", brightness=51, color_temp=400)`
6. `climate_control(action="set_temperature", entity_id="climate.bedroom", temperature=68.0)`

### Energy Saving Mode

**Natural Language:**
"Enable energy saving: turn off all lights except the living room, set the thermostat to 68°F, and turn off all media players"

**AI will execute:**
1. `list_devices(domain="light")` (to get all lights)
2. Multiple `lights_control(action="turn_off", ...)` calls (except living room)
3. `climate_control(action="set_temperature", entity_id="climate.living_room", temperature=68.0)`
4. `list_devices(domain="media_player")` (to get all media players)
5. Multiple `call_service(domain="media_player", service="turn_off", ...)` calls

### Security Check

**Natural Language:**
"Run a security check: tell me if any doors or windows are open, if any lights are on, and if the garage door is closed"

**AI will execute:**
1. `list_devices(domain="binary_sensor")` (to get door/window sensors)
2. `list_devices(domain="light")` (to check light states)
3. `call_service(domain="cover", service="get_state", entity_id="cover.garage_door")`
4. Return a summary of the security status

### Temperature Monitoring

**Natural Language:**
"What's the temperature in each room, and adjust the thermostats to keep all rooms at 72°F"

**AI will execute:**
1. `list_devices(domain="sensor")` (to find temperature sensors)
2. Multiple `query_history(entity_id="sensor.xxx_temperature")` calls
3. Multiple `climate_control(action="set_temperature", ..., temperature=72.0)` calls

### Party Mode

**Natural Language:**
"Set up for a party: turn all lights to 100% brightness with colorful colors, turn on the outdoor lights, and set the music volume to 70%"

**AI will execute:**
1. `list_devices(domain="light")` (to get all lights)
2. Multiple `lights_control(action="turn_on", ..., brightness=255, rgb_color=(r, g, b))` calls with different colors
3. `lights_control(action="turn_on", entity_id="light.outdoor", brightness=255)`
4. `media_player_control(action="set_volume", entity_id="media_player.living_room", volume_level=0.7)`

### Vacation Mode

**Natural Language:**
"Enable vacation mode: lock all doors, close all covers, turn off all lights except outdoor, set thermostat to 65°F, and arm the alarm"

**AI will execute:**
1. `list_devices(domain="lock")` → Multiple `lock_control(action="lock", ...)` calls
2. `list_devices(domain="cover")` → Multiple `cover_control(action="close", ...)` calls
3. `list_devices(domain="light")` → Turn off indoor lights, keep outdoor on
4. `climate_control(action="set_temperature", ..., temperature=65.0)`
5. `alarm_control(action="arm_away", entity_id="alarm_control_panel.home")`

### Cleaning Day

**Natural Language:**
"Start cleaning: open all blinds, turn on all lights, start the vacuum, and play upbeat music"

**AI will execute:**
1. `list_devices(domain="cover")` → Multiple `cover_control(action="open", ...)` calls
2. `list_devices(domain="light")` → Multiple `lights_control(action="turn_on", ...)` calls
3. `vacuum_control(action="start", entity_id="vacuum.robot_vacuum")`
4. `media_player_control(action="play_media", ..., media_content_id="spotify:playlist:...", media_content_type="playlist")`

### Weather-Based Automation

**Natural Language:**
"If it's going to rain today, close all outdoor covers and send me a notification"

**AI will execute:**
1. `weather_control(action="get_forecast", entity_id="weather.home", forecast_type="daily")`
2. Check forecast for rain
3. If rain predicted:
   - `list_devices(domain="cover", area="Outdoor")`
   - Multiple `cover_control(action="close", ...)` calls
   - `send_notification(message="Closing outdoor covers due to rain forecast", title="Weather Alert")`

### Smart Wake-Up

**Natural Language:**
"Set up my wake-up routine: gradually increase bedroom lights over 10 minutes, start the coffee maker, open the blinds, and play morning news"

**AI will execute:**
1. Create automation or script with:
   - `lights_control(action="turn_on", entity_id="light.bedroom", brightness=25)` (start dim)
   - Gradual brightness increases
   - `switch_control(action="turn_on", entity_id="switch.coffee_maker")`
   - `cover_control(action="open", entity_id="cover.bedroom_blinds")`
   - `media_player_control(action="play_media", ..., media_content_id="news_station")`

### Home Theater Setup

**Natural Language:**
"Prepare for movie night: close living room blinds, dim lights to 10%, turn on the TV, switch to HDMI 1, and set volume to 40%"

**AI will execute:**
1. `cover_control(action="close", entity_id="cover.living_room_blinds")`
2. `lights_control(action="turn_on", entity_id="light.living_room", brightness=25)`
3. `media_player_control(action="turn_on", entity_id="media_player.tv")`
4. `media_player_control(action="select_source", entity_id="media_player.tv", source="HDMI 1")`
5. `media_player_control(action="set_volume", entity_id="media_player.tv", volume_level=0.4)`

### Arrival Home

**Natural Language:**
"I'm arriving home: unlock the front door, turn on entry lights, open the garage door, set thermostat to 72°F, and disarm the alarm"

**AI will execute:**
1. `lock_control(action="unlock", entity_id="lock.front_door")`
2. `lights_control(action="turn_on", entity_id="light.entry")`
3. `cover_control(action="open", entity_id="cover.garage_door")`
4. `climate_control(action="set_temperature", entity_id="climate.main", temperature=72.0)`
5. `alarm_control(action="disarm", entity_id="alarm_control_panel.home", code="1234")`

### Leaving Home

**Natural Language:**
"I'm leaving: turn off all lights, lock all doors, close the garage, set thermostat to 68°F, arm the alarm, and start the vacuum"

**AI will execute:**
1. `list_devices(domain="light")` → Multiple `lights_control(action="turn_off", ...)` calls
2. `list_devices(domain="lock")` → Multiple `lock_control(action="lock", ...)` calls
3. `cover_control(action="close", entity_id="cover.garage_door")`
4. `climate_control(action="set_temperature", entity_id="climate.main", temperature=68.0)`
5. `alarm_control(action="arm_away", entity_id="alarm_control_panel.home")`
6. `vacuum_control(action="start", entity_id="vacuum.robot_vacuum")`

### Guest Mode

**Natural Language:**
"Enable guest mode: turn on guest room lights to 75%, set guest bathroom fan to low, unlock guest entrance, and send notification to my phone"

**AI will execute:**
1. `lights_control(action="turn_on", entity_id="light.guest_room", brightness=191)`
2. `fan_control(action="turn_on", entity_id="fan.guest_bathroom")`
3. `fan_control(action="set_percentage", entity_id="fan.guest_bathroom", percentage=33)`
4. `lock_control(action="unlock", entity_id="lock.guest_entrance")`
5. `send_notification(message="Guest mode enabled", title="Home Status", target="mobile_app_phone")`

### Seasonal Adjustments

**Natural Language:**
"Switch to winter mode: reverse all ceiling fans, set thermostats to heat mode at 70°F, and close all outdoor vents"

**AI will execute:**
1. `list_devices(domain="fan")` → Multiple `fan_control(action="set_direction", ..., direction="reverse")` calls
2. `list_devices(domain="climate")` → Multiple `climate_control(action="set_hvac_mode", ..., hvac_mode="heat")` calls
3. `list_devices(domain="climate")` → Multiple `climate_control(action="set_temperature", ..., temperature=70.0)` calls
4. `list_devices(domain="cover", area="Outdoor")` → Multiple `cover_control(action="close", ...)` calls

### Emergency Response

**Natural Language:**
"Emergency mode: turn on all lights, unlock all doors, open garage, sound the siren, and send emergency notification"

**AI will execute:**
1. `list_devices(domain="light")` → Multiple `lights_control(action="turn_on", ..., brightness=255)` calls
2. `list_devices(domain="lock")` → Multiple `lock_control(action="unlock", ...)` calls
3. `cover_control(action="open", entity_id="cover.garage_door")`
4. `siren_control(action="turn_on", entity_id="siren.alarm")`
5. `send_notification(message="Emergency mode activated!", title="EMERGENCY", target="all")`

---

## Error Handling Patterns

### Handling Entity Not Found Errors

**Problem:** Entity doesn't exist or has wrong ID

**Example:**
```python
result = lights_control(action="turn_on", entity_id="light.living_room")

if not result.get("success"):
    if result.get("error_type") == "entity_not_found":
        # List available lights to find correct entity_id
        available = lights_control(action="list")
        print("Available lights:", available.get("lights"))
```

**Best Practice:**
```python
# Always verify entity exists before controlling
def safe_light_control(entity_id, action, **kwargs):
    # First, check if entity exists
    result = lights_control(action="get", entity_id=entity_id)
    
    if not result.get("success"):
        print(f"Entity {entity_id} not found")
        return None
    
    # Entity exists, proceed with action
    return lights_control(action=action, entity_id=entity_id, **kwargs)
```

### Handling Service Call Failures

**Problem:** Service call fails due to device being offline or unsupported action

**Example:**
```python
result = switch_control(action="turn_on", entity_id="switch.coffee_maker")

if not result.get("success"):
    error_type = result.get("error_type")
    error_msg = result.get("error")
    
    if error_type == "service_call_error":
        print(f"Service call failed: {error_msg}")
        # Check device status
        status = switch_control(action="get", entity_id="switch.coffee_maker")
        print(f"Device state: {status}")
```

**Best Practice:**
```python
# Implement retry logic with exponential backoff
import time

def retry_service_call(func, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        result = func(**kwargs)
        
        if result.get("success"):
            return result
        
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"Retry {attempt + 1}/{max_retries} in {wait_time}s...")
            time.sleep(wait_time)
    
    return result  # Return last failed result
```

### Handling Authentication Errors

**Problem:** Invalid or expired token

**Example:**
```python
result = lights_control(action="list")

if not result.get("success"):
    if result.get("error_type") == "authentication_error":
        print("Authentication failed. Please check your HASS_TOKEN")
        print("Generate a new token at: http://homeassistant.local:8123/profile")
```

**Best Practice:**
```python
# Validate connection before performing operations
def validate_connection():
    result = list_devices()
    
    if not result.get("success"):
        error_type = result.get("error_type")
        
        if error_type == "authentication_error":
            raise Exception("Invalid Home Assistant token")
        elif error_type == "connection_error":
            raise Exception("Cannot connect to Home Assistant")
    
    return True

# Use at startup
try:
    validate_connection()
    print("Connected to Home Assistant successfully")
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)
```

### Handling Connection Errors

**Problem:** Cannot reach Home Assistant instance

**Example:**
```python
result = climate_control(action="list")

if not result.get("success"):
    if result.get("error_type") == "connection_error":
        print("Cannot connect to Home Assistant")
        print("Check HASS_HOST setting and network connectivity")
```

**Best Practice:**
```python
# Implement connection health check
def check_ha_health():
    try:
        result = list_devices()
        return result.get("success", False)
    except Exception:
        return False

# Use before critical operations
if not check_ha_health():
    print("Home Assistant is not reachable")
    # Implement fallback behavior or alert user
```

### Handling Validation Errors

**Problem:** Invalid parameter values

**Example:**
```python
# Brightness must be 0-255
result = lights_control(
    action="turn_on",
    entity_id="light.bedroom",
    brightness=500  # Invalid!
)

if not result.get("success"):
    if result.get("error_type") == "validation_error":
        print(f"Invalid parameter: {result.get('error')}")
```

**Best Practice:**
```python
# Validate parameters before calling
def safe_set_brightness(entity_id, brightness_percent):
    # Convert percentage to 0-255 range
    brightness = max(0, min(255, int(brightness_percent * 2.55)))
    
    return lights_control(
        action="turn_on",
        entity_id=entity_id,
        brightness=brightness
    )

# Usage
safe_set_brightness("light.bedroom", 50)  # 50% brightness
```

### Handling Configuration File Errors

**Problem:** YAML syntax errors or invalid configuration

**Example:**
```python
# Writing invalid YAML
result = config_control(
    action="write_file",
    filename="automations.yaml",
    content="invalid: yaml: content:"
)

if not result.get("success"):
    if "yaml" in result.get("error", "").lower():
        print("YAML syntax error detected")
        print(f"Error: {result.get('error')}")
        
        # Restore from backup
        backups = config_sync_control(action="list_backups")
        latest_backup = backups.get("backups", [{}])[0]
        
        if latest_backup:
            config_control(
                action="restore_file",
                filename="automations.yaml",
                backup_timestamp=latest_backup.get("timestamp")
            )
            print("Restored from backup")
```

**Best Practice:**
```python
import yaml

def safe_config_write(filename, content):
    """
    Safely write configuration with validation and automatic rollback.
    """
    # Step 1: Validate YAML syntax
    try:
        yaml.safe_load(content)
    except yaml.YAMLError as e:
        return {
            "success": False,
            "error": f"YAML syntax error: {str(e)}",
            "error_type": "validation_error"
        }
    
    # Step 2: Create backup
    backup_result = config_control(
        action="backup_file",
        filename=filename
    )
    
    if not backup_result.get("success"):
        return {
            "success": False,
            "error": "Failed to create backup",
            "error_type": "backup_error"
        }
    
    backup_file = backup_result.get("backup_file")
    
    # Step 3: Write file
    write_result = config_control(
        action="write_file",
        filename=filename,
        content=content
    )
    
    if not write_result.get("success"):
        return write_result
    
    # Step 4: Validate configuration
    validate_result = config_control(action="validate_config")
    
    if not validate_result.get("valid"):
        # Rollback on validation failure
        print("Configuration invalid, rolling back...")
        
        timestamp = backup_file.split(".")[-1]
        config_control(
            action="restore_file",
            filename=filename,
            backup_timestamp=timestamp
        )
        
        return {
            "success": False,
            "error": "Configuration validation failed",
            "validation_errors": validate_result.get("errors"),
            "error_type": "validation_error",
            "rolled_back": True
        }
    
    return {
        "success": True,
        "message": "Configuration updated successfully",
        "backup_created": backup_file
    }

# Usage
result = safe_config_write(
    "automations.yaml",
    """
- id: '1234567890'
  alias: Test Automation
  trigger:
    - platform: state
      entity_id: binary_sensor.motion
      to: 'on'
  action:
    - service: light.turn_on
      target:
        entity_id: light.hallway
"""
)

if result.get("success"):
    print("Configuration updated successfully")
else:
    print(f"Failed: {result.get('error')}")
    if result.get("rolled_back"):
        print("Changes were rolled back")
```

### Handling Automation Editor Errors

**Problem:** Automation ID not found or invalid structure

**Example:**
```python
# Try to update non-existent automation
result = automation_editor_control(
    action="update",
    automation_id="nonexistent_id",
    automation_config={"alias": "Test"}
)

if not result.get("success"):
    if "not found" in result.get("error", "").lower():
        print("Automation does not exist")
        
        # List available automations
        automations = automation_editor_control(action="list")
        print("Available automations:")
        for auto in automations.get("automations", []):
            print(f"  - {auto.get('id')}: {auto.get('alias')}")
```

**Best Practice:**
```python
def safe_automation_update(automation_id, new_config):
    """
    Safely update automation with existence check and validation.
    """
    # Step 1: Check if automation exists
    get_result = automation_editor_control(
        action="get",
        automation_id=automation_id
    )
    
    if not get_result.get("success"):
        return {
            "success": False,
            "error": f"Automation {automation_id} not found",
            "error_type": "not_found"
        }
    
    # Step 2: Validate new configuration structure
    required_fields = ["alias", "trigger", "action"]
    missing_fields = [f for f in required_fields if f not in new_config]
    
    if missing_fields:
        return {
            "success": False,
            "error": f"Missing required fields: {', '.join(missing_fields)}",
            "error_type": "validation_error"
        }
    
    # Step 3: Preserve ID and add mode if not specified
    new_config["id"] = automation_id
    if "mode" not in new_config:
        new_config["mode"] = "single"
    
    # Step 4: Update automation
    update_result = automation_editor_control(
        action="update",
        automation_id=automation_id,
        automation_config=new_config
    )
    
    if not update_result.get("success"):
        return update_result
    
    # Step 5: Verify update
    verify_result = automation_editor_control(
        action="get",
        automation_id=automation_id
    )
    
    if verify_result.get("success"):
        updated_alias = verify_result.get("automation", {}).get("alias")
        if updated_alias == new_config["alias"]:
            return {
                "success": True,
                "message": "Automation updated and verified",
                "backup_created": update_result.get("backup_created")
            }
    
    return {
        "success": False,
        "error": "Update succeeded but verification failed",
        "error_type": "verification_error"
    }

# Usage
result = safe_automation_update(
    "1234567890",
    {
        "alias": "Updated Morning Routine",
        "trigger": [{"platform": "time", "at": "06:30:00"}],
        "action": [{"service": "light.turn_on", "target": {"entity_id": "light.bedroom"}}]
    }
)
```

### Handling File Permission Errors

**Problem:** Cannot read or write configuration files

**Example:**
```python
result = config_control(
    action="read_file",
    filename="automations.yaml"
)

if not result.get("success"):
    error = result.get("error", "")
    
    if "permission" in error.lower() or "access" in error.lower():
        print("Permission denied accessing configuration file")
        print("Check that HA_CONFIG_PATH is set correctly")
        print("Ensure the MCP server has read/write permissions")
```

**Best Practice:**
```python
import os

def verify_config_access():
    """
    Verify configuration directory access before operations.
    """
    config_path = os.getenv("HA_CONFIG_PATH")
    
    if not config_path:
        return {
            "success": False,
            "error": "HA_CONFIG_PATH environment variable not set",
            "error_type": "configuration_error"
        }
    
    if not os.path.exists(config_path):
        return {
            "success": False,
            "error": f"Configuration path does not exist: {config_path}",
            "error_type": "path_error"
        }
    
    if not os.access(config_path, os.R_OK):
        return {
            "success": False,
            "error": f"No read permission for: {config_path}",
            "error_type": "permission_error"
        }
    
    if not os.access(config_path, os.W_OK):
        return {
            "success": False,
            "error": f"No write permission for: {config_path}",
            "error_type": "permission_error"
        }
    
    return {
        "success": True,
        "message": "Configuration directory accessible",
        "path": config_path
    }

# Use before configuration operations
access_check = verify_config_access()
if not access_check.get("success"):
    print(f"Configuration access error: {access_check.get('error')}")
    exit(1)

print(f"Configuration directory: {access_check.get('path')}")
```

### Handling Bulk Operation Failures

**Problem:** Some operations in bulk succeed, others fail

**Example:**
```python
# Turn on multiple lights
lights = ["light.living_room", "light.bedroom", "light.kitchen"]
results = []

for light in lights:
    result = lights_control(action="turn_on", entity_id=light)
    results.append({
        "entity_id": light,
        "success": result.get("success"),
        "error": result.get("error")
    })

# Check results
failed = [r for r in results if not r["success"]]
if failed:
    print(f"{len(failed)} lights failed to turn on:")
    for f in failed:
        print(f"  - {f['entity_id']}: {f['error']}")
```

**Best Practice:**
```python
# Implement robust bulk operation handler
def bulk_light_control(entity_ids, action, **kwargs):
    results = {
        "success": [],
        "failed": [],
        "total": len(entity_ids)
    }
    
    for entity_id in entity_ids:
        result = lights_control(
            action=action,
            entity_id=entity_id,
            **kwargs
        )
        
        if result.get("success"):
            results["success"].append(entity_id)
        else:
            results["failed"].append({
                "entity_id": entity_id,
                "error": result.get("error")
            })
    
    results["success_rate"] = len(results["success"]) / results["total"]
    return results

# Usage
results = bulk_light_control(
    ["light.living_room", "light.bedroom", "light.kitchen"],
    action="turn_on",
    brightness=128
)

print(f"Success rate: {results['success_rate']*100:.1f}%")
if results["failed"]:
    print("Failed entities:", results["failed"])
```

### Handling State Verification

**Problem:** Need to verify state change after operation

**Example:**
```python
# Turn on light and verify
result = lights_control(action="turn_on", entity_id="light.bedroom")

if result.get("success"):
    # Wait a moment for state to update
    time.sleep(0.5)
    
    # Verify state
    status = lights_control(action="get", entity_id="light.bedroom")
    if status.get("state") == "on":
        print("Light successfully turned on")
    else:
        print("Light command sent but state not updated")
```

**Best Practice:**
```python
# Implement state verification with timeout
def verify_state_change(entity_id, expected_state, timeout=5):
    import time
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        result = lights_control(action="get", entity_id=entity_id)
        
        if result.get("state") == expected_state:
            return True
        
        time.sleep(0.5)
    
    return False

# Usage
lights_control(action="turn_on", entity_id="light.bedroom")

if verify_state_change("light.bedroom", "on"):
    print("Light is on")
else:
    print("Light failed to turn on within timeout")
```

### Handling Concurrent Operations

**Problem:** Need to control multiple devices simultaneously

**Example:**
```python
import asyncio

async def control_multiple_lights():
    tasks = [
        lights_control(action="turn_on", entity_id="light.living_room", brightness=255),
        lights_control(action="turn_on", entity_id="light.bedroom", brightness=128),
        lights_control(action="turn_on", entity_id="light.kitchen", brightness=191)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Task {i} failed: {result}")
        elif not result.get("success"):
            print(f"Task {i} failed: {result.get('error')}")
```

**Best Practice:**
```python
# Implement safe concurrent operations with error handling
async def safe_concurrent_control(operations):
    """
    operations: list of dicts with 'func', 'args', 'kwargs'
    """
    results = {
        "completed": [],
        "failed": [],
        "exceptions": []
    }
    
    tasks = []
    for op in operations:
        task = op["func"](*op.get("args", []), **op.get("kwargs", {}))
        tasks.append(task)
    
    completed = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(completed):
        if isinstance(result, Exception):
            results["exceptions"].append({
                "operation": operations[i],
                "exception": str(result)
            })
        elif result.get("success"):
            results["completed"].append(result)
        else:
            results["failed"].append({
                "operation": operations[i],
                "error": result.get("error")
            })
    
    return results
```

---

## Tips for Effective Commands

### Be Specific

**Good:** "Turn on the living room light to 50% brightness"
**Less Good:** "Make it brighter" (AI has to guess which light and how much)

### Use Entity Names

**Good:** "Turn off the bedroom light"
**Less Good:** "Turn off the light" (if you have multiple lights)

### Provide Context

**Good:** "Set the thermostat to 72°F for sleeping"
**Less Good:** "Change the temperature" (AI has to guess the target)

### Combine Related Actions

**Good:** "Set up movie mode: dim lights, close blinds, and turn on the TV"
**Less Good:** Three separate commands for each action

### Check Status First

**Good:** "What's the current temperature, and then set it to 72°F if it's below 70°F"
**Less Good:** "Set the temperature to 72°F" (without checking current state)

---

## Troubleshooting Examples

### Entity Not Found

**Problem:** "Turn on the living room light" returns "Entity not found"

**Solution:**
1. Use `list_devices(domain="light")` to see all available lights
2. Check the exact entity_id (e.g., `light.living_room` vs `light.living_room_main`)
3. Verify the entity exists in Home Assistant

### Invalid Parameter

**Problem:** "Set the light brightness to 500" returns "Validation error"

**Solution:**
- Brightness must be 0-255
- Use: "Set the light brightness to 255" (for maximum)

### Service Call Failed

**Problem:** "Turn on the AC" returns "Service call failed"

**Solution:**
1. Check if the entity supports the requested service
2. Verify the entity is available (not offline)
3. Check Home Assistant logs for more details

#### Configuration Management Workflow

**Scenario:** Safely update Home Assistant automations with version control and backup.

**Implementation:**
```python
import os
import json
from datetime import datetime

def safe_automation_deployment():
    """
    Deploy automation changes with proper backup and validation.
    
    Workflow:
    1. Backup current configuration
    2. Show differences between local and deployed
    3. Validate new configuration
    4. Deploy with confirmation
    5. Reload and verify
    """
    
    results = {
        "backup": None,
        "diff": None,
        "validation": None,
        "deployment": None,
        "reload": None
    }
    
    # Step 1: Create backup
    print("Creating backup...")
    backup_result = config_control(
        action="backup_file",
        filename="automations.yaml"
    )
    
    if backup_result.get("success"):
        results["backup"] = backup_result.get("backup_file")
        print(f"✓ Backup created: {results['backup']}")
    else:
        print(f"✗ Backup failed: {backup_result.get('error')}")
        return results
    
    # Step 2: Show differences
    print("\nChecking differences...")
    diff_result = config_sync_control(
        action="diff",
        source_path="/path/to/my/config",
        filename="automations.yaml"
    )
    
    if diff_result.get("has_differences"):
        print("Changes detected:")
        print(diff_result.get("diff"))
        results["diff"] = "Changes found"
        
        # Ask for confirmation
        confirm = input("\nProceed with deployment? (yes/no): ")
        if confirm.lower() != "yes":
            print("Deployment cancelled")
            return results
    else:
        print("No changes detected")
        results["diff"] = "No changes"
        return results
    
    # Step 3: Copy new configuration
    print("\nDeploying configuration...")
    deploy_result = config_sync_control(
        action="copy_to_target",
        source_path="/path/to/my/config",
        files=["automations.yaml"],
        confirm=True
    )
    
    if deploy_result.get("success"):
        results["deployment"] = f"Deployed {deploy_result.get('files_copied')} files"
        print(f"✓ {results['deployment']}")
    else:
        print(f"✗ Deployment failed: {deploy_result.get('error')}")
        return results
    
    # Step 4: Validate configuration
    print("\nValidating configuration...")
    validate_result = config_control(action="validate_config")
    
    if validate_result.get("valid"):
        results["validation"] = "Configuration valid"
        print(f"✓ {results['validation']}")
    else:
        print(f"✗ Validation failed: {validate_result.get('errors')}")
        
        # Rollback
        print("\nRolling back to backup...")
        config_control(
            action="restore_file",
            filename="automations.yaml",
            backup_timestamp=results["backup"].split(".")[-1]
        )
        print("✓ Rolled back to previous configuration")
        return results
    
    # Step 5: Reload configuration
    print("\nReloading Home Assistant configuration...")
    reload_result = config_control(action="reload_config")
    
    if reload_result.get("success"):
        results["reload"] = "Configuration reloaded"
        print(f"✓ {results['reload']}")
    else:
        print(f"✗ Reload failed: {reload_result.get('error')}")
    
    # Step 6: Send success notification
    send_notification(
        message="Automation deployment completed successfully",
        title="Configuration Update"
    )
    
    print("\n=== Deployment Summary ===")
    for key, value in results.items():
        print(f"{key}: {value}")
    
    return results

# Usage
safe_automation_deployment()
```

#### Automation Creation and Testing Workflow

**Scenario:** Create a new automation programmatically, test it, and deploy it.

**Implementation:**
```python
def create_and_test_automation():
    """
    Create a new automation with proper testing and validation.
    """
    
    # Step 1: Define the automation
    new_automation = {
        "alias": "Motion-Activated Hallway Light",
        "description": "Turn on hallway light when motion detected at night",
        "trigger": [
            {
                "platform": "state",
                "entity_id": "binary_sensor.hallway_motion",
                "to": "on"
            }
        ],
        "condition": [
            {
                "condition": "time",
                "after": "22:00:00",
                "before": "06:00:00"
            },
            {
                "condition": "state",
                "entity_id": "light.hallway",
                "state": "off"
            }
        ],
        "action": [
            {
                "service": "light.turn_on",
                "target": {
                    "entity_id": "light.hallway"
                },
                "data": {
                    "brightness": 128,
                    "transition": 2
                }
            },
            {
                "delay": "00:05:00"
            },
            {
                "service": "light.turn_off",
                "target": {
                    "entity_id": "light.hallway"
                },
                "data": {
                    "transition": 5
                }
            }
        ],
        "mode": "single"
    }
    
    # Step 2: Validate entities exist
    print("Validating entities...")
    
    # Check motion sensor
    try:
        sensor_result = list_devices(domain="binary_sensor")
        sensors = [d["entity_id"] for d in sensor_result.get("devices", [])]
        
        if "binary_sensor.hallway_motion" not in sensors:
            print("✗ Motion sensor not found")
            return False
        print("✓ Motion sensor found")
    except Exception as e:
        print(f"✗ Error checking sensor: {e}")
        return False
    
    # Check light
    try:
        lights_result = lights_control(action="list")
        lights = [l["entity_id"] for l in lights_result.get("lights", [])]
        
        if "light.hallway" not in lights:
            print("✗ Hallway light not found")
            return False
        print("✓ Hallway light found")
    except Exception as e:
        print(f"✗ Error checking light: {e}")
        return False
    
    # Step 3: Create the automation
    print("\nCreating automation...")
    create_result = automation_editor_control(
        action="create",
        automation_config=new_automation
    )
    
    if not create_result.get("success"):
        print(f"✗ Failed to create automation: {create_result.get('error')}")
        return False
    
    automation_id = create_result.get("automation_id")
    print(f"✓ Automation created with ID: {automation_id}")
    print(f"✓ Backup created: {create_result.get('backup_created')}")
    
    # Step 4: Verify automation was created
    print("\nVerifying automation...")
    get_result = automation_editor_control(
        action="get",
        automation_id=automation_id
    )
    
    if get_result.get("success"):
        print("✓ Automation verified")
        print(f"  Alias: {get_result.get('automation', {}).get('alias')}")
        print(f"  Enabled: {get_result.get('automation', {}).get('enabled', True)}")
    else:
        print("✗ Could not verify automation")
        return False
    
    # Step 5: Test the automation manually
    print("\nTesting automation...")
    print("Triggering automation manually...")
    
    trigger_result = automation_control(
        action="trigger",
        automation_id=f"automation.{automation_id}"
    )
    
    if trigger_result.get("success"):
        print("✓ Automation triggered successfully")
    else:
        print(f"✗ Failed to trigger: {trigger_result.get('error')}")
    
    # Step 6: Send notification
    send_notification(
        message=f"New automation '{new_automation['alias']}' created and tested",
        title="Automation Created"
    )
    
    print("\n=== Automation Creation Complete ===")
    print(f"ID: {automation_id}")
    print(f"Alias: {new_automation['alias']}")
    print(f"Status: Active")
    
    return True

# Usage
create_and_test_automation()
```

#### Bulk Automation Management

**Scenario:** Manage multiple automations based on conditions (e.g., vacation mode).

**Implementation:**
```python
def vacation_mode_manager(enable_vacation=True):
    """
    Enable or disable vacation mode by managing multiple automations.
    
    Vacation mode:
    - Disables: Morning routines, presence-based automations
    - Enables: Security automations, random light patterns
    """
    
    # Define automation categories
    disable_during_vacation = [
        "morning_routine",
        "evening_routine",
        "presence_based",
        "work_from_home"
    ]
    
    enable_during_vacation = [
        "security_check",
        "random_lights",
        "vacation_mode"
    ]
    
    # Get all automations
    print("Fetching all automations...")
    automations_result = automation_editor_control(action="list")
    
    if not automations_result.get("success"):
        print("✗ Failed to fetch automations")
        return False
    
    automations = automations_result.get("automations", [])
    print(f"Found {len(automations)} automations")
    
    changes_made = []
    
    if enable_vacation:
        print("\n=== Enabling Vacation Mode ===")
        
        # Disable normal automations
        for automation in automations:
            alias = automation.get("alias", "").lower()
            automation_id = automation.get("id")
            
            # Check if should be disabled
            if any(keyword in alias for keyword in disable_during_vacation):
                if automation.get("enabled", True):
                    result = automation_editor_control(
                        action="disable",
                        automation_id=automation_id
                    )
                    if result.get("success"):
                        print(f"✓ Disabled: {automation.get('alias')}")
                        changes_made.append(f"Disabled {automation.get('alias')}")
            
            # Check if should be enabled
            elif any(keyword in alias for keyword in enable_during_vacation):
                if not automation.get("enabled", True):
                    result = automation_editor_control(
                        action="enable",
                        automation_id=automation_id
                    )
                    if result.get("success"):
                        print(f"✓ Enabled: {automation.get('alias')}")
                        changes_made.append(f"Enabled {automation.get('alias')}")
        
        # Set vacation mode input boolean
        input_boolean_control(
            action="turn_on",
            entity_id="input_boolean.vacation_mode"
        )
        
        # Arm alarm in away mode
        alarm_control(
            action="arm_away",
            entity_id="alarm_control_panel.home"
        )
        
        # Set climate to eco mode
        climates = climate_control(action="list")
        for climate in climates.get("climate_devices", []):
            climate_control(
                action="set_temperature",
                entity_id=climate["entity_id"],
                temperature=65.0  # Lower temp to save energy
            )
        
        changes_made.append("Set climate to eco mode (65°F)")
        changes_made.append("Armed alarm in away mode")
        
    else:
        print("\n=== Disabling Vacation Mode ===")
        
        # Re-enable normal automations
        for automation in automations:
            alias = automation.get("alias", "").lower()
            automation_id = automation.get("id")
            
            # Re-enable normal automations
            if any(keyword in alias for keyword in disable_during_vacation):
                if not automation.get("enabled", True):
                    result = automation_editor_control(
                        action="enable",
                        automation_id=automation_id
                    )
                    if result.get("success"):
                        print(f"✓ Enabled: {automation.get('alias')}")
                        changes_made.append(f"Enabled {automation.get('alias')}")
            
            # Disable vacation automations
            elif any(keyword in alias for keyword in enable_during_vacation):
                if automation.get("enabled", True):
                    result = automation_editor_control(
                        action="disable",
                        automation_id=automation_id
                    )
                    if result.get("success"):
                        print(f"✓ Disabled: {automation.get('alias')}")
                        changes_made.append(f"Disabled {automation.get('alias')}")
        
        # Disable vacation mode input boolean
        input_boolean_control(
            action="turn_off",
            entity_id="input_boolean.vacation_mode"
        )
        
        # Disarm alarm
        alarm_control(
            action="disarm",
            entity_id="alarm_control_panel.home",
            code="1234"
        )
        
        # Reset climate to normal
        climates = climate_control(action="list")
        for climate in climates.get("climate_devices", []):
            climate_control(
                action="set_temperature",
                entity_id=climate["entity_id"],
                temperature=72.0
            )
        
        changes_made.append("Reset climate to normal (72°F)")
        changes_made.append("Disarmed alarm")
    
    # Send notification
    mode_status = "enabled" if enable_vacation else "disabled"
    send_notification(
        message=f"Vacation mode {mode_status}\n" + "\n".join(changes_made),
        title="Vacation Mode Update"
    )
    
    print(f"\n=== Vacation Mode {mode_status.upper()} ===")
    print(f"Changes made: {len(changes_made)}")
    for change in changes_made:
        print(f"  - {change}")
    
    return True

# Usage
# Enable vacation mode
vacation_mode_manager(enable_vacation=True)

# Disable vacation mode (return home)
vacation_mode_manager(enable_vacation=False)
```

---

## Best Practices

### 1. Always List Before Controlling

**Why:** Ensures entity exists and you have the correct entity_id

**Example:**
```python
# Bad: Assume entity exists
lights_control(action="turn_on", entity_id="light.living_room")

# Good: Verify first
lights = lights_control(action="list")
living_room_lights = [l for l in lights.get("lights", []) 
                      if "living_room" in l["entity_id"]]

if living_room_lights:
    lights_control(action="turn_on", entity_id=living_room_lights[0]["entity_id"])
```

### 2. Use Descriptive Entity Names

**Why:** Makes automation more maintainable and readable

**Example:**
```python
# Bad: Generic names
lights_control(action="turn_on", entity_id="light.light_1")

# Good: Descriptive names
lights_control(action="turn_on", entity_id="light.living_room_main")
```

### 3. Implement Graceful Degradation

**Why:** System should continue working even if some devices fail

**Example:**
```python
def execute_morning_routine():
    # Critical operations
    try:
        lights_control(action="turn_on", entity_id="light.bedroom", brightness=128)
    except Exception as e:
        print(f"Critical: Bedroom light failed: {e}")
        return False
    
    # Non-critical operations
    try:
        switch_control(action="turn_on", entity_id="switch.coffee_maker")
    except Exception as e:
        print(f"Warning: Coffee maker failed: {e}")
        # Continue anyway
    
    try:
        cover_control(action="open", entity_id="cover.bedroom_blinds")
    except Exception as e:
        print(f"Warning: Blinds failed: {e}")
        # Continue anyway
    
    return True
```

### 4. Use Scenes for Complex States

**Why:** Scenes are faster and more reliable than multiple individual commands

**Example:**
```python
# Bad: Multiple individual commands
lights_control(action="turn_on", entity_id="light.living_room", brightness=25)
lights_control(action="turn_on", entity_id="light.kitchen", brightness=0)
lights_control(action="turn_on", entity_id="light.bedroom", brightness=0)
cover_control(action="close", entity_id="cover.living_room_blinds")
media_player_control(action="set_volume", entity_id="media_player.tv", volume_level=0.4)

# Good: Use a scene
scene_control(action="activate", scene_id="scene.movie_mode")
```

### 5. Cache Device Lists

**Why:** Reduces API calls and improves performance

**Example:**
```python
# Bad: List devices every time
def turn_on_all_lights():
    lights = lights_control(action="list")
    for light in lights.get("lights", []):
        lights_control(action="turn_on", entity_id=light["entity_id"])

# Good: Cache device list
class HomeController:
    def __init__(self):
        self._lights_cache = None
        self._cache_time = None
        self._cache_ttl = 60  # seconds
    
    def get_lights(self, force_refresh=False):
        import time
        
        now = time.time()
        
        if (force_refresh or 
            self._lights_cache is None or 
            now - self._cache_time > self._cache_ttl):
            
            result = lights_control(action="list")
            self._lights_cache = result.get("lights", [])
            self._cache_time = now
        
        return self._lights_cache
    
    def turn_on_all_lights(self):
        for light in self.get_lights():
            lights_control(action="turn_on", entity_id=light["entity_id"])
```

### 6. Validate Parameters Before Sending

**Why:** Prevents unnecessary API calls and provides better error messages

**Example:**
```python
def safe_set_light_brightness(entity_id, brightness_percent):
    # Validate entity_id format
    if not entity_id.startswith("light."):
        raise ValueError(f"Invalid light entity_id: {entity_id}")
    
    # Validate brightness range
    if not 0 <= brightness_percent <= 100:
        raise ValueError(f"Brightness must be 0-100, got {brightness_percent}")
    
    # Convert to Home Assistant scale (0-255)
    brightness = int(brightness_percent * 2.55)
    
    return lights_control(
        action="turn_on",
        entity_id=entity_id,
        brightness=brightness
    )
```

### 7. Use Automation for Time-Based Actions

**Why:** More reliable than running scripts continuously

**Example:**
```python
# Bad: Run script continuously checking time
import time

while True:
    current_hour = time.localtime().tm_hour
    if current_hour == 7:
        lights_control(action="turn_on", entity_id="light.bedroom")
    time.sleep(60)

# Good: Create automation in Home Assistant
automation_config = {
    "alias": "Morning Light",
    "trigger": {
        "platform": "time",
        "at": "07:00:00"
    },
    "action": {
        "service": "light.turn_on",
        "target": {
            "entity_id": "light.bedroom"
        }
    }
}
# Use automation_editor tool to create this
```

### 8. Group Related Operations

**Why:** Easier to maintain and understand

**Example:**
```python
# Bad: Scattered operations
def prepare_for_sleep():
    lights_control(action="turn_off", entity_id="light.living_room")
    # ... other code ...
    lights_control(action="turn_off", entity_id="light.kitchen")
    # ... other code ...
    lock_control(action="lock", entity_id="lock.front_door")

# Good: Grouped operations
def prepare_for_sleep():
    # Turn off all lights
    turn_off_all_lights()
    
    # Secure the house
    lock_all_doors()
    close_all_covers()
    
    # Set climate
    set_night_temperature()
    
    # Arm security
    arm_alarm()

def turn_off_all_lights():
    lights = lights_control(action="list")
    for light in lights.get("lights", []):
        lights_control(action="turn_off", entity_id=light["entity_id"])
```

### 9. Log Important Operations

**Why:** Helps with debugging and audit trail

**Example:**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def controlled_operation(func, *args, **kwargs):
    logger.info(f"Executing {func.__name__} with args={args}, kwargs={kwargs}")
    
    try:
        result = func(*args, **kwargs)
        
        if result.get("success"):
            logger.info(f"{func.__name__} succeeded")
        else:
            logger.error(f"{func.__name__} failed: {result.get('error')}")
        
        return result
    except Exception as e:
        logger.exception(f"{func.__name__} raised exception: {e}")
        raise

# Usage
controlled_operation(
    lights_control,
    action="turn_on",
    entity_id="light.bedroom",
    brightness=128
)
```

### 10. Handle State Transitions Gracefully

**Why:** Some devices take time to change state

**Example:**
```python
import time

def wait_for_cover_position(entity_id, target_position, timeout=30):
    """Wait for cover to reach target position"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        result = cover_control(action="get", entity_id=entity_id)
        current_position = result.get("attributes", {}).get("current_position")
        
        if current_position is not None:
            # Allow 5% tolerance
            if abs(current_position - target_position) <= 5:
                return True
        
        time.sleep(1)
    
    return False

# Usage
cover_control(action="set_position", entity_id="cover.garage_door", position=100)
if wait_for_cover_position("cover.garage_door", 100):
    print("Garage door fully open")
else:
    print("Garage door did not reach target position")
```

### 11. Use Environment-Specific Configurations

**Why:** Different settings for development, testing, and production

**Example:**
```python
import os

class Config:
    def __init__(self):
        self.env = os.getenv("ENVIRONMENT", "production")
        
        if self.env == "development":
            self.hass_host = "http://localhost:8123"
            self.retry_attempts = 1
            self.timeout = 5
        elif self.env == "testing":
            self.hass_host = "http://test-ha:8123"
            self.retry_attempts = 2
            self.timeout = 10
        else:  # production
            self.hass_host = os.getenv("HASS_HOST")
            self.retry_attempts = 3
            self.timeout = 30

config = Config()
```

### 12. Implement Health Checks

**Why:** Detect issues before they cause problems

**Example:**
```python
def health_check():
    """Comprehensive health check"""
    checks = {
        "connection": False,
        "authentication": False,
        "devices_available": False
    }
    
    # Check connection
    try:
        result = list_devices()
        checks["connection"] = True
        
        if result.get("success"):
            checks["authentication"] = True
            
            if result.get("total_devices", 0) > 0:
                checks["devices_available"] = True
    except Exception as e:
        print(f"Health check failed: {e}")
    
    return checks

# Run periodically
checks = health_check()
if not all(checks.values()):
    print(f"Health check issues: {checks}")
```

### 13. Use Descriptive Error Messages

**Why:** Makes troubleshooting easier

**Example:**
```python
def safe_climate_control(entity_id, temperature):
    # Validate entity_id
    if not entity_id.startswith("climate."):
        raise ValueError(
            f"Invalid climate entity_id: '{entity_id}'. "
            f"Must start with 'climate.'. "
            f"Example: 'climate.living_room'"
        )
    
    # Validate temperature range
    if not 50 <= temperature <= 90:
        raise ValueError(
            f"Temperature {temperature}°F is out of range. "
            f"Must be between 50°F and 90°F for safety."
        )
    
    result = climate_control(
        action="set_temperature",
        entity_id=entity_id,
        temperature=temperature
    )
    
    if not result.get("success"):
        error = result.get("error", "Unknown error")
        raise RuntimeError(
            f"Failed to set temperature for {entity_id} to {temperature}°F. "
            f"Error: {error}. "
            f"Check that the device is online and supports temperature control."
        )
    
    return result
```

### 14. Test with Mock Data

**Why:** Develop and test without affecting real devices

**Example:**
```python
class MockHomeAssistant:
    def __init__(self):
        self.mock_mode = True
        self.state = {}
    
    def lights_control(self, action, entity_id=None, **kwargs):
        if self.mock_mode:
            if action == "list":
                return {
                    "success": True,
                    "lights": [
                        {"entity_id": "light.living_room", "state": "off"},
                        {"entity_id": "light.bedroom", "state": "on"}
                    ]
                }
            elif action == "turn_on":
                self.state[entity_id] = "on"
                return {"success": True, "message": f"Mocked: {entity_id} turned on"}
        
        # Call real API
        return lights_control(action=action, entity_id=entity_id, **kwargs)

# Usage
ha = MockHomeAssistant()
result = ha.lights_control(action="turn_on", entity_id="light.bedroom")
print(result)  # Won't affect real device
```

### 15. Document Your Automations

**Why:** Makes maintenance and troubleshooting easier

**Example:**
```python
def morning_routine():
    """
    Morning Routine Automation
    
    Triggers: 7:00 AM on weekdays
    
    Actions:
    1. Gradually increase bedroom lights from 0% to 75% over 10 minutes
    2. Start coffee maker
    3. Open bedroom blinds
    4. Set thermostat to 72°F
    5. Play morning news on bedroom speaker
    
    Dependencies:
    - light.bedroom (Philips Hue)
    - switch.coffee_maker (Smart plug)
    - cover.bedroom_blinds (Somfy)
    - climate.bedroom (Nest)
    - media_player.bedroom_speaker (Sonos)
    
    Error Handling:
    - If lights fail, continue with other actions
    - If coffee maker fails, send notification
    - If blinds fail, log warning and continue
    
    Last Updated: 2024-01-15
    """
    # Implementation here
    pass
```

---

## Additional Resources

- [Home Assistant Entity Domains](https://www.home-assistant.io/integrations/#all)
- [Home Assistant Services](https://www.home-assistant.io/docs/scripts/service-calls/)
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

---

**Happy automating! 🏠✨**
