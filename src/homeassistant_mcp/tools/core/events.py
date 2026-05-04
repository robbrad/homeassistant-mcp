"""Events control tool for Home Assistant MCP server.

This tool provides event management capabilities including listing event types
and firing custom events.
"""

import logging
from collections.abc import Callable
from typing import Any, Literal

from fastmcp import Context

from ...exceptions import ServiceCallError

logger = logging.getLogger(__name__)


def register_tool(mcp: Any, get_client: Callable[[], Any]) -> None:
    """Register the events_control tool with the MCP server.

    Args:
        mcp: FastMCP server instance
        get_client: Function that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"api", "event"},
        timeout=30,
    )
    async def events_control(
        action: Literal["list", "fire"],
        event_type: str | None = None,
        event_data: dict[str, Any] | None = None,
        ctx: Context = None,
    ) -> dict[str, Any]:
        """Manage Home Assistant events.

        This tool provides event management capabilities for Home Assistant,
        allowing you to list available event types and fire custom events.

        Args:
            action: The action to perform:
                - list: Get all event types with listener counts (GET /api/events)
                - fire: Fire a custom event (POST /api/events/<event_type>)
            event_type: Event type name (required for 'fire' action)
            event_data: Optional event data dictionary (for 'fire' action)

        Returns:
            Dictionary containing the result:
            - list: {"success": True, "action": "list", "data": {...}}
            - fire: {"success": True, "action": "fire", "event_type": "...", "message": "..."}

        Examples:
            # List all event types
            events_control(action="list")

            # Fire a custom event without data
            events_control(action="fire", event_type="my_custom_event")

            # Fire a custom event with data
            events_control(
                action="fire",
                event_type="my_custom_event",
                event_data={"key": "value", "number": 42}
            )

        Raises:
            ServiceCallError: If the API call fails or parameters are invalid
        """
        client = get_client()

        try:
            if action == "list":
                if ctx:
                    await ctx.info("Listing event types")
                logger.info("Listing event types")
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                events = await client.get_events()
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return {"success": True, "action": "list", "data": events}

            elif action == "fire":
                # Validate event_type is provided
                if not event_type:
                    raise ServiceCallError("event_type is required for 'fire' action")

                # Validate event_type is a non-empty string
                if not isinstance(event_type, str) or len(event_type.strip()) == 0:
                    raise ServiceCallError(
                        f"Invalid event_type: must be a non-empty string, got {type(event_type).__name__}"
                    )

                if ctx:
                    await ctx.info(f"Firing event: {event_type}")
                logger.info(f"Firing event: {event_type}")
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await client.fire_event(event_type, event_data)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)

                return {
                    "success": True,
                    "action": "fire",
                    "event_type": event_type,
                    "message": f"Event '{event_type}' fired successfully",
                    "data": result,
                }

            else:
                # This should never happen due to Literal type, but handle it anyway
                raise ServiceCallError(f"Invalid action: {action}")

        except Exception as e:
            logger.error(f"Failed to execute events_control ({action}): {str(e)}")
            return {
                "success": False,
                "action": action,
                "event_type": event_type if event_type else None,
                "error": str(e),
                "error_type": type(e).__name__,
            }
