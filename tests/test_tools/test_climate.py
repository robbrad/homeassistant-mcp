"""Tests for climate control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import EntityNotFoundError, ServiceCallError
from src.homeassistant_mcp.tools.devices.climate import register_climate_tool


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock()

    # Domain-filtering side_effect for get_states
    async def _filtered_get_states(domain=None, area=None, limit=None):
        states = list(client._states_data)
        if domain:
            states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
        return states

    client._states_data = []
    client.get_states = AsyncMock(side_effect=_filtered_get_states)

    return client


@pytest.fixture
def mock_mcp():
    """Create a mock FastMCP instance."""
    mcp = MagicMock()
    mcp.tool = lambda **kwargs: lambda func: func
    return mcp


@pytest.fixture
def climate_control_func(mock_mcp, mock_client):
    """Register the climate control tool and return the function."""
    register_climate_tool(mock_mcp, lambda: mock_client)
    # The tool decorator returns the function itself in our mock
    return mock_mcp.tool.call_args[0][0] if mock_mcp.tool.called else None


@pytest.mark.asyncio
async def test_list_climate_devices(mock_client):
    """Test listing all climate devices."""
    # Setup mock data
    mock_client._states_data = [
        {
            "entity_id": "climate.living_room",
            "state": "heat",
            "attributes": {
                "friendly_name": "Living Room Thermostat",
                "current_temperature": 70.0,
                "temperature": 72.0,
                "hvac_mode": "heat",
                "fan_mode": "auto",
            },
        },
        {
            "entity_id": "climate.bedroom",
            "state": "cool",
            "attributes": {
                "friendly_name": "Bedroom AC",
                "current_temperature": 75.0,
                "target_temp_high": 78.0,
                "target_temp_low": 72.0,
                "hvac_mode": "cool",
            },
        },
        {"entity_id": "light.kitchen", "state": "on", "attributes": {}},
    ]

    # Import and call the function directly
    from src.homeassistant_mcp.tools.devices.climate import _list_climate_devices

    result = await _list_climate_devices(mock_client)

    # Verify the result
    assert result["success"] is True
    assert result["count"] == 2
    assert len(result["climate_devices"]) == 2

    # Check first device
    device1 = result["climate_devices"][0]
    assert device1["entity_id"] == "climate.living_room"
    assert device1["name"] == "Living Room Thermostat"
    assert device1["state"] == "heat"
    assert device1["current_temperature"] == 70.0
    assert device1["target_temperature"] == 72.0
    assert device1["hvac_mode"] == "heat"
    assert device1["fan_mode"] == "auto"

    # Check second device
    device2 = result["climate_devices"][1]
    assert device2["entity_id"] == "climate.bedroom"
    assert device2["name"] == "Bedroom AC"
    assert device2["state"] == "cool"
    assert device2["current_temperature"] == 75.0
    assert device2["target_temp_high"] == 78.0
    assert device2["target_temp_low"] == 72.0
    assert device2["hvac_mode"] == "cool"


@pytest.mark.asyncio
async def test_get_climate_device(mock_client):
    """Test getting details for a specific climate device."""
    # Setup mock data
    mock_client.get_state.return_value = {
        "entity_id": "climate.living_room",
        "state": "heat",
        "last_changed": "2024-01-01T12:00:00",
        "last_updated": "2024-01-01T12:00:00",
        "attributes": {
            "friendly_name": "Living Room Thermostat",
            "current_temperature": 70.0,
            "temperature": 72.0,
            "hvac_mode": "heat",
            "fan_mode": "auto",
            "hvac_modes": ["off", "heat", "cool", "auto"],
        },
    }

    from src.homeassistant_mcp.tools.devices.climate import _get_climate_device

    result = await _get_climate_device(mock_client, "climate.living_room")

    # Verify the result
    assert result["success"] is True
    assert result["climate_device"]["entity_id"] == "climate.living_room"
    assert result["climate_device"]["name"] == "Living Room Thermostat"
    assert result["climate_device"]["state"] == "heat"
    assert result["climate_device"]["last_changed"] == "2024-01-01T12:00:00"
    assert "attributes" in result["climate_device"]

    # Verify the client was called correctly
    mock_client.get_state.assert_called_once_with("climate.living_room")


@pytest.mark.asyncio
async def test_get_climate_device_invalid_entity():
    """Test getting a non-climate entity raises an error."""
    mock_client = AsyncMock()

    from src.homeassistant_mcp.tools.devices.climate import _get_climate_device

    with pytest.raises(EntityNotFoundError) as exc_info:
        await _get_climate_device(mock_client, "light.living_room")

    assert "not a climate entity" in str(exc_info.value)


@pytest.mark.asyncio
async def test_set_hvac_mode(mock_client):
    """Test setting HVAC mode."""
    from src.homeassistant_mcp.tools.devices.climate import _set_hvac_mode

    result = await _set_hvac_mode(mock_client, "climate.living_room", "heat")

    # Verify the result
    assert result["success"] is True
    assert result["entity_id"] == "climate.living_room"
    assert result["hvac_mode"] == "heat"
    assert "set to 'heat'" in result["message"]

    # Verify the service call
    mock_client.call_service.assert_called_once_with(
        "climate", "set_hvac_mode", {"entity_id": "climate.living_room", "hvac_mode": "heat"}
    )


@pytest.mark.asyncio
async def test_set_hvac_mode_invalid_entity():
    """Test setting HVAC mode on non-climate entity raises an error."""
    mock_client = AsyncMock()

    from src.homeassistant_mcp.tools.devices.climate import _set_hvac_mode

    with pytest.raises(EntityNotFoundError) as exc_info:
        await _set_hvac_mode(mock_client, "light.living_room", "heat")

    assert "not a climate entity" in str(exc_info.value)


@pytest.mark.asyncio
async def test_set_temperature_single_setpoint(mock_client):
    """Test setting temperature for single-setpoint device."""
    from src.homeassistant_mcp.tools.devices.climate import _set_temperature

    result = await _set_temperature(mock_client, "climate.living_room", temperature=72.0)

    # Verify the result
    assert result["success"] is True
    assert result["entity_id"] == "climate.living_room"
    assert result["temperature"] == 72.0
    assert "updated" in result["message"]

    # Verify the service call
    mock_client.call_service.assert_called_once_with(
        "climate", "set_temperature", {"entity_id": "climate.living_room", "temperature": 72.0}
    )


@pytest.mark.asyncio
async def test_set_temperature_dual_setpoint(mock_client):
    """Test setting temperature range for dual-setpoint device."""
    from src.homeassistant_mcp.tools.devices.climate import _set_temperature

    result = await _set_temperature(
        mock_client, "climate.living_room", target_temp_high=78.0, target_temp_low=72.0
    )

    # Verify the result
    assert result["success"] is True
    assert result["entity_id"] == "climate.living_room"
    assert result["target_temp_high"] == 78.0
    assert result["target_temp_low"] == 72.0

    # Verify the service call
    mock_client.call_service.assert_called_once_with(
        "climate",
        "set_temperature",
        {"entity_id": "climate.living_room", "target_temp_high": 78.0, "target_temp_low": 72.0},
    )


@pytest.mark.asyncio
async def test_set_temperature_missing_high():
    """Test that providing only target_temp_low returns an error."""
    mock_client = AsyncMock()

    from src.homeassistant_mcp.tools.devices.climate import _set_temperature

    result = await _set_temperature(mock_client, "climate.living_room", target_temp_low=72.0)

    # Verify error response
    assert result["success"] is False
    assert "target_temp_high is required" in result["error"]

    # Verify no service call was made
    mock_client.call_service.assert_not_called()


@pytest.mark.asyncio
async def test_set_temperature_missing_low():
    """Test that providing only target_temp_high returns an error."""
    mock_client = AsyncMock()

    from src.homeassistant_mcp.tools.devices.climate import _set_temperature

    result = await _set_temperature(mock_client, "climate.living_room", target_temp_high=78.0)

    # Verify error response
    assert result["success"] is False
    assert "target_temp_low is required" in result["error"]

    # Verify no service call was made
    mock_client.call_service.assert_not_called()


@pytest.mark.asyncio
async def test_set_temperature_no_parameters():
    """Test that providing no temperature parameters returns an error."""
    mock_client = AsyncMock()

    from src.homeassistant_mcp.tools.devices.climate import _set_temperature

    result = await _set_temperature(mock_client, "climate.living_room")

    # Verify error response
    assert result["success"] is False
    assert "must be provided" in result["error"]

    # Verify no service call was made
    mock_client.call_service.assert_not_called()


@pytest.mark.asyncio
async def test_set_temperature_conflicting_parameters():
    """Test that providing both single and dual setpoint parameters returns an error."""
    mock_client = AsyncMock()

    from src.homeassistant_mcp.tools.devices.climate import _set_temperature

    result = await _set_temperature(
        mock_client,
        "climate.living_room",
        temperature=72.0,
        target_temp_high=78.0,
        target_temp_low=70.0,
    )

    # Verify error response
    assert result["success"] is False
    assert "Cannot specify both" in result["error"]

    # Verify no service call was made
    mock_client.call_service.assert_not_called()


@pytest.mark.asyncio
async def test_set_temperature_invalid_entity():
    """Test setting temperature on non-climate entity raises an error."""
    mock_client = AsyncMock()

    from src.homeassistant_mcp.tools.devices.climate import _set_temperature

    with pytest.raises(EntityNotFoundError) as exc_info:
        await _set_temperature(mock_client, "light.living_room", temperature=72.0)

    assert "not a climate entity" in str(exc_info.value)


@pytest.mark.asyncio
async def test_set_fan_mode(mock_client):
    """Test setting fan mode."""
    from src.homeassistant_mcp.tools.devices.climate import _set_fan_mode

    result = await _set_fan_mode(mock_client, "climate.living_room", "auto")

    # Verify the result
    assert result["success"] is True
    assert result["entity_id"] == "climate.living_room"
    assert result["fan_mode"] == "auto"
    assert "set to 'auto'" in result["message"]

    # Verify the service call
    mock_client.call_service.assert_called_once_with(
        "climate", "set_fan_mode", {"entity_id": "climate.living_room", "fan_mode": "auto"}
    )


@pytest.mark.asyncio
async def test_set_fan_mode_invalid_entity():
    """Test setting fan mode on non-climate entity raises an error."""
    mock_client = AsyncMock()

    from src.homeassistant_mcp.tools.devices.climate import _set_fan_mode

    with pytest.raises(EntityNotFoundError) as exc_info:
        await _set_fan_mode(mock_client, "light.living_room", "auto")

    assert "not a climate entity" in str(exc_info.value)


@pytest.mark.asyncio
async def test_climate_control_list_action(mock_client):
    """Test climate_control with list action."""
    mock_client._states_data = [
        {
            "entity_id": "climate.living_room",
            "state": "heat",
            "attributes": {"friendly_name": "Living Room"},
        }
    ]

    from src.homeassistant_mcp.tools.devices.climate import register_climate_tool

    # Create a real tool function
    tool_func = None

    def mock_tool_decorator(**kwargs):
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp = MagicMock()
    mock_mcp.tool = mock_tool_decorator

    register_climate_tool(mock_mcp, lambda: mock_client)

    result = await tool_func(action="list")

    assert result["success"] is True
    assert result["count"] == 1


@pytest.mark.asyncio
async def test_climate_control_get_action_missing_entity_id(mock_client):
    """Test climate_control get action without entity_id."""
    from src.homeassistant_mcp.tools.devices.climate import register_climate_tool

    tool_func = None

    def mock_tool_decorator(**kwargs):
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp = MagicMock()
    mock_mcp.tool = mock_tool_decorator

    register_climate_tool(mock_mcp, lambda: mock_client)

    result = await tool_func(action="get")

    assert result["success"] is False
    assert "entity_id is required" in result["error"]


@pytest.mark.asyncio
async def test_climate_control_set_hvac_mode_missing_mode(mock_client):
    """Test climate_control set_hvac_mode action without hvac_mode."""
    from src.homeassistant_mcp.tools.devices.climate import register_climate_tool

    tool_func = None

    def mock_tool_decorator(**kwargs):
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp = MagicMock()
    mock_mcp.tool = mock_tool_decorator

    register_climate_tool(mock_mcp, lambda: mock_client)

    result = await tool_func(action="set_hvac_mode", entity_id="climate.living_room")

    assert result["success"] is False
    assert "hvac_mode is required" in result["error"]


@pytest.mark.asyncio
async def test_climate_control_set_fan_mode_missing_mode(mock_client):
    """Test climate_control set_fan_mode action without fan_mode."""
    from src.homeassistant_mcp.tools.devices.climate import register_climate_tool

    tool_func = None

    def mock_tool_decorator(**kwargs):
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp = MagicMock()
    mock_mcp.tool = mock_tool_decorator

    register_climate_tool(mock_mcp, lambda: mock_client)

    result = await tool_func(action="set_fan_mode", entity_id="climate.living_room")

    assert result["success"] is False
    assert "fan_mode is required" in result["error"]


@pytest.mark.asyncio
async def test_climate_control_entity_not_found_error(mock_client):
    """Test climate_control handles EntityNotFoundError."""
    mock_client.get_state.side_effect = EntityNotFoundError("Entity not found")

    from src.homeassistant_mcp.tools.devices.climate import register_climate_tool

    tool_func = None

    def mock_tool_decorator(**kwargs):
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp = MagicMock()
    mock_mcp.tool = mock_tool_decorator

    register_climate_tool(mock_mcp, lambda: mock_client)

    result = await tool_func(action="get", entity_id="climate.nonexistent")

    assert result["success"] is False
    assert "Entity not found" in result["error"]


@pytest.mark.asyncio
async def test_climate_control_service_call_error(mock_client):
    """Test climate_control handles ServiceCallError."""
    mock_client.call_service.side_effect = ServiceCallError("Service call failed")

    from src.homeassistant_mcp.tools.devices.climate import register_climate_tool

    tool_func = None

    def mock_tool_decorator(**kwargs):
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp = MagicMock()
    mock_mcp.tool = mock_tool_decorator

    register_climate_tool(mock_mcp, lambda: mock_client)

    result = await tool_func(
        action="set_hvac_mode", entity_id="climate.living_room", hvac_mode="heat"
    )

    assert result["success"] is False
    assert "Service call failed" in result["error"]


@pytest.mark.asyncio
async def test_climate_control_unexpected_error(mock_client):
    """Test climate_control handles unexpected errors."""
    mock_client.get_states.side_effect = Exception("Unexpected error")

    from src.homeassistant_mcp.tools.devices.climate import register_climate_tool

    tool_func = None

    def mock_tool_decorator(**kwargs):
        def decorator(func):
            nonlocal tool_func
            tool_func = func
            return func

        return decorator

    mock_mcp = MagicMock()
    mock_mcp.tool = mock_tool_decorator

    register_climate_tool(mock_mcp, lambda: mock_client)

    result = await tool_func(action="list")

    assert result["success"] is False
    assert "unexpected error" in result["error"].lower()
