"""Logbook query tool for Home Assistant MCP server."""

import logging
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


def register_logbook_tool(mcp: Any, get_client: Any) -> None:
    """Register the logbook query tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool()
    async def logbook_query(
        timestamp: Annotated[
            str,
            Field(
                description=(
                    "ISO 8601 timestamp for the start of the logbook period. "
                    "Example: '2024-01-15T10:00:00+00:00' or '2024-01-15T10:00:00Z'"
                )
            ),
        ],
        end_time: Annotated[
            str | None,
            Field(
                description=(
                    "Optional ISO 8601 timestamp for the end of the logbook period. "
                    "If not provided, defaults to current time."
                )
            ),
        ] = None,
        entity: Annotated[
            str | None,
            Field(
                description=(
                    "Optional entity ID filter. HIGHLY RECOMMENDED for large installations. "
                    "Example: 'light.living_room'"
                )
            ),
        ] = None,
        limit: Annotated[
            int,
            Field(
                ge=1,
                le=500,
                description="Maximum number of logbook entries to return (default 100, max 500)",
            ),
        ] = 100,
    ) -> dict:
        """Query human-readable logbook entries with filtering support.

        ⚠️ IMPORTANT: Logbook queries can return extensive data. For large Home Assistant
        installations, ALWAYS use entity filter to prevent context overflow.

        The logbook provides human-readable entries for events and state changes in
        Home Assistant. Without filtering, it may return entries for ALL entities and
        events, which can easily exceed AI assistant context limits.

        FILTERING BEST PRACTICES:
        1. Always specify entity filter when querying specific device history
        2. Use shorter time ranges for unfiltered queries
        3. Default limit is 100 entries to prevent overwhelming responses
        4. Logbook entries are more verbose than raw history data

        Examples:
        - Query specific entity: logbook_query(
            timestamp="2024-01-15T10:00:00Z",
            entity="light.living_room"
          )
        - Query time range: logbook_query(
            timestamp="2024-01-15T10:00:00Z",
            end_time="2024-01-15T12:00:00Z",
            entity="sensor.motion"
          )
        - Recent events with limit: logbook_query(
            timestamp="2024-01-15T10:00:00Z",
            limit=50
          )

        Args:
            timestamp: ISO 8601 timestamp for the start of the logbook period
            end_time: Optional ISO 8601 timestamp for the end (defaults to now)
            entity: Optional entity ID filter (RECOMMENDED for large installations)
            limit: Maximum number of logbook entries to return (default 100, max 500)

        Returns:
            Dictionary containing:
                - success: Boolean indicating success
                - timestamp: Start timestamp used
                - end_time: End timestamp used (or null)
                - entity: Entity filter used (or null)
                - limit: Limit applied
                - entry_count: Number of entries in response
                - truncated: Whether results were truncated due to limit
                - logbook: List of logbook entry dictionaries
        """
        client: HomeAssistantClient = get_client()

        try:
            logger.info(f"Querying logbook from {timestamp}, entity={entity}, limit={limit}")

            # Call the client method with all parameters
            logbook_data = await client.get_logbook(
                timestamp=timestamp,
                end_time=end_time,
                entity=entity,
                limit=limit,
            )

            # Count entries in response
            entry_count = len(logbook_data) if logbook_data else 0

            # Check if results were truncated (client applies limit)
            # We can't know the true total, but we can indicate if we hit the limit
            truncated = entry_count >= limit

            logger.info(f"Retrieved {entry_count} logbook entries")

            return {
                "success": True,
                "timestamp": timestamp,
                "end_time": end_time,
                "entity": entity,
                "limit": limit,
                "entry_count": entry_count,
                "truncated": truncated,
                "logbook": logbook_data,
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
        except ValueError as e:
            # Handle invalid timestamp format
            logger.warning(f"Invalid timestamp format: {str(e)}")
            return {
                "error": f"Invalid timestamp format: {str(e)}. Use ISO 8601 format like '2024-01-15T10:00:00Z'",
                "success": False,
                "error_type": "validation_error",
            }
        except Exception as e:
            logger.error(f"Unexpected error in logbook_query: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }
