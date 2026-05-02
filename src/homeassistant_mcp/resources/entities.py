"""Entity state resources for MCP.

Provides read-only access to Home Assistant entity states through MCP resources.
"""

import json
import logging
from collections.abc import Callable
from typing import Any

from fastmcp.resources import TextResource

from ..exceptions import EntityNotFoundError
from .models import ResourceErrorCode, ResourceType, build_error_response, build_resource_envelope

logger = logging.getLogger(__name__)


def register_entity_resources(mcp: Any, get_client: Callable[[], Any]) -> None:
    """Register entity state resource handlers.

    Args:
        mcp: The FastMCP server instance
        get_client: Function that returns the HomeAssistantClient instance
    """

    @mcp.resource("hass://entity/{entity_id}")
    async def get_entity_resource(entity_id: str) -> TextResource:
        """Get entity state and attributes.

        Resource URI: hass://entity/{entity_id}

        Returns standardized response envelope with entity state, attributes,
        last_changed, last_updated, domain, and friendly_name.

        Args:
            entity_id: The entity ID extracted from the URI

        Returns:
            TextResource with application/json MIME type and standardized envelope

        Raises:
            EntityNotFoundError: If the entity does not exist
        """
        uri = f"hass://entity/{entity_id}"
        logger.debug(f"Fetching entity resource: {entity_id}")

        client = get_client()
        try:
            # Fetch entity state from Home Assistant
            state = await client.get_state(entity_id)

            # Extract domain from entity_id (format: domain.object_id)
            domain = entity_id.split(".")[0] if "." in entity_id else "unknown"

            # Extract friendly_name from attributes
            friendly_name = state.get("attributes", {}).get("friendly_name", entity_id)

            # Build response data with all required fields
            data = {
                "entity_id": state.get("entity_id", entity_id),
                "state": state.get("state", "unknown"),
                "attributes": state.get("attributes", {}),
                "last_changed": state.get("last_changed", ""),
                "last_updated": state.get("last_updated", ""),
                "domain": domain,
                "friendly_name": friendly_name,
            }

            # Build standardized response envelope
            envelope = build_resource_envelope(
                uri=uri,
                resource_type=ResourceType.ENTITY,
                data=data,
                cache_ttl=5,  # 5 seconds cache TTL for entity states
            )

            # Return TextResource with proper MIME type and hints
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
            logger.error(f"Error fetching entity resource {entity_id}: {e}", exc_info=True)

            # Build sanitized error response (no internal details leaked)
            error_response = build_error_response(
                uri=uri,
                error_code=ResourceErrorCode.INTERNAL,
                message="Internal server error while fetching entity state",
            )

            # Return error as TextResource
            return TextResource(
                uri=uri,  # type: ignore[arg-type]
                mime_type="application/json",
                text=json.dumps(error_response, indent=2, default=str),
            )
