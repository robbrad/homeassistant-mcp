"""Property-based tests for URI parsing and validation.

This module tests the following properties:
- Property 1: URI Scheme Consistency
- Property 2: Invalid URI Error Handling

Validates Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.homeassistant_mcp.resources.parsing import parse_resource_uri, validate_entity_id


# Custom strategies for generating test data
@st.composite
def valid_entity_id_strategy(draw):
    """Generate valid Home Assistant entity IDs (domain.object_id)."""
    domains = ["light", "switch", "sensor", "climate", "binary_sensor", "cover", "fan", "lock"]
    domain = draw(st.sampled_from(domains))

    # Generate valid object_id (lowercase letters, numbers, underscores only)
    # Must not start or end with underscore
    object_id = draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789_",
            min_size=1,
            max_size=30,
        ).filter(lambda x: x and not x.startswith("_") and not x.endswith("_") and "_" not in x[:1])
    )

    return f"{domain}.{object_id}"


@st.composite
def valid_area_id_strategy(draw):
    """Generate valid area IDs."""
    return draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789_",
            min_size=1,
            max_size=30,
        ).filter(lambda x: x and not x.startswith("_") and not x.endswith("_"))
    )


@st.composite
def valid_device_id_strategy(draw):
    """Generate valid device IDs (alphanumeric strings)."""
    return draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            min_size=1,
            max_size=40,
        )
    )


@st.composite
def invalid_scheme_strategy(draw):
    """Generate invalid URI schemes."""
    invalid_schemes = ["http", "https", "ftp", "file", "ws", "wss", ""]
    return draw(st.sampled_from(invalid_schemes))


@st.composite
def invalid_entity_id_strategy(draw):
    """Generate invalid entity IDs."""
    invalid_patterns = [
        "",  # Empty
        "nodomain",  # Missing domain separator
        "Light.room",  # Uppercase
        "light.living-room",  # Hyphen
        "light.living room",  # Space
        "light.living.room.extra",  # Multiple dots
        ".object_id",  # Missing domain
        "domain.",  # Missing object_id
    ]
    return draw(st.sampled_from(invalid_patterns))


# Feature: mcp-resources-layer, Property 1: URI Scheme Consistency
@given(entity_id=valid_entity_id_strategy())
@settings(max_examples=100, deadline=None)
def test_property_1_entity_uri_scheme_consistency(entity_id: str):
    """
    Property 1: URI Scheme Consistency (Entity)

    For any valid entity resource URI, the scheme must be `hass://` and the path
    must match the pattern entity/{entity_id}.

    Validates: Requirements 1.1, 1.2
    """
    uri = f"hass://entity/{entity_id}"
    result = parse_resource_uri(uri)

    # Verify scheme is always "hass"
    assert result["scheme"] == "hass"

    # Verify resource type is "entity"
    assert result["resource_type"] == "entity"

    # Verify resource_id matches the entity_id
    assert result["resource_id"] == entity_id

    # Verify query_params is a dict (empty or not)
    assert isinstance(result["query_params"], dict)


@given(area_id=valid_area_id_strategy())
@settings(max_examples=100, deadline=None)
def test_property_1_area_uri_scheme_consistency(area_id: str):
    """
    Property 1: URI Scheme Consistency (Area)

    For any valid area resource URI, the scheme must be `hass://` and the path
    must match the pattern area/{area_id}.

    Validates: Requirements 1.1, 1.3
    """
    uri = f"hass://area/{area_id}"
    result = parse_resource_uri(uri)

    # Verify scheme is always "hass"
    assert result["scheme"] == "hass"

    # Verify resource type is "area"
    assert result["resource_type"] == "area"

    # Verify resource_id matches the area_id
    assert result["resource_id"] == area_id

    # Verify query_params is a dict
    assert isinstance(result["query_params"], dict)


@given(device_id=valid_device_id_strategy())
@settings(max_examples=100, deadline=None)
def test_property_1_device_uri_scheme_consistency(device_id: str):
    """
    Property 1: URI Scheme Consistency (Device)

    For any valid device resource URI, the scheme must be `hass://` and the path
    must match the pattern device/{device_id}.

    Validates: Requirements 1.1, 1.4
    """
    uri = f"hass://device/{device_id}"
    result = parse_resource_uri(uri)

    # Verify scheme is always "hass"
    assert result["scheme"] == "hass"

    # Verify resource type is "device"
    assert result["resource_type"] == "device"

    # Verify resource_id matches the device_id
    assert result["resource_id"] == device_id

    # Verify query_params is a dict
    assert isinstance(result["query_params"], dict)


def test_property_1_services_uri_scheme_consistency():
    """
    Property 1: URI Scheme Consistency (Services)

    For the static services resource URI, the scheme must be `hass://` and the path
    must be exactly "services".

    Validates: Requirements 1.1, 1.5
    """
    uri = "hass://services"
    result = parse_resource_uri(uri)

    # Verify scheme is always "hass"
    assert result["scheme"] == "hass"

    # Verify resource type is "services"
    assert result["resource_type"] == "services"

    # Verify resource_id is None for static resources
    assert result["resource_id"] is None

    # Verify query_params is a dict
    assert isinstance(result["query_params"], dict)


@given(
    entity_id=valid_entity_id_strategy(),
    hours=st.integers(min_value=1, max_value=168),
    limit=st.integers(min_value=1, max_value=1000),
    offset=st.integers(min_value=0, max_value=10000),
)
@settings(max_examples=100, deadline=None)
def test_property_1_history_uri_scheme_consistency(
    entity_id: str, hours: int, limit: int, offset: int
):
    """
    Property 1: URI Scheme Consistency (History)

    For any valid history resource URI, the scheme must be `hass://` and the path
    must match the pattern entity/{entity_id}/history with optional query parameters.

    Validates: Requirements 1.1, 1.6
    """
    uri = f"hass://entity/{entity_id}/history?hours={hours}&limit={limit}&offset={offset}"
    result = parse_resource_uri(uri)

    # Verify scheme is always "hass"
    assert result["scheme"] == "hass"

    # Verify resource type is "history"
    assert result["resource_type"] == "history"

    # Verify resource_id matches the entity_id
    assert result["resource_id"] == entity_id

    # Verify query_params contains the parameters
    assert "hours" in result["query_params"]
    assert "limit" in result["query_params"]
    assert "offset" in result["query_params"]

    # Verify query param values (parse_qs returns lists)
    assert result["query_params"]["hours"] == [str(hours)]
    assert result["query_params"]["limit"] == [str(limit)]
    assert result["query_params"]["offset"] == [str(offset)]


# Feature: mcp-resources-layer, Property 2: Invalid URI Error Handling
@given(
    scheme=invalid_scheme_strategy(),
    entity_id=valid_entity_id_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_2_invalid_scheme_error_handling(scheme: str, entity_id: str):
    """
    Property 2: Invalid URI Error Handling (Invalid Scheme)

    For any malformed or invalid URI with wrong scheme, the system must return
    a structured error (raise ValueError).

    Validates: Requirements 1.8, 14.1
    """
    if scheme:
        uri = f"{scheme}://entity/{entity_id}"
    else:
        uri = f"entity/{entity_id}"  # No scheme at all

    with pytest.raises(ValueError, match="Invalid URI scheme|URI cannot be empty"):
        parse_resource_uri(uri)


@given(invalid_id=invalid_entity_id_strategy())
@settings(max_examples=100, deadline=None)
def test_property_2_invalid_entity_id_error_handling(invalid_id: str):
    """
    Property 2: Invalid URI Error Handling (Invalid Entity ID)

    For any entity URI with invalid entity_id format, the system must return
    a structured error (raise ValueError).

    Validates: Requirements 1.8, 14.2
    """
    # Skip empty string as it's handled by URI parsing
    if not invalid_id:
        with pytest.raises(ValueError):
            parse_resource_uri(f"hass://entity/{invalid_id}")
    else:
        # For non-empty invalid entity IDs, test both URI parsing and direct validation
        with pytest.raises(ValueError):
            validate_entity_id(invalid_id)


@given(
    resource_type=st.sampled_from(["invalid", "unknown", "bad_type", "123", "entity_wrong"]),
    resource_id=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=1, max_size=20),
)
@settings(max_examples=100, deadline=None)
def test_property_2_invalid_resource_type_error_handling(resource_type: str, resource_id: str):
    """
    Property 2: Invalid URI Error Handling (Invalid Resource Type)

    For any URI with invalid resource type, the system must return a structured
    error (raise ValueError).

    Validates: Requirements 1.8, 14.3
    """
    uri = f"hass://{resource_type}/{resource_id}"

    with pytest.raises(
        ValueError, match="Invalid resource type|Invalid static resource|Three-part paths"
    ):
        parse_resource_uri(uri)


@given(
    resource_type=st.sampled_from(["entity", "area", "device"]),
)
@settings(max_examples=100, deadline=None)
def test_property_2_empty_resource_id_error_handling(resource_type: str):
    """
    Property 2: Invalid URI Error Handling (Empty Resource ID)

    For any URI with empty resource ID, the system must return a structured
    error (raise ValueError).

    Validates: Requirements 1.8, 14.4
    """
    uri = f"hass://{resource_type}/"

    with pytest.raises(ValueError, match="Resource ID cannot be empty|URI path cannot be empty"):
        parse_resource_uri(uri)


@given(
    entity_id=valid_entity_id_strategy(),
    invalid_segment=st.text(
        alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=1, max_size=20
    ).filter(lambda x: x != "history"),
)
@settings(max_examples=100, deadline=None)
def test_property_2_invalid_history_path_error_handling(entity_id: str, invalid_segment: str):
    """
    Property 2: Invalid URI Error Handling (Invalid History Path)

    For any URI with invalid history path (not ending in /history), the system
    must return a structured error (raise ValueError).

    Validates: Requirements 1.8, 14.5
    """
    uri = f"hass://entity/{entity_id}/{invalid_segment}"

    with pytest.raises(ValueError, match="Third path segment must be 'history'|Invalid URI path"):
        parse_resource_uri(uri)


def test_property_2_empty_uri_error_handling():
    """
    Property 2: Invalid URI Error Handling (Empty URI)

    For an empty URI, the system must return a structured error (raise ValueError).

    Validates: Requirements 1.8, 14.6
    """
    with pytest.raises(ValueError, match="URI cannot be empty"):
        parse_resource_uri("")


def test_property_2_uri_without_path_error_handling():
    """
    Property 2: Invalid URI Error Handling (URI Without Path)

    For a URI without path, the system must return a structured error (raise ValueError).

    Validates: Requirements 1.8, 14.6
    """
    with pytest.raises(ValueError, match="URI path cannot be empty"):
        parse_resource_uri("hass://")
