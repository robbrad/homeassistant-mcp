"""Unit tests for configuration management."""

import pytest
from pydantic import ValidationError

from homeassistant_mcp.config import Settings, get_settings, reset_settings


@pytest.fixture(autouse=True)
def reset_settings_fixture():
    """Reset settings singleton before and after each test."""
    reset_settings()
    yield
    reset_settings()


@pytest.fixture
def valid_env_vars(monkeypatch):
    """Set valid environment variables for testing."""
    monkeypatch.setenv("HASS_HOST", "http://homeassistant.local:8123")
    monkeypatch.setenv("HASS_TOKEN", "test_token_with_sufficient_length_12345")


@pytest.fixture
def clear_env_vars(monkeypatch):
    """Clear all relevant environment variables and prevent .env file loading."""
    env_vars = [
        "HASS_HOST",
        "HASS_TOKEN",
        "SERVER_NAME",
        "SERVER_VERSION",
        "CACHE_TTL_STATES",
        "CACHE_TTL_ENTITY",
        "LOG_LEVEL",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)
    # Prevent pydantic-settings from reading the real .env file
    monkeypatch.setattr(
        "homeassistant_mcp.config.Settings.model_config",
        {**Settings.model_config, "env_file": None},
    )


class TestSettingsValidation:
    """Test settings validation."""

    def test_valid_configuration(self, valid_env_vars):
        """Test that valid configuration loads successfully."""
        settings = Settings()

        assert settings.hass_host == "http://homeassistant.local:8123"
        assert settings.hass_token == "test_token_with_sufficient_length_12345"
        assert settings.server_name == "Home Assistant MCP"
        assert settings.server_version == "2.0.0"
        assert settings.cache_ttl_states == 30
        assert settings.cache_ttl_entity == 10
        assert settings.log_level == "INFO"

    def test_missing_hass_host(self, monkeypatch, clear_env_vars):
        """Test that missing hass_host raises ValidationError."""
        monkeypatch.setenv("HASS_TOKEN", "test_token_with_sufficient_length_12345")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        # Check if any error is related to hass_host field
        assert any(
            error["loc"][0] in ("hass_host", "HASS_HOST")
            or "hass_host" in str(error["loc"]).lower()
            for error in errors
        )

    def test_missing_hass_token(self, monkeypatch, clear_env_vars):
        """Test that missing hass_token raises ValidationError."""
        monkeypatch.setenv("HASS_HOST", "http://homeassistant.local:8123")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        # Check if any error is related to hass_token field
        assert any(
            error["loc"][0] in ("hass_token", "HASS_TOKEN")
            or "hass_token" in str(error["loc"]).lower()
            for error in errors
        )

    def test_empty_hass_host(self, monkeypatch, clear_env_vars):
        """Test that empty hass_host raises ValidationError."""
        monkeypatch.setenv("HASS_HOST", "")
        monkeypatch.setenv("HASS_TOKEN", "test_token_with_sufficient_length_12345")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        # Check if any error is related to hass_host field and mentions empty
        assert any(
            (
                error["loc"][0] in ("hass_host", "HASS_HOST")
                or "hass_host" in str(error["loc"]).lower()
            )
            and (
                "cannot be empty" in str(error.get("msg", "")).lower()
                or "empty" in str(error.get("ctx", {})).lower()
                or error["type"] == "value_error"
            )
            for error in errors
        )

    def test_empty_hass_token(self, monkeypatch, clear_env_vars):
        """Test that empty hass_token raises ValidationError."""
        monkeypatch.setenv("HASS_HOST", "http://homeassistant.local:8123")
        monkeypatch.setenv("HASS_TOKEN", "")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        # Check if any error is related to hass_token field and mentions empty
        assert any(
            (
                error["loc"][0] in ("hass_token", "HASS_TOKEN")
                or "hass_token" in str(error["loc"]).lower()
            )
            and (
                "cannot be empty" in str(error.get("msg", "")).lower()
                or "empty" in str(error.get("ctx", {})).lower()
                or error["type"] == "value_error"
            )
            for error in errors
        )


class TestHassHostValidation:
    """Test hass_host validation."""

    def test_hass_host_with_http(self, monkeypatch, clear_env_vars):
        """Test that http:// URLs are accepted."""
        monkeypatch.setenv("HASS_HOST", "http://homeassistant.local:8123")
        monkeypatch.setenv("HASS_TOKEN", "test_token_with_sufficient_length_12345")

        settings = Settings()
        assert settings.hass_host == "http://homeassistant.local:8123"

    def test_hass_host_with_https(self, monkeypatch, clear_env_vars):
        """Test that https:// URLs are accepted."""
        monkeypatch.setenv("HASS_HOST", "https://homeassistant.example.com")
        monkeypatch.setenv("HASS_TOKEN", "test_token_with_sufficient_length_12345")

        settings = Settings()
        assert settings.hass_host == "https://homeassistant.example.com"

    def test_hass_host_without_protocol(self, monkeypatch, clear_env_vars):
        """Test that URLs without protocol are rejected."""
        monkeypatch.setenv("HASS_HOST", "homeassistant.local:8123")
        monkeypatch.setenv("HASS_TOKEN", "test_token_with_sufficient_length_12345")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        # Check if any error is related to hass_host field and mentions protocol
        assert any(
            (
                error["loc"][0] in ("hass_host", "HASS_HOST")
                or "hass_host" in str(error["loc"]).lower()
            )
            and (
                "must start with http" in str(error.get("msg", "")).lower()
                or "http" in str(error.get("ctx", {})).lower()
                or error["type"] == "value_error"
            )
            for error in errors
        )

    def test_hass_host_trailing_slash_removed(self, monkeypatch, clear_env_vars):
        """Test that trailing slashes are removed from hass_host."""
        monkeypatch.setenv("HASS_HOST", "http://homeassistant.local:8123/")
        monkeypatch.setenv("HASS_TOKEN", "test_token_with_sufficient_length_12345")

        settings = Settings()
        assert settings.hass_host == "http://homeassistant.local:8123"

    def test_hass_host_multiple_trailing_slashes(self, monkeypatch, clear_env_vars):
        """Test that multiple trailing slashes are removed."""
        monkeypatch.setenv("HASS_HOST", "http://homeassistant.local:8123///")
        monkeypatch.setenv("HASS_TOKEN", "test_token_with_sufficient_length_12345")

        settings = Settings()
        assert settings.hass_host == "http://homeassistant.local:8123"


class TestHassTokenValidation:
    """Test hass_token validation."""

    def test_valid_token(self, monkeypatch, clear_env_vars):
        """Test that valid tokens are accepted."""
        monkeypatch.setenv("HASS_HOST", "http://homeassistant.local:8123")
        monkeypatch.setenv("HASS_TOKEN", "test_token_with_sufficient_length_12345")

        settings = Settings()
        assert settings.hass_token == "test_token_with_sufficient_length_12345"

    def test_token_too_short(self, monkeypatch, clear_env_vars):
        """Test that short tokens are rejected."""
        monkeypatch.setenv("HASS_HOST", "http://homeassistant.local:8123")
        monkeypatch.setenv("HASS_TOKEN", "short")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        # Check if any error is related to hass_token field and mentions short/length
        assert any(
            (
                error["loc"][0] in ("hass_token", "HASS_TOKEN")
                or "hass_token" in str(error["loc"]).lower()
            )
            and (
                "too short" in str(error.get("msg", "")).lower()
                or "short" in str(error.get("ctx", {})).lower()
                or error["type"] == "value_error"
            )
            for error in errors
        )

    def test_token_whitespace_stripped(self, monkeypatch, clear_env_vars):
        """Test that whitespace is stripped from tokens."""
        monkeypatch.setenv("HASS_HOST", "http://homeassistant.local:8123")
        monkeypatch.setenv("HASS_TOKEN", "  test_token_with_sufficient_length_12345  ")

        settings = Settings()
        assert settings.hass_token == "test_token_with_sufficient_length_12345"


class TestOptionalSettings:
    """Test optional settings with defaults."""

    def test_default_server_name(self, valid_env_vars):
        """Test default server name."""
        settings = Settings()
        assert settings.server_name == "Home Assistant MCP"

    def test_custom_server_name(self, monkeypatch, valid_env_vars):
        """Test custom server name."""
        monkeypatch.setenv("SERVER_NAME", "My Custom MCP Server")

        settings = Settings()
        assert settings.server_name == "My Custom MCP Server"

    def test_default_cache_ttls(self, valid_env_vars):
        """Test default cache TTL values."""
        settings = Settings()
        assert settings.cache_ttl_states == 30
        assert settings.cache_ttl_entity == 10

    def test_custom_cache_ttls(self, monkeypatch, valid_env_vars):
        """Test custom cache TTL values."""
        monkeypatch.setenv("CACHE_TTL_STATES", "60")
        monkeypatch.setenv("CACHE_TTL_ENTITY", "20")

        settings = Settings()
        assert settings.cache_ttl_states == 60
        assert settings.cache_ttl_entity == 20

    def test_zero_cache_ttl(self, monkeypatch, valid_env_vars):
        """Test that zero cache TTL is allowed (disables caching)."""
        monkeypatch.setenv("CACHE_TTL_STATES", "0")
        monkeypatch.setenv("CACHE_TTL_ENTITY", "0")

        settings = Settings()
        assert settings.cache_ttl_states == 0
        assert settings.cache_ttl_entity == 0

    def test_negative_cache_ttl(self, monkeypatch, valid_env_vars):
        """Test that negative cache TTL is rejected."""
        monkeypatch.setenv("CACHE_TTL_STATES", "-1")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("cache_ttl_states",) for error in errors)


class TestLogLevelValidation:
    """Test log level validation."""

    def test_default_log_level(self, valid_env_vars):
        """Test default log level."""
        settings = Settings()
        assert settings.log_level == "INFO"

    @pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    def test_valid_log_levels(self, monkeypatch, valid_env_vars, level):
        """Test that all valid log levels are accepted."""
        monkeypatch.setenv("LOG_LEVEL", level)

        settings = Settings()
        assert settings.log_level == level

    @pytest.mark.parametrize("level", ["debug", "info", "warning", "error", "critical"])
    def test_case_insensitive_log_levels(self, monkeypatch, valid_env_vars, level):
        """Test that log levels are case-insensitive."""
        monkeypatch.setenv("LOG_LEVEL", level)

        settings = Settings()
        assert settings.log_level == level.upper()

    def test_invalid_log_level(self, monkeypatch, valid_env_vars):
        """Test that invalid log levels are rejected."""
        monkeypatch.setenv("LOG_LEVEL", "INVALID")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("log_level",) and "must be one of" in str(error["msg"])
            for error in errors
        )


class TestGetSettings:
    """Test get_settings singleton function."""

    def test_get_settings_returns_singleton(self, valid_env_vars):
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_get_settings_with_valid_config(self, valid_env_vars):
        """Test get_settings with valid configuration."""
        settings = get_settings()

        assert settings.hass_host == "http://homeassistant.local:8123"
        assert settings.hass_token == "test_token_with_sufficient_length_12345"

    def test_get_settings_with_invalid_config(self, clear_env_vars):
        """Test that get_settings raises ValidationError with invalid config."""
        with pytest.raises(ValidationError):
            get_settings()

    def test_reset_settings(self, valid_env_vars):
        """Test that reset_settings clears the singleton."""
        settings1 = get_settings()
        reset_settings()
        settings2 = get_settings()

        # Should be different instances after reset
        assert settings1 is not settings2

        # But should have the same values
        assert settings1.hass_host == settings2.hass_host
        assert settings1.hass_token == settings2.hass_token
