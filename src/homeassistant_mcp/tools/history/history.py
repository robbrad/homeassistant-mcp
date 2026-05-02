"""History query tool for Home Assistant MCP server."""

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


def register_history_tool(mcp: Any, get_client: Any) -> None:
    """Register the history query tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool()
    async def history_query(
        timestamp: Annotated[
            str,
            Field(
                description=(
                    "ISO 8601 timestamp for the start of the history period. "
                    "Example: '2024-01-15T10:00:00+00:00' or '2024-01-15T10:00:00Z'"
                )
            ),
        ],
        end_time: Annotated[
            str | None,
            Field(
                description=(
                    "Optional ISO 8601 timestamp for the end of the history period. "
                    "If not provided, defaults to current time."
                )
            ),
        ] = None,
        filter_entity_id: Annotated[
            list[str] | None,
            Field(
                description=(
                    "Optional list of entity IDs to filter. HIGHLY RECOMMENDED for large installations. "
                    "Example: ['sensor.temperature', 'light.living_room']"
                )
            ),
        ] = None,
        minimal_response: Annotated[
            bool,
            Field(
                description="If True, return minimal data without attributes to reduce response size"
            ),
        ] = False,
        limit: Annotated[
            int,
            Field(
                ge=1,
                le=500,
                description="Maximum number of history entries per entity (default 100, max 500)",
            ),
        ] = 100,
    ) -> dict:
        """Query historical state changes with filtering support.

        ⚠️ IMPORTANT: History queries can return extensive data. For large Home Assistant
        installations, ALWAYS use filter_entity_id to prevent context overflow.

        This tool retrieves historical state changes for entities over a time period.
        Without filtering, it may return data for ALL entities, which can easily exceed
        AI assistant context limits.

        FILTERING BEST PRACTICES:
        1. Always specify filter_entity_id with specific entities when possible
        2. Use shorter time ranges for unfiltered queries
        3. Use minimal_response=True to reduce data size
        4. Default limit is 100 entries per entity to prevent overwhelming responses

        Examples:
        - Query specific sensor: history_query(
            timestamp="2024-01-15T10:00:00Z",
            filter_entity_id=["sensor.bedroom_temperature"]
          )
        - Query multiple entities: history_query(
            timestamp="2024-01-15T10:00:00Z",
            end_time="2024-01-15T12:00:00Z",
            filter_entity_id=["light.living_room", "light.bedroom"]
          )
        - Minimal response: history_query(
            timestamp="2024-01-15T10:00:00Z",
            filter_entity_id=["sensor.temperature"],
            minimal_response=True
          )

        Args:
            timestamp: ISO 8601 timestamp for the start of the history period
            end_time: Optional ISO 8601 timestamp for the end (defaults to now)
            filter_entity_id: Optional list of entity IDs to filter (RECOMMENDED)
            minimal_response: If True, return minimal data without attributes
            limit: Maximum number of history entries per entity (default 100, max 500)

        Returns:
            Dictionary containing:
                - success: Boolean indicating success
                - timestamp: Start timestamp used
                - end_time: End timestamp used (or null)
                - filter_entity_id: Entity filter used (or null)
                - minimal_response: Whether minimal response was used
                - limit: Limit applied per entity
                - entity_count: Number of entities in response
                - history: List of lists, one per entity, containing state dictionaries
        """
        client: HomeAssistantClient = get_client()

        try:
            logger.info(
                f"Querying history from {timestamp}, "
                f"filter={filter_entity_id}, limit={limit}, minimal={minimal_response}"
            )

            # Call the client method with all parameters
            history_data = await client.get_history(
                timestamp=timestamp,
                end_time=end_time,
                filter_entity_id=filter_entity_id,
                minimal_response=minimal_response,
                limit=limit,
            )

            # Count entities in response
            entity_count = len(history_data) if history_data else 0

            logger.info(f"Retrieved history data for {entity_count} entities")

            return {
                "success": True,
                "timestamp": timestamp,
                "end_time": end_time,
                "filter_entity_id": filter_entity_id,
                "minimal_response": minimal_response,
                "limit": limit,
                "entity_count": entity_count,
                "history": history_data,
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
            logger.error(f"Unexpected error in history_query: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }
