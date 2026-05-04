"""Scene activation tool for Home Assistant MCP server."""

import logging
from typing import Annotated, Any, Literal

from fastmcp import Context
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


def register_scene_tool(mcp: Any, get_client: Any) -> None:
    """Register the scene control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool(
        annotations={"openWorldHint": True},
        tags={"automation", "scene"},
        timeout=30,
    )
    async def scene_control(
        action: Annotated[
            Literal["list", "activate"],
            Field(description="Action to perform: list all scenes or activate a specific scene"),
        ],
        scene_id: Annotated[
            str | None,
            Field(
                description="Scene entity ID (required for activate). Example: 'scene.movie_time'"
            ),
        ] = None,
        ctx: Context = None,
    ) -> dict:
        """Manage and activate Home Assistant scenes.

        This tool allows you to list all available scenes and activate specific scenes
        to apply predefined device configurations.

        Actions:
        - list: Get all available scene entities
        - activate: Trigger a specific scene to apply its configuration

        Examples:
        - List all scenes: scene_control(action="list")
        - Activate scene: scene_control(action="activate", scene_id="scene.movie_time")

        Args:
            action: The action to perform
            scene_id: The scene entity ID (required for activate)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if ctx:
                await ctx.info(f"Executing scene_control action={action}")

            if action == "list":
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _list_scenes(client)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

            elif action == "activate":
                if not scene_id:
                    return {"error": "scene_id is required for 'activate' action", "success": False}
                if ctx:
                    await ctx.report_progress(progress=50, total=100)
                result = await _activate_scene(client, scene_id)
                if ctx:
                    await ctx.report_progress(progress=100, total=100)
                return result

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
            logger.error(f"Unexpected error in scene_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_scenes(client: HomeAssistantClient) -> dict:
    """List all scene entities.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing list of scenes
    """
    logger.info("Listing all scene entities")

    # Get all states and filter for scenes
    all_states = await client.get_states()
    scenes = [state for state in all_states if state.get("entity_id", "").startswith("scene.")]

    # Format the response
    scene_list = []
    for scene in scenes:
        scene_info = {
            "entity_id": scene.get("entity_id"),
            "name": scene.get("attributes", {}).get("friendly_name", scene.get("entity_id")),
        }

        scene_list.append(scene_info)

    logger.info(f"Found {len(scene_list)} scene entities")

    return {"success": True, "count": len(scene_list), "scenes": scene_list}


async def _activate_scene(client: HomeAssistantClient, scene_id: str) -> dict:
    """Activate a scene.

    Args:
        client: The Home Assistant client
        scene_id: The scene entity ID

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the scene entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Activating scene: {scene_id}")

    # Validate that this is a scene entity
    if not scene_id.startswith("scene."):
        raise EntityNotFoundError(
            f"Entity '{scene_id}' is not a scene entity. Scene entities must start with 'scene.'"
        )

    # Verify the scene exists
    await client.get_state(scene_id)

    # Call the turn_on service to activate the scene
    service_data = {"entity_id": scene_id}
    await client.call_service("scene", "turn_on", service_data)

    logger.info(f"Successfully activated scene: {scene_id}")

    return {
        "success": True,
        "message": f"Scene '{scene_id}' activated successfully",
        "entity_id": scene_id,
    }
