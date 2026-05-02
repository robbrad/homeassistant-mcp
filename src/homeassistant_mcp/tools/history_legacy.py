"""History query tool for Home Assistant MCP server."""

import logging
from datetime import datetime, timedelta
from typing import Annotated, Any

from pydantic import Field

from ..exceptions import (
    AuthenticationError,
    ConnectionError,
    EntityNotFoundError,
    HomeAssistantError,
    ServiceCallError,
)
from ..hass.client import HomeAssistantClient

logger = logging.getLogger(__name__)


def register_history_tool(mcp: Any, get_client: Any) -> None:
    """Register the history query tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool()
    async def query_history(
        entity_id: Annotated[
            str,
            Field(
                description="Entity ID to query history for. Example: 'sensor.temperature' or 'light.living_room'"
            ),
        ],
        hours: Annotated[
            int | None,
            Field(ge=1, le=168, description="Number of hours to look back (1-168, default: 24)"),
        ] = 24,
        limit: Annotated[
            int | None,
            Field(
                ge=1,
                le=1000,
                description="Maximum number of history entries to return (1-1000, default: 100)",
            ),
        ] = 100,
    ) -> dict:
        """Query historical state data for a Home Assistant entity.

        This tool retrieves historical state changes for a specific entity over a time period.
        Useful for analyzing trends, checking past states, or debugging automation behavior.

        Examples:
        - Get last 24 hours: query_history(entity_id="sensor.temperature")
        - Get last week: query_history(entity_id="light.living_room", hours=168)
        - Get last hour with limit: query_history(entity_id="sensor.motion", hours=1, limit=50)

        Args:
            entity_id: The entity ID to query history for
            hours: Number of hours to look back (1-168, default: 24)
            limit: Maximum number of history entries to return (1-1000, default: 100)

        Returns:
            Dictionary containing historical state data
        """
        client: HomeAssistantClient = get_client()

        try:
            return await _query_history(
                client,
                entity_id,
                hours if hours is not None else 24,
                limit if limit is not None else 100,
            )

        except EntityNotFoundError as e:
            logger.warning(f"Entity not found: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "entity_not_found"}
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
            logger.error(f"Unexpected error in query_history: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _query_history(
    client: HomeAssistantClient, entity_id: str, hours: int, limit: int
) -> dict:
    """Query historical state data for an entity.

    Args:
        client: The Home Assistant client
        entity_id: The entity ID to query
        hours: Number of hours to look back
        limit: Maximum number of entries to return

    Returns:
        Dictionary containing historical state data

    Raises:
        EntityNotFoundError: If the entity is not found
        ServiceCallError: If the API call fails
    """
    logger.info(f"Querying history for {entity_id}, last {hours} hours, limit {limit}")

    # Verify the entity exists
    await client.get_state(entity_id)

    # Calculate timestamp for the start of the history query
    from datetime import timezone

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)

    # Format timestamps in ISO format
    start_timestamp = start_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    end_timestamp = end_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    # Query history from Home Assistant using new API signature
    # The history API endpoint returns a list of state changes
    history_data = await client.get_history(
        timestamp=start_timestamp,
        end_time=end_timestamp,
        filter_entity_id=[entity_id] if entity_id else None,
    )

    # Process and limit the results
    if not history_data or len(history_data) == 0:
        logger.info(f"No history found for {entity_id}")
        return {
            "success": True,
            "entity_id": entity_id,
            "start_time": start_timestamp,
            "end_time": end_timestamp,
            "count": 0,
            "history": [],
        }

    # History data is typically a list of lists, where each inner list contains states for an entity
    # We take the first list (our entity) and limit the results
    entity_history = (
        history_data[0] if isinstance(history_data, list) and len(history_data) > 0 else []
    )

    # Limit the number of entries
    limited_history = entity_history[:limit] if len(entity_history) > limit else entity_history

    # Format the history entries
    formatted_history = []
    for entry in limited_history:
        formatted_entry = {
            "state": entry.get("state"),
            "last_changed": entry.get("last_changed"),
            "last_updated": entry.get("last_updated"),
        }

        # Include relevant attributes if available
        attributes = entry.get("attributes", {})
        if attributes:
            # Include commonly useful attributes
            relevant_attrs = {}
            for key in [
                "friendly_name",
                "unit_of_measurement",
                "device_class",
                "brightness",
                "temperature",
            ]:
                if key in attributes:
                    relevant_attrs[key] = attributes[key]

            if relevant_attrs:
                formatted_entry["attributes"] = relevant_attrs

        formatted_history.append(formatted_entry)

    logger.info(f"Retrieved {len(formatted_history)} history entries for {entity_id}")

    return {
        "success": True,
        "entity_id": entity_id,
        "start_time": start_timestamp,
        "end_time": end_timestamp,
        "hours": hours,
        "count": len(formatted_history),
        "total_available": len(entity_history),
        "limited": len(entity_history) > limit,
        "history": formatted_history,
    }
