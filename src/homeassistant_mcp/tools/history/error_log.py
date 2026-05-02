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
    async def error_log_get(
        max_length: int = 5000,
    ) -> dict:
        """Retrieve Home Assistant error logs.

        This tool retrieves the error log from Home Assistant as plain text.
        The error log contains Python exceptions, warnings, and error messages from
        Home Assistant core and integrations.

        The log is truncated to max_length characters to prevent context overflow.
        Only the most recent entries (end of log) are returned.

        Use this tool to:
        - Diagnose problems with Home Assistant
        - Monitor system health
        - Troubleshoot integration issues
        - Debug automation failures

        Args:
            max_length: Maximum characters to return (default 5000, max 20000).
                        Returns the most recent log entries (tail of log).

        Returns:
            Dictionary containing:
                - success: Boolean indicating success
                - log_size: Total size of the log in bytes
                - returned_size: Size of the returned portion
                - truncated: Whether the log was truncated
                - has_errors: Boolean indicating if log contains content
                - error_log: The error log text (truncated to max_length)
        """
        client: HomeAssistantClient = get_client()

        # Clamp max_length
        max_length = max(500, min(max_length, 20000))

        try:
            logger.info("Retrieving Home Assistant error log")

            # Call the client method to get error log
            error_log = await client.get_error_log()

            # Calculate log size
            log_size = len(error_log) if error_log else 0
            has_errors = log_size > 0
            truncated = log_size > max_length

            # Truncate to tail (most recent entries)
            if truncated:
                error_log = "... [truncated, showing last {} chars of {}] ...\n{}".format(
                    max_length, log_size, error_log[-max_length:]
                )

            logger.info(
                f"Retrieved error log ({log_size} bytes, truncated={truncated})"
            )

            return {
                "success": True,
                "log_size": log_size,
                "returned_size": len(error_log),
                "truncated": truncated,
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
