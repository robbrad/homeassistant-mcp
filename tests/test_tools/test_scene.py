"""Tests for scene control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import EntityNotFoundError, ServiceCallError
from src.homeassistant_mcp.tools.automation.scene import (
    _activate_scene,
    _list_scenes,
    register_scene_tool,
)


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock()

    # Domain-filtering side_effect for get_states
    async def _filtered_get_states(domain=None, area=None, limit=None):
        states = list(client._states_data)
        if domain:
            states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
        return states

    client._states_data = []
    client.get_states = AsyncMock(side_effect=_filtered_get_states)

    return client


@pytest.fixture
def mock_mcp():
    """Create a mock FastMCP instance."""
    mcp = MagicMock()
    mcp.tool = lambda **kwargs: lambda func: func
    return mcp


@pytest.fixture
def mock_states():
    """Create mock scene states."""
    return [
        {
            "entity_id": "scene.movie_time",
            "state": "scening",
            "attributes": {
                "friendly_name": "Movie Time",
            },
        },
        {
            "entity_id": "scene.good_morning",
            "state": "scening",
            "attributes": {
                "friendly_name": "Good Morning",
            },
        },
        {
            "entity_id": "scene.romantic_dinner",
            "state": "scening",
            "attributes": {
                "friendly_name": "Romantic Dinner",
            },
        },
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
            },
        },
    ]


class TestListScenes:
    """Tests for listing scenes."""

    @pytest.mark.asyncio
    async def test_list_scenes_success(self, mock_client, mock_states):
        """Test successfully listing all scenes."""
        mock_client._states_data = mock_states

        result = await _list_scenes(mock_client)

        assert result["success"] is True
        assert result["count"] == 3
        assert len(result["scenes"]) == 3

        # Verify scene information
        scene_ids = [s["entity_id"] for s in result["scenes"]]
        assert "scene.movie_time" in scene_ids
        assert "scene.good_morning" in scene_ids
        assert "scene.romantic_dinner" in scene_ids

        # Verify non-scene entities are filtered out
        assert "light.living_room" not in scene_ids

        # Verify friendly names are included
        movie_scene = next(s for s in result["scenes"] if s["entity_id"] == "scene.movie_time")
        assert movie_scene["name"] == "Movie Time"

    @pytest.mark.asyncio
    async def test_list_scenes_empty(self, mock_client):
        """Test listing scenes when none exist."""
        mock_client._states_data = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"friendly_name": "Living Room"},
            }
        ]

        result = await _list_scenes(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["scenes"] == []

    @pytest.mark.asyncio
    async def test_list_scenes_no_friendly_name(self, mock_client):
        """Test listing scenes without friendly names."""
        mock_client._states_data = [
            {"entity_id": "scene.test_scene", "state": "scening", "attributes": {}}
        ]

        result = await _list_scenes(mock_client)

        assert result["success"] is True
        assert result["count"] == 1
        # Should fall back to entity_id when no friendly_name
        assert result["scenes"][0]["name"] == "scene.test_scene"


class TestActivateScene:
    """Tests for activating scenes."""

    @pytest.mark.asyncio
    async def test_activate_scene_success(self, mock_client):
        """Test successfully activating a scene."""
        scene_id = "scene.movie_time"
        mock_client.get_state.return_value = {
            "entity_id": scene_id,
            "state": "scening",
            "attributes": {"friendly_name": "Movie Time"},
        }
        mock_client.call_service.return_value = None

        result = await _activate_scene(mock_client, scene_id)

        assert result["success"] is True
        assert result["entity_id"] == scene_id
        assert "activated successfully" in result["message"]

        # Verify service call
        mock_client.call_service.assert_called_once_with(
            "scene", "turn_on", {"entity_id": scene_id}
        )

    @pytest.mark.asyncio
    async def test_activate_scene_not_found(self, mock_client):
        """Test activating a non-existent scene."""
        scene_id = "scene.nonexistent"
        mock_client.get_state.side_effect = EntityNotFoundError(f"Entity {scene_id} not found")

        with pytest.raises(EntityNotFoundError):
            await _activate_scene(mock_client, scene_id)

        # Service should not be called
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_activate_scene_invalid_entity_type(self, mock_client):
        """Test activating with a non-scene entity ID."""
        invalid_id = "light.living_room"

        with pytest.raises(EntityNotFoundError) as exc_info:
            await _activate_scene(mock_client, invalid_id)

        assert "not a scene entity" in str(exc_info.value)
        assert "scene." in str(exc_info.value)

        # Should not call get_state or call_service
        mock_client.get_state.assert_not_called()
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_activate_scene_service_call_error(self, mock_client):
        """Test handling service call errors."""
        scene_id = "scene.movie_time"
        mock_client.get_state.return_value = {"entity_id": scene_id, "state": "scening"}
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _activate_scene(mock_client, scene_id)


class TestSceneControlTool:
    """Tests for the scene_control tool function."""

    @pytest.mark.asyncio
    async def test_scene_control_list(self, mock_mcp, mock_client, mock_states):
        """Test scene_control with list action."""
        mock_client._states_data = mock_states

        # Create a real tool registration
        tool_func = None

        def capture_tool(**kwargs):
            def decorator(func):
                nonlocal tool_func
                tool_func = func
                return func

            return decorator

        mock_mcp.tool = capture_tool
        register_scene_tool(mock_mcp, lambda: mock_client)

        # Call the tool
        result = await tool_func(action="list")

        assert result["success"] is True
        assert result["count"] == 3
        assert len(result["scenes"]) == 3

    @pytest.mark.asyncio
    async def test_scene_control_activate_success(self, mock_mcp, mock_client):
        """Test scene_control with activate action."""
        scene_id = "scene.movie_time"
        mock_client.get_state.return_value = {"entity_id": scene_id, "state": "scening"}
        mock_client.call_service.return_value = None

        # Create a real tool registration
        tool_func = None

        def capture_tool(**kwargs):
            def decorator(func):
                nonlocal tool_func
                tool_func = func
                return func

            return decorator

        mock_mcp.tool = capture_tool
        register_scene_tool(mock_mcp, lambda: mock_client)

        # Call the tool
        result = await tool_func(action="activate", scene_id=scene_id)

        assert result["success"] is True
        assert result["entity_id"] == scene_id

    @pytest.mark.asyncio
    async def test_scene_control_activate_missing_scene_id(self, mock_mcp, mock_client):
        """Test scene_control activate without scene_id."""
        # Create a real tool registration
        tool_func = None

        def capture_tool(**kwargs):
            def decorator(func):
                nonlocal tool_func
                tool_func = func
                return func

            return decorator

        mock_mcp.tool = capture_tool
        register_scene_tool(mock_mcp, lambda: mock_client)

        # Call the tool without scene_id
        result = await tool_func(action="activate")

        assert result["success"] is False
        assert "scene_id is required" in result["error"]

    @pytest.mark.asyncio
    async def test_scene_control_entity_not_found(self, mock_mcp, mock_client):
        """Test scene_control with non-existent scene."""
        scene_id = "scene.nonexistent"
        mock_client.get_state.side_effect = EntityNotFoundError(f"Entity {scene_id} not found")

        # Create a real tool registration
        tool_func = None

        def capture_tool(**kwargs):
            def decorator(func):
                nonlocal tool_func
                tool_func = func
                return func

            return decorator

        mock_mcp.tool = capture_tool
        register_scene_tool(mock_mcp, lambda: mock_client)

        # Call the tool
        result = await tool_func(action="activate", scene_id=scene_id)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_scene_control_service_call_error(self, mock_mcp, mock_client):
        """Test scene_control with service call error."""
        scene_id = "scene.movie_time"
        mock_client.get_state.return_value = {"entity_id": scene_id}
        mock_client.call_service.side_effect = ServiceCallError("Service failed")

        # Create a real tool registration
        tool_func = None

        def capture_tool(**kwargs):
            def decorator(func):
                nonlocal tool_func
                tool_func = func
                return func

            return decorator

        mock_mcp.tool = capture_tool
        register_scene_tool(mock_mcp, lambda: mock_client)

        # Call the tool
        result = await tool_func(action="activate", scene_id=scene_id)

        assert result["success"] is False
        assert "Service failed" in result["error"]
