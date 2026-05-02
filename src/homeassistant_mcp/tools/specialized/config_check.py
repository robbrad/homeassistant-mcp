"""Configuration validation tool for Home Assistant MCP server."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def register_config_check_tool(mcp: Any, get_client: Any) -> None:
    """Register configuration check tool.

    Args:
        mcp: FastMCP server instance
        get_client: Function that returns HomeAssistantClient instance
    """

    @mcp.tool()
    async def config_check() -> dict[str, Any]:
        """Validate Home Assistant configuration without restarting.

        This tool triggers Home Assistant's configuration validation to check for
        errors and warnings in the configuration files. This is useful for:
        - Verifying configuration changes before restarting
        - Catching syntax errors in YAML files
        - Identifying deprecated configuration options
        - Checking for missing required fields

        The validation runs without restarting Home Assistant, making it safe to
        use for pre-deployment checks.

        Returns:
            Dictionary with success status and validation results:
            - On success: {
                "success": True,
                "result": "valid" or "invalid",
                "errors": [...],  # List of error messages
                "warnings": [...]  # List of warning messages
              }
            - On error: {"success": False, "error": "...", "error_type": "..."}

        Examples:
            # Check configuration
            config_check()

            # Result when valid:
            # {
            #   "success": True,
            #   "result": "valid",
            #   "errors": [],
            #   "warnings": []
            # }

            # Result when invalid:
            # {
            #   "success": True,
            #   "result": "invalid",
            #   "errors": ["Invalid domain: invalid_domain"],
            #   "warnings": ["Deprecated option: old_option"]
            # }

        Note: This tool requires appropriate permissions in Home Assistant.
        Some installations may restrict configuration validation to administrators.
        """
        client = get_client()

        try:
            logger.info("Checking Home Assistant configuration")
            result = await client.check_config()

            # Extract validation results
            # Home Assistant returns different formats, normalize them
            errors = result.get("errors", [])
            warnings = result.get("warnings", [])

            # Determine if configuration is valid
            is_valid = len(errors) == 0

            return {
                "success": True,
                "result": "valid" if is_valid else "invalid",
                "errors": errors if isinstance(errors, list) else [str(errors)],
                "warnings": warnings if isinstance(warnings, list) else [str(warnings)],
                "details": result,
            }

        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Configuration check failed: {error_type}: {str(e)}")
            return {"success": False, "error": str(e), "error_type": error_type}
