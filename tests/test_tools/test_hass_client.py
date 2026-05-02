"""Unit tests for Home Assistant API client."""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.homeassistant_mcp.hass.client import (
    AuthenticationError,
    ConnectionError,
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx AsyncClient."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def hass_client(mock_httpx_client):
    """Create a HomeAssistantClient with mocked httpx client."""
    with patch(
        "src.homeassistant_mcp.hass.client.httpx.AsyncClient", return_value=mock_httpx_client
    ):
        client = HomeAssistantClient(
            base_url="http://homeassistant.local:8123", token="test_token_1234567890"
        )
        client.client = mock_httpx_client
        return client


class TestHomeAssistantClientInit:
    """Tests for HomeAssistantClient initialization."""

    def test_init_strips_trailing_slash(self):
        """Test that trailing slashes are removed from base_url."""
        with patch("src.homeassistant_mcp.hass.client.httpx.AsyncClient"):
            client = HomeAssistantClient(
                base_url="http://homeassistant.local:8123/", token="test_token"
            )
            assert client.base_url == "http://homeassistant.local:8123"

    def test_init_sets_auth_header(self):
        """Test that authorization header is set correctly."""
        with patch("src.homeassistant_mcp.hass.client.httpx.AsyncClient") as mock_client:
            HomeAssistantClient(
                base_url="http://homeassistant.local:8123", token="test_token_1234567890"
            )

            # Verify AsyncClient was called with correct headers
            call_kwargs = mock_client.call_args.kwargs
            assert "Authorization" in call_kwargs["headers"]
            assert call_kwargs["headers"]["Authorization"] == "Bearer test_token_1234567890"
            assert call_kwargs["headers"]["Content-Type"] == "application/json"


class TestGetStates:
    """Tests for get_states method."""

    @pytest.mark.asyncio
    async def test_get_states_success(self, hass_client, mock_httpx_client):
        """Test successful retrieval of all entity states."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"brightness": 255},
                "last_changed": "2024-01-01T12:00:00",
                "last_updated": "2024-01-01T12:00:00",
            },
            {
                "entity_id": "climate.bedroom",
                "state": "heat",
                "attributes": {"temperature": 22},
                "last_changed": "2024-01-01T11:00:00",
                "last_updated": "2024-01-01T11:00:00",
            },
        ]
        mock_httpx_client.get.return_value = mock_response

        # Call method
        states = await hass_client.get_states()

        # Verify
        assert len(states) == 2
        assert states[0]["entity_id"] == "light.living_room"
        assert states[1]["entity_id"] == "climate.bedroom"
        mock_httpx_client.get.assert_called_once_with("/states")

    @pytest.mark.asyncio
    async def test_get_states_authentication_error(self, hass_client, mock_httpx_client):
        """Test handling of 401 authentication error."""
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_httpx_client.get.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )

        # Verify exception is raised
        with pytest.raises(AuthenticationError) as exc_info:
            await hass_client.get_states()

        assert "Invalid Home Assistant token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_states_connection_error(self, hass_client, mock_httpx_client):
        """Test handling of connection errors."""
        # Mock connection error
        mock_httpx_client.get.side_effect = httpx.ConnectError("Connection refused")

        # Verify exception is raised
        with pytest.raises(ConnectionError) as exc_info:
            await hass_client.get_states()

        assert "Failed to connect to Home Assistant" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_states_http_error(self, hass_client, mock_httpx_client):
        """Test handling of other HTTP errors."""
        # Mock 500 response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_httpx_client.get.side_effect = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=mock_response
        )

        # Verify exception is raised
        with pytest.raises(ServiceCallError) as exc_info:
            await hass_client.get_states()

        assert "HTTP 500" in str(exc_info.value)


class TestGetState:
    """Tests for get_state method."""

    @pytest.mark.asyncio
    async def test_get_state_success(self, hass_client, mock_httpx_client):
        """Test successful retrieval of single entity state."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"brightness": 255, "color_temp": 370},
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }
        mock_httpx_client.get.return_value = mock_response

        # Call method
        state = await hass_client.get_state("light.living_room")

        # Verify
        assert state["entity_id"] == "light.living_room"
        assert state["state"] == "on"
        assert state["attributes"]["brightness"] == 255
        mock_httpx_client.get.assert_called_once_with("/states/light.living_room")

    @pytest.mark.asyncio
    async def test_get_state_not_found(self, hass_client, mock_httpx_client):
        """Test handling of 404 entity not found error."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Entity not found"

        mock_httpx_client.get.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )

        # Verify exception is raised
        with pytest.raises(EntityNotFoundError) as exc_info:
            await hass_client.get_state("light.nonexistent")

        assert "light.nonexistent" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_state_authentication_error(self, hass_client, mock_httpx_client):
        """Test handling of 401 authentication error."""
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_httpx_client.get.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )

        # Verify exception is raised
        with pytest.raises(AuthenticationError) as exc_info:
            await hass_client.get_state("light.living_room")

        assert "Invalid Home Assistant token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_state_connection_error(self, hass_client, mock_httpx_client):
        """Test handling of connection errors."""
        # Mock connection error
        mock_httpx_client.get.side_effect = httpx.ConnectError("Connection refused")

        # Verify exception is raised
        with pytest.raises(ConnectionError) as exc_info:
            await hass_client.get_state("light.living_room")

        assert "Failed to connect to Home Assistant" in str(exc_info.value)


class TestCallService:
    """Tests for call_service method."""

    @pytest.mark.asyncio
    async def test_call_service_success(self, hass_client, mock_httpx_client):
        """Test successful service call."""
        # Mock response
        mock_response = Mock()
        mock_response.text = '{"context": {"id": "123"}}'
        mock_response.json.return_value = {"context": {"id": "123"}}
        mock_httpx_client.post.return_value = mock_response

        # Call method
        result = await hass_client.call_service(
            domain="light",
            service="turn_on",
            data={"entity_id": "light.living_room", "brightness": 255},
        )

        # Verify
        assert "context" in result
        mock_httpx_client.post.assert_called_once_with(
            "/services/light/turn_on", json={"entity_id": "light.living_room", "brightness": 255}
        )

    @pytest.mark.asyncio
    async def test_call_service_no_data(self, hass_client, mock_httpx_client):
        """Test service call without data parameter."""
        # Mock response
        mock_response = Mock()
        mock_response.text = ""
        mock_response.json.return_value = {}
        mock_httpx_client.post.return_value = mock_response

        # Call method
        result = await hass_client.call_service(domain="automation", service="trigger")

        # Verify
        assert result == {}
        mock_httpx_client.post.assert_called_once_with("/services/automation/trigger", json={})

    @pytest.mark.asyncio
    async def test_call_service_empty_response(self, hass_client, mock_httpx_client):
        """Test service call with empty response."""
        # Mock response with empty text
        mock_response = Mock()
        mock_response.text = ""
        mock_httpx_client.post.return_value = mock_response

        # Call method
        result = await hass_client.call_service(
            domain="light", service="turn_off", data={"entity_id": "light.living_room"}
        )

        # Verify
        assert result == {}

    @pytest.mark.asyncio
    async def test_call_service_authentication_error(self, hass_client, mock_httpx_client):
        """Test handling of 401 authentication error."""
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_httpx_client.post.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )

        # Verify exception is raised
        with pytest.raises(AuthenticationError) as exc_info:
            await hass_client.call_service("light", "turn_on")

        assert "Invalid Home Assistant token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_call_service_bad_request(self, hass_client, mock_httpx_client):
        """Test handling of 400 bad request error."""
        # Mock 400 response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid service data"

        mock_httpx_client.post.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=mock_response
        )

        # Verify exception is raised
        with pytest.raises(ServiceCallError) as exc_info:
            await hass_client.call_service("light", "turn_on", {"invalid": "data"})

        assert "Invalid service call" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_call_service_not_found(self, hass_client, mock_httpx_client):
        """Test handling of 404 service not found error."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Service not found"

        mock_httpx_client.post.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )

        # Verify exception is raised
        with pytest.raises(ServiceCallError) as exc_info:
            await hass_client.call_service("invalid", "service")

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_call_service_connection_error(self, hass_client, mock_httpx_client):
        """Test handling of connection errors."""
        # Mock connection error
        mock_httpx_client.post.side_effect = httpx.ConnectError("Connection refused")

        # Verify exception is raised
        with pytest.raises(ConnectionError) as exc_info:
            await hass_client.call_service("light", "turn_on")

        assert "Failed to connect to Home Assistant" in str(exc_info.value)


class TestClientLifecycle:
    """Tests for client lifecycle management."""

    @pytest.mark.asyncio
    async def test_close(self, hass_client, mock_httpx_client):
        """Test closing the client."""
        await hass_client.close()
        mock_httpx_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_httpx_client):
        """Test using client as async context manager."""
        with patch(
            "src.homeassistant_mcp.hass.client.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            async with HomeAssistantClient(
                base_url="http://homeassistant.local:8123", token="test_token"
            ) as client:
                assert client is not None

            # Verify close was called
            mock_httpx_client.aclose.assert_called_once()


class TestCacheIntegration:
    """Tests for cache integration in HomeAssistantClient."""

    @pytest.mark.asyncio
    async def test_get_states_uses_cache(self, hass_client, mock_httpx_client):
        """Test that get_states uses cache on subsequent calls."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = [{"entity_id": "light.living_room", "state": "on"}]
        mock_httpx_client.get.return_value = mock_response

        # First call - should hit API
        states1 = await hass_client.get_states()
        assert len(states1) == 1
        assert mock_httpx_client.get.call_count == 1

        # Second call - should use cache
        states2 = await hass_client.get_states()
        assert len(states2) == 1
        assert states1 == states2
        # API should not be called again
        assert mock_httpx_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_state_uses_cache(self, hass_client, mock_httpx_client):
        """Test that get_state uses cache on subsequent calls."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"brightness": 255},
        }
        mock_httpx_client.get.return_value = mock_response

        # First call - should hit API
        state1 = await hass_client.get_state("light.living_room")
        assert state1["state"] == "on"
        assert mock_httpx_client.get.call_count == 1

        # Second call - should use cache
        state2 = await hass_client.get_state("light.living_room")
        assert state2["state"] == "on"
        assert state1 == state2
        # API should not be called again
        assert mock_httpx_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_call_service_invalidates_cache(self, hass_client, mock_httpx_client):
        """Test that call_service invalidates relevant cache entries."""
        # Setup: Cache some states
        get_response = Mock()
        get_response.json.return_value = [{"entity_id": "light.living_room", "state": "off"}]
        mock_httpx_client.get.return_value = get_response

        # Get states to populate cache
        await hass_client.get_states()
        assert mock_httpx_client.get.call_count == 1

        # Call service
        post_response = Mock()
        post_response.text = ""
        mock_httpx_client.post.return_value = post_response

        await hass_client.call_service(
            domain="light", service="turn_on", data={"entity_id": "light.living_room"}
        )

        # Get states again - should hit API because cache was invalidated
        await hass_client.get_states()
        assert mock_httpx_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_call_service_invalidates_specific_entity(self, hass_client, mock_httpx_client):
        """Test that call_service invalidates specific entity cache."""
        # Setup: Cache entity state
        get_response = Mock()
        get_response.json.return_value = {"entity_id": "light.living_room", "state": "off"}
        mock_httpx_client.get.return_value = get_response

        # Get state to populate cache
        await hass_client.get_state("light.living_room")
        assert mock_httpx_client.get.call_count == 1

        # Call service on that entity
        post_response = Mock()
        post_response.text = ""
        mock_httpx_client.post.return_value = post_response

        await hass_client.call_service(
            domain="light", service="turn_on", data={"entity_id": "light.living_room"}
        )

        # Get state again - should hit API because cache was invalidated
        await hass_client.get_state("light.living_room")
        assert mock_httpx_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_call_service_invalidates_multiple_entities(self, hass_client, mock_httpx_client):
        """Test that call_service invalidates cache for multiple entities."""
        # Setup: Cache entity states
        get_response = Mock()
        get_response.json.return_value = {"entity_id": "light.living_room", "state": "off"}
        mock_httpx_client.get.return_value = get_response

        # Cache two entities
        await hass_client.get_state("light.living_room")
        await hass_client.get_state("light.bedroom")
        assert mock_httpx_client.get.call_count == 2

        # Call service on multiple entities
        post_response = Mock()
        post_response.text = ""
        mock_httpx_client.post.return_value = post_response

        await hass_client.call_service(
            domain="light",
            service="turn_on",
            data={"entity_id": ["light.living_room", "light.bedroom"]},
        )

        # Get states again - should hit API because cache was invalidated
        await hass_client.get_state("light.living_room")
        await hass_client.get_state("light.bedroom")
        assert mock_httpx_client.get.call_count == 4

    @pytest.mark.asyncio
    async def test_cache_ttl_configuration(self):
        """Test that cache TTL can be configured."""
        with patch("src.homeassistant_mcp.hass.client.httpx.AsyncClient"):
            client = HomeAssistantClient(
                base_url="http://homeassistant.local:8123",
                token="test_token",
                cache_ttl_states=60,
                cache_ttl_entity=20,
            )

            assert client.cache_ttl_states == 60
            assert client.cache_ttl_entity == 20

    @pytest.mark.asyncio
    async def test_cache_default_ttl(self):
        """Test that cache uses default TTL values."""
        with patch("src.homeassistant_mcp.hass.client.httpx.AsyncClient"):
            client = HomeAssistantClient(
                base_url="http://homeassistant.local:8123", token="test_token"
            )

            assert client.cache_ttl_states == 30
            assert client.cache_ttl_entity == 10
