"""Tests for the notification tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import ServiceCallError
from src.homeassistant_mcp.tools.notify import register_notify_tool


@pytest.fixture
def mock_mcp():
    """Create a mock FastMCP instance."""
    mcp = MagicMock()
    mcp.tool = lambda: lambda func: func
    return mcp


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock()
    client.call_service = AsyncMock()
    return client


@pytest.fixture
def get_client(mock_client):
    """Create a get_client callable."""
    return lambda: mock_client


@pytest.fixture
def send_notification_tool(mock_mcp, get_client):
    """Register and return the send_notification tool."""
    register_notify_tool(mock_mcp, get_client)
    # The tool function is the decorated function
    # We need to get it from the registration
    return mock_mcp.tool.call_args[0][0] if mock_mcp.tool.called else None


@pytest.mark.asyncio
async def test_send_simple_notification(mock_mcp, get_client, mock_client):
    """Test sending a simple notification with just a message."""
    register_notify_tool(mock_mcp, get_client)

    # Import the function directly for testing
    from src.homeassistant_mcp.tools.notify import _send_notification

    result = await _send_notification(mock_client, message="Test notification")

    assert result["success"] is True
    assert result["message"] == "Notification sent successfully"

    # Verify the service was called correctly
    mock_client.call_service.assert_called_once_with(
        "notify", "notify", {"message": "Test notification"}
    )


@pytest.mark.asyncio
async def test_send_notification_with_title(mock_client):
    """Test sending a notification with a title."""
    from src.homeassistant_mcp.tools.notify import _send_notification

    result = await _send_notification(mock_client, message="Test message", title="Test Title")

    assert result["success"] is True
    assert result["title"] == "Test Title"

    # Verify the service was called with title
    mock_client.call_service.assert_called_once_with(
        "notify", "notify", {"message": "Test message", "title": "Test Title"}
    )


@pytest.mark.asyncio
async def test_send_notification_with_target(mock_client):
    """Test sending a notification to a specific target."""
    from src.homeassistant_mcp.tools.notify import _send_notification

    result = await _send_notification(
        mock_client, message="Test message", target="mobile_app_phone"
    )

    assert result["success"] is True
    assert result["target"] == "mobile_app_phone"

    # Verify the service was called with target
    mock_client.call_service.assert_called_once_with(
        "notify", "mobile_app_phone", {"message": "Test message", "target": "mobile_app_phone"}
    )


@pytest.mark.asyncio
async def test_send_notification_with_all_parameters(mock_client):
    """Test sending a notification with all optional parameters."""
    from src.homeassistant_mcp.tools.notify import _send_notification

    result = await _send_notification(
        mock_client,
        message="Complete notification",
        title="Important Alert",
        target="mobile_app_tablet",
    )

    assert result["success"] is True
    assert result["title"] == "Important Alert"
    assert result["target"] == "mobile_app_tablet"

    # Verify the service was called with all parameters
    mock_client.call_service.assert_called_once_with(
        "notify",
        "mobile_app_tablet",
        {
            "message": "Complete notification",
            "title": "Important Alert",
            "target": "mobile_app_tablet",
        },
    )


@pytest.mark.asyncio
async def test_send_notification_with_notify_prefix_in_target(mock_client):
    """Test that notify. prefix is handled correctly in target."""
    from src.homeassistant_mcp.tools.notify import _send_notification

    result = await _send_notification(
        mock_client, message="Test message", target="notify.mobile_app_phone"
    )

    assert result["success"] is True

    # Verify the service was called with the prefix removed
    mock_client.call_service.assert_called_once_with(
        "notify",
        "mobile_app_phone",
        {"message": "Test message", "target": "notify.mobile_app_phone"},
    )


@pytest.mark.asyncio
async def test_send_notification_service_unavailable(mock_client):
    """Test error handling when notification service is unavailable."""
    from src.homeassistant_mcp.tools.notify import _send_notification

    # Mock the service call to raise an error
    mock_client.call_service.side_effect = ServiceCallError(
        "Service notify.mobile_app_phone not found"
    )

    with pytest.raises(ServiceCallError) as exc_info:
        await _send_notification(mock_client, message="Test message", target="mobile_app_phone")

    assert "unavailable" in str(exc_info.value).lower()
    assert "mobile_app_phone" in str(exc_info.value)


@pytest.mark.asyncio
async def test_send_notification_generic_service_error(mock_client):
    """Test error handling for generic service errors."""
    from src.homeassistant_mcp.tools.notify import _send_notification

    # Mock the service call to raise a generic error
    mock_client.call_service.side_effect = ServiceCallError("Connection timeout")

    with pytest.raises(ServiceCallError) as exc_info:
        await _send_notification(mock_client, message="Test message")

    assert "Connection timeout" in str(exc_info.value)


@pytest.mark.asyncio
async def test_send_notification_long_message(mock_client):
    """Test sending a notification with a long message."""
    from src.homeassistant_mcp.tools.notify import _send_notification

    long_message = "A" * 500  # Very long message

    result = await _send_notification(mock_client, message=long_message)

    assert result["success"] is True

    # Verify the full message was sent
    call_args = mock_client.call_service.call_args
    assert call_args[0][2]["message"] == long_message


@pytest.mark.asyncio
async def test_send_notification_empty_title(mock_client):
    """Test that empty title is not included in service data."""
    from src.homeassistant_mcp.tools.notify import _send_notification

    result = await _send_notification(mock_client, message="Test message", title=None)

    assert result["success"] is True
    assert "title" not in result

    # Verify title was not included in service call
    call_args = mock_client.call_service.call_args
    assert "title" not in call_args[0][2]


@pytest.mark.asyncio
async def test_send_notification_special_characters(mock_client):
    """Test sending notifications with special characters."""
    from src.homeassistant_mcp.tools.notify import _send_notification

    message = "Alert! Temperature > 30°C 🔥"
    title = "⚠️ Warning"

    result = await _send_notification(mock_client, message=message, title=title)

    assert result["success"] is True

    # Verify special characters are preserved
    call_args = mock_client.call_service.call_args
    assert call_args[0][2]["message"] == message
    assert call_args[0][2]["title"] == title


@pytest.mark.asyncio
async def test_send_notification_tool_authentication_error(mock_mcp, get_client, mock_client):
    """Test tool wrapper handles authentication errors."""
    from src.homeassistant_mcp.exceptions import AuthenticationError

    mock_client.call_service.side_effect = AuthenticationError("Invalid token")

    registered_func = None

    def capture_tool():
        def decorator(func):
            nonlocal registered_func
            registered_func = func
            return func

        return decorator

    mock_mcp.tool = capture_tool
    register_notify_tool(mock_mcp, get_client)

    result = await registered_func(message="Test")

    assert result["success"] is False
    assert result["error_type"] == "authentication_error"
    assert "Invalid token" in result["error"]


@pytest.mark.asyncio
async def test_send_notification_tool_connection_error(mock_mcp, get_client, mock_client):
    """Test tool wrapper handles connection errors."""
    from src.homeassistant_mcp.exceptions import ConnectionError

    mock_client.call_service.side_effect = ConnectionError("Connection refused")

    registered_func = None

    def capture_tool():
        def decorator(func):
            nonlocal registered_func
            registered_func = func
            return func

        return decorator

    mock_mcp.tool = capture_tool
    register_notify_tool(mock_mcp, get_client)

    result = await registered_func(message="Test")

    assert result["success"] is False
    assert result["error_type"] == "connection_error"
    assert "Connection refused" in result["error"]


@pytest.mark.asyncio
async def test_send_notification_tool_service_call_error(mock_mcp, get_client, mock_client):
    """Test tool wrapper handles service call errors."""
    from src.homeassistant_mcp.exceptions import ServiceCallError

    mock_client.call_service.side_effect = ServiceCallError("Service failed")

    registered_func = None

    def capture_tool():
        def decorator(func):
            nonlocal registered_func
            registered_func = func
            return func

        return decorator

    mock_mcp.tool = capture_tool
    register_notify_tool(mock_mcp, get_client)

    result = await registered_func(message="Test")

    assert result["success"] is False
    assert result["error_type"] == "service_call_error"
    assert "Service failed" in result["error"]


@pytest.mark.asyncio
async def test_send_notification_tool_home_assistant_error(mock_mcp, get_client, mock_client):
    """Test tool wrapper handles generic Home Assistant errors."""
    from src.homeassistant_mcp.exceptions import HomeAssistantError

    mock_client.call_service.side_effect = HomeAssistantError("Generic error")

    registered_func = None

    def capture_tool():
        def decorator(func):
            nonlocal registered_func
            registered_func = func
            return func

        return decorator

    mock_mcp.tool = capture_tool
    register_notify_tool(mock_mcp, get_client)

    result = await registered_func(message="Test")

    assert result["success"] is False
    assert result["error_type"] == "home_assistant_error"
    assert "Generic error" in result["error"]


@pytest.mark.asyncio
async def test_send_notification_tool_unexpected_error(mock_mcp, get_client, mock_client):
    """Test tool wrapper handles unexpected errors."""
    mock_client.call_service.side_effect = ValueError("Unexpected error")

    registered_func = None

    def capture_tool():
        def decorator(func):
            nonlocal registered_func
            registered_func = func
            return func

        return decorator

    mock_mcp.tool = capture_tool
    register_notify_tool(mock_mcp, get_client)

    result = await registered_func(message="Test")

    assert result["success"] is False
    assert result["error_type"] == "unexpected_error"
    assert "unexpected error occurred" in result["error"].lower()
