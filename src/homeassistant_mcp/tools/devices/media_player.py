"""Media player control tool for Home Assistant MCP server."""

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


def register_media_player_tool(mcp: Any, get_client: Any) -> None:
    """Register the media player control tool with the FastMCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance
    """

    @mcp.tool()
    async def media_player_control(
        action: Annotated[
            Literal[
                "list",
                "get",
                "play",
                "pause",
                "stop",
                "toggle",
                "next_track",
                "previous_track",
                "set_volume",
                "volume_up",
                "volume_down",
                "mute",
                "unmute",
                "select_source",
                "play_media",
            ],
            Field(
                description="Action to perform: list all media players, get specific player, "
                "control playback (play/pause/stop/toggle/next/previous), "
                "control volume (set_volume/volume_up/volume_down/mute/unmute), "
                "select input source, or play specific media"
            ),
        ],
        entity_id: Annotated[
            str | None,
            Field(
                description="Media player entity ID (required for most actions). "
                "Example: 'media_player.living_room'"
            ),
        ] = None,
        volume_level: Annotated[
            float | None,
            Field(
                ge=0.0,
                le=1.0,
                description="Volume level (0.0-1.0). Only used with set_volume action.",
            ),
        ] = None,
        source: Annotated[
            str | None,
            Field(description="Input source name. Only used with select_source action."),
        ] = None,
        media_content_id: Annotated[
            str | None,
            Field(
                description="Media content identifier (URL, file path, or content ID). "
                "Only used with play_media action."
            ),
        ] = None,
        media_content_type: Annotated[
            str | None,
            Field(
                description="Media content type (e.g., 'music', 'video', 'playlist', 'url'). "
                "Only used with play_media action."
            ),
        ] = None,
    ) -> dict:
        """Control media players in Home Assistant.

        This tool allows you to list all media players, get details about a specific player,
        control playback, adjust volume, switch input sources, and play specific media content.

        Actions:
        - list: Get all media player entities with their current state, volume, and media info
        - get: Get detailed information about a specific media player
        - play: Start playback
        - pause: Pause playback
        - stop: Stop playback
        - toggle: Toggle between play and pause
        - next_track: Skip to next track
        - previous_track: Go to previous track
        - set_volume: Set volume level (0.0-1.0)
        - volume_up: Increase volume
        - volume_down: Decrease volume
        - mute: Mute audio
        - unmute: Unmute audio
        - select_source: Switch input source
        - play_media: Play specific media content

        Examples:
        - List all players: media_player_control(action="list")
        - Get player details: media_player_control(action="get", entity_id="media_player.living_room")
        - Play: media_player_control(action="play", entity_id="media_player.living_room")
        - Pause: media_player_control(action="pause", entity_id="media_player.living_room")
        - Set volume: media_player_control(action="set_volume", entity_id="media_player.living_room", volume_level=0.5)
        - Select source: media_player_control(action="select_source", entity_id="media_player.living_room", source="HDMI 1")
        - Play media: media_player_control(action="play_media", entity_id="media_player.living_room",
                                          media_content_id="http://example.com/song.mp3", media_content_type="music")

        Note: The list action returns entities from the HA states API. If some
            entities are missing, use states_control(action="list", domain="media_player")
            or list_devices(domain="media_player") for a more complete view.

        Args:
            action: The action to perform
            entity_id: The media player entity ID (required for most actions)
            volume_level: Volume level 0.0-1.0 (optional, for set_volume)
            source: Input source name (optional, for select_source)
            media_content_id: Media content identifier (optional, for play_media)
            media_content_type: Media content type (optional, for play_media)

        Returns:
            Dictionary containing the result of the action
        """
        client: HomeAssistantClient = get_client()

        try:
            if action == "list":
                return await _list_media_players(client)

            elif action == "get":
                if not entity_id:
                    return {"error": "entity_id is required for 'get' action", "success": False}
                return await _get_media_player(client, entity_id)

            elif action in ["play", "pause", "stop", "toggle", "next_track", "previous_track"]:
                if not entity_id:
                    return {
                        "error": f"entity_id is required for '{action}' action",
                        "success": False,
                    }
                return await _playback_control(client, entity_id, action)

            elif action == "set_volume":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'set_volume' action",
                        "success": False,
                    }
                if volume_level is None:
                    return {
                        "error": "volume_level is required for 'set_volume' action",
                        "success": False,
                    }
                return await _set_volume(client, entity_id, volume_level)

            elif action in ["volume_up", "volume_down"]:
                if not entity_id:
                    return {
                        "error": f"entity_id is required for '{action}' action",
                        "success": False,
                    }
                return await _volume_control(client, entity_id, action)

            elif action in ["mute", "unmute"]:
                if not entity_id:
                    return {
                        "error": f"entity_id is required for '{action}' action",
                        "success": False,
                    }
                return await _mute_control(client, entity_id, action)

            elif action == "select_source":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'select_source' action",
                        "success": False,
                    }
                if not source:
                    return {
                        "error": "source is required for 'select_source' action",
                        "success": False,
                    }
                return await _select_source(client, entity_id, source)

            elif action == "play_media":
                if not entity_id:
                    return {
                        "error": "entity_id is required for 'play_media' action",
                        "success": False,
                    }
                if not media_content_id:
                    return {
                        "error": "media_content_id is required for 'play_media' action",
                        "success": False,
                    }
                if not media_content_type:
                    return {
                        "error": "media_content_type is required for 'play_media' action",
                        "success": False,
                    }
                return await _play_media(client, entity_id, media_content_id, media_content_type)

            # This should never be reached due to Literal type, but mypy needs it
            return {"error": f"Unknown action: {action}", "success": False}

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
            logger.error(f"Unexpected error in media_player_control: {str(e)}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "success": False,
                "error_type": "unexpected_error",
            }


async def _list_media_players(client: HomeAssistantClient) -> dict:
    """List all media player entities.

    Args:
        client: The Home Assistant client

    Returns:
        Dictionary containing list of media players with their states
    """
    logger.info("Listing all media player entities")

    # Get all states and filter for media players
    all_states = await client.get_states()
    media_players = [
        state for state in all_states if state.get("entity_id", "").startswith("media_player.")
    ]

    # Format the response
    player_list = []
    for player in media_players:
        attributes = player.get("attributes", {})
        player_info = {
            "entity_id": player.get("entity_id"),
            "name": attributes.get("friendly_name", player.get("entity_id")),
            "state": player.get("state"),
        }

        # Add volume if available
        if "volume_level" in attributes:
            player_info["volume_level"] = attributes["volume_level"]

        # Add media information if available
        if "media_title" in attributes:
            player_info["media_title"] = attributes["media_title"]
        if "media_artist" in attributes:
            player_info["media_artist"] = attributes["media_artist"]
        if "media_album_name" in attributes:
            player_info["media_album_name"] = attributes["media_album_name"]

        # Add source information if available
        if "source" in attributes:
            player_info["source"] = attributes["source"]
        if "source_list" in attributes:
            player_info["available_sources"] = attributes["source_list"]

        player_list.append(player_info)

    logger.info(f"Found {len(player_list)} media player entities")

    return {"success": True, "count": len(player_list), "media_players": player_list}


async def _get_media_player(client: HomeAssistantClient, entity_id: str) -> dict:
    """Get detailed information about a specific media player.

    Args:
        client: The Home Assistant client
        entity_id: The media player entity ID

    Returns:
        Dictionary containing detailed media player information

    Raises:
        EntityNotFoundError: If the media player entity is not found
    """
    logger.info(f"Getting details for media player: {entity_id}")

    # Validate that this is a media player entity
    if not entity_id.startswith("media_player."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a media player entity. "
            "Media player entities must start with 'media_player.'"
        )

    # Get the entity state
    state = await client.get_state(entity_id)

    # Format the response with all available information
    player_info = {
        "entity_id": state.get("entity_id"),
        "name": state.get("attributes", {}).get("friendly_name", entity_id),
        "state": state.get("state"),
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": state.get("attributes", {}),
    }

    logger.info(f"Retrieved details for {entity_id}: state={state.get('state')}")

    return {"success": True, "media_player": player_info}


async def _playback_control(client: HomeAssistantClient, entity_id: str, action: str) -> dict:
    """Control media player playback.

    Args:
        client: The Home Assistant client
        entity_id: The media player entity ID
        action: The playback action (play, pause, stop, toggle, next_track, previous_track)

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the media player entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Performing {action} on media player: {entity_id}")

    # Validate that this is a media player entity
    if not entity_id.startswith("media_player."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a media player entity. "
            "Media player entities must start with 'media_player.'"
        )

    # Map action to service name
    service_map = {
        "play": "media_play",
        "pause": "media_pause",
        "stop": "media_stop",
        "toggle": "media_play_pause",
        "next_track": "media_next_track",
        "previous_track": "media_previous_track",
    }

    service_name = service_map.get(action)
    if not service_name:
        return {"error": f"Unknown playback action: {action}", "success": False}

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("media_player", service_name, service_data)

    logger.info(f"Successfully performed {action} on media player: {entity_id}")

    return {
        "success": True,
        "message": f"Media player '{entity_id}' {action} executed",
        "entity_id": entity_id,
    }


async def _set_volume(client: HomeAssistantClient, entity_id: str, volume_level: float) -> dict:
    """Set the volume level of a media player.

    Args:
        client: The Home Assistant client
        entity_id: The media player entity ID
        volume_level: Volume level (0.0-1.0)

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the media player entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Setting volume to {volume_level} for media player: {entity_id}")

    # Validate that this is a media player entity
    if not entity_id.startswith("media_player."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a media player entity. "
            "Media player entities must start with 'media_player.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id, "volume_level": volume_level}
    await client.call_service("media_player", "volume_set", service_data)

    logger.info(f"Successfully set volume to {volume_level} for media player: {entity_id}")

    return {
        "success": True,
        "message": f"Media player '{entity_id}' volume set to {volume_level}",
        "entity_id": entity_id,
        "volume_level": volume_level,
    }


async def _volume_control(client: HomeAssistantClient, entity_id: str, action: str) -> dict:
    """Control media player volume (up/down).

    Args:
        client: The Home Assistant client
        entity_id: The media player entity ID
        action: The volume action (volume_up or volume_down)

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the media player entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Performing {action} on media player: {entity_id}")

    # Validate that this is a media player entity
    if not entity_id.startswith("media_player."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a media player entity. "
            "Media player entities must start with 'media_player.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id}
    await client.call_service("media_player", action, service_data)

    logger.info(f"Successfully performed {action} on media player: {entity_id}")

    return {
        "success": True,
        "message": f"Media player '{entity_id}' {action} executed",
        "entity_id": entity_id,
    }


async def _mute_control(client: HomeAssistantClient, entity_id: str, action: str) -> dict:
    """Control media player mute state.

    Args:
        client: The Home Assistant client
        entity_id: The media player entity ID
        action: The mute action (mute or unmute)

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the media player entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Performing {action} on media player: {entity_id}")

    # Validate that this is a media player entity
    if not entity_id.startswith("media_player."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a media player entity. "
            "Media player entities must start with 'media_player.'"
        )

    # Determine mute state
    is_muted = action == "mute"

    # Call the service
    service_data = {"entity_id": entity_id, "is_volume_muted": is_muted}
    await client.call_service("media_player", "volume_mute", service_data)

    logger.info(f"Successfully performed {action} on media player: {entity_id}")

    return {
        "success": True,
        "message": f"Media player '{entity_id}' {action}d",
        "entity_id": entity_id,
        "is_muted": is_muted,
    }


async def _select_source(client: HomeAssistantClient, entity_id: str, source: str) -> dict:
    """Select input source for a media player.

    Args:
        client: The Home Assistant client
        entity_id: The media player entity ID
        source: The source name to select

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the media player entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Selecting source '{source}' for media player: {entity_id}")

    # Validate that this is a media player entity
    if not entity_id.startswith("media_player."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a media player entity. "
            "Media player entities must start with 'media_player.'"
        )

    # Call the service
    service_data = {"entity_id": entity_id, "source": source}
    await client.call_service("media_player", "select_source", service_data)

    logger.info(f"Successfully selected source '{source}' for media player: {entity_id}")

    return {
        "success": True,
        "message": f"Media player '{entity_id}' source set to '{source}'",
        "entity_id": entity_id,
        "source": source,
    }


async def _play_media(
    client: HomeAssistantClient, entity_id: str, media_content_id: str, media_content_type: str
) -> dict:
    """Play specific media content on a media player.

    Args:
        client: The Home Assistant client
        entity_id: The media player entity ID
        media_content_id: Media content identifier (URL, file path, or content ID)
        media_content_type: Media content type (e.g., 'music', 'video', 'playlist', 'url')

    Returns:
        Dictionary containing the result of the operation

    Raises:
        EntityNotFoundError: If the media player entity is not found
        ServiceCallError: If the service call fails
    """
    logger.info(f"Playing media on {entity_id}: type={media_content_type}, id={media_content_id}")

    # Validate that this is a media player entity
    if not entity_id.startswith("media_player."):
        raise EntityNotFoundError(
            f"Entity '{entity_id}' is not a media player entity. "
            "Media player entities must start with 'media_player.'"
        )

    # Call the service
    service_data = {
        "entity_id": entity_id,
        "media_content_id": media_content_id,
        "media_content_type": media_content_type,
    }
    await client.call_service("media_player", "play_media", service_data)

    logger.info(f"Successfully started playing media on media player: {entity_id}")

    return {
        "success": True,
        "message": f"Media player '{entity_id}' playing {media_content_type}",
        "entity_id": entity_id,
        "media_content_id": media_content_id,
        "media_content_type": media_content_type,
    }
