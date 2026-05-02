"""Calendar access tool for Home Assistant MCP server."""

import logging
from typing import Any, Literal

logger = logging.getLogger(__name__)


def register_calendar_tool(mcp: Any, get_client: Any) -> None:
    """Register calendar access tool.

    Args:
        mcp: FastMCP server instance
        get_client: Function that returns HomeAssistantClient instance
    """

    @mcp.tool()
    async def calendar_access(
        action: Literal["list", "get_events"],
        calendar_entity_id: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, Any]:
        """Access Home Assistant calendar data.

        This tool provides access to calendar entities and their events.

        Actions:
        - list: Get all calendar entities (GET /api/calendars)
        - get_events: Get calendar events for a specific calendar (GET /api/calendars/<entity_id>)

        Args:
            action: Action to perform (list or get_events)
            calendar_entity_id: Calendar entity ID (required for get_events action)
            start: Start date/time in ISO 8601 format (optional, for get_events)
            end: End date/time in ISO 8601 format (optional, for get_events)

        Returns:
            Dictionary with success status and data:
            - For list: {"success": True, "calendars": [...]}
            - For get_events: {"success": True, "events": [...]}
            - On error: {"success": False, "error": "...", "error_type": "..."}

        Examples:
            # List all calendars
            calendar_access(action="list")

            # Get all events from a calendar
            calendar_access(action="get_events", calendar_entity_id="calendar.personal")

            # Get events in a date range
            calendar_access(
                action="get_events",
                calendar_entity_id="calendar.personal",
                start="2024-01-01T00:00:00",
                end="2024-01-31T23:59:59"
            )

        Note: Date/time values should be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).
        """
        client = get_client()

        try:
            if action == "list":
                logger.info("Listing calendar entities")
                calendars = await client.get_calendars()
                return {"success": True, "calendars": calendars, "count": len(calendars)}

            elif action == "get_events":
                if not calendar_entity_id:
                    return {
                        "success": False,
                        "error": "calendar_entity_id is required for get_events action",
                        "error_type": "validation_error",
                    }

                logger.info(f"Fetching events for calendar: {calendar_entity_id}")
                events = await client.get_calendar_events(
                    calendar_entity_id=calendar_entity_id, start=start, end=end
                )

                return {
                    "success": True,
                    "calendar_entity_id": calendar_entity_id,
                    "events": events,
                    "count": len(events),
                    "start": start,
                    "end": end,
                }

            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "error_type": "validation_error",
                }

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Calendar access failed: {error_type}: {str(e)}")
            return {"success": False, "error": str(e), "error_type": error_type}
