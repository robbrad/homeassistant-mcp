"""Specialized tools for Home Assistant MCP server."""

from .calendar import register_calendar_tool
from .camera_proxy import register_camera_proxy_tool
from .config_check import register_config_check_tool
from .intent import register_intent_tool
from .template import register_template_tool

__all__ = [
    "register_camera_proxy_tool",
    "register_calendar_tool",
    "register_template_tool",
    "register_config_check_tool",
    "register_intent_tool",
]
