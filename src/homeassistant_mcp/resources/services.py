"""Services resources for MCP.

Provides read-only access to Home Assistant services through MCP resources.
"""

import json
import logging
from collections.abc import Callable
from typing import Any

from fastmcp.resources import TextResource

from .models import ResourceErrorCode, ResourceType, build_error_response, build_resource_envelope

logger = logging.getLogger(__name__)


def register_services_resources(mcp: Any, get_client: Callable[[], Any]) -> None:
    """Register services resource handlers.

    Args:
        mcp: The FastMCP server instance
        get_client: Function that returns the HomeAssistantClient instance
    """

    @mcp.resource("hass://services")
    async def get_services_resource() -> TextResource:
        """Get all available services.

        Resource URI: hass://services

        Returns standardized response envelope with all services organized by domain.
        Each service includes descriptions and parameter definitions.

        Returns:
            TextResource with application/json MIME type and standardized envelope

        Raises:
            Exception: If services retrieval fails
        """
        uri = "hass://services"
        logger.debug("Fetching services resource")

        client = get_client()
        try:
            # Get all services from Home Assistant
            services = await client.get_services()

            # Build standardized response envelope
            envelope = build_resource_envelope(
                uri=uri,
                resource_type=ResourceType.SERVICES,
                data=services,
                cache_ttl=300,  # 300 seconds (5 minutes) cache TTL for services
            )

            # Return TextResource with proper MIME type and hints
            return TextResource(
                uri=uri,  # type: ignore[arg-type]
                mime_type="application/json",
                text=json.dumps(envelope, indent=2, default=str),
            )

        except Exception as e:
            # Log full error details internally for debugging
            logger.error(f"Error fetching services resource: {e}", exc_info=True)

            # Build sanitized error response (no internal details leaked)
            error_response = build_error_response(
                uri=uri,
                error_code=ResourceErrorCode.INTERNAL,
                message="Internal server error while fetching services",
            )

            # Return error as TextResource
            return TextResource(
                uri=uri,  # type: ignore[arg-type]
                mime_type="application/json",
                text=json.dumps(error_response, indent=2, default=str),
            )
