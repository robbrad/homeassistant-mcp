"""Unit tests for the media player control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.devices.media_player import (
    _get_media_player,
    _list_media_players,
    _mute_control,
    _play_media,
    _playback_control,
    _select_source,
    _set_volume,
    _volume_control,
)


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)
    return client


@pytest.fixture
def sample_media_player_states():
    """Sample media player entity states for testing."""
    return [
        {
            "entity_id": "media_player.living_room",
            "state": "playing",
            "attributes": {
                "friendly_name": "Living Room Speaker",
                "volume_level": 0.5,
                "media_title": "Test Song",
                "media_artist": "Test Artist",
                "media_album_name": "Test Album",
                "source": "Spotify",
                "source_list": ["Spotify", "Radio", "Bluetooth"],
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "media_player.bedroom",
            "state": "paused",
            "attributes": {
                "friendly_name": "Bedroom TV",
                "volume_level": 0.3,
                "source": "HDMI 1",
                "source_list": ["HDMI 1", "HDMI 2", "Netflix"],
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "media_player.kitchen",
            "state": "idle",
            "attributes": {
                "friendly_name": "Kitchen Radio",
                "volume_level": 0.7,
            },
            "last_changed": "2024-01-01T10:00:00",
            "last_updated": "2024-01-01T10:00:00",
        },
        {
            "entity_id": "light.garage",
            "state": "on",
            "attributes": {
                "friendly_name": "Garage Light",
            },
        },
    ]


class TestListMediaPlayers:
    """Tests for listing media players."""

    @pytest.mark.asyncio
    async def test_list_media_players_success(self, mock_client, sample_media_player_states):
        """Test successfully listing all media players."""
        mock_client.get_states.return_value = sample_media_player_states

        result = await _list_media_players(mock_client)

        assert result["success"] is True
        assert result["count"] == 3  # Only media players, not the light
        assert len(result["media_players"]) == 3

        # Verify living room player data
        living_room = next(
            player
            for player in result["media_players"]
            if player["entity_id"] == "media_player.living_room"
        )
        assert living_room["name"] == "Living Room Speaker"
        assert living_room["state"] == "playing"
        assert living_room["volume_level"] == 0.5
        assert living_room["media_title"] == "Test Song"
        assert living_room["media_artist"] == "Test Artist"
        assert living_room["source"] == "Spotify"
        assert "Spotify" in living_room["available_sources"]

        # Verify bedroom player (paused)
        bedroom = next(
            player
            for player in result["media_players"]
            if player["entity_id"] == "media_player.bedroom"
        )
        assert bedroom["state"] == "paused"
        assert bedroom["volume_level"] == 0.3

    @pytest.mark.asyncio
    async def test_list_media_players_empty(self, mock_client):
        """Test listing media players when no media players exist."""
        mock_client.get_states.return_value = [
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {},
            }
        ]

        result = await _list_media_players(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["media_players"] == []


class TestGetMediaPlayer:
    """Tests for getting a specific media player."""

    @pytest.mark.asyncio
    async def test_get_media_player_success(self, mock_client):
        """Test successfully getting a specific media player."""
        mock_client.get_state.return_value = {
            "entity_id": "media_player.living_room",
            "state": "playing",
            "attributes": {
                "friendly_name": "Living Room Speaker",
                "volume_level": 0.5,
                "media_title": "Test Song",
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_media_player(mock_client, "media_player.living_room")

        assert result["success"] is True
        assert result["media_player"]["entity_id"] == "media_player.living_room"
        assert result["media_player"]["name"] == "Living Room Speaker"
        assert result["media_player"]["state"] == "playing"
        assert result["media_player"]["last_changed"] == "2024-01-01T12:00:00"

        mock_client.get_state.assert_called_once_with("media_player.living_room")

    @pytest.mark.asyncio
    async def test_get_media_player_not_found(self, mock_client):
        """Test getting a media player that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'media_player.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_media_player(mock_client, "media_player.nonexistent")

    @pytest.mark.asyncio
    async def test_get_media_player_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not a media player."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_media_player(mock_client, "light.garage")

        assert "not a media player entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestPlaybackControl:
    """Tests for playback control actions."""

    @pytest.mark.asyncio
    async def test_play_success(self, mock_client):
        """Test successfully playing media."""
        mock_client.call_service.return_value = {}

        result = await _playback_control(mock_client, "media_player.living_room", "play")

        assert result["success"] is True
        assert result["entity_id"] == "media_player.living_room"
        assert "play" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "media_player", "media_play", {"entity_id": "media_player.living_room"}
        )

    @pytest.mark.asyncio
    async def test_pause_success(self, mock_client):
        """Test successfully pausing media."""
        mock_client.call_service.return_value = {}

        result = await _playback_control(mock_client, "media_player.living_room", "pause")

        assert result["success"] is True
        mock_client.call_service.assert_called_once_with(
            "media_player", "media_pause", {"entity_id": "media_player.living_room"}
        )

    @pytest.mark.asyncio
    async def test_stop_success(self, mock_client):
        """Test successfully stopping media."""
        mock_client.call_service.return_value = {}

        result = await _playback_control(mock_client, "media_player.living_room", "stop")

        assert result["success"] is True
        mock_client.call_service.assert_called_once_with(
            "media_player", "media_stop", {"entity_id": "media_player.living_room"}
        )

    @pytest.mark.asyncio
    async def test_toggle_success(self, mock_client):
        """Test successfully toggling playback."""
        mock_client.call_service.return_value = {}

        result = await _playback_control(mock_client, "media_player.living_room", "toggle")

        assert result["success"] is True
        mock_client.call_service.assert_called_once_with(
            "media_player", "media_play_pause", {"entity_id": "media_player.living_room"}
        )

    @pytest.mark.asyncio
    async def test_next_track_success(self, mock_client):
        """Test successfully skipping to next track."""
        mock_client.call_service.return_value = {}

        result = await _playback_control(mock_client, "media_player.living_room", "next_track")

        assert result["success"] is True
        mock_client.call_service.assert_called_once_with(
            "media_player", "media_next_track", {"entity_id": "media_player.living_room"}
        )

    @pytest.mark.asyncio
    async def test_previous_track_success(self, mock_client):
        """Test successfully going to previous track."""
        mock_client.call_service.return_value = {}

        result = await _playback_control(mock_client, "media_player.living_room", "previous_track")

        assert result["success"] is True
        mock_client.call_service.assert_called_once_with(
            "media_player", "media_previous_track", {"entity_id": "media_player.living_room"}
        )

    @pytest.mark.asyncio
    async def test_playback_control_invalid_entity_type(self, mock_client):
        """Test playback control with invalid entity type."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _playback_control(mock_client, "light.garage", "play")

        assert "not a media player entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_playback_control_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _playback_control(mock_client, "media_player.living_room", "play")


class TestVolumeControl:
    """Tests for volume control actions."""

    @pytest.mark.asyncio
    async def test_set_volume_success(self, mock_client):
        """Test successfully setting volume."""
        mock_client.call_service.return_value = {}

        result = await _set_volume(mock_client, "media_player.living_room", 0.75)

        assert result["success"] is True
        assert result["entity_id"] == "media_player.living_room"
        assert result["volume_level"] == 0.75
        assert "0.75" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "media_player",
            "volume_set",
            {"entity_id": "media_player.living_room", "volume_level": 0.75},
        )

    @pytest.mark.asyncio
    async def test_set_volume_invalid_entity_type(self, mock_client):
        """Test setting volume with invalid entity type."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _set_volume(mock_client, "light.garage", 0.5)

        assert "not a media player entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_volume_up_success(self, mock_client):
        """Test successfully increasing volume."""
        mock_client.call_service.return_value = {}

        result = await _volume_control(mock_client, "media_player.living_room", "volume_up")

        assert result["success"] is True
        assert result["entity_id"] == "media_player.living_room"

        mock_client.call_service.assert_called_once_with(
            "media_player", "volume_up", {"entity_id": "media_player.living_room"}
        )

    @pytest.mark.asyncio
    async def test_volume_down_success(self, mock_client):
        """Test successfully decreasing volume."""
        mock_client.call_service.return_value = {}

        result = await _volume_control(mock_client, "media_player.living_room", "volume_down")

        assert result["success"] is True
        mock_client.call_service.assert_called_once_with(
            "media_player", "volume_down", {"entity_id": "media_player.living_room"}
        )

    @pytest.mark.asyncio
    async def test_volume_control_invalid_entity_type(self, mock_client):
        """Test volume control with invalid entity type."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _volume_control(mock_client, "light.garage", "volume_up")

        assert "not a media player entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestMuteControl:
    """Tests for mute control actions."""

    @pytest.mark.asyncio
    async def test_mute_success(self, mock_client):
        """Test successfully muting media player."""
        mock_client.call_service.return_value = {}

        result = await _mute_control(mock_client, "media_player.living_room", "mute")

        assert result["success"] is True
        assert result["entity_id"] == "media_player.living_room"
        assert result["is_muted"] is True
        assert "muted" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "media_player",
            "volume_mute",
            {"entity_id": "media_player.living_room", "is_volume_muted": True},
        )

    @pytest.mark.asyncio
    async def test_unmute_success(self, mock_client):
        """Test successfully unmuting media player."""
        mock_client.call_service.return_value = {}

        result = await _mute_control(mock_client, "media_player.living_room", "unmute")

        assert result["success"] is True
        assert result["entity_id"] == "media_player.living_room"
        assert result["is_muted"] is False
        assert "unmuted" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "media_player",
            "volume_mute",
            {"entity_id": "media_player.living_room", "is_volume_muted": False},
        )

    @pytest.mark.asyncio
    async def test_mute_control_invalid_entity_type(self, mock_client):
        """Test mute control with invalid entity type."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _mute_control(mock_client, "light.garage", "mute")

        assert "not a media player entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestSelectSource:
    """Tests for source selection."""

    @pytest.mark.asyncio
    async def test_select_source_success(self, mock_client):
        """Test successfully selecting input source."""
        mock_client.call_service.return_value = {}

        result = await _select_source(mock_client, "media_player.living_room", "HDMI 1")

        assert result["success"] is True
        assert result["entity_id"] == "media_player.living_room"
        assert result["source"] == "HDMI 1"
        assert "HDMI 1" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "media_player",
            "select_source",
            {"entity_id": "media_player.living_room", "source": "HDMI 1"},
        )

    @pytest.mark.asyncio
    async def test_select_source_invalid_entity_type(self, mock_client):
        """Test selecting source with invalid entity type."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _select_source(mock_client, "light.garage", "HDMI 1")

        assert "not a media player entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_select_source_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _select_source(mock_client, "media_player.living_room", "HDMI 1")


class TestPlayMedia:
    """Tests for playing specific media."""

    @pytest.mark.asyncio
    async def test_play_media_success(self, mock_client):
        """Test successfully playing specific media."""
        mock_client.call_service.return_value = {}

        result = await _play_media(
            mock_client,
            "media_player.living_room",
            "http://example.com/song.mp3",
            "music",
        )

        assert result["success"] is True
        assert result["entity_id"] == "media_player.living_room"
        assert result["media_content_id"] == "http://example.com/song.mp3"
        assert result["media_content_type"] == "music"
        assert "music" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "media_player",
            "play_media",
            {
                "entity_id": "media_player.living_room",
                "media_content_id": "http://example.com/song.mp3",
                "media_content_type": "music",
            },
        )

    @pytest.mark.asyncio
    async def test_play_media_video(self, mock_client):
        """Test playing video content."""
        mock_client.call_service.return_value = {}

        result = await _play_media(
            mock_client,
            "media_player.living_room",
            "http://example.com/video.mp4",
            "video",
        )

        assert result["success"] is True
        assert result["media_content_type"] == "video"

    @pytest.mark.asyncio
    async def test_play_media_playlist(self, mock_client):
        """Test playing playlist."""
        mock_client.call_service.return_value = {}

        result = await _play_media(
            mock_client,
            "media_player.living_room",
            "spotify:playlist:abc123",
            "playlist",
        )

        assert result["success"] is True
        assert result["media_content_type"] == "playlist"

    @pytest.mark.asyncio
    async def test_play_media_invalid_entity_type(self, mock_client):
        """Test playing media with invalid entity type."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _play_media(mock_client, "light.garage", "http://example.com/song.mp3", "music")

        assert "not a media player entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_play_media_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _play_media(
                mock_client,
                "media_player.living_room",
                "http://example.com/song.mp3",
                "music",
            )


class TestMediaPlayerControlIntegration:
    """Integration tests for the media_player_control tool function."""

    @pytest.mark.asyncio
    async def test_media_player_control_list_action(self, mock_client, sample_media_player_states):
        """Test the media_player_control function with list action."""
        from src.homeassistant_mcp.tools.devices.media_player import register_media_player_tool

        mock_client.get_states.return_value = sample_media_player_states

        # Create a mock FastMCP instance
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        # Register the tool
        register_media_player_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_media_player_control_missing_entity_id(self):
        """Test media_player_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.devices.media_player import register_media_player_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_media_player_tool(mock_mcp, lambda: mock_client)

        # Test get without entity_id
        result = await registered_func(action="get")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test play without entity_id
        result = await registered_func(action="play")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test set_volume without entity_id
        result = await registered_func(action="set_volume", volume_level=0.5)
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

    @pytest.mark.asyncio
    async def test_media_player_control_missing_parameters(self):
        """Test media_player_control with missing required parameters."""
        from src.homeassistant_mcp.tools.devices.media_player import register_media_player_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_media_player_tool(mock_mcp, lambda: mock_client)

        # Test set_volume without volume_level
        result = await registered_func(action="set_volume", entity_id="media_player.test")
        assert result["success"] is False
        assert "volume_level is required" in result["error"]

        # Test select_source without source
        result = await registered_func(action="select_source", entity_id="media_player.test")
        assert result["success"] is False
        assert "source is required" in result["error"]

        # Test play_media without media_content_id
        result = await registered_func(
            action="play_media", entity_id="media_player.test", media_content_type="music"
        )
        assert result["success"] is False
        assert "media_content_id is required" in result["error"]

        # Test play_media without media_content_type
        result = await registered_func(
            action="play_media",
            entity_id="media_player.test",
            media_content_id="http://example.com/song.mp3",
        )
        assert result["success"] is False
        assert "media_content_type is required" in result["error"]

    @pytest.mark.asyncio
    async def test_media_player_control_error_handling(self):
        """Test media_player_control error handling."""
        from src.homeassistant_mcp.tools.devices.media_player import register_media_player_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.get_state.side_effect = EntityNotFoundError("Entity not found")

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_media_player_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="media_player.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
        assert result["error_type"] == "entity_not_found"

    @pytest.mark.asyncio
    async def test_media_player_control_all_playback_actions(self):
        """Test all playback control actions."""
        from src.homeassistant_mcp.tools.devices.media_player import register_media_player_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.call_service.return_value = {}

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_media_player_tool(mock_mcp, lambda: mock_client)

        # Test all playback actions
        playback_actions = ["play", "pause", "stop", "toggle", "next_track", "previous_track"]
        for action in playback_actions:
            result = await registered_func(action=action, entity_id="media_player.test")
            assert result["success"] is True, f"Failed for action: {action}"
            assert result["entity_id"] == "media_player.test"
