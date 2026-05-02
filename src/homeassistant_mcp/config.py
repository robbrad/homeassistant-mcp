"""Configuration management for Home Assistant MCP server."""

import os
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be configured via environment variables with the prefix 'HASS_'
    or without prefix for backward compatibility.
    """

    model_config = SettingsConfigDict(
        env_file=str(Path.cwd() / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings sources to conditionally load .env file.

        In test mode (when PYTEST_CURRENT_TEST is set), skip dotenv_settings
        to allow tests to control environment variables directly.
        """
        if os.getenv("PYTEST_CURRENT_TEST"):
            # In test mode: only use init_settings and env_settings
            return (init_settings, env_settings, file_secret_settings)
        else:
            # In production: use all sources including .env file
            return (init_settings, env_settings, dotenv_settings, file_secret_settings)

    # Home Assistant Configuration (Required)
    hass_host: str = Field(
        ...,
        description="Home Assistant host URL (e.g., http://homeassistant.local:8123)",
        alias="HASS_HOST",
    )
    hass_token: str = Field(
        ..., description="Home Assistant long-lived access token", alias="HASS_TOKEN"
    )

    # Server Configuration (Optional)
    server_name: str = Field(default="Home Assistant MCP", description="MCP server name")
    server_version: str = Field(default="", description="MCP server version (auto-detected)")

    def model_post_init(self, __context: Any) -> None:
        if not self.server_version:
            from importlib.metadata import version as _get_version

            try:
                object.__setattr__(self, "server_version", _get_version("homeassistant-mcp"))
            except Exception:
                object.__setattr__(self, "server_version", "unknown")

    # Cache Configuration (Optional)
    cache_ttl_states: int = Field(
        default=30, ge=0, description="Cache TTL for bulk state queries in seconds"
    )
    cache_ttl_entity: int = Field(
        default=10, ge=0, description="Cache TTL for individual entity queries in seconds"
    )

    # Logging Configuration (Optional)
    log_level: str = Field(
        default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    # Configuration File Management (Optional)
    ha_config_path: str | None = Field(
        default=None,
        description="Path to Home Assistant configuration directory for file management",
        alias="HA_CONFIG_PATH",
    )

    @field_validator("hass_host")
    @classmethod
    def validate_hass_host(cls, v: str) -> str:
        """Validate and normalize Home Assistant host URL."""
        if not v:
            raise ValueError("hass_host cannot be empty")

        # Remove trailing slashes
        v = v.rstrip("/")

        # Ensure it starts with http:// or https://
        if not v.startswith(("http://", "https://")):
            raise ValueError("hass_host must start with http:// or https:// " f"(got: {v})")

        return v

    @field_validator("hass_token")
    @classmethod
    def validate_hass_token(cls, v: str) -> str:
        """Validate Home Assistant token."""
        if not v or not v.strip():
            raise ValueError("hass_token cannot be empty")

        # Basic length check (Home Assistant tokens are typically long)
        if len(v.strip()) < 20:
            raise ValueError(
                "hass_token appears to be too short. "
                "Please use a valid Home Assistant long-lived access token"
            )

        return v.strip()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()

        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels} (got: {v})")

        return v_upper


# Singleton instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings singleton.

    Returns:
        Settings: The application settings instance.

    Raises:
        ValidationError: If required settings are missing or invalid.
    """
    global _settings

    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]

    return _settings


def reset_settings() -> None:
    """Reset the settings singleton.

    This is primarily useful for testing to ensure a clean state.
    """
    global _settings
    _settings = None
