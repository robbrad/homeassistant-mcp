"""Camera proxy tool for retrieving camera images through Home Assistant."""

import base64
import logging
from typing import Any

from ...exceptions import HomeAssistantError

logger = logging.getLogger(__name__)


def register_camera_proxy_tool(mcp: Any, get_client: Any) -> None:
    """Register the camera proxy tool with the MCP server.

    Args:
        mcp: FastMCP server instance
        get_client: Function that returns the HomeAssistantClient instance
    """

    @mcp.tool()
    async def camera_proxy_get(
        entity_id: str,
        width: int | None = None,
        height: int | None = None,
        return_base64: bool = True,
    ) -> dict[str, Any]:
        """Get camera image through Home Assistant proxy.

        Retrieves camera images through Home Assistant's camera proxy endpoint,
        with optional resizing and format conversion.

        Args:
            entity_id: Camera entity ID (e.g., "camera.front_door")
            width: Optional image width in pixels for resizing
            height: Optional image height in pixels for resizing
            return_base64: Return as base64 string (default) or binary data

        Returns:
            Dictionary containing:
            - success: Boolean indicating success
            - image_data: Base64-encoded image string (if return_base64=True)
            - image_bytes: Binary image data (if return_base64=False)
            - content_type: MIME type of the image (e.g., "image/jpeg")
            - width: Requested width (if specified)
            - height: Requested height (if specified)
            - entity_id: Camera entity ID

        Examples:
            Get camera image as base64:
            >>> camera_proxy_get("camera.front_door")

            Get resized camera image:
            >>> camera_proxy_get("camera.front_door", width=640, height=480)

            Get binary image data:
            >>> camera_proxy_get("camera.front_door", return_base64=False)

        Note:
            - Images are retrieved through Home Assistant's proxy for security
            - Resizing is performed by Home Assistant if width/height specified
            - Base64 encoding is recommended for AI assistant compatibility
            - Binary format is more efficient for direct file operations
        """
        try:
            client = get_client()

            logger.info(
                f"Retrieving camera image for {entity_id} "
                f"(width={width}, height={height}, base64={return_base64})"
            )

            # Get camera image from Home Assistant
            image_bytes = await client.get_camera_proxy(
                entity_id=entity_id, width=width, height=height
            )

            # Determine content type (Home Assistant typically returns JPEG)
            # In a real implementation, we could inspect the image header
            content_type = "image/jpeg"

            result: dict[str, Any] = {
                "success": True,
                "entity_id": entity_id,
                "content_type": content_type,
            }

            if width is not None:
                result["width"] = width
            if height is not None:
                result["height"] = height

            if return_base64:
                # Encode as base64 for AI assistant compatibility
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                result["image_data"] = image_base64
                logger.info(
                    f"Successfully retrieved camera image for {entity_id} "
                    f"({len(image_base64)} base64 characters)"
                )
            else:
                # Return binary data
                result["image_bytes"] = image_bytes
                logger.info(
                    f"Successfully retrieved camera image for {entity_id} "
                    f"({len(image_bytes)} bytes)"
                )

            return result

        except HomeAssistantError as e:
            logger.error(f"Failed to retrieve camera image for {entity_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "entity_id": entity_id,
            }
        except Exception as e:
            logger.exception(f"Unexpected error retrieving camera image for {entity_id}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "UnexpectedError",
                "entity_id": entity_id,
            }
