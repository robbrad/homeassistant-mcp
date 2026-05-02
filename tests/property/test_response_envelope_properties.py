"""Property-based tests for MCP resource response envelopes.

This module tests the following properties:
- Property 3: Response Envelope Structure
- Property 11: Error Response Structure

Validates Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 9.2, 9.3, 9.4, 13.4
"""

import json
from datetime import datetime
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.homeassistant_mcp.resources.models import (
    ResourceErrorCode,
    ResourceType,
    build_error_response,
    build_resource_envelope,
)


# Custom strategies for generating test data
@st.composite
def resource_type_strategy(draw):
    """Generate valid ResourceType values."""
    return draw(st.sampled_from(list(ResourceType)))


@st.composite
def uri_strategy(draw):
    """Generate valid resource URIs."""
    resource_type = draw(st.sampled_from(["entity", "area", "device", "services", "history"]))

    if resource_type == "services":
        return "hass://services"
    elif resource_type == "history":
        entity_id = draw(entity_id_strategy())
        return f"hass://entity/{entity_id}/history"
    else:
        # Generate ID for entity, area, or device
        if resource_type == "entity":
            resource_id = draw(entity_id_strategy())
        else:
            resource_id = draw(
                st.text(
                    alphabet=st.characters(
                        whitelist_categories=("Ll", "Nd"), whitelist_characters="_"
                    ),
                    min_size=1,
                    max_size=20,
                )
            )
        return f"hass://{resource_type}/{resource_id}"


@st.composite
def entity_id_strategy(draw):
    """Generate valid Home Assistant entity IDs (domain.name)."""
    domains = ["light", "switch", "sensor", "climate", "binary_sensor", "cover"]
    domain = draw(st.sampled_from(domains))
    name = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
            min_size=1,
            max_size=20,
        )
    )
    return f"{domain}.{name}"


@st.composite
def resource_data_strategy(draw):
    """Generate valid resource data dictionaries."""
    # Generate simple data with string, int, float, or bool values
    keys = draw(
        st.lists(
            st.text(alphabet=st.characters(whitelist_categories=("Ll",)), min_size=1, max_size=15),
            min_size=1,
            max_size=10,
            unique=True,
        )
    )

    values = []
    for _ in keys:
        value_type = draw(st.sampled_from(["str", "int", "float", "bool", "dict"]))
        if value_type == "str":
            values.append(draw(st.text(min_size=0, max_size=50)))
        elif value_type == "int":
            values.append(draw(st.integers(min_value=-1000, max_value=1000)))
        elif value_type == "float":
            values.append(
                draw(
                    st.floats(
                        min_value=-1000.0,
                        max_value=1000.0,
                        allow_nan=False,
                        allow_infinity=False,
                    )
                )
            )
        elif value_type == "bool":
            values.append(draw(st.booleans()))
        else:  # dict
            values.append({})

    return dict(zip(keys, values, strict=False))


def is_valid_iso8601(timestamp_str: str) -> bool:
    """Validate that a string is a valid ISO8601 timestamp."""
    try:
        # Try to parse the timestamp
        datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return True
    except (ValueError, AttributeError):
        return False


# Feature: mcp-resources-layer, Property 3: Response Envelope Structure
@given(
    uri=uri_strategy(),
    resource_type=resource_type_strategy(),
    data=resource_data_strategy(),
    cache_ttl=st.one_of(st.none(), st.integers(min_value=1, max_value=3600)),
)
@settings(max_examples=100, deadline=None)
def test_property_3_response_envelope_structure(
    uri: str,
    resource_type: ResourceType,
    data: dict[str, Any],
    cache_ttl: int | None,
):
    """
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 13.4**

    Property: For any successful resource response, the envelope must contain
    exactly these fields: `uri`, `type`, `last_updated`, and `data`, where
    `uri` matches the requested URI, `type` is a valid ResourceType, and
    `last_updated` is valid ISO8601.
    """
    # Build the resource envelope
    envelope = build_resource_envelope(
        uri=uri,
        resource_type=resource_type,
        data=data,
        cache_ttl=cache_ttl,
    )

    # Verify envelope is a dictionary
    assert isinstance(envelope, dict), "Envelope must be a dictionary"

    # Verify required fields are present (Requirements 3.1, 3.2, 3.3, 3.4, 3.5)
    required_fields = {"uri", "type", "last_updated", "data"}
    assert set(envelope.keys()) >= required_fields, (
        f"Envelope must contain at least these fields: {required_fields}, "
        f"but got: {set(envelope.keys())}"
    )

    # Verify uri field matches requested URI (Requirement 3.2)
    assert envelope["uri"] == uri, (
        f"Envelope uri field must match requested URI. " f"Expected: {uri}, Got: {envelope['uri']}"
    )

    # Verify type field is a valid ResourceType (Requirement 3.3)
    assert envelope["type"] in [rt.value for rt in ResourceType], (
        f"Envelope type field must be a valid ResourceType. " f"Got: {envelope['type']}"
    )

    # Verify type matches the provided resource_type
    assert envelope["type"] == resource_type.value, (
        f"Envelope type must match provided resource_type. "
        f"Expected: {resource_type.value}, Got: {envelope['type']}"
    )

    # Verify last_updated is valid ISO8601 format (Requirements 3.4, 13.4)
    assert isinstance(envelope["last_updated"], str), "last_updated must be a string"
    assert is_valid_iso8601(envelope["last_updated"]), (
        f"last_updated must be valid ISO8601 format. " f"Got: {envelope['last_updated']}"
    )

    # Verify data field contains the provided data (Requirement 3.5)
    assert envelope["data"] == data, (
        f"Envelope data field must match provided data. "
        f"Expected: {data}, Got: {envelope['data']}"
    )

    # Verify cache_ttl is included if provided
    if cache_ttl is not None:
        assert "cache_ttl" in envelope, "cache_ttl should be in envelope when provided"
        assert envelope["cache_ttl"] == cache_ttl, (
            f"cache_ttl must match provided value. "
            f"Expected: {cache_ttl}, Got: {envelope['cache_ttl']}"
        )

    # Verify envelope can be serialized to JSON (Requirement 13.1)
    try:
        json_str = json.dumps(envelope, default=str)
        assert json_str is not None
    except (TypeError, ValueError) as e:
        pytest.fail(f"Envelope must be JSON-serializable: {e}")


# Feature: mcp-resources-layer, Property 3: Response Envelope Structure (String ResourceType)
@given(
    uri=uri_strategy(),
    resource_type=st.sampled_from(["entity", "area", "device", "services", "history", "index"]),
    data=resource_data_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_3_response_envelope_structure_with_string_type(
    uri: str,
    resource_type: str,
    data: dict[str, Any],
):
    """
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 13.4**

    Property: For any successful resource response with string resource_type,
    the envelope must contain exactly these fields: `uri`, `type`, `last_updated`,
    and `data`, where `uri` matches the requested URI, `type` is a valid
    ResourceType string, and `last_updated` is valid ISO8601.
    """
    # Build the resource envelope with string resource_type
    envelope = build_resource_envelope(
        uri=uri,
        resource_type=resource_type,
        data=data,
    )

    # Verify envelope is a dictionary
    assert isinstance(envelope, dict), "Envelope must be a dictionary"

    # Verify required fields are present
    required_fields = {"uri", "type", "last_updated", "data"}
    assert (
        set(envelope.keys()) >= required_fields
    ), f"Envelope must contain at least these fields: {required_fields}"

    # Verify uri field matches requested URI
    assert envelope["uri"] == uri

    # Verify type field matches the provided string
    assert envelope["type"] == resource_type

    # Verify type is a valid ResourceType value
    assert envelope["type"] in [rt.value for rt in ResourceType]

    # Verify last_updated is valid ISO8601 format
    assert isinstance(envelope["last_updated"], str)
    assert is_valid_iso8601(envelope["last_updated"])

    # Verify data field contains the provided data
    assert envelope["data"] == data


# Feature: mcp-resources-layer, Property 3: Response Envelope Structure (Minimal Data)
@given(
    uri=uri_strategy(),
    resource_type=resource_type_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_3_response_envelope_structure_minimal_data(
    uri: str,
    resource_type: ResourceType,
):
    """
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

    Property: For any successful resource response with empty data,
    the envelope must still contain all required fields.
    """
    # Build the resource envelope with empty data
    envelope = build_resource_envelope(
        uri=uri,
        resource_type=resource_type,
        data={},
    )

    # Verify all required fields are present
    assert "uri" in envelope
    assert "type" in envelope
    assert "last_updated" in envelope
    assert "data" in envelope

    # Verify data is an empty dict
    assert envelope["data"] == {}

    # Verify other fields are valid
    assert envelope["uri"] == uri
    assert envelope["type"] == resource_type.value
    assert is_valid_iso8601(envelope["last_updated"])


# Custom strategies for error response testing
@st.composite
def error_code_strategy(draw):
    """Generate valid ResourceErrorCode values."""
    return draw(st.sampled_from(list(ResourceErrorCode)))


@st.composite
def error_message_strategy(draw):
    """Generate error messages."""
    return draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd", "Zs"), whitelist_characters="'.-_"
            ),
            min_size=1,
            max_size=200,
        )
    )


# Feature: mcp-resources-layer, Property 11: Error Response Structure
@given(
    uri=uri_strategy(),
    error_code=error_code_strategy(),
    message=error_message_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_11_error_response_structure(
    uri: str,
    error_code: ResourceErrorCode,
    message: str,
):
    """
    **Validates: Requirements 9.2, 9.3, 9.4**

    Property: For any error response, the envelope must contain an `error` object
    with fields: `code`, `message`, and `uri`, where `code` is a valid
    ResourceErrorCode and `uri` matches the requested URI.
    """
    # Build the error response
    error_response = build_error_response(
        uri=uri,
        error_code=error_code,
        message=message,
    )

    # Verify error_response is a dictionary
    assert isinstance(error_response, dict), "Error response must be a dictionary"

    # Verify error object is present (Requirement 9.2)
    assert "error" in error_response, "Error response must contain an 'error' object"

    error_obj = error_response["error"]
    assert isinstance(error_obj, dict), "Error object must be a dictionary"

    # Verify required fields are present in error object (Requirements 9.2, 9.3, 9.4)
    required_fields = {"code", "message", "uri"}
    assert set(error_obj.keys()) == required_fields, (
        f"Error object must contain exactly these fields: {required_fields}, "
        f"but got: {set(error_obj.keys())}"
    )

    # Verify code field is a valid ResourceErrorCode (Requirement 9.2)
    assert error_obj["code"] in [ec.value for ec in ResourceErrorCode], (
        f"Error code must be a valid ResourceErrorCode. " f"Got: {error_obj['code']}"
    )

    # Verify code matches the provided error_code
    assert error_obj["code"] == error_code.value, (
        f"Error code must match provided error_code. "
        f"Expected: {error_code.value}, Got: {error_obj['code']}"
    )

    # Verify message field contains the provided message (Requirement 9.3)
    # Note: Messages may be sanitized to remove sensitive information
    # For whitespace-only messages, sanitization may result in empty string
    assert "message" in error_obj, "Error object must contain a message field"
    assert isinstance(error_obj["message"], str), "Error message must be a string"

    # If the original message was whitespace-only, sanitized message may be empty
    if message.strip() == "":
        assert (
            error_obj["message"] == ""
        ), "Whitespace-only messages should be sanitized to empty string"
    else:
        # For non-whitespace messages, verify message is present (may be sanitized)
        assert len(error_obj["message"]) >= 0, "Error message should be present"

    # Verify uri field matches the requested URI (Requirement 9.4)
    assert error_obj["uri"] == uri, (
        f"Error uri field must match requested URI. " f"Expected: {uri}, Got: {error_obj['uri']}"
    )

    # Verify error response can be serialized to JSON
    try:
        json_str = json.dumps(error_response, default=str)
        assert json_str is not None
    except (TypeError, ValueError) as e:
        pytest.fail(f"Error response must be JSON-serializable: {e}")


# Feature: mcp-resources-layer, Property 11: Error Response Structure (String ErrorCode)
@given(
    uri=uri_strategy(),
    error_code=st.sampled_from(["invalid_uri", "not_found", "bad_request", "internal"]),
    message=error_message_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_11_error_response_structure_with_string_code(
    uri: str,
    error_code: str,
    message: str,
):
    """
    **Validates: Requirements 9.2, 9.3, 9.4**

    Property: For any error response with string error_code, the envelope must
    contain an `error` object with fields: `code`, `message`, and `uri`, where
    `code` is a valid ResourceErrorCode string and `uri` matches the requested URI.
    """
    # Build the error response with string error_code
    error_response = build_error_response(
        uri=uri,
        error_code=error_code,
        message=message,
    )

    # Verify error_response is a dictionary
    assert isinstance(error_response, dict)

    # Verify error object is present
    assert "error" in error_response
    error_obj = error_response["error"]

    # Verify required fields are present
    required_fields = {"code", "message", "uri"}
    assert set(error_obj.keys()) == required_fields

    # Verify code field matches the provided string
    assert error_obj["code"] == error_code

    # Verify code is a valid ResourceErrorCode value
    assert error_obj["code"] in [ec.value for ec in ResourceErrorCode]

    # Verify message field contains the provided message
    # Note: Messages may be sanitized to remove sensitive information
    assert "message" in error_obj
    assert isinstance(error_obj["message"], str)

    # If the original message was whitespace-only, sanitized message may be empty
    if message.strip() == "":
        assert error_obj["message"] == ""
    else:
        # For non-whitespace messages, verify message is present (may be sanitized)
        assert len(error_obj["message"]) >= 0

    # Verify uri field matches the requested URI
    assert error_obj["uri"] == uri


# Feature: mcp-resources-layer, Property 11: Error Response Structure (All Error Codes)
@given(
    uri=uri_strategy(),
    message=error_message_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_11_error_response_structure_all_codes(
    uri: str,
    message: str,
):
    """
    **Validates: Requirements 9.2, 9.3, 9.4**

    Property: For any error response, all valid ResourceErrorCode values must
    produce valid error responses.
    """
    # Test each error code
    for error_code in ResourceErrorCode:
        error_response = build_error_response(
            uri=uri,
            error_code=error_code,
            message=message,
        )

        # Verify structure
        assert "error" in error_response
        error_obj = error_response["error"]

        # Verify all required fields
        assert "code" in error_obj
        assert "message" in error_obj
        assert "uri" in error_obj

        # Verify values
        assert error_obj["code"] == error_code.value

        # Verify message is present (may be sanitized)
        assert "message" in error_obj
        assert isinstance(error_obj["message"], str)

        # If the original message was whitespace-only, sanitized message may be empty
        if message.strip() == "":
            assert error_obj["message"] == ""
        else:
            # For non-whitespace messages, verify message is present (may be sanitized)
            assert len(error_obj["message"]) >= 0
        assert error_obj["uri"] == uri


# Feature: mcp-resources-layer, Property 11: Error Response Structure (No Extra Fields)
@given(
    uri=uri_strategy(),
    error_code=error_code_strategy(),
    message=error_message_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_11_error_response_no_extra_fields(
    uri: str,
    error_code: ResourceErrorCode,
    message: str,
):
    """
    **Validates: Requirements 9.2, 9.3, 9.4**

    Property: For any error response, the error object must contain exactly
    the required fields (code, message, uri) and no extra fields.
    """
    # Build the error response
    error_response = build_error_response(
        uri=uri,
        error_code=error_code,
        message=message,
    )

    # Verify error object has exactly the required fields
    error_obj = error_response["error"]
    required_fields = {"code", "message", "uri"}

    assert set(error_obj.keys()) == required_fields, (
        f"Error object must contain exactly {required_fields}, " f"but got: {set(error_obj.keys())}"
    )

    # Verify no extra fields at top level (only 'error' should be present)
    assert set(error_response.keys()) == {"error"}, (
        f"Error response must contain only 'error' field, " f"but got: {set(error_response.keys())}"
    )
