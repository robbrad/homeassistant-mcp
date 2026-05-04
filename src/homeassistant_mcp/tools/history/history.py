"""History query tool for Home Assistant MCP server."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from pydantic import Field

from ...exceptions import (
    AuthenticationError,
    ConnectionError,
    HomeAssistantError,
    ServiceCallError,
)
from ...hass.client import HomeAssistantClient

logger = logging.getLogger(__name__)


def register_history_tool(mcp: Any, get_client: Any) -> None:
    """Register the history query tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool()
    async def history_query(
        entity_id: Annotated[
            str,
            Field(
                description=(
                    "Entity ID to query history for. Required to prevent "
                    "returning history for all entities. "
                    "Example: 'sensor.temperature' or 'light.living_room'"
                )
            ),
        ],
        hours: Annotated[
            float,
            Field(
                gt=0,
                le=168,
                description=(
                    "Number of hours of history to retrieve (default 24, max 168 / 7 days). "
                    "Example: 1 for last hour, 24 for last day, 48 for last 2 days."
                ),
            ),
        ] = 24,
        minimal_response: Annotated[
            bool,
            Field(
                description="If True, return minimal data without attributes to reduce response size"
            ),
        ] = True,
        limit: Annotated[
            int,
            Field(
                ge=1,
                le=500,
                description="Maximum number of history entries to return (default 50, max 500)",
            ),
        ] = 50,
    ) -> dict:
        """Query historical state changes for a specific entity.

        Returns state change history for the given entity over the specified
        time period. Results are returned most-recent-first.

        Examples:
            # Last 24 hours for a sensor
            history_query(entity_id="sensor.bedroom_temperature")

            # Last 2 hours for a light
            history_query(entity_id="light.living_room", hours=2)

            # Last week with full attributes
            history_query(entity_id="climate.thermostat", hours=168, minimal_response=False)

        Args:
            entity_id: Entity ID to query (required)
            hours: Hours of history to look back (default 24, max 168)
            minimal_response: Return minimal data without attributes (default True)
            limit: Max entries to return (default 50, max 500)

        Returns:
            Dictionary containing:
                - success: Boolean indicating success
                - entity_id: The queried entity
                - period: Human-readable time period
                - entry_count: Number of state changes found
                - history: List of state change records (most recent first)
        """
        client: HomeAssistantClient = get_client()

        try:
            # Calculate timestamps from hours
            now = datetime.now(timezone.utc)
            start = now - timedelta(hours=hours)
            timestamp = start.isoformat()
            end_time = now.isoformat()

            logger.info(
                f"Querying history for {entity_id}, "
                f"last {hours}h, limit={limit}, minimal={minimal_response}"
            )

            history_data = await client.get_history(
                timestamp=timestamp,
                end_time=end_time,
                filter_entity_id=[entity_id],
                minimal_response=minimal_response,
                limit=limit,
            )

            # Flatten — API returns list of lists, one per entity
            entries = []
            if history_data:
                for entity_history in history_data:
                    entries.extend(entity_history)

            # Sort most recent first
            entries.sort(
                key=lambda e: e.get("last_changed", ""),
                reverse=True,
            )

            # Apply limit
            truncated = len(entries) > limit
            entries = entries[:limit]

            # Build human-readable period string
            if hours < 1:
                period = f"last {int(hours * 60)} minutes"
            elif hours == 1:
                period = "last hour"
            elif hours <= 48:
                period = f"last {int(hours)} hours"
            else:
                period = f"last {hours / 24:.0f} days"

            logger.info(f"Retrieved {len(entries)} history entries for {entity_id}")

            return {
                "success": True,
                "entity_id": entity_id,
                "period": period,
                "entry_count": len(entries),
                "truncated": truncated,
                "history": entries,
            }

        except AuthenticationError as e:
            logger.error(f"Authentication error: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "authentication_error"}
        except ConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "connection_error"}
        except ServiceCallError as e:
            logger.error(f"Service call error: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "service_call_error"}
        except HomeAssistantError as e:
            logger.error(f"Home Assistant error: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "home_assistant_error"}
        except Exception as e:
            logger.error(f"Unexpected error in history_query: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }
