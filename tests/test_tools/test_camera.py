"""Unit tests for the camera control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.devices.camera import (
    _get_camera,
    _get_snapshot,
    _get_stream_url,
    _list_cameras,
    _set_motion_detection,
)


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)
    return client


@pytest.fixture
def sample_camera_states():
    """Sample camera entity states for testing."""
    return [
        {
            "entity_id": "camera.front_door",
            "state": "idle",
            "attributes": {
                "friendly_name": "Front Door Camera",
                "supported_features": 3,
                "motion_detection": True,
                "model_name": "Nest Cam",
                "entity_picture": "/api/camera_proxy/camera.front_door",
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "camera.back_yard",
            "state": "recording",
            "attributes": {
                "friendly_name": "Back Yard Camera",
                "supported_features": 1,
                "motion_detection": False,
                "model_name": "Ring Camera",
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "camera.garage",
            "state": "idle",
            "attributes": {
                "friendly_name": "Garage Camera",
            },
            "last_changed": "2024-01-01T10:00:00",
            "last_updated": "2024-01-01T10:00:00",
        },
        {
            "entity_id": "light.porch",
            "state": "on",
            "attributes": {
                "friendly_name": "Porch Light",
            },
        },
    ]


class TestListCameras:
    """Tests for listing cameras."""

    @pytest.mark.asyncio
    async def test_list_cameras_success(self, mock_client, sample_camera_states):
        """Test successfully listing all cameras."""
        mock_client.get_states.return_value = sample_camera_states

        result = await _list_cameras(mock_client)

        assert result["success"] is True
        assert result["count"] == 3  # Only cameras, not the light
        assert len(result["cameras"]) == 3

        # Verify front door camera data
        front_door = next(
            cam for cam in result["cameras"] if cam["entity_id"] == "camera.front_door"
        )
        assert front_door["name"] == "Front Door Camera"
        assert front_door["state"] == "idle"
        assert front_door["supported_features"] == 3
        assert front_door["motion_detection"] is True
        assert front_door["model"] == "Nest Cam"

        # Verify back yard camera
        back_yard = next(cam for cam in result["cameras"] if cam["entity_id"] == "camera.back_yard")
        assert back_yard["state"] == "recording"
        assert back_yard["motion_detection"] is False

        # Verify garage camera (minimal attributes)
        garage = next(cam for cam in result["cameras"] if cam["entity_id"] == "camera.garage")
        assert garage["state"] == "idle"
        assert "motion_detection" not in garage
        assert "model" not in garage

    @pytest.mark.asyncio
    async def test_list_cameras_empty(self, mock_client):
        """Test listing cameras when no cameras exist."""
        mock_client.get_states.return_value = [
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {},
            }
        ]

        result = await _list_cameras(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["cameras"] == []


class TestGetCamera:
    """Tests for getting a specific camera."""

    @pytest.mark.asyncio
    async def test_get_camera_success(self, mock_client):
        """Test successfully getting a specific camera."""
        mock_client.get_state.return_value = {
            "entity_id": "camera.front_door",
            "state": "idle",
            "attributes": {
                "friendly_name": "Front Door Camera",
                "supported_features": 3,
                "motion_detection": True,
                "model_name": "Nest Cam",
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_camera(mock_client, "camera.front_door")

        assert result["success"] is True
        assert result["camera"]["entity_id"] == "camera.front_door"
        assert result["camera"]["name"] == "Front Door Camera"
        assert result["camera"]["state"] == "idle"
        assert result["camera"]["last_changed"] == "2024-01-01T12:00:00"
        assert result["camera"]["attributes"]["motion_detection"] is True

        mock_client.get_state.assert_called_once_with("camera.front_door")

    @pytest.mark.asyncio
    async def test_get_camera_not_found(self, mock_client):
        """Test getting a camera that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'camera.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_camera(mock_client, "camera.nonexistent")

    @pytest.mark.asyncio
    async def test_get_camera_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not a camera."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_camera(mock_client, "light.porch")

        assert "not a camera entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestGetSnapshot:
    """Tests for getting camera snapshots."""

    @pytest.mark.asyncio
    async def test_get_snapshot_with_file_path(self, mock_client):
        """Test successfully getting a snapshot with file output."""
        mock_client.call_service.return_value = {}

        result = await _get_snapshot(mock_client, "camera.front_door", "/tmp/snapshot.jpg")

        assert result["success"] is True
        assert result["entity_id"] == "camera.front_door"
        assert result["output_path"] == "/tmp/snapshot.jpg"
        assert "saved" in result["message"].lower()

        mock_client.call_service.assert_called_once_with(
            "camera",
            "snapshot",
            {"entity_id": "camera.front_door", "filename": "/tmp/snapshot.jpg"},
        )

    @pytest.mark.asyncio
    async def test_get_snapshot_without_file_path(self, mock_client):
        """Test getting a snapshot without file output (base64 mode)."""
        mock_client.call_service.return_value = {}

        result = await _get_snapshot(mock_client, "camera.front_door")

        assert result["success"] is True
        assert result["entity_id"] == "camera.front_door"
        assert "note" in result

        mock_client.call_service.assert_called_once_with(
            "camera", "snapshot", {"entity_id": "camera.front_door"}
        )

    @pytest.mark.asyncio
    async def test_get_snapshot_invalid_entity_type(self, mock_client):
        """Test getting snapshot for an entity that is not a camera."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_snapshot(mock_client, "light.porch", "/tmp/snapshot.jpg")

        assert "not a camera entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_snapshot_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = Exception("Camera not responding")

        with pytest.raises(ServiceCallError) as exc_info:
            await _get_snapshot(mock_client, "camera.front_door", "/tmp/snapshot.jpg")

        assert "Failed to get snapshot" in str(exc_info.value)


class TestSetMotionDetection:
    """Tests for enabling/disabling motion detection."""

    @pytest.mark.asyncio
    async def test_enable_motion_detection(self, mock_client):
        """Test successfully enabling motion detection."""
        mock_client.call_service.return_value = {}

        result = await _set_motion_detection(mock_client, "camera.front_door", True)

        assert result["success"] is True
        assert result["entity_id"] == "camera.front_door"
        assert result["motion_detection_enabled"] is True
        assert "enable" in result["message"].lower()

        mock_client.call_service.assert_called_once_with(
            "camera", "enable_motion_detection", {"entity_id": "camera.front_door"}
        )

    @pytest.mark.asyncio
    async def test_disable_motion_detection(self, mock_client):
        """Test successfully disabling motion detection."""
        mock_client.call_service.return_value = {}

        result = await _set_motion_detection(mock_client, "camera.front_door", False)

        assert result["success"] is True
        assert result["entity_id"] == "camera.front_door"
        assert result["motion_detection_enabled"] is False
        assert "disable" in result["message"].lower()

        mock_client.call_service.assert_called_once_with(
            "camera", "disable_motion_detection", {"entity_id": "camera.front_door"}
        )

    @pytest.mark.asyncio
    async def test_set_motion_detection_invalid_entity_type(self, mock_client):
        """Test motion detection for an entity that is not a camera."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _set_motion_detection(mock_client, "light.porch", True)

        assert "not a camera entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_motion_detection_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _set_motion_detection(mock_client, "camera.front_door", True)


class TestGetStreamUrl:
    """Tests for getting stream URLs."""

    @pytest.mark.asyncio
    async def test_get_stream_url_with_entity_picture(self, mock_client):
        """Test getting stream URL when entity_picture is available."""
        mock_client.get_state.return_value = {
            "entity_id": "camera.front_door",
            "state": "idle",
            "attributes": {
                "friendly_name": "Front Door Camera",
                "entity_picture": "/api/camera_proxy/camera.front_door",
            },
        }

        result = await _get_stream_url(mock_client, "camera.front_door")

        assert result["success"] is True
        assert result["entity_id"] == "camera.front_door"
        assert result["stream_url"] == "/api/camera_proxy/camera.front_door"
        assert "note" in result

    @pytest.mark.asyncio
    async def test_get_stream_url_without_entity_picture(self, mock_client):
        """Test getting stream URL when entity_picture is not available."""
        mock_client.get_state.return_value = {
            "entity_id": "camera.front_door",
            "state": "idle",
            "attributes": {
                "friendly_name": "Front Door Camera",
            },
        }

        result = await _get_stream_url(mock_client, "camera.front_door")

        assert result["success"] is True
        assert result["entity_id"] == "camera.front_door"
        assert result["stream_url"] == "/api/camera_proxy/camera.front_door"

    @pytest.mark.asyncio
    async def test_get_stream_url_invalid_entity_type(self, mock_client):
        """Test getting stream URL for an entity that is not a camera."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_stream_url(mock_client, "light.porch")

        assert "not a camera entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_stream_url_entity_not_found(self, mock_client):
        """Test getting stream URL for a camera that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError("Entity not found")

        with pytest.raises(EntityNotFoundError):
            await _get_stream_url(mock_client, "camera.nonexistent")


class TestCameraControlIntegration:
    """Integration tests for the camera_control tool function."""

    @pytest.mark.asyncio
    async def test_camera_control_list_action(self, mock_client, sample_camera_states):
        """Test the camera_control function with list action."""
        from src.homeassistant_mcp.tools.devices.camera import register_camera_tool

        mock_client.get_states.return_value = sample_camera_states

        # Create a mock FastMCP instance
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        # Register the tool
        register_camera_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_camera_control_missing_entity_id(self):
        """Test camera_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.devices.camera import register_camera_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_camera_tool(mock_mcp, lambda: mock_client)

        # Test get without entity_id
        result = await registered_func(action="get")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test snapshot without entity_id
        result = await registered_func(action="snapshot")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test enable_motion_detection without entity_id
        result = await registered_func(action="enable_motion_detection")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test get_stream_url without entity_id
        result = await registered_func(action="get_stream_url")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

    @pytest.mark.asyncio
    async def test_camera_control_snapshot_action(self):
        """Test camera_control with snapshot action."""
        from src.homeassistant_mcp.tools.devices.camera import register_camera_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.call_service.return_value = {}

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_camera_tool(mock_mcp, lambda: mock_client)

        # Test snapshot with file path
        result = await registered_func(
            action="snapshot", entity_id="camera.front_door", output_path="/tmp/snap.jpg"
        )
        assert result["success"] is True
        assert result["entity_id"] == "camera.front_door"
        assert result["output_path"] == "/tmp/snap.jpg"

    @pytest.mark.asyncio
    async def test_camera_control_motion_detection_actions(self):
        """Test camera_control with motion detection actions."""
        from src.homeassistant_mcp.tools.devices.camera import register_camera_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.call_service.return_value = {}

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_camera_tool(mock_mcp, lambda: mock_client)

        # Test enable motion detection
        result = await registered_func(
            action="enable_motion_detection", entity_id="camera.front_door"
        )
        assert result["success"] is True
        assert result["motion_detection_enabled"] is True

        # Test disable motion detection
        result = await registered_func(
            action="disable_motion_detection", entity_id="camera.front_door"
        )
        assert result["success"] is True
        assert result["motion_detection_enabled"] is False

    @pytest.mark.asyncio
    async def test_camera_control_get_stream_url_action(self):
        """Test camera_control with get_stream_url action."""
        from src.homeassistant_mcp.tools.devices.camera import register_camera_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.get_state.return_value = {
            "entity_id": "camera.front_door",
            "state": "idle",
            "attributes": {
                "entity_picture": "/api/camera_proxy/camera.front_door",
            },
        }

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_camera_tool(mock_mcp, lambda: mock_client)

        # Test get stream URL
        result = await registered_func(action="get_stream_url", entity_id="camera.front_door")
        assert result["success"] is True
        assert result["entity_id"] == "camera.front_door"
        assert "stream_url" in result

    @pytest.mark.asyncio
    async def test_camera_control_error_handling(self):
        """Test camera_control error handling."""
        from src.homeassistant_mcp.tools.devices.camera import register_camera_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.get_state.side_effect = EntityNotFoundError("Entity not found")

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_camera_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="camera.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
        assert result["error_type"] == "entity_not_found"
