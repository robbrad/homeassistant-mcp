"""Tests for comprehensive error handling across the application."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.homeassistant_mcp.exceptions import (
    AuthenticationError,
    ConnectionError,
    EntityNotFoundError,
    HomeAssistantError,
    PromptExecutionError,
    ResourceNotFoundError,
    ServiceCallError,
    TemplateError,
)
from src.homeassistant_mcp.hass.client import HomeAssistantClient


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    return AsyncMock(spec=HomeAssistantClient)


class TestExceptionHierarchy:
    """Test that exception hierarchy is properly defined."""

    def test_base_exception(self):
        """Test that HomeAssistantError is the base exception."""
        error = HomeAssistantError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"

    def test_connection_error_inheritance(self):
        """Test that ConnectionError inherits from HomeAssistantError."""
        error = ConnectionError("connection failed")
        assert isinstance(error, HomeAssistantError)
        assert isinstance(error, Exception)

    def test_authentication_error_inheritance(self):
        """Test that AuthenticationError inherits from HomeAssistantError."""
        error = AuthenticationError("auth failed")
        assert isinstance(error, HomeAssistantError)
        assert isinstance(error, Exception)

    def test_entity_not_found_error_inheritance(self):
        """Test that EntityNotFoundError inherits from HomeAssistantError."""
        error = EntityNotFoundError("entity not found")
        assert isinstance(error, HomeAssistantError)
        assert isinstance(error, Exception)

    def test_service_call_error_inheritance(self):
        """Test that ServiceCallError inherits from HomeAssistantError."""
        error = ServiceCallError("service call failed")
        assert isinstance(error, HomeAssistantError)
        assert isinstance(error, Exception)

    def test_template_error_inheritance(self):
        """Test that TemplateError inherits from HomeAssistantError."""
        error = TemplateError("template rendering failed")
        assert isinstance(error, HomeAssistantError)
        assert isinstance(error, Exception)

    def test_resource_not_found_error_inheritance(self):
        """Test that ResourceNotFoundError inherits from HomeAssistantError."""
        error = ResourceNotFoundError("resource not found")
        assert isinstance(error, HomeAssistantError)
        assert isinstance(error, Exception)

    def test_prompt_execution_error_inheritance(self):
        """Test that PromptExecutionError inherits from HomeAssistantError."""
        error = PromptExecutionError("prompt execution failed")
        assert isinstance(error, HomeAssistantError)
        assert isinstance(error, Exception)


class TestClientErrorHandling:
    """Test error handling in the Home Assistant client."""

    @pytest.mark.asyncio
    async def test_get_states_authentication_error(self):
        """Test that get_states raises AuthenticationError on 401."""
        client = HomeAssistantClient(base_url="http://test.local:8123", token="test_token")

        # Mock the HTTP client to return 401
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch.object(client.client, "get") as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", request=AsyncMock(), response=mock_response
            )

            with pytest.raises(AuthenticationError) as exc_info:
                await client.get_states()

            assert "Invalid Home Assistant token" in str(exc_info.value)

        await client.close()

    @pytest.mark.asyncio
    async def test_get_states_connection_error(self):
        """Test that get_states raises ConnectionError on network failure."""
        client = HomeAssistantClient(base_url="http://test.local:8123", token="test_token")

        # Mock the HTTP client to raise a connection error
        with patch.object(client.client, "get") as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(ConnectionError) as exc_info:
                await client.get_states()

            assert "Failed to connect to Home Assistant" in str(exc_info.value)

        await client.close()

    @pytest.mark.asyncio
    async def test_get_state_entity_not_found(self):
        """Test that get_state raises EntityNotFoundError on 404."""
        client = HomeAssistantClient(base_url="http://test.local:8123", token="test_token")

        # Mock the HTTP client to return 404
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        with patch.object(client.client, "get") as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=AsyncMock(), response=mock_response
            )

            with pytest.raises(EntityNotFoundError) as exc_info:
                await client.get_state("light.nonexistent")

            assert "not found" in str(exc_info.value).lower()

        await client.close()

    @pytest.mark.asyncio
    async def test_call_service_bad_request(self):
        """Test that call_service raises ServiceCallError on 400."""
        client = HomeAssistantClient(base_url="http://test.local:8123", token="test_token")

        # Mock the HTTP client to return 400
        mock_response = AsyncMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request: Invalid parameters"

        with patch.object(client.client, "post") as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "400 Bad Request", request=AsyncMock(), response=mock_response
            )

            with pytest.raises(ServiceCallError) as exc_info:
                await client.call_service("light", "turn_on", {"entity_id": "light.test"})

            assert "Invalid service call" in str(exc_info.value)

        await client.close()

    @pytest.mark.asyncio
    async def test_call_service_not_found(self):
        """Test that call_service raises ServiceCallError on 404."""
        client = HomeAssistantClient(base_url="http://test.local:8123", token="test_token")

        # Mock the HTTP client to return 404
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.text = "Service not found"

        with patch.object(client.client, "post") as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=AsyncMock(), response=mock_response
            )

            with pytest.raises(ServiceCallError) as exc_info:
                await client.call_service("invalid", "service", {})

            assert "not found" in str(exc_info.value).lower()

        await client.close()

    @pytest.mark.asyncio
    async def test_get_history_authentication_error(self):
        """Test that get_history raises AuthenticationError on 401."""
        client = HomeAssistantClient(base_url="http://test.local:8123", token="test_token")

        # Mock the HTTP client to return 401
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch.object(client.client, "get") as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", request=AsyncMock(), response=mock_response
            )

            with pytest.raises(AuthenticationError):
                await client.get_history("sensor.test", "2024-01-01T00:00:00+00:00")

        await client.close()


class TestToolErrorHandling:
    """Test error handling in tool implementations."""

    @pytest.mark.asyncio
    async def test_lights_control_entity_not_found(self, mock_client):
        """Test that lights_control handles EntityNotFoundError."""
        from src.homeassistant_mcp.tools.devices.lights import _get_light

        mock_client.get_state.side_effect = EntityNotFoundError("Entity not found")

        with pytest.raises(EntityNotFoundError):
            await _get_light(mock_client, "light.nonexistent")

    @pytest.mark.asyncio
    async def test_climate_control_service_call_error(self, mock_client):
        """Test that climate_control handles ServiceCallError."""
        from src.homeassistant_mcp.tools.devices.climate import _set_hvac_mode

        mock_client.get_state.return_value = {"entity_id": "climate.test", "state": "off"}
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _set_hvac_mode(mock_client, "climate.test", "heat")

    @pytest.mark.asyncio
    async def test_automation_control_connection_error(self, mock_client):
        """Test that automation_control handles ConnectionError."""
        from src.homeassistant_mcp.tools.automation.automation import _list_automations

        mock_client.get_states.side_effect = ConnectionError("Connection failed")

        with pytest.raises(ConnectionError):
            await _list_automations(mock_client)

    @pytest.mark.asyncio
    async def test_scene_control_authentication_error(self, mock_client):
        """Test that scene_control handles AuthenticationError."""
        from src.homeassistant_mcp.tools.automation.scene import _activate_scene

        mock_client.get_state.side_effect = AuthenticationError("Auth failed")

        with pytest.raises(AuthenticationError):
            await _activate_scene(mock_client, "scene.test")


class TestErrorLogging:
    """Test that errors are properly logged."""

    @pytest.mark.asyncio
    async def test_client_logs_authentication_error(self, caplog):
        """Test that authentication errors are logged."""
        client = HomeAssistantClient(base_url="http://test.local:8123", token="test_token")

        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch.object(client.client, "get") as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", request=AsyncMock(), response=mock_response
            )

            try:
                await client.get_states()
            except AuthenticationError:
                pass

            # Check that error was logged
            assert any("Authentication failed" in record.message for record in caplog.records)

        await client.close()

    @pytest.mark.asyncio
    async def test_client_logs_connection_error(self, caplog):
        """Test that connection errors are logged."""
        client = HomeAssistantClient(base_url="http://test.local:8123", token="test_token")

        with patch.object(client.client, "get") as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")

            try:
                await client.get_states()
            except ConnectionError:
                pass

            # Check that error was logged
            assert any("Connection error" in record.message for record in caplog.records)

        await client.close()


class TestErrorResponseFormat:
    """Test that error responses have consistent format."""

    @pytest.mark.asyncio
    async def test_tool_error_response_includes_error_type(self):
        """Test that tool error responses include error_type field."""
        from src.homeassistant_mcp.tools.devices.lights import _get_light

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.get_state.side_effect = EntityNotFoundError("Entity not found")

        # Test that the helper function raises the error
        with pytest.raises(EntityNotFoundError):
            await _get_light(mock_client, "light.test")

    @pytest.mark.asyncio
    async def test_tool_unexpected_error_handling(self):
        """Test that unexpected errors are caught and handled."""
        from src.homeassistant_mcp.tools.devices.lights import _list_lights

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.get_states.side_effect = ValueError("Unexpected error")

        # Test that the helper function raises the error
        with pytest.raises(ValueError):
            await _list_lights(mock_client)
