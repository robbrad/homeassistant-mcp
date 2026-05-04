"""Unit tests for the generic control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.control import _call_service


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)
    return client


class TestCallService:
    """Tests for calling generic services."""

    @pytest.mark.asyncio
    async def test_call_service_basic(self, mock_client):
        """Test calling a service without additional data."""
        mock_client.call_service.return_value = {}

        result = await _call_service(
            mock_client, domain="switch", service="turn_on", entity_id="switch.fan", data=None
        )

        assert result["success"] is True
        assert result["domain"] == "switch"
        assert result["service"] == "turn_on"
        assert result["entity_id"] == "switch.fan"
        assert "called successfully" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "switch", "turn_on", {"entity_id": "switch.fan"}
        )

    @pytest.mark.asyncio
    async def test_call_service_with_data(self, mock_client):
        """Test calling a service with additional data."""
        mock_client.call_service.return_value = {}

        result = await _call_service(
            mock_client,
            domain="media_player",
            service="volume_set",
            entity_id="media_player.living_room",
            data={"volume_level": 0.5},
        )

        assert result["success"] is True
        assert result["domain"] == "media_player"
        assert result["service"] == "volume_set"
        assert result["entity_id"] == "media_player.living_room"
        assert result["data"]["volume_level"] == 0.5

        mock_client.call_service.assert_called_once_with(
            "media_player",
            "volume_set",
            {"entity_id": "media_player.living_room", "volume_level": 0.5},
        )

    @pytest.mark.asyncio
    async def test_call_service_without_entity_id(self, mock_client):
        """Test calling a service without entity_id (e.g., homeassistant.restart)."""
        mock_client.call_service.return_value = {}

        result = await _call_service(
            mock_client, domain="homeassistant", service="restart", entity_id=None, data=None
        )

        assert result["success"] is True
        assert result["domain"] == "homeassistant"
        assert result["service"] == "restart"
        assert result["entity_id"] is None

        # Should call with empty dict when no entity_id or data
        mock_client.call_service.assert_called_once_with("homeassistant", "restart", {})

    @pytest.mark.asyncio
    async def test_call_service_with_complex_data(self, mock_client):
        """Test calling a service with complex data structure."""
        mock_client.call_service.return_value = {}

        complex_data = {
            "media_content_id": "http://example.com/music.mp3",
            "media_content_type": "music",
            "extra": {"shuffle": True, "repeat": "all"},
        }

        result = await _call_service(
            mock_client,
            domain="media_player",
            service="play_media",
            entity_id="media_player.bedroom",
            data=complex_data,
        )

        assert result["success"] is True
        assert result["data"]["media_content_id"] == "http://example.com/music.mp3"
        assert result["data"]["extra"]["shuffle"] is True

        # Verify the data was passed correctly
        call_args = mock_client.call_service.call_args
        assert call_args[0][0] == "media_player"  # domain
        assert call_args[0][1] == "play_media"  # service
        service_data = call_args[0][2]  # data dict
        assert service_data["entity_id"] == "media_player.bedroom"
        assert service_data["media_content_id"] == "http://example.com/music.mp3"

    @pytest.mark.asyncio
    async def test_call_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _call_service(
                mock_client,
                domain="light",
                service="turn_on",
                entity_id="light.nonexistent",
                data=None,
            )

    @pytest.mark.asyncio
    async def test_call_service_preserves_original_data(self, mock_client):
        """Test that the original data dict is not modified."""
        mock_client.call_service.return_value = {}

        original_data = {"brightness": 128}
        original_data_copy = original_data.copy()

        await _call_service(
            mock_client,
            domain="light",
            service="turn_on",
            entity_id="light.living_room",
            data=original_data,
        )

        # Original data should not be modified
        assert original_data == original_data_copy

    @pytest.mark.asyncio
    async def test_call_service_various_domains(self, mock_client):
        """Test calling services across different domains."""
        mock_client.call_service.return_value = {}

        test_cases = [
            ("cover", "open_cover", "cover.garage"),
            ("lock", "lock", "lock.front_door"),
            ("vacuum", "start", "vacuum.roomba"),
            ("script", "turn_on", "script.movie_mode"),
            ("climate", "set_temperature", "climate.thermostat"),
        ]

        for domain, service, entity_id in test_cases:
            result = await _call_service(
                mock_client, domain=domain, service=service, entity_id=entity_id, data=None
            )

            assert result["success"] is True
            assert result["domain"] == domain
            assert result["service"] == service
            assert result["entity_id"] == entity_id


class TestControlToolIntegration:
    """Integration tests for the call_service tool function."""

    @pytest.mark.asyncio
    async def test_control_tool_registration(self, mock_client):
        """Test the call_service tool registration and execution."""
        from src.homeassistant_mcp.tools.control import register_control_tool

        mock_client.call_service.return_value = {}

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
        register_control_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(domain="switch", service="turn_on", entity_id="switch.fan")

        assert result["success"] is True
        assert result["domain"] == "switch"

    @pytest.mark.asyncio
    async def test_control_tool_error_handling(self):
        """Test control tool error handling."""
        from src.homeassistant_mcp.tools.control import register_control_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.call_service.side_effect = ServiceCallError("Service not found")

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_control_tool(mock_mcp, lambda: mock_client)

        # Test with ServiceCallError
        result = await registered_func(
            domain="invalid", service="invalid_service", entity_id="invalid.entity"
        )

        assert result["success"] is False
        assert "Service not found" in result["error"]

    @pytest.mark.asyncio
    async def test_control_tool_with_optional_parameters(self, mock_client):
        """Test control tool with optional entity_id and data."""
        from src.homeassistant_mcp.tools.control import register_control_tool

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

        register_control_tool(mock_mcp, lambda: mock_client)

        # Test without entity_id
        result = await registered_func(domain="homeassistant", service="restart")

        assert result["success"] is True
        assert result["entity_id"] is None

        # Test with data
        result = await registered_func(
            domain="light", service="turn_on", entity_id="light.bedroom", data={"brightness": 200}
        )

        assert result["success"] is True
        assert result["data"]["brightness"] == 200
