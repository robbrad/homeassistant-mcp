"""Entity history resources for MCP.

Provides read-only access to Home Assistant entity historical state changes
through MCP resources with query parameter support.
"""

import json
import logging
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from fastmcp.resources import TextResource

from ..exceptions import EntityNotFoundError
from .models import ResourceErrorCode, ResourceType, build_error_response, build_resource_envelope

logger = logging.getLogger(__name__)


def register_history_resources(mcp: Any, get_client: Callable[[], Any]) -> None:
    """Register entity history resource handlers.

    Args:
        mcp: The FastMCP server instance
        get_client: Function that returns the HomeAssistantClient instance
    """

    @mcp.resource("hass://entity/{entity_id}/history")
    async def get_entity_history_resource(
        entity_id: str,
        hours: int = 24,
        limit: int = 100,
        offset: int = 0,
    ) -> TextResource:
        """Get historical state changes for an entity.

        Resource URI: hass://entity/{entity_id}/history{?hours,limit,offset}

        Query Parameters:
            hours: Number of hours of history to retrieve (default: 24)
            limit: Maximum number of history entries to return (default: 100)
            offset: Pagination offset for history entries (default: 0)

        Returns standardized response envelope with historical state entries,
        each containing state, last_changed, last_updated, and attributes.

        Args:
            entity_id: The entity ID extracted from the URI
            hours: Number of hours to look back (default: 24)
            limit: Maximum entries to return (default: 100)
            offset: Pagination offset (default: 0)

        Returns:
            TextResource with application/json MIME type and standardized envelope

        Raises:
            EntityNotFoundError: If the entity does not exist
        """
        uri = f"hass://entity/{entity_id}/history?hours={hours}&limit={limit}&offset={offset}"
        logger.debug(
            f"Fetching history resource: {entity_id} (hours={hours}, limit={limit}, offset={offset})"
        )

        client = get_client()
        try:
            # Calculate start timestamp from hours parameter
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            timestamp = start_time.isoformat()

            # Fetch history from Home Assistant
            # Note: get_history returns list of lists (one list per entity)
            history_data = await client.get_history(
                timestamp=timestamp,
                filter_entity_id=[entity_id],
                minimal_response=False,
                limit=limit + offset,  # Fetch more to handle offset
            )

            # Extract the history for this specific entity
            # history_data is a list of lists, we want the first (and only) list
            entries = history_data[0] if history_data and len(history_data) > 0 else []

            # Apply offset and limit
            total_entries = len(entries)
            entries = entries[offset : offset + limit]

            # Build response data with history entries
            data = {
                "entity_id": entity_id,
                "hours": hours,
                "limit": limit,
                "offset": offset,
                "entries": entries,
                "entry_count": len(entries),
                "has_more": (offset + len(entries)) < total_entries,
            }

            # Build standardized response envelope
            envelope = build_resource_envelope(
                uri=uri,
                resource_type=ResourceType.HISTORY,
                data=data,
                cache_ttl=60,  # 60 seconds cache TTL for history
            )

            # Return TextResource with proper MIME type
            return TextResource(
                uri=uri,  # type: ignore[arg-type]
                mime_type="application/json",
                text=json.dumps(envelope, indent=2, default=str),
            )

        except EntityNotFoundError:
            # Log the error with full context
            logger.warning(f"Entity not found: {entity_id}")

            # Build sanitized error response
            error_response = build_error_response(
                uri=uri,
                error_code=ResourceErrorCode.NOT_FOUND,
                message=f"Entity '{entity_id}' not found in Home Assistant",
            )

            # Return error as TextResource
            return TextResource(
                uri=uri,  # type: ignore[arg-type]
                mime_type="application/json",
                text=json.dumps(error_response, indent=2, default=str),
            )

        except Exception as e:
            # Log full error details internally for debugging
            logger.error(f"Error fetching history resource {entity_id}: {e}", exc_info=True)

            # Build sanitized error response (no internal details leaked)
            error_response = build_error_response(
                uri=uri,
                error_code=ResourceErrorCode.INTERNAL,
                message="Internal server error while fetching entity history",
            )

            # Return error as TextResource
            return TextResource(
                uri=uri,  # type: ignore[arg-type]
                mime_type="application/json",
                text=json.dumps(error_response, indent=2, default=str),
            )
