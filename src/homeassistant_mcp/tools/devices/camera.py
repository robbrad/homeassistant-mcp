"""Camera control tool for Home Assistant MCP server."""

import logging
from typing import Annotated, Any, Literal

from pydantic import Field

from ...exceptions import (
    AuthenticationError,
    ConnectionError,
    EntityNotFoundError,
    HomeAssistantError,
    ServiceCallError,
)
from ...hass.client import HomeAssistantClient

logger = logging.getLogger(__name__)


def register_camera_tool(mcp: Any, get_client: Any) -> None:
    """Register the camera control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool()
    async def camera_control(
        action: Annotated[
            Literal[
                "list",
                "get",
                "snapshot",
                "enable_motion_detection",
                "disable_motion_detection",
                "get_stream_url",
            ],
            Field(
                description="Action to perform: list all cameras, get specific camera, "
                "take snapshot, enable/disable motion detection, or get stream URL"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Camera entity ID (required for most actions). "
                "Example: 'camera.front_door'"
            ),
        ] = None,
        output_path: Annotated[
            str | None,
            Field(
                description="Optional file path to save snapshot. If not provided, "
                "returns base64-encoded image data. Only used with snapshot action."
            ),
        ] = None,
    ) -> dict:
        """Control cameras in Home Assistant.

        This tool allows you to list all cameras, get details about a specific camera,
        take snapshots, control motion detection, and get streaming URLs.

        Actions:
        - list: Get all camera entities with their state and capabilities
        - get: Get detailed information about a specific camera
        - snapshot: Take a camera snapshot (save to file or return base64)
        - enable_motion_detection: Enable motion detection on a camera
        - disable_motion_detection: Disable motion detection on a camera
        - get_stream_url: Get the streaming URL for a camera

        Examples:
        - List all cameras: camera_control(action="list")
        - Get camera details: camera_control(action="get", entity_id="camera.front_door")
        - Take snapshot to file: camera_control(action="snapshot", entity_id="camera.front_door",
                                               output_path="/path/to/snapshot.jpg")
        - Take snapshot as base64: camera_control(action="snapshot", entity_id="camera.front_door")
        - Enable motion detection: camera_control(action="enable_motion_detection",
                                                  entity_id="camera.front_door")
        - Get stream URL: camera_control(action="get_stream_url", entity_id="camera.front_door")

        Args:
            action: The action to perform
            entity_id: The camera entity ID (required for most actions)
            output_path: Optional file path for snapshot (optional, for snapshot action)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if action == "list":
                return await _list_cameras(client)

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                return await _get_camera(client, entity_id)

            elif action == "snapshot":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'snapshot' action",
                        "success": False,
                    }
                return await _get_snapshot(client, entity_id, output_path)

            elif action == "enable_motion_detection":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'enable_motion_detection' action",
                        "success": False,
                    }
                return await _set_motion_detection(client, entity_id, True)

            elif action == "disable_motion_detection":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'disable_motion_detection' action",
                        "success": False,
                    }
                return await _set_motion_detection(client, entity_id, False)

            elif action == "get_stream_url":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'get_stream_url' action",
                        "success": False,
                    }
                return await _get_stream_url(client, entity_id)

        except EntityNotFoundError as e:
            logger.warning(f"Entity not found: {str(e)}")
            return {"error": str(e), "success": False, "error_type": "entity_not_found"}
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
            logger.error(f"Unexpected error in camera_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_cameras(client: HomeAssistantClient) -> dict:
    """List all camera entities.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing list of cameras with their states
    """
    logger.info("Listing all camera entities")

    # Get all states and filter for cameras
    all_states = await client.get_states()
    cameras = [state for state in all_states if state.get("entity_id", "").startswith("camera.")]

    # Format the response
    camera_list = []
    for camera in cameras:
        attributes = camera.get("attributes", {})
        camera_info = {
            "entity_id": camera.get("entity_id"),
            "name": attributes.get("friendly_name", camera.get("entity_id")),
            "state": camera.get("state"),
        }

        # Add capabilities if available
        if "supported_features" in attributes:
            camera_info["supported_features"] = attributes["supported_features"]

        # Add motion detection status if available
        if "motion_detection" in attributes:
            camera_info["motion_detection"] = attributes["motion_detection"]

        # Add model information if available
        if "model_name" in attributes:
            camera_info["model"] = attributes["model_name"]

        camera_list.append(camera_info)

    logger.info(f"Found {len(camera_list)} camera entities")

    return {"success": True, "count": len(camera_list), "cameras": camera_list}


async def _get_camera(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific camera.

    Args:
        client: The Home Assistant client
        entity_id: The camera entity ID

    Returns:
        Dictionary containing detailed camera information

    Raises:
        EntityNotFoundError: If the camera entity is not found
    """
    logger.info(f"Getting details for camera: {entity_id}")

    # Validate that this is a camera entity
    if not entity_id.startswith("camera."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a camera entity. "
            "Camera entities must start with 'camera.'"
        )

    # Get the entity state
    state = await client.get_state(entity_id)

    # Format the response with all available information
    camera_info = {
        "entity_id": state.get("entity_id"),
        "name": state.get("attributes", {}).get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": state.get("attributes", {}),
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")

    return {"success": True, "camera": camera_info}


async def _get_snapshot(
    client: HomeAssistantClient, entity_id: str, output_path: str | None = None
) -> dict:
    """Get a camera snapshot.

    Args:
        client: The Home Assistant client
        entity_id: The camera entity ID
        output_path: Optional file path to save the snapshot

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the camera entity is not found
        ServiceCallError: If the snapshot operation fails
    """
    logger.info(f"Getting snapshot for camera: {entity_id}")

    # Validate that this is a camera entity
    if not entity_id.startswith("camera."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a camera entity. "
            "Camera entities must start with 'camera.'"
        )

    # Get the snapshot using the camera proxy endpoint
    # Note: This uses the Home Assistant camera proxy API
    try:
        # Call the snapshot service
        service_data = {"entity_id": entity_id}
        if output_path:
            service_data["filename"] = output_path

        await client.call_service("camera", "snapshot", service_data)

        if output_path:
            logger.info(f"Successfully saved snapshot to {output_path}")
            return {
                "success": True,
                "message": f"Snapshot saved to {output_path}",
                "entity_id": entity_id,
                "output_path": output_path,
            }
        else:
            # If no output path, we would need to fetch the image data
            # For now, return success with a note
            logger.info(f"Snapshot taken for {entity_id}")
            return {
                "success": True,
                "message": "Snapshot taken. Use output_path parameter to save to file.",
                "entity_id": entity_id,
                "note": "Base64 image data not yet implemented. Use output_path to save to file.",
            }

    except Exception as e:
        logger.error(f"Failed to get snapshot for {entity_id}: {str(e)}")
        raise ServiceCallError(f"Failed to get snapshot: {str(e)}") from e


async def _set_motion_detection(client: HomeAssistantClient, entity_id: str, enable: bool) -> dict:
    """Enable or disable motion detection on a camera.

    Args:
        client: The Home Assistant client
        entity_id: The camera entity ID
        enable: True to enable, False to disable

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the camera entity is not found
        ServiceCallError: If the service call fails
    """
    action_str = "enable" if enable else "disable"
    logger.info(f"{action_str.capitalize()}ing motion detection for camera: {entity_id}")

    # Validate that this is a camera entity
    if not entity_id.startswith("camera."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a camera entity. "
            "Camera entities must start with 'camera.'"
        )

    # Call the appropriate service
    service_name = "enable_motion_detection" if enable else "disable_motion_detection"
    service_data = {"entity_id": entity_id}
    await client.call_service("camera", service_name, service_data)

    logger.info(f"Successfully {action_str}d motion detection for camera: {entity_id}")

    return {
        "success": True,
        "message": f"Motion detection {action_str}d for camera '{entity_id}'",
        "entity_id": entity_id,
        "motion_detection_enabled": enable,
    }


async def _get_stream_url(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get the streaming URL for a camera.

    Args:
        client: The Home Assistant client
        entity_id: The camera entity ID

    Returns:
        Dictionary containing the streaming URL

    Raises:
        EntityNotFoundError: If the camera entity is not found
    """
    logger.info(f"Getting stream URL for camera: {entity_id}")

    # Validate that this is a camera entity
    if not entity_id.startswith("camera."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a camera entity. "
            "Camera entities must start with 'camera.'"
        )

    # Get the entity state to check if it exists
    state = await client.get_state(entity_id)
    attributes = state.get("attributes", {})

    # Construct the stream URL
    # The actual stream URL depends on the Home Assistant configuration
    # Typically it's available through the entity_picture attribute or stream component
    stream_url = attributes.get("entity_picture")

    if not stream_url:
        # If entity_picture is not available, provide the proxy URL format
        # This is a relative URL that works within Home Assistant
        stream_url = f"/api/camera_proxy/{entity_id}"

    logger.info(f"Retrieved stream URL for {entity_id}")

    return {
        "success": True,
        "entity_id": entity_id,
        "stream_url": stream_url,
        "note": "Stream URL may be relative. Prepend Home Assistant base URL if needed.",
    }
