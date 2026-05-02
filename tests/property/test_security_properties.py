"""Property-based tests for MCP resource security.

This module tests the following properties:
- Property 12: Security - No Information Leakage

Validates Requirements: 9.5, 9.6, 9.7
"""

import re

from hypothesis import given, settings
from hypothesis import strategies as st

from src.homeassistant_mcp.resources.models import (
    ResourceErrorCode,
    build_error_response,
)

# Patterns that should NOT appear in error messages
SENSITIVE_PATTERNS = [
    # Internal URLs (http://, https://, with various formats)
    r"https?://[^\s]+",
    # Authentication tokens (Bearer tokens, JWT-like patterns, long alphanumeric strings)
    r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
    r"eyJ[A-Za-z0-9\-._~+/]+=*\.[A-Za-z0-9\-._~+/]+=*\.[A-Za-z0-9\-._~+/]+=*",  # JWT pattern
    r"token[:\s=]+[A-Za-z0-9\-._~+/]{20,}",  # Generic token pattern
    # Home Assistant configuration paths (Unix and Windows)
    r"/config/[^\s]*",
    r"/home/[^\s]*/\.homeassistant",
    r"C:\\[^\s]*\\homeassistant",
    r"/usr/share/hassio",
    # API keys and secrets
    r"api[_-]?key[:\s=]+[A-Za-z0-9\-._~+/]{20,}",
    r"secret[:\s=]+[A-Za-z0-9\-._~+/]{20,}",
]


def contains_sensitive_information(message: str) -> tuple[bool, str | None]:
    """Check if a message contains sensitive information.

    Args:
        message: The error message to check

    Returns:
        Tuple of (has_sensitive_info, matched_pattern)
    """
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return True, pattern
    return False, None


# Custom strategies for generating test data
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
def error_code_strategy(draw):
    """Generate valid ResourceErrorCode values."""
    return draw(st.sampled_from(list(ResourceErrorCode)))


@st.composite
def safe_error_message_strategy(draw):
    """Generate safe error messages without sensitive information."""
    templates = [
        "Entity not found",
        "Resource unavailable",
        "Invalid request",
        "Internal server error",
        "Failed to fetch data",
        "Connection failed",
        "Operation timed out",
        "Invalid entity ID",
        "Service unavailable",
        "Bad request",
    ]
    return draw(st.sampled_from(templates))


@st.composite
def error_message_with_internal_url_strategy(draw):
    """Generate error messages that contain internal URLs (should be sanitized)."""
    base_message = draw(safe_error_message_strategy())
    urls = [
        "http://homeassistant.local:8123",
        "https://192.168.1.100:8123",
        "http://hassio.local/api/states",
        "https://home-assistant:8123/api",
    ]
    url = draw(st.sampled_from(urls))

    # Create message with URL in various formats
    format_choice = draw(st.integers(min_value=0, max_value=2))
    if format_choice == 0:
        return f"{base_message}: {url}"
    elif format_choice == 1:
        return f"Failed to connect to {url}"
    else:
        return f"{base_message} at {url}/api/states"


@st.composite
def error_message_with_token_strategy(draw):
    """Generate error messages that contain tokens (should be sanitized)."""
    base_message = draw(safe_error_message_strategy())

    # Generate different token formats
    token_type = draw(st.integers(min_value=0, max_value=2))
    if token_type == 0:
        # JWT-like token
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIzYTU1MGY4Mjg3NmE0YmRlYjJmMDcxYTk0MTUzZjY1YSJ9.UJ92igK8SQbMUJ7KY6STHR9K3YkjlELl"
    elif token_type == 1:
        # Bearer token
        token = "Bearer abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"
    else:
        # Generic long token
        token = "token=3a550f82876a4bdeb2f071a941353f65a"

    # Create message with token in various formats
    format_choice = draw(st.integers(min_value=0, max_value=2))
    if format_choice == 0:
        return f"{base_message}: Invalid token {token}"
    elif format_choice == 1:
        return f"Authentication failed with {token}"
    else:
        return f"{base_message}. Token: {token}"


@st.composite
def error_message_with_config_path_strategy(draw):
    """Generate error messages that contain config paths (should be sanitized)."""
    base_message = draw(safe_error_message_strategy())

    # Generate different path formats
    path_type = draw(st.integers(min_value=0, max_value=3))
    if path_type == 0:
        path = "/config/configuration.yaml"
    elif path_type == 1:
        path = "/home/homeassistant/.homeassistant/secrets.yaml"
    elif path_type == 2:
        path = "C:\\Users\\homeassistant\\AppData\\homeassistant\\config"
    else:
        path = "/usr/share/hassio/homeassistant"

    # Create message with path in various formats
    format_choice = draw(st.integers(min_value=0, max_value=2))
    if format_choice == 0:
        return f"{base_message}: Failed to read {path}"
    elif format_choice == 1:
        return f"Configuration error in {path}"
    else:
        return f"{base_message} at {path}"


# Feature: mcp-resources-layer, Property 12: Security - No Information Leakage
@given(
    uri=uri_strategy(),
    error_code=error_code_strategy(),
    message=safe_error_message_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_12_no_information_leakage_safe_messages(
    uri: str,
    error_code: ResourceErrorCode,
    message: str,
):
    """
    **Validates: Requirements 9.5, 9.6, 9.7**

    Property: For any error response with safe messages, the message must not
    contain internal URLs, authentication tokens, or Home Assistant configuration paths.

    This test verifies that safe error messages remain safe after processing.
    """
    # Build the error response
    error_response = build_error_response(
        uri=uri,
        error_code=error_code,
        message=message,
    )

    # Extract the error message
    error_message = error_response["error"]["message"]

    # Verify no sensitive information is present
    has_sensitive, matched_pattern = contains_sensitive_information(error_message)

    assert not has_sensitive, (
        f"Error message contains sensitive information matching pattern: {matched_pattern}\n"
        f"Message: {error_message}\n"
        f"Requirement 9.5: Must not leak internal URLs\n"
        f"Requirement 9.6: Must not leak authentication tokens\n"
        f"Requirement 9.7: Must not leak Home Assistant configuration paths"
    )


# Feature: mcp-resources-layer, Property 12: Security - No Information Leakage (URLs)
@given(
    uri=uri_strategy(),
    error_code=error_code_strategy(),
    message=error_message_with_internal_url_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_12_no_internal_urls_in_errors(
    uri: str,
    error_code: ResourceErrorCode,
    message: str,
):
    """
    **Validates: Requirement 9.5**

    Property: For any error response, the message must not contain internal URLs.

    This test verifies that error messages containing internal URLs are properly
    sanitized before being returned to clients.

    Note: This test expects that the system will sanitize messages containing URLs.
    If the current implementation doesn't sanitize, this test will fail, indicating
    that sanitization logic needs to be added.
    """
    # Build the error response
    error_response = build_error_response(
        uri=uri,
        error_code=error_code,
        message=message,
    )

    # Extract the error message
    error_message = error_response["error"]["message"]

    # Check for internal URLs
    url_pattern = r"https?://[^\s]+"
    url_match = re.search(url_pattern, error_message, re.IGNORECASE)

    assert url_match is None, (
        f"Error message contains internal URL: {url_match.group() if url_match else 'N/A'}\n"
        f"Full message: {error_message}\n"
        f"Requirement 9.5: Error messages must not leak internal URLs\n"
        f"Original message: {message}"
    )


# Feature: mcp-resources-layer, Property 12: Security - No Information Leakage (Tokens)
@given(
    uri=uri_strategy(),
    error_code=error_code_strategy(),
    message=error_message_with_token_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_12_no_tokens_in_errors(
    uri: str,
    error_code: ResourceErrorCode,
    message: str,
):
    """
    **Validates: Requirement 9.6**

    Property: For any error response, the message must not contain authentication tokens.

    This test verifies that error messages containing authentication tokens are
    properly sanitized before being returned to clients.

    Note: This test expects that the system will sanitize messages containing tokens.
    If the current implementation doesn't sanitize, this test will fail, indicating
    that sanitization logic needs to be added.
    """
    # Build the error response
    error_response = build_error_response(
        uri=uri,
        error_code=error_code,
        message=message,
    )

    # Extract the error message
    error_message = error_response["error"]["message"]

    # Check for various token patterns
    token_patterns = [
        r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
        r"eyJ[A-Za-z0-9\-._~+/]+=*\.[A-Za-z0-9\-._~+/]+=*\.[A-Za-z0-9\-._~+/]+=*",  # JWT
        r"token[:\s=]+[A-Za-z0-9\-._~+/]{20,}",
    ]

    for pattern in token_patterns:
        token_match = re.search(pattern, error_message, re.IGNORECASE)
        assert token_match is None, (
            f"Error message contains authentication token matching pattern: {pattern}\n"
            f"Matched: {token_match.group() if token_match else 'N/A'}\n"
            f"Full message: {error_message}\n"
            f"Requirement 9.6: Error messages must not leak authentication tokens\n"
            f"Original message: {message}"
        )


# Feature: mcp-resources-layer, Property 12: Security - No Information Leakage (Config Paths)
@given(
    uri=uri_strategy(),
    error_code=error_code_strategy(),
    message=error_message_with_config_path_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_12_no_config_paths_in_errors(
    uri: str,
    error_code: ResourceErrorCode,
    message: str,
):
    """
    **Validates: Requirement 9.7**

    Property: For any error response, the message must not contain Home Assistant
    configuration paths.

    This test verifies that error messages containing configuration paths are
    properly sanitized before being returned to clients.

    Note: This test expects that the system will sanitize messages containing paths.
    If the current implementation doesn't sanitize, this test will fail, indicating
    that sanitization logic needs to be added.
    """
    # Build the error response
    error_response = build_error_response(
        uri=uri,
        error_code=error_code,
        message=message,
    )

    # Extract the error message
    error_message = error_response["error"]["message"]

    # Check for configuration paths
    path_patterns = [
        r"/config/[^\s]*",
        r"/home/[^\s]*/\.homeassistant",
        r"C:\\[^\s]*\\homeassistant",
        r"/usr/share/hassio",
    ]

    for pattern in path_patterns:
        path_match = re.search(pattern, error_message, re.IGNORECASE)
        assert path_match is None, (
            f"Error message contains configuration path matching pattern: {pattern}\n"
            f"Matched: {path_match.group() if path_match else 'N/A'}\n"
            f"Full message: {error_message}\n"
            f"Requirement 9.7: Error messages must not leak Home Assistant configuration paths\n"
            f"Original message: {message}"
        )


# Feature: mcp-resources-layer, Property 12: Security - No Information Leakage (Comprehensive)
@given(
    uri=uri_strategy(),
    error_code=error_code_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_12_no_information_leakage_comprehensive(
    uri: str,
    error_code: ResourceErrorCode,
):
    """
    **Validates: Requirements 9.5, 9.6, 9.7**

    Property: For any error response, regardless of the error message content,
    the final error response must not contain any sensitive information.

    This comprehensive test checks all types of sensitive information patterns.
    """
    # Test with various potentially sensitive messages
    sensitive_messages = [
        "Failed to connect to http://homeassistant.local:8123/api/states",
        "Authentication failed with token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature",
        "Configuration error in /config/configuration.yaml",
        "Bearer token abc123def456ghi789jkl012mno345pqr678 is invalid",
        "Cannot read /home/homeassistant/.homeassistant/secrets.yaml",
        "API call to https://192.168.1.100:8123 failed",
        "Token 3a550f82876a4bdeb2f071a941353f65a is invalid",
        "Error in C:\\Users\\homeassistant\\AppData\\homeassistant\\config",
    ]

    for sensitive_message in sensitive_messages:
        # Build the error response
        error_response = build_error_response(
            uri=uri,
            error_code=error_code,
            message=sensitive_message,
        )

        # Extract the error message
        error_message = error_response["error"]["message"]

        # Verify no sensitive information is present
        has_sensitive, matched_pattern = contains_sensitive_information(error_message)

        # Note: This test will fail if sanitization is not implemented
        # The failure indicates that sanitization logic needs to be added
        assert not has_sensitive, (
            f"Error message contains sensitive information matching pattern: {matched_pattern}\n"
            f"Message: {error_message}\n"
            f"Original message: {sensitive_message}\n"
            f"Requirements violated:\n"
            f"  9.5: Must not leak internal URLs\n"
            f"  9.6: Must not leak authentication tokens\n"
            f"  9.7: Must not leak Home Assistant configuration paths\n"
            f"\nThis test failure indicates that message sanitization needs to be implemented."
        )


# Feature: mcp-resources-layer, Property 12: Security - No Information Leakage (Edge Cases)
@given(
    uri=uri_strategy(),
    error_code=error_code_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_12_no_information_leakage_edge_cases(
    uri: str,
    error_code: ResourceErrorCode,
):
    """
    **Validates: Requirements 9.5, 9.6, 9.7**

    Property: For any error response with edge case messages (empty, very long,
    special characters), the message must not contain sensitive information.
    """
    # Test edge cases
    edge_case_messages = [
        "",  # Empty message
        "Error",  # Minimal message
        "A" * 1000,  # Very long message
        "Error: \n\t\r special chars !@#$%^&*()",  # Special characters
    ]

    for message in edge_case_messages:
        # Build the error response
        error_response = build_error_response(
            uri=uri,
            error_code=error_code,
            message=message,
        )

        # Extract the error message
        error_message = error_response["error"]["message"]

        # Verify no sensitive information is present
        has_sensitive, matched_pattern = contains_sensitive_information(error_message)

        assert not has_sensitive, (
            f"Error message contains sensitive information in edge case\n"
            f"Pattern: {matched_pattern}\n"
            f"Message: {error_message[:100]}...\n"
            f"Original: {message[:100]}..."
        )
