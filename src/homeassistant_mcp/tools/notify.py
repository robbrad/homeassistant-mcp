"""Notification tool for Home Assistant MCP server."""

import logging
from typing import Annotated, Any

from pydantic import Field

from ..exceptions import (
    AuthenticationError,
    ConnectionError,
    HomeAssistantError,
    ServiceCallError,
)
from ..hass.client import HomeAssistantClient

logger = logging.getLogger(__name__)


def register_notify_tool(mcp: Any, get_client: Any) -> None:
    """Register the notification tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool()
    async def send_notification(
        message: Annotated[str, Field(description="The notification message to send")],
        title: Annotated[
            str | None, Field(description="Optional title for the notification")
        ] = None,
        target: Annotated[
            str | None,
            Field(
                description="Optional target device or service for the notification. Example: 'mobile_app_phone'"
            ),
        ] = None,
    ) -> dict:
        """Send notifications through Home Assistant.

        This tool allows you to send notifications to users through Home Assistant's
        notification services. You can send simple messages or include optional titles
        and target specific devices or notification services.

        Examples:
        - Simple notification: send_notification(message="The door is open")
        - With title: send_notification(message="Motion detected", title="Security Alert")
        - To specific device: send_notification(message="Task complete", target="mobile_app_phone")

        Args:
            message: The notification message to send
            title: Optional title for the notification
            target: Optional target device or service

        Returns:
            Dictionary containing the result of the operation
        """
        client: HomeAssistantClient = get_client()

        try:
            return await _send_notification(client, message, title, target)

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
            logger.error(f"Unexpected error in send_notification: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _send_notification(
    client: HomeAssistantClient,
    message: str,
    title: str | None = None,
    target: str | None = None,
) -> dict:
    """Send a notification through Home Assistant.

    Args:
        client: The Home Assistant client
        message: The notification message
        title: Optional notification title
        target: Optional target device or service

    Returns:
        Dictionary containing the result of the operation

    Raises:
        ServiceCallError: If the notification service call fails
    """
    logger.info(
        f"Sending notification: message='{message[:50]}...', title={title}, target={target}"
    )

    # Build the service data
    service_data = {"message": message}

    if title:
        service_data["title"] = title

    # Determine the service to call
    # If target is specified, use it as the service name (e.g., "mobile_app_phone")
    # Otherwise, use the generic "notify" service
    if target:
        # Target can be a full service name like "mobile_app_phone" or just "phone"
        # If it doesn't contain "notify.", prepend it
        if not target.startswith("notify."):
            service_name = target
        else:
            # Remove "notify." prefix if present
            service_name = target.replace("notify.", "")

        service_data["target"] = target
    else:
        service_name = "notify"

    # Call the notification service
    try:
        await client.call_service("notify", service_name, service_data)
    except ServiceCallError as e:
        # Check if this is because the notification service is unavailable
        error_msg = str(e).lower()
        if "not found" in error_msg or "unavailable" in error_msg:
            raise ServiceCallError(
                f"Notification service '{service_name}' is unavailable. "
                f"Please check your Home Assistant notification configuration."
            ) from e
        raise

    logger.info("Successfully sent notification")

    result = {
        "success": True,
        "message": "Notification sent successfully",
    }

    if title:
        result["title"] = title
    if target:
        result["target"] = target

    return result
