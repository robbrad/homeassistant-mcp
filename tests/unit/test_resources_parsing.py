"""Unit tests for URI parsing and validation utilities.

This module tests the parsing.py utilities for:
- URI parsing (parse_resource_uri)
- Entity ID validation (validate_entity_id)
- Query parameter validation (validate_query_params)

Validates Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 14.2, 14.3, 14.4, 2.6
"""

import pytest

from src.homeassistant_mcp.resources.parsing import (
    parse_resource_uri,
    validate_entity_id,
    validate_query_params,
)


class TestParseResourceURI:
    """Tests for parse_resource_uri function."""

    def test_parse_entity_uri(self):
        """Test parsing valid entity URI."""
        result = parse_resource_uri("hass://entity/light.living_room")

        assert result["scheme"] == "hass"
        assert result["resource_type"] == "entity"
        assert result["resource_id"] == "light.living_room"
        assert result["query_params"] == {}

    def test_parse_area_uri(self):
        """Test parsing valid area URI."""
        result = parse_resource_uri("hass://area/living_room")

        assert result["scheme"] == "hass"
        assert result["resource_type"] == "area"
        assert result["resource_id"] == "living_room"
        assert result["query_params"] == {}

    def test_parse_device_uri(self):
        """Test parsing valid device URI."""
        result = parse_resource_uri("hass://device/abc123def456")

        assert result["scheme"] == "hass"
        assert result["resource_type"] == "device"
        assert result["resource_id"] == "abc123def456"
        assert result["query_params"] == {}

    def test_parse_services_uri(self):
        """Test parsing static services URI."""
        result = parse_resource_uri("hass://services")

        assert result["scheme"] == "hass"
        assert result["resource_type"] == "services"
        assert result["resource_id"] is None
        assert result["query_params"] == {}

    def test_parse_history_uri_without_params(self):
        """Test parsing history URI without query parameters."""
        result = parse_resource_uri("hass://entity/sensor.temperature/history")

        assert result["scheme"] == "hass"
        assert result["resource_type"] == "history"
        assert result["resource_id"] == "sensor.temperature"
        assert result["query_params"] == {}

    def test_parse_history_uri_with_params(self):
        """Test parsing history URI with query parameters."""
        result = parse_resource_uri("hass://entity/sensor.temperature/history?hours=12&limit=50")

        assert result["scheme"] == "hass"
        assert result["resource_type"] == "history"
        assert result["resource_id"] == "sensor.temperature"
        assert result["query_params"] == {"hours": ["12"], "limit": ["50"]}

    def test_parse_history_uri_with_all_params(self):
        """Test parsing history URI with all query parameters."""
        result = parse_resource_uri(
            "hass://entity/sensor.temp/history?hours=24&limit=100&offset=10"
        )

        assert result["scheme"] == "hass"
        assert result["resource_type"] == "history"
        assert result["resource_id"] == "sensor.temp"
        assert result["query_params"] == {
            "hours": ["24"],
            "limit": ["100"],
            "offset": ["10"],
        }

    def test_invalid_scheme_rejection(self):
        """Test that invalid scheme is rejected."""
        with pytest.raises(ValueError, match="Invalid URI scheme"):
            parse_resource_uri("http://entity/light.living_room")

    def test_empty_uri_rejection(self):
        """Test that empty URI is rejected."""
        with pytest.raises(ValueError, match="URI cannot be empty"):
            parse_resource_uri("")

    def test_empty_path_rejection(self):
        """Test that empty path is rejected."""
        with pytest.raises(ValueError, match="URI path cannot be empty"):
            parse_resource_uri("hass://")

    def test_invalid_static_resource_rejection(self):
        """Test that invalid static resource is rejected."""
        with pytest.raises(ValueError, match="Invalid static resource"):
            parse_resource_uri("hass://invalid")

    def test_invalid_resource_type_rejection(self):
        """Test that invalid resource type is rejected."""
        with pytest.raises(ValueError, match="Invalid resource type"):
            parse_resource_uri("hass://invalid_type/some_id")

    def test_empty_resource_id_rejection(self):
        """Test that empty resource ID is rejected."""
        with pytest.raises(ValueError, match="Resource ID cannot be empty"):
            parse_resource_uri("hass://entity/")

    def test_invalid_three_part_path_rejection(self):
        """Test that invalid three-part path is rejected."""
        with pytest.raises(ValueError, match="Three-part paths must start with 'entity'"):
            parse_resource_uri("hass://area/living_room/invalid")

    def test_invalid_history_path_rejection(self):
        """Test that invalid history path is rejected."""
        with pytest.raises(ValueError, match="Third path segment must be 'history'"):
            parse_resource_uri("hass://entity/light.living_room/invalid")

    def test_too_many_path_segments_rejection(self):
        """Test that URIs with too many path segments are rejected."""
        with pytest.raises(ValueError, match="Invalid URI path"):
            parse_resource_uri("hass://entity/light.living_room/history/extra")


class TestValidateEntityId:
    """Tests for validate_entity_id function."""

    def test_valid_entity_id(self):
        """Test validation of valid entity ID."""
        assert validate_entity_id("light.living_room") is True

    def test_valid_entity_id_with_numbers(self):
        """Test validation of entity ID with numbers."""
        assert validate_entity_id("sensor.temperature_1") is True

    def test_valid_entity_id_with_underscores(self):
        """Test validation of entity ID with underscores."""
        assert validate_entity_id("binary_sensor.motion_detector_2") is True

    def test_empty_entity_id_rejection(self):
        """Test that empty entity ID is rejected."""
        with pytest.raises(ValueError, match="Entity ID cannot be empty"):
            validate_entity_id("")

    def test_missing_domain_rejection(self):
        """Test that entity ID without domain is rejected."""
        with pytest.raises(ValueError, match="Invalid entity_id format"):
            validate_entity_id("living_room")

    def test_uppercase_rejection(self):
        """Test that uppercase letters are rejected."""
        with pytest.raises(ValueError, match="Invalid entity_id format"):
            validate_entity_id("Light.living_room")

    def test_special_characters_rejection(self):
        """Test that special characters are rejected."""
        with pytest.raises(ValueError, match="Invalid entity_id format"):
            validate_entity_id("light.living-room")

    def test_spaces_rejection(self):
        """Test that spaces are rejected."""
        with pytest.raises(ValueError, match="Invalid entity_id format"):
            validate_entity_id("light.living room")

    def test_multiple_dots_rejection(self):
        """Test that multiple dots are rejected."""
        with pytest.raises(ValueError, match="Invalid entity_id format"):
            validate_entity_id("light.living.room")


class TestValidateQueryParams:
    """Tests for validate_query_params function."""

    def test_valid_int_params(self):
        """Test validation and coercion of integer parameters."""
        result = validate_query_params(
            {"hours": ["24"], "limit": ["100"]}, {"hours": int, "limit": int}
        )

        assert result == {"hours": 24, "limit": 100}

    def test_valid_float_params(self):
        """Test validation and coercion of float parameters."""
        result = validate_query_params({"temperature": ["22.5"]}, {"temperature": float})

        assert result == {"temperature": 22.5}

    def test_valid_bool_params_true(self):
        """Test validation and coercion of boolean parameters (true values)."""
        for true_value in ["true", "True", "1", "yes", "Yes"]:
            result = validate_query_params({"enabled": [true_value]}, {"enabled": bool})
            assert result == {"enabled": True}

    def test_valid_bool_params_false(self):
        """Test validation and coercion of boolean parameters (false values)."""
        for false_value in ["false", "False", "0", "no", "No"]:
            result = validate_query_params({"enabled": [false_value]}, {"enabled": bool})
            assert result == {"enabled": False}

    def test_valid_string_params(self):
        """Test validation of string parameters."""
        result = validate_query_params({"name": ["test_name"]}, {"name": str})

        assert result == {"name": "test_name"}

    def test_missing_optional_params(self):
        """Test that missing optional parameters are skipped."""
        result = validate_query_params(
            {"hours": ["24"]}, {"hours": int, "limit": int, "offset": int}
        )

        assert result == {"hours": 24}
        assert "limit" not in result
        assert "offset" not in result

    def test_invalid_int_type(self):
        """Test that invalid integer values are rejected."""
        with pytest.raises(ValueError, match="Invalid value for parameter 'hours'"):
            validate_query_params({"hours": ["invalid"]}, {"hours": int})

    def test_invalid_float_type(self):
        """Test that invalid float values are rejected."""
        with pytest.raises(ValueError, match="Invalid value for parameter 'temp'"):
            validate_query_params({"temp": ["not_a_number"]}, {"temp": float})

    def test_invalid_bool_type(self):
        """Test that invalid boolean values are rejected."""
        with pytest.raises(ValueError, match="Invalid value for parameter 'enabled'"):
            validate_query_params({"enabled": ["maybe"]}, {"enabled": bool})

    def test_empty_param_value(self):
        """Test that empty parameter values are rejected."""
        with pytest.raises(ValueError, match="has no value"):
            validate_query_params({"hours": []}, {"hours": int})

    def test_multiple_values_uses_first(self):
        """Test that multiple values for same parameter uses first value."""
        result = validate_query_params({"hours": ["24", "48"]}, {"hours": int})

        assert result == {"hours": 24}

    def test_mixed_param_types(self):
        """Test validation with mixed parameter types."""
        result = validate_query_params(
            {"hours": ["12"], "limit": ["50"], "name": ["test"], "enabled": ["true"]},
            {"hours": int, "limit": int, "name": str, "enabled": bool},
        )

        assert result == {
            "hours": 12,
            "limit": 50,
            "name": "test",
            "enabled": True,
        }
