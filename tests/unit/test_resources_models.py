"""Unit tests for MCP resources envelope builder functions.

Tests the build_resource_envelope and build_error_response functions
to ensure they create standardized response envelopes correctly.
"""

from datetime import datetime, timezone

from homeassistant_mcp.resources.models import (
    ResourceErrorCode,
    ResourceType,
    build_error_response,
    build_resource_envelope,
)


class TestBuildResourceEnvelope:
    """Tests for build_resource_envelope function."""

    def test_build_envelope_with_entity_type(self):
        """Test building envelope with entity resource type."""
        uri = "hass://entity/light.living_room"
        data = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"brightness": 255},
        }

        envelope = build_resource_envelope(
            uri=uri,
            resource_type=ResourceType.ENTITY,
            data=data,
        )

        assert envelope["uri"] == uri
        assert envelope["type"] == "entity"
        assert "last_updated" in envelope
        assert envelope["data"] == data
        assert "cache_ttl" not in envelope

    def test_build_envelope_with_area_type(self):
        """Test building envelope with area resource type."""
        uri = "hass://area/living_room"
        data = {
            "area_id": "living_room",
            "entity_count": 5,
            "entities": [],
        }

        envelope = build_resource_envelope(
            uri=uri,
            resource_type=ResourceType.AREA,
            data=data,
        )

        assert envelope["uri"] == uri
        assert envelope["type"] == "area"
        assert envelope["data"] == data

    def test_build_envelope_with_device_type(self):
        """Test building envelope with device resource type."""
        uri = "hass://device/abc123"
        data = {
            "device_id": "abc123",
            "entity_count": 3,
            "entities": [],
        }

        envelope = build_resource_envelope(
            uri=uri,
            resource_type=ResourceType.DEVICE,
            data=data,
        )

        assert envelope["uri"] == uri
        assert envelope["type"] == "device"
        assert envelope["data"] == data

    def test_build_envelope_with_services_type(self):
        """Test building envelope with services resource type."""
        uri = "hass://services"
        data = {
            "light": {
                "turn_on": {"description": "Turn on light"},
            }
        }

        envelope = build_resource_envelope(
            uri=uri,
            resource_type=ResourceType.SERVICES,
            data=data,
        )

        assert envelope["uri"] == uri
        assert envelope["type"] == "services"
        assert envelope["data"] == data

    def test_build_envelope_with_history_type(self):
        """Test building envelope with history resource type."""
        uri = "hass://entity/sensor.temperature/history?hours=12"
        data = {
            "entity_id": "sensor.temperature",
            "entries": [],
        }

        envelope = build_resource_envelope(
            uri=uri,
            resource_type=ResourceType.HISTORY,
            data=data,
        )

        assert envelope["uri"] == uri
        assert envelope["type"] == "history"
        assert envelope["data"] == data

    def test_build_envelope_with_string_type(self):
        """Test building envelope with string resource type instead of enum."""
        uri = "hass://entity/light.bedroom"
        data = {"entity_id": "light.bedroom"}

        envelope = build_resource_envelope(
            uri=uri,
            resource_type="entity",  # String instead of enum
            data=data,
        )

        assert envelope["uri"] == uri
        assert envelope["type"] == "entity"
        assert envelope["data"] == data

    def test_build_envelope_with_cache_ttl(self):
        """Test building envelope with cache TTL hint."""
        uri = "hass://entity/light.kitchen"
        data = {"entity_id": "light.kitchen", "state": "off"}
        cache_ttl = 5

        envelope = build_resource_envelope(
            uri=uri,
            resource_type=ResourceType.ENTITY,
            data=data,
            cache_ttl=cache_ttl,
        )

        assert envelope["uri"] == uri
        assert envelope["type"] == "entity"
        assert envelope["data"] == data
        assert envelope["cache_ttl"] == 5

    def test_build_envelope_with_zero_cache_ttl(self):
        """Test building envelope with zero cache TTL (no caching)."""
        uri = "hass://entity/sensor.motion"
        data = {"entity_id": "sensor.motion", "state": "on"}

        envelope = build_resource_envelope(
            uri=uri,
            resource_type=ResourceType.ENTITY,
            data=data,
            cache_ttl=0,
        )

        assert envelope["cache_ttl"] == 0

    def test_build_envelope_iso8601_timestamp(self):
        """Test that last_updated is in ISO8601 format."""
        uri = "hass://entity/light.test"
        data = {"entity_id": "light.test"}

        envelope = build_resource_envelope(
            uri=uri,
            resource_type=ResourceType.ENTITY,
            data=data,
        )

        # Verify ISO8601 format by parsing
        timestamp = envelope["last_updated"]
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed.tzinfo is not None  # Has timezone
        assert isinstance(parsed, datetime)

    def test_build_envelope_timestamp_is_utc(self):
        """Test that last_updated timestamp is in UTC."""
        uri = "hass://entity/light.test"
        data = {"entity_id": "light.test"}

        envelope = build_resource_envelope(
            uri=uri,
            resource_type=ResourceType.ENTITY,
            data=data,
        )

        timestamp = envelope["last_updated"]
        # ISO8601 UTC timestamps end with Z or +00:00
        assert timestamp.endswith("Z") or timestamp.endswith("+00:00")

    def test_build_envelope_with_empty_data(self):
        """Test building envelope with empty data dictionary."""
        uri = "hass://services"
        data = {}

        envelope = build_resource_envelope(
            uri=uri,
            resource_type=ResourceType.SERVICES,
            data=data,
        )

        assert envelope["uri"] == uri
        assert envelope["data"] == {}

    def test_build_envelope_with_nested_data(self):
        """Test building envelope with deeply nested data structures."""
        uri = "hass://entity/climate.thermostat"
        data = {
            "entity_id": "climate.thermostat",
            "state": "heat",
            "attributes": {
                "temperature": 22.5,
                "target_temp_high": 24,
                "target_temp_low": 20,
                "hvac_modes": ["off", "heat", "cool", "auto"],
                "preset_modes": ["home", "away", "sleep"],
            },
        }

        envelope = build_resource_envelope(
            uri=uri,
            resource_type=ResourceType.ENTITY,
            data=data,
        )

        assert envelope["data"] == data
        assert envelope["data"]["attributes"]["hvac_modes"] == ["off", "heat", "cool", "auto"]

    def test_build_envelope_required_fields_present(self):
        """Test that all required envelope fields are present."""
        uri = "hass://entity/light.test"
        data = {"entity_id": "light.test"}

        envelope = build_resource_envelope(
            uri=uri,
            resource_type=ResourceType.ENTITY,
            data=data,
        )

        # Verify all required fields
        assert "uri" in envelope
        assert "type" in envelope
        assert "last_updated" in envelope
        assert "data" in envelope

    def test_build_envelope_with_various_ttl_values(self):
        """Test building envelopes with different TTL values for different resource types."""
        test_cases = [
            (ResourceType.ENTITY, 5),
            (ResourceType.AREA, 30),
            (ResourceType.DEVICE, 30),
            (ResourceType.SERVICES, 300),
            (ResourceType.HISTORY, 60),
        ]

        for resource_type, ttl in test_cases:
            envelope = build_resource_envelope(
                uri=f"hass://test/{resource_type.value}",
                resource_type=resource_type,
                data={},
                cache_ttl=ttl,
            )

            assert envelope["cache_ttl"] == ttl


class TestBuildErrorResponse:
    """Tests for build_error_response function."""

    def test_build_error_with_not_found_code(self):
        """Test building error response with not_found error code."""
        uri = "hass://entity/light.nonexistent"
        message = "Entity 'light.nonexistent' not found"

        error = build_error_response(
            uri=uri,
            error_code=ResourceErrorCode.NOT_FOUND,
            message=message,
        )

        assert "error" in error
        assert error["error"]["code"] == "not_found"
        assert error["error"]["message"] == message
        assert error["error"]["uri"] == uri

    def test_build_error_with_invalid_uri_code(self):
        """Test building error response with invalid_uri error code."""
        uri = "http://entity/light.test"
        message = "Invalid URI scheme: expected 'hass://', got 'http://'"

        error = build_error_response(
            uri=uri,
            error_code=ResourceErrorCode.INVALID_URI,
            message=message,
        )

        assert error["error"]["code"] == "invalid_uri"
        # Message will be sanitized - http:// will be replaced with "Home Assistant"
        assert "Invalid URI scheme" in error["error"]["message"]
        assert "Home Assistant" in error["error"]["message"]
        assert error["error"]["uri"] == uri

    def test_build_error_with_bad_request_code(self):
        """Test building error response with bad_request error code."""
        uri = "hass://entity/sensor.temp/history?hours=invalid"
        message = "Invalid query parameter type: hours must be an integer"

        error = build_error_response(
            uri=uri,
            error_code=ResourceErrorCode.BAD_REQUEST,
            message=message,
        )

        assert error["error"]["code"] == "bad_request"
        assert error["error"]["message"] == message

    def test_build_error_with_internal_code(self):
        """Test building error response with internal error code."""
        uri = "hass://entity/light.test"
        message = "Internal server error"

        error = build_error_response(
            uri=uri,
            error_code=ResourceErrorCode.INTERNAL,
            message=message,
        )

        assert error["error"]["code"] == "internal"
        assert error["error"]["message"] == message

    def test_build_error_with_string_code(self):
        """Test building error response with string error code instead of enum."""
        uri = "hass://entity/light.test"
        message = "Not found"

        error = build_error_response(
            uri=uri,
            error_code="not_found",  # String instead of enum
            message=message,
        )

        assert error["error"]["code"] == "not_found"
        assert error["error"]["message"] == message

    def test_build_error_structure(self):
        """Test that error response has correct structure."""
        uri = "hass://entity/light.test"
        message = "Test error"

        error = build_error_response(
            uri=uri,
            error_code=ResourceErrorCode.INTERNAL,
            message=message,
        )

        # Verify structure
        assert isinstance(error, dict)
        assert "error" in error
        assert isinstance(error["error"], dict)
        assert "code" in error["error"]
        assert "message" in error["error"]
        assert "uri" in error["error"]

    def test_build_error_with_empty_message(self):
        """Test building error response with empty message."""
        uri = "hass://entity/light.test"
        message = ""

        error = build_error_response(
            uri=uri,
            error_code=ResourceErrorCode.INTERNAL,
            message=message,
        )

        assert error["error"]["message"] == ""

    def test_build_error_with_long_message(self):
        """Test building error response with long error message."""
        uri = "hass://entity/light.test"
        message = "A" * 500  # Very long message

        error = build_error_response(
            uri=uri,
            error_code=ResourceErrorCode.INTERNAL,
            message=message,
        )

        # Long messages of repeated characters may be sanitized to empty
        # (they match the pattern for API keys: 20+ alphanumeric chars)
        assert "message" in error["error"]
        assert isinstance(error["error"]["message"], str)

    def test_build_error_with_special_characters_in_message(self):
        """Test building error response with special characters in message."""
        uri = "hass://entity/light.test"
        message = "Error: Entity 'light.test' not found! (Check configuration.yaml)"

        error = build_error_response(
            uri=uri,
            error_code=ResourceErrorCode.NOT_FOUND,
            message=message,
        )

        assert error["error"]["message"] == message

    def test_build_error_all_error_codes(self):
        """Test building error responses with all error code types."""
        uri = "hass://entity/light.test"
        error_codes = [
            ResourceErrorCode.INVALID_URI,
            ResourceErrorCode.NOT_FOUND,
            ResourceErrorCode.BAD_REQUEST,
            ResourceErrorCode.INTERNAL,
        ]

        for code in error_codes:
            error = build_error_response(
                uri=uri,
                error_code=code,
                message=f"Test error for {code.value}",
            )

            assert error["error"]["code"] == code.value
            assert error["error"]["uri"] == uri


class TestEnvelopeTimestamps:
    """Tests for timestamp generation in envelopes."""

    def test_timestamp_format_is_iso8601(self):
        """Test that timestamps follow ISO8601 format."""
        envelope = build_resource_envelope(
            uri="hass://entity/light.test",
            resource_type=ResourceType.ENTITY,
            data={},
        )

        timestamp = envelope["last_updated"]

        # Should be parseable as ISO8601
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)

    def test_timestamp_includes_timezone(self):
        """Test that timestamps include timezone information."""
        envelope = build_resource_envelope(
            uri="hass://entity/light.test",
            resource_type=ResourceType.ENTITY,
            data={},
        )

        timestamp = envelope["last_updated"]
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        # Should have timezone info
        assert parsed.tzinfo is not None
        assert parsed.tzinfo == timezone.utc

    def test_timestamp_is_recent(self):
        """Test that generated timestamp is recent (within last second)."""
        before = datetime.now(timezone.utc)

        envelope = build_resource_envelope(
            uri="hass://entity/light.test",
            resource_type=ResourceType.ENTITY,
            data={},
        )

        after = datetime.now(timezone.utc)

        timestamp = envelope["last_updated"]
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        # Timestamp should be between before and after
        assert before <= parsed <= after


class TestCacheTTLInclusion:
    """Tests for cache TTL hint inclusion in envelopes."""

    def test_cache_ttl_included_when_provided(self):
        """Test that cache_ttl is included when provided."""
        envelope = build_resource_envelope(
            uri="hass://entity/light.test",
            resource_type=ResourceType.ENTITY,
            data={},
            cache_ttl=5,
        )

        assert "cache_ttl" in envelope
        assert envelope["cache_ttl"] == 5

    def test_cache_ttl_not_included_when_none(self):
        """Test that cache_ttl is not included when None."""
        envelope = build_resource_envelope(
            uri="hass://entity/light.test",
            resource_type=ResourceType.ENTITY,
            data={},
            cache_ttl=None,
        )

        assert "cache_ttl" not in envelope

    def test_cache_ttl_not_included_by_default(self):
        """Test that cache_ttl is not included by default."""
        envelope = build_resource_envelope(
            uri="hass://entity/light.test",
            resource_type=ResourceType.ENTITY,
            data={},
        )

        assert "cache_ttl" not in envelope

    def test_cache_ttl_zero_is_included(self):
        """Test that cache_ttl of 0 is included (explicit no-cache)."""
        envelope = build_resource_envelope(
            uri="hass://entity/light.test",
            resource_type=ResourceType.ENTITY,
            data={},
            cache_ttl=0,
        )

        assert "cache_ttl" in envelope
        assert envelope["cache_ttl"] == 0

    def test_cache_ttl_large_value(self):
        """Test that large cache_ttl values are handled correctly."""
        envelope = build_resource_envelope(
            uri="hass://services",
            resource_type=ResourceType.SERVICES,
            data={},
            cache_ttl=3600,  # 1 hour
        )

        assert envelope["cache_ttl"] == 3600
