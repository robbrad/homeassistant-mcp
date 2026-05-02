"""Area resources for MCP.

Provides read-only access to Home Assistant area information through MCP resources.
"""

import json
import logging
from collections.abc import Callable
from typing import Any

from fastmcp.resources import TextResource

from .models import (
    EntitySummary,
    ResourceErrorCode,
    ResourceType,
    build_error_response,
    build_resource_envelope,
)

logger = logging.getLogger(__name__)


def register_area_resources(mcp: Any, get_client: Callable[[], Any]) -> None:
    """Register area resource handlers.

    Args:
        mcp: The FastMCP server instance
        get_client: Function that returns the HomeAssistantClient instance
    """

    @mcp.resource("hass://area/{area_id}")
    async def get_area_resource(area_id: str) -> TextResource:
        """Get area information and associated entities.

        Resource URI: hass://area/{area_id}

        Returns lightweight entity summaries (entity_id, state, domain, friendly_name only)
        to avoid large payloads. Truncates to 50 entities if area has more.

        Args:
            area_id: The area ID extracted from the URI

        Returns:
            TextResource with JSON-formatted area data

        Raises:
            Exception: If area retrieval fails
        """
        uri = f"hass://area/{area_id}"
        logger.debug(f"Fetching area resource: {area_id}")

        client = get_client()
        try:
            # Get all states and filter by area
            states = await client.get_states(area=area_id)

            # Build lightweight entity summaries (only 4 fields, no full attributes)
            entities = []
            for state in states[:50]:  # Truncate at 50 entities
                # Extract domain from entity_id
                domain = (
                    state["entity_id"].split(".")[0] if "." in state["entity_id"] else "unknown"
                )

                # Extract friendly_name from attributes
                friendly_name = state.get("attributes", {}).get("friendly_name", state["entity_id"])

                # Create lightweight summary using EntitySummary model
                entity_summary = EntitySummary(
                    entity_id=state["entity_id"],
                    state=state["state"],
                    domain=domain,
                    friendly_name=friendly_name,
                )
                entities.append(entity_summary.model_dump())

            # Build response data
            data = {
                "area_id": area_id,
                "entity_count": len(states),
                "entities": entities,
                "truncated": len(states) > 50,
            }

            # Build standardized response envelope with cache TTL hint of 30 seconds
            envelope = build_resource_envelope(
                uri=uri,
                resource_type=ResourceType.AREA,
                data=data,
                cache_ttl=30,
            )

            # Return TextResource with application/json MIME type
            return TextResource(
                uri=uri,  # type: ignore[arg-type]
                mime_type="application/json",
                text=json.dumps(envelope, indent=2, default=str),
            )

        except Exception as e:
            # Log full error details internally for debugging
            logger.error(f"Error fetching area resource {area_id}: {e}", exc_info=True)

            # Build sanitized error response (no internal details leaked)
            error_response = build_error_response(
                uri=uri,
                error_code=ResourceErrorCode.INTERNAL,
                message="Internal server error while fetching area resource",
            )

            # Return error as TextResource
            return TextResource(
                uri=uri,  # type: ignore[arg-type]
                mime_type="application/json",
                text=json.dumps(error_response, indent=2, default=str),
            )
