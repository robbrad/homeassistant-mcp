"""Intent handling tool for Home Assistant MCP server."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def register_intent_tool(mcp: Any, get_client: Any) -> None:
    """Register intent handling tool.

    Args:
        mcp: FastMCP server instance
        get_client: Function that returns HomeAssistantClient instance
    """

    @mcp.tool()
    async def intent_handle(
        intent_type: str,
        intent_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Handle a Home Assistant intent for natural language processing.

        This tool processes structured intents that Home Assistant can understand,
        enabling natural language control of devices and services. Intents are
        higher-level commands that Home Assistant translates into actions.

        Common built-in intents include:
        - HassTurnOn: Turn on devices
        - HassTurnOff: Turn off devices
        - HassToggle: Toggle device state
        - HassSetPosition: Set position (covers, etc.)
        - HassLightSet: Set light properties
        - HassClimateSetTemperature: Set thermostat temperature

        Args:
            intent_type: Type of intent (e.g., "HassTurnOn", "HassTurnOff")
            intent_data: Optional intent data including:
                - name: Entity name or area
                - domain: Entity domain (light, switch, etc.)
                - area: Area name
                - floor: Floor name
                - device_class: Device class
                Additional fields depend on the intent type

        Returns:
            Dictionary with success status and intent response:
            - On success: {
                "success": True,
                "speech": {...},  # Speech response
                "card": {...},    # Optional card data
                "response_type": "...",
                "language": "...",
                "data": {...}     # Optional additional data
              }
            - On error: {"success": False, "error": "...", "error_type": "..."}

        Examples:
            # Turn on living room lights
            intent_handle(
                intent_type="HassTurnOn",
                intent_data={"name": "living room", "domain": "light"}
            )

            # Turn off all lights in bedroom
            intent_handle(
                intent_type="HassTurnOff",
                intent_data={"area": "bedroom", "domain": "light"}
            )

            # Set thermostat temperature
            intent_handle(
                intent_type="HassClimateSetTemperature",
                intent_data={"name": "thermostat", "temperature": 72}
            )

            # Toggle kitchen light
            intent_handle(
                intent_type="HassToggle",
                intent_data={"name": "kitchen light"}
            )

        Note: Intent handling requires Home Assistant's conversation/intent system
        to be configured. Some intents may require specific integrations or
        custom intent scripts.
        """
        client = get_client()

        try:
            logger.info(f"Handling intent: {intent_type}")
            result = await client.handle_intent(intent_type=intent_type, intent_data=intent_data)

            return {
                "success": True,
                "intent_type": intent_type,
                "speech": result.get("speech", {}),
                "card": result.get("card"),
                "response_type": result.get("response_type", ""),
                "language": result.get("language", ""),
                "data": result.get("data"),
                "raw_response": result,
            }

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Intent handling failed: {error_type}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": error_type,
                "intent_type": intent_type,
            }
