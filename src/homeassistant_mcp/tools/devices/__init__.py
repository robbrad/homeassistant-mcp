"""Home Assistant device control tools."""

from .alarm import register_alarm_tool
from .camera import register_camera_tool
from .climate import register_climate_tool
from .cover import register_cover_tool
from .fan import register_fan_tool
from .humidifier import register_humidifier_tool
from .lawn_mower import register_lawn_mower_tool
from .lights import register_lights_tool
from .lock import register_lock_tool
from .media_player import register_media_player_tool
from .siren import register_siren_tool
from .switch import register_switch_tool
from .vacuum import register_vacuum_tool
from .valve import register_valve_tool
from .water_heater import register_water_heater_tool
from .weather import register_weather_tool

__all__ = [
    "register_alarm_tool",
    "register_camera_tool",
    "register_climate_tool",
    "register_cover_tool",
    "register_fan_tool",
    "register_humidifier_tool",
    "register_lawn_mower_tool",
    "register_lights_tool",
    "register_lock_tool",
    "register_media_player_tool",
    "register_siren_tool",
    "register_switch_tool",
    "register_vacuum_tool",
    "register_valve_tool",
    "register_water_heater_tool",
    "register_weather_tool",
]
