"""Template rendering tool for Home Assistant MCP server."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def register_template_tool(mcp: Any, get_client: Any) -> None:
    """Register template rendering tool.

    Args:
        mcp: FastMCP server instance
        get_client: Function that returns HomeAssistantClient instance
    """

    @mcp.tool()
    async def template_render(
        template: str,
    ) -> dict[str, Any]:
        """Render a Home Assistant template.

        This tool renders Home Assistant templates, which can include:
        - Entity state references: {{ states('sensor.temperature') }}
        - Attributes: {{ state_attr('light.living_room', 'brightness') }}
        - Time/date functions: {{ now() }}, {{ today_at() }}
        - Math operations: {{ (states('sensor.temp') | float) * 1.8 + 32 }}
        - Conditional logic: {% if ... %}...{% endif %}
        - Loops: {% for ... %}...{% endfor %}

        Args:
            template: Template string to render using Jinja2 syntax

        Returns:
            Dictionary with success status and rendered output:
            - On success: {"success": True, "result": "rendered output"}
            - On error: {"success": False, "error": "...", "error_type": "..."}

        Examples:
            # Get current temperature
            template_render(template="{{ states('sensor.living_room_temperature') }}")

            # Calculate fahrenheit from celsius
            template_render(template="{{ (states('sensor.temp_c') | float) * 1.8 + 32 }}")

            # Conditional logic
            template_render(template="{% if is_state('light.living_room', 'on') %}Light is on{% else %}Light is off{% endif %}")

            # List all lights that are on
            template_render(template="{% for state in states.light %}{% if state.state == 'on' %}{{ state.name }}, {% endif %}{% endfor %}")

        Note: Templates are evaluated in the Home Assistant context with access to
        all entities, states, and template functions. Invalid syntax or references
        to unavailable entities will return an error.
        """
        client = get_client()

        try:
            logger.info("Rendering template")
            result = await client.render_template(template)

            return {"success": True, "result": result, "template": template}

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Template rendering failed: {error_type}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": error_type,
                "template": template,
            }
