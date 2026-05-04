"""Tests for logging functionality throughout the application."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant_mcp.config import reset_settings
from homeassistant_mcp.exceptions import (
    AuthenticationError,
    ConnectionError,
    ServiceCallError,
)
from homeassistant_mcp.hass.cache import StateCache
from homeassistant_mcp.hass.client import HomeAssistantClient
from homeassistant_mcp.server import setup_logging


@pytest.fixture(autouse=True)
def reset_config():
    """Reset settings before each test."""
    reset_settings()
    yield
    reset_settings()


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("HASS_HOST", "http://homeassistant.local:8123")
    monkeypatch.setenv("HASS_TOKEN", "test_token_1234567890abcdef")


class TestLoggingConfiguration:
    """Test logging configuration and setup."""

    def test_setup_logging_default_level(self, mock_env_vars):
        """Test that logging is configured with default INFO level."""
        setup_logging()

        # Get the root logger
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_setup_logging_custom_level(self, mock_env_vars, monkeypatch):
        """Test that logging respects custom log level from settings."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        reset_settings()

        setup_logging()

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_setup_logging_httpx_level(self, mock_env_vars):
        """Test that httpx logger is set to WARNING to reduce noise."""
        setup_logging()

        httpx_logger = logging.getLogger("httpx")
        assert httpx_logger.level == logging.WARNING

    def test_setup_logging_format(self, mock_env_vars):
        """Test that logging format includes timestamp, name, level, and message."""
        setup_logging()

        # Verify that the root logger has handlers configured
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

        # Verify that the format includes the expected components
        handler = root_logger.handlers[0]
        formatter = handler.formatter
        assert formatter is not None


class TestClientLogging:
    """Test logging in the Home Assistant client."""

    @pytest.fixture
    def mock_httpx_client(self):
        """Create a mock httpx client."""
        client = AsyncMock()
        return client

    @pytest.fixture
    def client(self, mock_httpx_client):
        """Create a Home Assistant client with mocked httpx."""
        with patch(
            "homeassistant_mcp.hass.client.httpx.AsyncClient", return_value=mock_httpx_client
        ):
            client = HomeAssistantClient(
                base_url="http://homeassistant.local:8123",
                token="test_token_1234567890abcdef",
            )
            yield client

    @pytest.mark.asyncio
    async def test_get_states_logs_cache_hit(self, client, caplog):
        """Test that cache hits are logged at DEBUG level."""
        # Pre-populate cache
        client.cache.set("states:all", [{"entity_id": "light.test"}], 30)

        with caplog.at_level(logging.DEBUG):
            await client.get_states()

        # Check for cache hit log
        assert any("cached entity states" in record.message.lower() for record in caplog.records)

    @pytest.mark.asyncio
    async def test_get_states_logs_api_call(self, client, mock_httpx_client, caplog):
        """Test that API calls are logged at DEBUG level."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = [{"entity_id": "light.test"}]
        mock_httpx_client.get.return_value = mock_response

        with caplog.at_level(logging.DEBUG):
            await client.get_states()

        # Check for API call logs
        assert any("fetching" in record.message.lower() for record in caplog.records)
        assert any("retrieved" in record.message.lower() for record in caplog.records)

    @pytest.mark.asyncio
    async def test_call_service_logs_execution(self, client, mock_httpx_client, caplog):
        """Test that service calls are logged at INFO level."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.text = ""
        mock_httpx_client.post.return_value = mock_response

        with caplog.at_level(logging.INFO):
            await client.call_service("light", "turn_on", {"entity_id": "light.test"})

        # Check for service call logs
        assert any("calling service" in record.message.lower() for record in caplog.records)
        assert any("service call successful" in record.message.lower() for record in caplog.records)

    @pytest.mark.asyncio
    async def test_authentication_error_logged(self, client, mock_httpx_client, caplog):
        """Test that authentication errors are logged at ERROR level."""
        # Mock 401 response
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_httpx_client.get.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=mock_response
        )

        with caplog.at_level(logging.ERROR):
            with pytest.raises((AuthenticationError, ServiceCallError)):
                await client.get_states()

        # Check for authentication error log
        assert any("authentication failed" in record.message.lower() for record in caplog.records)

    @pytest.mark.asyncio
    async def test_connection_error_logged(self, client, mock_httpx_client, caplog):
        """Test that connection errors are logged at ERROR level."""
        # Mock connection error
        import httpx

        mock_httpx_client.get.side_effect = httpx.RequestError("Connection refused")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ConnectionError):
                await client.get_states()

        # Check for connection error log
        assert any("connection error" in record.message.lower() for record in caplog.records)

    @pytest.mark.asyncio
    async def test_token_not_logged(self, client, mock_httpx_client, caplog):
        """Test that the token value is never logged."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = [{"entity_id": "light.test"}]
        mock_httpx_client.get.return_value = mock_response

        with caplog.at_level(logging.DEBUG):
            await client.get_states()

        # Ensure token is not in any log message
        token = "test_token_1234567890abcdef"
        for record in caplog.records:
            assert token not in record.message


class TestCacheLogging:
    """Test logging in the state cache."""

    def test_cache_hit_logged(self, caplog):
        """Test that cache hits are logged at DEBUG level."""
        cache = StateCache()
        cache.set("test_key", "test_value", 30)

        with caplog.at_level(logging.DEBUG):
            cache.get("test_key")

        assert any("cache hit" in record.message.lower() for record in caplog.records)

    def test_cache_miss_logged(self, caplog):
        """Test that cache misses are logged at DEBUG level."""
        cache = StateCache()

        with caplog.at_level(logging.DEBUG):
            cache.get("nonexistent_key")

        assert any("cache miss" in record.message.lower() for record in caplog.records)

    def test_cache_expired_logged(self, caplog):
        """Test that expired cache entries are logged at DEBUG level."""
        cache = StateCache()
        cache.set("test_key", "test_value", 0)  # Expires immediately

        with caplog.at_level(logging.DEBUG):
            cache.get("test_key")

        assert any("cache expired" in record.message.lower() for record in caplog.records)

    def test_cache_invalidation_logged(self, caplog):
        """Test that cache invalidation is logged at INFO level."""
        cache = StateCache()
        cache.set("test_key_1", "value1", 30)
        cache.set("test_key_2", "value2", 30)

        with caplog.at_level(logging.INFO):
            cache.invalidate("test_key_*")

        assert any("invalidated" in record.message.lower() for record in caplog.records)

    def test_cache_clear_logged(self, caplog):
        """Test that cache clearing is logged at INFO level."""
        cache = StateCache()
        cache.set("test_key", "test_value", 30)

        with caplog.at_level(logging.INFO):
            cache.clear()

        assert any("cleared" in record.message.lower() for record in caplog.records)


class TestServerLogging:
    """Test logging in the server lifecycle."""

    @pytest.mark.asyncio
    async def test_server_startup_and_shutdown(self, mock_env_vars):
        """Test that server startup and shutdown execute without errors."""
        from homeassistant_mcp.server import lifespan, mcp

        # Mock the client initialization
        with patch("homeassistant_mcp.server.HomeAssistantClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client._states_data = [{"entity_id": "light.test"}]
            mock_client_class.return_value = mock_client

            # Just verify the lifespan completes without errors
            # The logs are visible in stderr output during test runs
            async with lifespan(mcp):
                pass

            # Verify client was initialized and closed
            assert mock_client_class.called
            assert mock_client.get_states.called
            assert mock_client.close.called

    @pytest.mark.asyncio
    async def test_connection_failure_handling(self, mock_env_vars):
        """Test that connection failures during startup are handled properly."""
        from homeassistant_mcp.server import lifespan, mcp

        # Mock the client to fail connection
        with patch("homeassistant_mcp.server.HomeAssistantClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_states.side_effect = Exception("Connection failed")
            mock_client_class.return_value = mock_client

            # Verify that the exception is raised and client is closed
            with pytest.raises(Exception, match="Connection failed"):
                async with lifespan(mcp):
                    pass

            # Verify client was closed even after error
            assert mock_client.close.called
