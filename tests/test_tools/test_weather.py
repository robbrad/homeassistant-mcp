"""Unit tests for the weather information tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.devices.weather import (
    _get_forecast,
    _get_weather,
    _list_weather_entities,
)


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)

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
def sample_weather_states():
    """Sample weather entity states for testing."""
    return [
        {
            "entity_id": "weather.home",
            "state": "sunny",
            "attributes": {
                "friendly_name": "Home Weather",
                "temperature": 72.5,
                "temperature_unit": "°F",
                "humidity": 65,
                "pressure": 1013.25,
                "pressure_unit": "hPa",
                "wind_speed": 10.5,
                "wind_speed_unit": "mph",
                "wind_bearing": 180,
                "visibility": 10,
                "visibility_unit": "mi",
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "weather.forecast",
            "state": "cloudy",
            "attributes": {
                "friendly_name": "Weather Forecast",
                "temperature": 68.0,
                "temperature_unit": "°F",
                "humidity": 70,
                "pressure": 1010.0,
                "pressure_unit": "hPa",
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "sensor.temperature",
            "state": "72",
            "attributes": {
                "friendly_name": "Temperature Sensor",
            },
        },
    ]


@pytest.fixture
def sample_daily_forecast():
    """Sample daily forecast data for testing."""
    return {
        "weather.home": {
            "forecast": [
                {
                    "datetime": "2024-01-01T00:00:00",
                    "condition": "sunny",
                    "temperature": 75.0,
                    "templow": 60.0,
                    "precipitation": 0.0,
                    "precipitation_probability": 10,
                    "wind_speed": 12.0,
                    "wind_bearing": 180,
                    "humidity": 60,
                    "pressure": 1015.0,
                },
                {
                    "datetime": "2024-01-02T00:00:00",
                    "condition": "cloudy",
                    "temperature": 70.0,
                    "templow": 58.0,
                    "precipitation": 0.5,
                    "precipitation_probability": 40,
                    "wind_speed": 15.0,
                    "wind_bearing": 200,
                },
                {
                    "datetime": "2024-01-03T00:00:00",
                    "condition": "rainy",
                    "temperature": 65.0,
                    "templow": 55.0,
                    "precipitation": 2.5,
                    "precipitation_probability": 80,
                },
            ]
        }
    }


@pytest.fixture
def sample_hourly_forecast():
    """Sample hourly forecast data for testing."""
    return {
        "weather.home": {
            "forecast": [
                {
                    "datetime": "2024-01-01T12:00:00",
                    "condition": "sunny",
                    "temperature": 72.0,
                    "precipitation": 0.0,
                    "precipitation_probability": 5,
                    "wind_speed": 10.0,
                },
                {
                    "datetime": "2024-01-01T13:00:00",
                    "condition": "sunny",
                    "temperature": 74.0,
                    "precipitation": 0.0,
                    "precipitation_probability": 5,
                    "wind_speed": 11.0,
                },
            ]
        }
    }


class TestListWeatherEntities:
    """Tests for listing weather entities."""

    @pytest.mark.asyncio
    async def test_list_weather_entities_success(self, mock_client, sample_weather_states):
        """Test successfully listing all weather entities."""
        mock_client._states_data = sample_weather_states

        result = await _list_weather_entities(mock_client)

        assert result["success"] is True
        assert result["count"] == 2  # Only weather entities, not the sensor
        assert len(result["weather_entities"]) == 2

        # Verify home weather data
        home_weather = next(
            entity for entity in result["weather_entities"] if entity["entity_id"] == "weather.home"
        )
        assert home_weather["name"] == "Home Weather"
        assert home_weather["state"] == "sunny"
        assert home_weather["temperature"] == 72.5
        assert home_weather["humidity"] == 65
        assert home_weather["pressure"] == 1013.25

        # Verify forecast weather data
        forecast_weather = next(
            entity
            for entity in result["weather_entities"]
            if entity["entity_id"] == "weather.forecast"
        )
        assert forecast_weather["state"] == "cloudy"
        assert forecast_weather["temperature"] == 68.0

    @pytest.mark.asyncio
    async def test_list_weather_entities_empty(self, mock_client):
        """Test listing weather entities when none exist."""
        mock_client._states_data = [
            {
                "entity_id": "sensor.temperature",
                "state": "72",
                "attributes": {},
            }
        ]

        result = await _list_weather_entities(mock_client)

        assert result["success"] is True
        assert result["count"] == 0
        assert result["weather_entities"] == []


class TestGetWeather:
    """Tests for getting current weather conditions."""

    @pytest.mark.asyncio
    async def test_get_weather_success(self, mock_client):
        """Test successfully getting current weather conditions."""
        mock_client.get_state.return_value = {
            "entity_id": "weather.home",
            "state": "sunny",
            "attributes": {
                "friendly_name": "Home Weather",
                "temperature": 72.5,
                "temperature_unit": "°F",
                "humidity": 65,
                "pressure": 1013.25,
                "pressure_unit": "hPa",
                "wind_speed": 10.5,
                "wind_speed_unit": "mph",
                "wind_bearing": 180,
                "visibility": 10,
                "visibility_unit": "mi",
            },
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_weather(mock_client, "weather.home")

        assert result["success"] is True
        assert result["weather"]["entity_id"] == "weather.home"
        assert result["weather"]["name"] == "Home Weather"
        assert result["weather"]["condition"] == "sunny"
        assert result["weather"]["temperature"] == 72.5
        assert result["weather"]["temperature_unit"] == "°F"
        assert result["weather"]["humidity"] == 65
        assert result["weather"]["pressure"] == 1013.25
        assert result["weather"]["wind_speed"] == 10.5
        assert result["weather"]["wind_bearing"] == 180
        assert result["weather"]["visibility"] == 10

        mock_client.get_state.assert_called_once_with("weather.home")

    @pytest.mark.asyncio
    async def test_get_weather_minimal_attributes(self, mock_client):
        """Test getting weather with minimal attributes."""
        mock_client.get_state.return_value = {
            "entity_id": "weather.simple",
            "state": "cloudy",
            "attributes": {
                "friendly_name": "Simple Weather",
                "temperature": 68.0,
            },
            "last_updated": "2024-01-01T12:00:00",
        }

        result = await _get_weather(mock_client, "weather.simple")

        assert result["success"] is True
        assert result["weather"]["condition"] == "cloudy"
        assert result["weather"]["temperature"] == 68.0
        # Verify optional fields are not present
        assert "humidity" not in result["weather"]
        assert "pressure" not in result["weather"]

    @pytest.mark.asyncio
    async def test_get_weather_not_found(self, mock_client):
        """Test getting weather for an entity that doesn't exist."""
        mock_client.get_state.side_effect = EntityNotFoundError(
            "Entity 'weather.nonexistent' not found"
        )

        with pytest.raises(EntityNotFoundError):
            await _get_weather(mock_client, "weather.nonexistent")

    @pytest.mark.asyncio
    async def test_get_weather_invalid_entity_type(self, mock_client):
        """Test getting weather for an entity that is not a weather entity."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_weather(mock_client, "sensor.temperature")

        assert "not a weather entity" in str(exc_info.value)
        mock_client.get_state.assert_not_called()


class TestGetForecast:
    """Tests for getting weather forecasts."""

    @pytest.mark.asyncio
    async def test_get_daily_forecast_success(self, mock_client, sample_daily_forecast):
        """Test successfully getting daily forecast."""
        mock_client.call_service.return_value = sample_daily_forecast

        result = await _get_forecast(mock_client, "weather.home", "daily")

        assert result["success"] is True
        assert result["entity_id"] == "weather.home"
        assert result["forecast_type"] == "daily"
        assert len(result["forecast"]) == 3

        # Verify first forecast entry
        first_day = result["forecast"][0]
        assert first_day["datetime"] == "2024-01-01T00:00:00"
        assert first_day["condition"] == "sunny"
        assert first_day["temperature"] == 75.0
        assert first_day["templow"] == 60.0
        assert first_day["precipitation"] == 0.0
        assert first_day["precipitation_probability"] == 10
        assert first_day["wind_speed"] == 12.0
        assert first_day["wind_bearing"] == 180
        assert first_day["humidity"] == 60
        assert first_day["pressure"] == 1015.0

        # Verify second forecast entry (partial data)
        second_day = result["forecast"][1]
        assert second_day["condition"] == "cloudy"
        assert second_day["temperature"] == 70.0
        assert "humidity" not in second_day  # Not present in sample data
        assert "pressure" not in second_day

        mock_client.call_service.assert_called_once_with(
            "weather", "get_forecasts", {"entity_id": "weather.home", "type": "daily"}
        )

    @pytest.mark.asyncio
    async def test_get_hourly_forecast_success(self, mock_client, sample_hourly_forecast):
        """Test successfully getting hourly forecast."""
        mock_client.call_service.return_value = sample_hourly_forecast

        result = await _get_forecast(mock_client, "weather.home", "hourly")

        assert result["success"] is True
        assert result["entity_id"] == "weather.home"
        assert result["forecast_type"] == "hourly"
        assert len(result["forecast"]) == 2

        # Verify first hourly entry
        first_hour = result["forecast"][0]
        assert first_hour["datetime"] == "2024-01-01T12:00:00"
        assert first_hour["condition"] == "sunny"
        assert first_hour["temperature"] == 72.0
        assert first_hour["precipitation"] == 0.0

        mock_client.call_service.assert_called_once_with(
            "weather", "get_forecasts", {"entity_id": "weather.home", "type": "hourly"}
        )

    @pytest.mark.asyncio
    async def test_get_forecast_empty(self, mock_client):
        """Test getting forecast when no forecast data is available."""
        mock_client.call_service.return_value = {"weather.home": {"forecast": []}}

        result = await _get_forecast(mock_client, "weather.home", "daily")

        assert result["success"] is True
        assert result["forecast"] == []

    @pytest.mark.asyncio
    async def test_get_forecast_invalid_entity_type(self, mock_client):
        """Test getting forecast for an entity that is not a weather entity."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_forecast(mock_client, "sensor.temperature", "daily")

        assert "not a weather entity" in str(exc_info.value)
        mock_client.call_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_forecast_service_error(self, mock_client):
        """Test handling service call errors when getting forecast."""
        mock_client.call_service.side_effect = Exception("Service unavailable")

        with pytest.raises(ServiceCallError) as exc_info:
            await _get_forecast(mock_client, "weather.home", "daily")

        assert "Failed to get forecast" in str(exc_info.value)


class TestWeatherControlIntegration:
    """Integration tests for the weather_control tool function."""

    @pytest.mark.asyncio
    async def test_weather_control_list_action(self, mock_client, sample_weather_states):
        """Test the weather_control function with list action."""
        from src.homeassistant_mcp.tools.devices.weather import register_weather_tool

        mock_client._states_data = sample_weather_states

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
        register_weather_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func(action="list")

        assert result["success"] is True
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_weather_control_get_action(self, mock_client):
        """Test the weather_control function with get action."""
        from src.homeassistant_mcp.tools.devices.weather import register_weather_tool

        mock_client.get_state.return_value = {
            "entity_id": "weather.home",
            "state": "sunny",
            "attributes": {
                "friendly_name": "Home Weather",
                "temperature": 72.5,
                "humidity": 65,
            },
            "last_updated": "2024-01-01T12:00:00",
        }

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool(**kwargs):
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_weather_tool(mock_mcp, lambda: mock_client)

        result = await registered_func(action="get", entity_id="weather.home")

        assert result["success"] is True
        assert result["weather"]["condition"] == "sunny"
        assert result["weather"]["temperature"] == 72.5

    @pytest.mark.asyncio
    async def test_weather_control_missing_entity_id(self):
        """Test weather_control with actions that require entity_id but it's missing."""
        from src.homeassistant_mcp.tools.devices.weather import register_weather_tool

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

        register_weather_tool(mock_mcp, lambda: mock_client)

        # Test get without entity_id
        result = await registered_func(action="get")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

        # Test get_forecast without entity_id
        result = await registered_func(action="get_forecast", forecast_type="daily")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]

    @pytest.mark.asyncio
    async def test_weather_control_missing_forecast_type(self):
        """Test weather_control get_forecast without forecast_type."""
        from src.homeassistant_mcp.tools.devices.weather import register_weather_tool

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

        register_weather_tool(mock_mcp, lambda: mock_client)

        # Test get_forecast without forecast_type
        result = await registered_func(action="get_forecast", entity_id="weather.home")
        assert result["success"] is False
        assert "forecast_type is required" in result["error"]

    @pytest.mark.asyncio
    async def test_weather_control_error_handling(self):
        """Test weather_control error handling."""
        from src.homeassistant_mcp.tools.devices.weather import register_weather_tool

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

        register_weather_tool(mock_mcp, lambda: mock_client)

        # Test with EntityNotFoundError
        result = await registered_func(action="get", entity_id="weather.nonexistent")
        assert result["success"] is False
        assert "Entity not found" in result["error"]
        assert result["error_type"] == "entity_not_found"
