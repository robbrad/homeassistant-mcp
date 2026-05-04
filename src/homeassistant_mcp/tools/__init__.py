"""Home Assistant MCP tools module."""

# Device control tools (organized in devices/ subdirectory)
# Automation tools (organized in automation/ subdirectory)
from .automation import (
    register_automation_tool,
    register_scene_tool,
    register_script_tool,
)

# Other tools (remain in tools/ root)
from .control import register_control_tool
from .device_list import register_devices_tool  # Device listing tool
from .devices import (
    register_alarm_tool,
    register_camera_tool,
    register_climate_tool,
    register_cover_tool,
    register_fan_tool,
    register_humidifier_tool,
    register_lawn_mower_tool,
    register_lights_tool,
    register_lock_tool,
    register_media_player_tool,
    register_siren_tool,
    register_switch_tool,
    register_vacuum_tool,
    register_valve_tool,
    register_water_heater_tool,
    register_weather_tool,
)

# Input helper tools (organized in helpers/ subdirectory)
from .helpers import (
    register_input_boolean_tool,
    register_input_datetime_tool,
    register_input_number_tool,
    register_input_select_tool,
    register_input_text_tool,
)
from .history import register_history_tools  # New history tools
from .notify import register_notify_tool
from .state import register_state_tools

__all__ = [
    "register_alarm_tool",
    "register_lights_tool",
    "register_climate_tool",
    "register_devices_tool",
    "register_automation_tool",
    "register_scene_tool",
    "register_notify_tool",
    "register_history_tools",
    "register_control_tool",
    "register_state_tools",
    "register_switch_tool",
    "register_cover_tool",
    "register_lock_tool",
    "register_media_player_tool",
    "register_camera_tool",
    "register_vacuum_tool",
    "register_fan_tool",
    "register_script_tool",
    "register_input_boolean_tool",
    "register_input_number_tool",
    "register_input_select_tool",
    "register_input_text_tool",
    "register_input_datetime_tool",
    "register_weather_tool",
    "register_water_heater_tool",
    "register_humidifier_tool",
    "register_siren_tool",
    "register_valve_tool",
    "register_lawn_mower_tool",
]
