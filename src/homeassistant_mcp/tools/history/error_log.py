"""Error log retrieval tool for Home Assistant MCP server."""

import logging
from typing import Any

from ...exceptions import (
    AuthenticationError,
    ConnectionError,
    HomeAssistantError,
    ServiceCallError,
)
from ...hass.client import HomeAssistantClient

logger = logging.getLogger(__name__)


def register_error_log_tool(mcp: Any, get_client: Any) -> None:
    """Register the error log retrieval tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool()
    async def error_log_get() -> dict:
        """Retrieve Home Assistant error logs.

        This tool retrieves the complete error log from Home Assistant as plain text.
        The error log contains Python exceptions, warnings, and error messages from
        Home Assistant core and integrations.

        Use this tool to:
        - Diagnose problems with Home Assistant
        - Monitor system health
        - Troubleshoot integration issues
        - Debug automation failures

        Returns:
            Dictionary containing:
                - success: Boolean indicating success
                - log_size: Size of the log in bytes
                - has_errors: Boolean indicating if log contains content
                - error_log: The complete error log as plain text (or empty string)
        """
        client: HomeAssistantClient = get_client()

        try:
            logger.info("Retrieving Home Assistant error log")

            # Call the client method to get error log
            error_log = await client.get_error_log()

            # Calculate log size
            log_size = len(error_log) if error_log else 0
            has_errors = log_size > 0

            logger.info(f"Retrieved error log ({log_size} bytes, has_errors={has_errors})")

            return {
                "success": True,
                "log_size": log_size,
                "has_errors": has_errors,
                "error_log": error_log,
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
            logger.error(f"Unexpected error in error_log_get: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }
