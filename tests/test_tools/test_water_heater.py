"""Unit tests for the water heater control tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.devices.water_heater import (
    _get_water_heater,
    _list_water_heaters,
    _set_away_mode,
    _set_operation_mode,
    _set_temperature,
    _turn_off_water_heater,
    _turn_on_water_heater,
)


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)
    return client


@pytest.fixture
def sample_water_heater_states():
    """Sample water heater entity states for testing."""
    return [
        {
            "entity_id": "water_heater.tank",
            "state": "electric",
            "attributes": {
                "friendly_name": "Water Heater Tank",
                "temperature": 50.0,
                "target_temp": 55.0,
                "operation_mode": "electric",
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "water_heater.basement",
            "state": "eco",
            "attributes": {
                "friendly_name": "Basement Water Heater",
                "temperature": 45.0,
                "target_temp": 50.0,
                "operation_mode": "eco",
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "climate.living_room",
            "state": "heat",
            "attributes": {
                "friendly_name": "Living Room Climate",
            },
        },
    ]


class TestListWaterHeaters:
    """Tests for listing water heaters."""

    @pytest.mark.asyncio
    async def test_list_water_heaters_success(self, mock_client, sample_water_heater_states):
        """Test successfully listing all water heaters."""
        mock_client.get_states.return_value = sample_water_heater_states

        result = await _list_water_heaters(mock_client)

        assert result["success"] is True
        assert result["count"] == 2  # Only water heaters, not the climate
        assert len(result["water_heaters"]) == 2

        # Verify water heater data
        tank = next(wh for wh in result["water_heaters"] if wh["entity_id"] == "water_heater.tank")
        assert tank["name"] == "Water Heater Tank"
        assert tank["state"] == "electric"
        assert tank["current_temperature"] == 50.0
        assert tank["target_temperature"] == 55.0
        assert tank["operation_mode"] == "electric"

    @pytest.mark.asyncio
    async def test_list_water_heaters_empty(self, mock_client):
        """Test listing water heaters when no water heaters exist."""
        mock_client.get_states.return_value = [
            {
                "entity_id": "climate.test",
                "state": "heat",
                "attributes": {},
            }
        ]

        result = await _list_water_heaters(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["water_heaters"] == []


class TestGetWaterHeater:
    """Tests for getting a specific water heater."""

    @pytest.mark.asyncio
    async def test_get_water_heater_success(self, mock_client):
        """Test successfully getting a specific water heater."""
        mock_client.get_state.return_value = {
            "entity_id": "water_heater.tank",
            "state": "electric",
            "attributes": {
                "friendly_name": "Water Heater Tank",
                "temperature": 50.0,
                "target_temp": 55.0,
                "operation_mode": "electric",
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_water_heater(mock_client, "water_heater.tank")

        assert result["success"] is True
        assert result["water_heater"]["entity_id"] == "water_heater.tank"
        assert result["water_heater"]["name"] == "Water Heater Tank"
        assert result["water_heater"]["state"] == "electric"
        assert result["water_heater"]["last_changed"] == "2024-01-01T12:00:00"

        mock_client.get_state.assert_called_once_with("water_heater.tank")

    @pytest.mark.asyncio
    async def test_get_water_heater_not_found(self, mock_client):
        """Test getting a water heater that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'water_heater.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_water_heater(mock_client, "water_heater.nonexistent")

    @pytest.mark.asyncio
    async def test_get_water_heater_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not a water heater."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_water_heater(mock_client, "climate.living_room")

        assert "not a water heater entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestTurnOnWaterHeater:
    """Tests for turning on water heaters."""

    @pytest.mark.asyncio
    async def test_turn_on_water_heater_success(self, mock_client):
        """Test successfully turning on a water heater."""
        mock_client.call_service.return_value = {}

        result = await _turn_on_water_heater(mock_client, "water_heater.tank")

        assert result["success"] is True
        assert result["entity_id"] == "water_heater.tank"
        assert "turned on" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "water_heater", "turn_on", {"entity_id": "water_heater.tank"}
        )

    @pytest.mark.asyncio
    async def test_turn_on_water_heater_invalid_entity_type(self, mock_client):
        """Test turning on an entity that is not a water heater."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _turn_on_water_heater(mock_client, "climate.living_room")

        assert "not a water heater entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_turn_on_water_heater_service_error(self, mock_client):
        """Test handling service call errors."""
        mock_client.call_service.side_effect = ServiceCallError("Service call failed")

        with pytest.raises(ServiceCallError):
            await _turn_on_water_heater(mock_client, "water_heater.tank")


class TestTurnOffWaterHeater:
    """Tests for turning off water heaters."""

    @pytest.mark.asyncio
    async def test_turn_off_water_heater_success(self, mock_client):
        """Test successfully turning off a water heater."""
        mock_client.call_service.return_value = {}

        result = await _turn_off_water_heater(mock_client, "water_heater.tank")

        assert result["success"] is True
        assert result["entity_id"] == "water_heater.tank"
        assert "turned off" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "water_heater", "turn_off", {"entity_id": "water_heater.tank"}
        )

    @pytest.mark.asyncio
    async def test_turn_off_water_heater_invalid_entity_type(self, mock_client):
        """Test turning off an entity that is not a water heater."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _turn_off_water_heater(mock_client, "climate.living_room")

        assert "not a water heater entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestSetTemperature:
    """Tests for setting water heater temperature."""

    @pytest.mark.asyncio
    async def test_set_temperature_success(self, mock_client):
        """Test successfully setting water heater temperature."""
        mock_client.call_service.return_value = {}

        result = await _set_temperature(mock_client, "water_heater.tank", 60.0)

        assert result["success"] is True
        assert result["entity_id"] == "water_heater.tank"
        assert result["temperature"] == 60.0
        assert "temperature set to 60.0" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "water_heater",
            "set_temperature",
            {"entity_id": "water_heater.tank", "temperature": 60.0},
        )

    @pytest.mark.asyncio
    async def test_set_temperature_invalid_entity_type(self, mock_client):
        """Test setting temperature for an entity that is not a water heater."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _set_temperature(mock_client, "climate.living_room", 60.0)

        assert "not a water heater entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestSetOperationMode:
    """Tests for setting water heater operation mode."""

    @pytest.mark.asyncio
    async def test_set_operation_mode_success(self, mock_client):
        """Test successfully setting water heater operation mode."""
        mock_client.call_service.return_value = {}

        result = await _set_operation_mode(mock_client, "water_heater.tank", "eco")

        assert result["success"] is True
        assert result["entity_id"] == "water_heater.tank"
        assert result["operation_mode"] == "eco"
        assert "operation mode set to 'eco'" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "water_heater",
            "set_operation_mode",
            {"entity_id": "water_heater.tank", "operation_mode": "eco"},
        )

    @pytest.mark.asyncio
    async def test_set_operation_mode_invalid_entity_type(self, mock_client):
        """Test setting operation mode for an entity that is not a water heater."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _set_operation_mode(mock_client, "climate.living_room", "eco")

        assert "not a water heater entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestSetAwayMode:
    """Tests for setting water heater away mode."""

    @pytest.mark.asyncio
    async def test_set_away_mode_enable_success(self, mock_client):
        """Test successfully enabling water heater away mode."""
        mock_client.call_service.return_value = {}

        result = await _set_away_mode(mock_client, "water_heater.tank", True)

        assert result["success"] is True
        assert result["entity_id"] == "water_heater.tank"
        assert result["away_mode"] is True
        assert "away mode enabled" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "water_heater", "set_away_mode", {"entity_id": "water_heater.tank", "away_mode": "on"}
        )

    @pytest.mark.asyncio
    async def test_set_away_mode_disable_success(self, mock_client):
        """Test successfully disabling water heater away mode."""
        mock_client.call_service.return_value = {}

        result = await _set_away_mode(mock_client, "water_heater.tank", False)

        assert result["success"] is True
        assert result["entity_id"] == "water_heater.tank"
        assert result["away_mode"] is False
        assert "away mode disabled" in result["message"]

        mock_client.call_service.assert_called_once_with(
            "water_heater", "set_away_mode", {"entity_id": "water_heater.tank", "away_mode": "off"}
        )

    @pytest.mark.asyncio
    async def test_set_away_mode_invalid_entity_type(self, mock_client):
        """Test setting away mode for an entity that is not a water heater."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _set_away_mode(mock_client, "climate.living_room", True)

        assert "not a water heater entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()


class TestWaterHeaterControlIntegration:
    """Integration tests for the water_heater_control tool function."""

    @pytest.mark.asyncio
    async def test_water_heater_control_list_action(self, mock_client, sample_water_heater_states):
        """Test the water_heater_control function with list action."""
        from src.homeassistant_mcp.tools.devices.water_heater import register_water_heater_tool

        mock_client.get_states.return_value = sample_water_heater_states

        # Create a mock FastMCP instance
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        # Register the tool
        register_water_heater_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_water_heater_control_missing_entity_id(self):
        """Test water_heater_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.devices.water_heater import register_water_heater_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_water_heater_tool(mock_mcp, lambda: mock_client)

        # Test get without entity_id
        result = await registered_func(action="get")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test turn_on without entity_id
        result = await registered_func(action="turn_on")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test set_temperature without entity_id
        result = await registered_func(action="set_temperature", temperature=60.0)
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test set_temperature without temperature
        result = await registered_func(action="set_temperature", entity_id="water_heater.tank")
        assert result["success"] is False
        assert "temperature is required" in result["error"]

    @pytest.mark.asyncio
    async def test_water_heater_control_error_handling(self):
        """Test water_heater_control error handling."""
        from src.homeassistant_mcp.tools.devices.water_heater import register_water_heater_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.get_state.side_effect = EntityNotFoundError("Entity not found")

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_water_heater_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="water_heater.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
        assert result["error_type"] == "entity_not_found"
