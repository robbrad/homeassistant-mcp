"""API information tool for Home Assistant MCP server.

This tool provides access to basic Home Assistant API information including
status, configuration, and loaded components.
"""

import logging
from collections.abc import Callable
from typing import Any, Literal

from fastmcp import Context

from ...exceptions import ServiceCallError

logger = logging.getLogger(__name__)


def register_tool(mcp: Any, get_client: Callable[[], Any]) -> None:
    """Register the api_info tool with the MCP server.

    Args:
        mcp: FastMCP server instance
        get_client: Function that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"readOnlyHint": True, "openWorldHint": True},
        tags={"api", "read"},
        timeout=30,
    )
    async def api_info(
        action: Literal["status", "config", "components"],
        ctx: Context = None,
    ) -> dict[str, Any]:
        """Get Home Assistant API information.

        This tool provides access to core Home Assistant API endpoints for
        retrieving system information, configuration, and loaded components.

        Args:
            action: The type of information to retrieve:
                - status: Check API running status (GET /api/)
                - config: Get current configuration (GET /api/config)
                - components: List loaded components (GET /api/components)

        Returns:
            Dictionary containing the requested information:
            - status: {"message": "API running."}
            - config: Configuration dict with location, units, version, etc.
            - components: {"components": ["component1", "component2", ...]}

        Examples:
            # Check if API is running
            api_info(action="status")

            # Get Home Assistant configuration
            api_info(action="config")

            # List all loaded components
            api_info(action="components")

        Raises:
            ServiceCallError: If the API call fails
        """
        client = get_client()

        try:
            if action == "status":
                if ctx:
                    await ctx.info("Fetching API status")
                logger.info("Fetching API status")
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await client.get_api_status()
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return {"success": True, "action": "status", "data": result}

            elif action == "config":
                if ctx:
                    await ctx.info("Fetching Home Assistant configuration")
                logger.info("Fetching Home Assistant configuration")
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await client.get_config()
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                # Strip large internal fields to reduce context size
                for key in ["allowlist_external_dirs", "allowlist_external_urls", "safe_mode"]:
                    result.pop(key, None)
                return {"success": True, "action": "config", "data": result}

            elif action == "components":
                if ctx:
                    await ctx.info("Fetching loaded components")
                logger.info("Fetching loaded components")
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                components = await client.get_components()
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return {
                    "success": True,
                    "action": "components",
                    "data": {"count": len(components), "components": sorted(components)},
                }

            else:
                # This should never happen due to Literal type, but handle it anyway
                raise ServiceCallError(f"Invalid action: {action}")

        except Exception as e:
            logger.error(f"Failed to fetch API info ({action}): {str(e)}")
            return {
                "success": False,
                "action": action,
                "error": str(e),
                "error_type": type(e).__name__,
            }
