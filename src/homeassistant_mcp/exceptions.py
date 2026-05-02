"""Custom exception classes for Home Assistant MCP server.

This module defines the exception hierarchy for the Home Assistant MCP server,
providing specific error types for different failure scenarios.
"""


class HomeAssistantError(Exception):
    """Base exception for Home Assistant related errors.

    All custom exceptions in this module inherit from this base class,
    allowing for easy catching of all Home Assistant-related errors.
    """

    pass


class ConnectionError(HomeAssistantError):
    """Raised when connection to Home Assistant fails.

    This exception is raised when the server cannot establish or maintain
    a connection to the Home Assistant instance. Common causes include:
    - Network connectivity issues
    - Incorrect host URL
    - Home Assistant instance not running
    - Firewall blocking the connection
    """

    pass


class AuthenticationError(HomeAssistantError):
    """Raised when authentication with Home Assistant fails.

    This exception is raised when the provided authentication token is
    invalid, expired, or missing. This typically results in HTTP 401
    responses from the Home Assistant API.
    """

    pass


class EntityNotFoundError(HomeAssistantError):
    """Raised when a requested entity is not found.

    This exception is raised when attempting to access an entity that
    does not exist in Home Assistant. This typically results in HTTP 404
    responses from the Home Assistant API.
    """

    pass


class ServiceCallError(HomeAssistantError):
    """Raised when a Home Assistant service call fails.

    This exception is raised when a service call to Home Assistant fails
    for reasons other than authentication or connection issues. Common causes:
    - Invalid service parameters
    - Service not available
    - Entity in invalid state for the requested operation
    - Home Assistant internal errors
    """

    pass


class ValidationError(HomeAssistantError):
    """Raised when input validation fails.

    This exception is raised when tool parameters fail validation checks
    that occur before making API calls to Home Assistant. This includes:
    - Invalid parameter types
    - Out-of-range numeric values
    - Missing required parameters
    - Invalid parameter combinations
    """

    pass


class CacheError(HomeAssistantError):
    """Raised when cache operations fail.

    This exception is raised when there are issues with cache operations,
    though in practice cache failures are typically handled gracefully
    without raising exceptions.
    """

    pass


class TemplateError(HomeAssistantError):
    """Raised when template rendering fails.

    This exception is raised when Home Assistant template rendering fails
    due to syntax errors, invalid template expressions, or runtime errors
    during template evaluation. Common causes include:
    - Invalid Jinja2 syntax
    - Undefined variables or filters
    - Type errors in template expressions
    - Circular references in templates
    """

    pass


class ResourceNotFoundError(HomeAssistantError):
    """Raised when an MCP resource is not found.

    This exception is raised when attempting to access an MCP resource
    that does not exist or has an invalid URI format. This includes:
    - Invalid resource URI patterns
    - Non-existent entity, area, or device IDs in resource URIs
    - Unsupported resource types
    """

    pass


class PromptExecutionError(HomeAssistantError):
    """Raised when MCP prompt execution fails.

    This exception is raised when an MCP prompt fails to execute properly.
    Common causes include:
    - Invalid prompt arguments
    - Missing required prompt parameters
    - Errors during prompt conversation flow generation
    - Failures in underlying tool calls within prompts
    """

    pass
