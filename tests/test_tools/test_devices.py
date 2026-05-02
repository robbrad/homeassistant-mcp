"""Unit tests for the device listing tool."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import HomeAssistantClient, ServiceCallError
from src.homeassistant_mcp.tools.device_list import _list_and_filter_devices


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)
    return client


@pytest.fixture
def sample_device_states():
    """Sample device entity states for testing across multiple domains."""
    return [
        # Lights
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "area_name": "Living Room",
                "floor_name": "Ground Floor",
                "brightness": 255,
            },
        },
        {
            "entity_id": "light.bedroom",
            "state": "off",
            "attributes": {
                "friendly_name": "Bedroom Light",
                "area_name": "Bedroom",
                "floor_name": "First Floor",
            },
        },
        {
            "entity_id": "light.kitchen",
            "state": "on",
            "attributes": {
                "friendly_name": "Kitchen Light",
                "area_name": "Kitchen",
                "floor_name": "Ground Floor",
                "brightness": 128,
            },
        },
        # Switches
        {
            "entity_id": "switch.garage",
            "state": "on",
            "attributes": {
                "friendly_name": "Garage Switch",
                "area_name": "Garage",
                "floor_name": "Ground Floor",
            },
        },
        {
            "entity_id": "switch.porch",
            "state": "off",
            "attributes": {
                "friendly_name": "Porch Switch",
                "area_name": "Porch",
                "floor_name": "Ground Floor",
            },
        },
        # Sensors
        {
            "entity_id": "sensor.temperature",
            "state": "72.5",
            "attributes": {
                "friendly_name": "Temperature Sensor",
                "area_name": "Living Room",
                "floor_name": "Ground Floor",
                "unit_of_measurement": "°F",
            },
        },
        {
            "entity_id": "sensor.humidity",
            "state": "45",
            "attributes": {
                "friendly_name": "Humidity Sensor",
                "area_name": "Bedroom",
                "floor_name": "First Floor",
                "unit_of_measurement": "%",
            },
        },
        # Climate
        {
            "entity_id": "climate.thermostat",
            "state": "heat",
            "attributes": {
                "friendly_name": "Main Thermostat",
                "area_name": "Living Room",
                "floor_name": "Ground Floor",
                "current_temperature": 72,
                "temperature": 75,
            },
        },
        # Binary sensors
        {
            "entity_id": "binary_sensor.door",
            "state": "off",
            "attributes": {
                "friendly_name": "Front Door",
                "area_name": "Entrance",
                "floor_name": "Ground Floor",
            },
        },
        {
            "entity_id": "binary_sensor.motion",
            "state": "on",
            "attributes": {
                "friendly_name": "Motion Sensor",
                "area_name": "Living Room",
                "floor_name": "Ground Floor",
            },
        },
        # Unavailable device
        {
            "entity_id": "light.unavailable",
            "state": "unavailable",
            "attributes": {
                "friendly_name": "Unavailable Light",
                "area_name": "Basement",
                "floor_name": "Basement",
            },
        },
    ]


class TestListAndFilterDevices:
    """Tests for listing and filtering devices."""

    @pytest.mark.asyncio
    async def test_list_all_devices(self, mock_client, sample_device_states):
        """Test listing all devices without filters."""
        mock_client.get_states.return_value = sample_device_states

        result = await _list_and_filter_devices(mock_client)

        assert result["success"] is True
        assert result["total_devices"] == 11
        assert result["domain_count"] == 5  # light, switch, sensor, climate, binary_sensor
        assert result["filters_applied"] is None

        # Verify domains are present
        assert "light" in result["domains"]
        assert "switch" in result["domains"]
        assert "sensor" in result["domains"]
        assert "climate" in result["domains"]
        assert "binary_sensor" in result["domains"]

        # Verify light domain statistics
        light_domain = result["domains"]["light"]
        assert light_domain["total"] == 4  # Including unavailable
        assert light_domain["active"] == 3  # Excluding unavailable
        assert "on" in light_domain["states"]
        assert "off" in light_domain["states"]
        assert "unavailable" in light_domain["states"]
        assert len(light_domain["sample_devices"]) <= 5

    @pytest.mark.asyncio
    async def test_filter_by_domain(self, mock_client, sample_device_states):
        """Test filtering devices by domain."""
        mock_client.get_states.return_value = sample_device_states

        result = await _list_and_filter_devices(mock_client, domain="light")

        assert result["success"] is True
        assert result["total_devices"] == 4
        assert result["domain_count"] == 1
        assert result["filters_applied"]["domain"] == "light"

        # Verify only light domain is present
        assert "light" in result["domains"]
        assert "switch" not in result["domains"]

        # Verify light statistics
        light_domain = result["domains"]["light"]
        assert light_domain["total"] == 4
        assert light_domain["active"] == 3

    @pytest.mark.asyncio
    async def test_filter_by_area(self, mock_client, sample_device_states):
        """Test filtering devices by area."""
        mock_client.get_states.return_value = sample_device_states

        result = await _list_and_filter_devices(mock_client, area="Living Room")

        assert result["success"] is True
        assert result["total_devices"] == 4  # light, sensor, climate, binary_sensor
        assert result["filters_applied"]["area"] == "Living Room"

        # Verify domains in Living Room
        assert "light" in result["domains"]
        assert "sensor" in result["domains"]
        assert "climate" in result["domains"]
        assert "binary_sensor" in result["domains"]

        # Verify each domain has correct count
        assert result["domains"]["light"]["total"] == 1
        assert result["domains"]["sensor"]["total"] == 1
        assert result["domains"]["climate"]["total"] == 1
        assert result["domains"]["binary_sensor"]["total"] == 1

    @pytest.mark.asyncio
    async def test_filter_by_floor(self, mock_client, sample_device_states):
        """Test filtering devices by floor."""
        mock_client.get_states.return_value = sample_device_states

        result = await _list_and_filter_devices(mock_client, floor="Ground Floor")

        assert result["success"] is True
        assert result["total_devices"] == 8
        assert result["filters_applied"]["floor"] == "Ground Floor"

        # Verify domains on Ground Floor
        assert "light" in result["domains"]
        assert "switch" in result["domains"]
        assert "sensor" in result["domains"]
        assert "climate" in result["domains"]
        assert "binary_sensor" in result["domains"]

        # Verify bedroom light (First Floor) is not included
        for domain_data in result["domains"].values():
            for device in domain_data["sample_devices"]:
                assert device["entity_id"] != "light.bedroom"

    @pytest.mark.asyncio
    async def test_filter_by_domain_and_area(self, mock_client, sample_device_states):
        """Test filtering devices by both domain and area."""
        mock_client.get_states.return_value = sample_device_states

        result = await _list_and_filter_devices(mock_client, domain="light", area="Living Room")

        assert result["success"] is True
        assert result["total_devices"] == 1
        assert result["domain_count"] == 1
        assert result["filters_applied"]["domain"] == "light"
        assert result["filters_applied"]["area"] == "Living Room"

        # Verify only living room light
        light_domain = result["domains"]["light"]
        assert light_domain["total"] == 1
        assert light_domain["sample_devices"][0]["entity_id"] == "light.living_room"

    @pytest.mark.asyncio
    async def test_filter_by_domain_and_floor(self, mock_client, sample_device_states):
        """Test filtering devices by domain and floor."""
        mock_client.get_states.return_value = sample_device_states

        result = await _list_and_filter_devices(mock_client, domain="light", floor="First Floor")

        assert result["success"] is True
        assert result["total_devices"] == 1
        assert result["filters_applied"]["domain"] == "light"
        assert result["filters_applied"]["floor"] == "First Floor"

        # Verify only bedroom light
        light_domain = result["domains"]["light"]
        assert light_domain["total"] == 1
        assert light_domain["sample_devices"][0]["entity_id"] == "light.bedroom"

    @pytest.mark.asyncio
    async def test_filter_by_all_criteria(self, mock_client, sample_device_states):
        """Test filtering devices by domain, area, and floor."""
        mock_client.get_states.return_value = sample_device_states

        result = await _list_and_filter_devices(
            mock_client, domain="light", area="Kitchen", floor="Ground Floor"
        )

        assert result["success"] is True
        assert result["total_devices"] == 1
        assert result["filters_applied"]["domain"] == "light"
        assert result["filters_applied"]["area"] == "Kitchen"
        assert result["filters_applied"]["floor"] == "Ground Floor"

        # Verify only kitchen light
        light_domain = result["domains"]["light"]
        assert light_domain["total"] == 1
        assert light_domain["sample_devices"][0]["entity_id"] == "light.kitchen"

    @pytest.mark.asyncio
    async def test_filter_no_matches(self, mock_client, sample_device_states):
        """Test filtering with criteria that match no devices."""
        mock_client.get_states.return_value = sample_device_states

        result = await _list_and_filter_devices(
            mock_client, domain="light", area="Nonexistent Area"
        )

        assert result["success"] is True
        assert result["total_devices"] == 0
        assert result["domain_count"] == 0
        assert result["domains"] == {}

    @pytest.mark.asyncio
    async def test_case_insensitive_area_filter(self, mock_client, sample_device_states):
        """Test that area filtering is case-insensitive."""
        mock_client.get_states.return_value = sample_device_states

        result = await _list_and_filter_devices(mock_client, area="living room")

        assert result["success"] is True
        assert result["total_devices"] == 4

        # Also test with different case
        result2 = await _list_and_filter_devices(mock_client, area="LIVING ROOM")
        assert result2["total_devices"] == 4

    @pytest.mark.asyncio
    async def test_case_insensitive_floor_filter(self, mock_client, sample_device_states):
        """Test that floor filtering is case-insensitive."""
        mock_client.get_states.return_value = sample_device_states

        result = await _list_and_filter_devices(mock_client, floor="ground floor")

        assert result["success"] is True
        assert result["total_devices"] == 8

    @pytest.mark.asyncio
    async def test_device_statistics(self, mock_client, sample_device_states):
        """Test that device statistics are calculated correctly."""
        mock_client.get_states.return_value = sample_device_states

        result = await _list_and_filter_devices(mock_client, domain="light")

        light_domain = result["domains"]["light"]

        # Verify statistics
        assert light_domain["total"] == 4
        assert light_domain["active"] == 3  # Excluding unavailable

        # Verify state counts
        assert light_domain["states"]["on"] == 2
        assert light_domain["states"]["off"] == 1
        assert light_domain["states"]["unavailable"] == 1

    @pytest.mark.asyncio
    async def test_sample_devices_format(self, mock_client, sample_device_states):
        """Test that sample devices have correct format."""
        mock_client.get_states.return_value = sample_device_states

        result = await _list_and_filter_devices(mock_client, domain="light")

        light_domain = result["domains"]["light"]
        sample_device = light_domain["sample_devices"][0]

        # Verify sample device has required fields
        assert "entity_id" in sample_device
        assert "name" in sample_device
        assert "state" in sample_device
        assert "area" in sample_device
        assert "floor" in sample_device

    @pytest.mark.asyncio
    async def test_sample_devices_limit(self, mock_client):
        """Test that sample devices are limited to 5 per domain."""
        # Create 10 light entities
        many_lights = [
            {
                "entity_id": f"light.test_{i}",
                "state": "on",
                "attributes": {
                    "friendly_name": f"Test Light {i}",
                },
            }
            for i in range(10)
        ]

        mock_client.get_states.return_value = many_lights

        result = await _list_and_filter_devices(mock_client, domain="light")

        light_domain = result["domains"]["light"]
        assert light_domain["total"] == 10
        assert len(light_domain["sample_devices"]) == 5  # Limited to 5

    @pytest.mark.asyncio
    async def test_devices_without_area_or_floor(self, mock_client):
        """Test handling devices without area or floor attributes."""
        devices_without_location = [
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {
                    "friendly_name": "Test Light",
                    # No area or floor
                },
            },
        ]

        mock_client.get_states.return_value = devices_without_location

        result = await _list_and_filter_devices(mock_client)

        assert result["success"] is True
        assert result["total_devices"] == 1

        sample_device = result["domains"]["light"]["sample_devices"][0]
        assert sample_device["area"] is None
        assert sample_device["floor"] is None

    @pytest.mark.asyncio
    async def test_devices_with_area_id_instead_of_name(self, mock_client):
        """Test handling devices with area_id instead of area_name."""
        devices_with_area_id = [
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {
                    "friendly_name": "Test Light",
                    "area_id": "living_room",
                    # No area_name
                },
            },
        ]

        mock_client.get_states.return_value = devices_with_area_id

        result = await _list_and_filter_devices(mock_client, area="living_room")

        assert result["success"] is True
        assert result["total_devices"] == 1

    @pytest.mark.asyncio
    async def test_empty_entity_list(self, mock_client):
        """Test handling empty entity list."""
        mock_client.get_states.return_value = []

        result = await _list_and_filter_devices(mock_client)

        assert result["success"] is True
        assert result["total_devices"] == 0
        assert result["domain_count"] == 0
        assert result["domains"] == {}

    @pytest.mark.asyncio
    async def test_entities_without_entity_id(self, mock_client):
        """Test handling entities without entity_id field."""
        invalid_entities = [
            {
                "state": "on",
                "attributes": {},
                # No entity_id
            },
            {
                "entity_id": "light.valid",
                "state": "on",
                "attributes": {},
            },
        ]

        mock_client.get_states.return_value = invalid_entities

        result = await _list_and_filter_devices(mock_client)

        assert result["success"] is True
        assert result["total_devices"] == 1  # Only the valid one

    @pytest.mark.asyncio
    async def test_multiple_domains_grouping(self, mock_client, sample_device_states):
        """Test that devices are correctly grouped by domain."""
        mock_client.get_states.return_value = sample_device_states

        result = await _list_and_filter_devices(mock_client)

        # Verify all expected domains are present
        expected_domains = ["light", "switch", "sensor", "climate", "binary_sensor"]
        for domain in expected_domains:
            assert domain in result["domains"]

        # Verify counts for each domain
        assert result["domains"]["light"]["total"] == 4
        assert result["domains"]["switch"]["total"] == 2
        assert result["domains"]["sensor"]["total"] == 2
        assert result["domains"]["climate"]["total"] == 1
        assert result["domains"]["binary_sensor"]["total"] == 2


class TestListDevicesIntegration:
    """Integration tests for the list_devices tool function."""

    @pytest.mark.asyncio
    async def test_list_devices_tool_registration(self, mock_client, sample_device_states):
        """Test the list_devices tool registration and execution."""
        from src.homeassistant_mcp.tools.device_list import register_devices_tool

        mock_client.get_states.return_value = sample_device_states

        # Create a mock FastMCP instance
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        # Register the tool
        register_devices_tool(mock_mcp, lambda: mock_client)

        # Call the registered function
        result = await registered_func()

        assert result["success"] is True
        assert result["total_devices"] == 11
        assert result["domain_count"] == 5

    @pytest.mark.asyncio
    async def test_list_devices_with_filters(self, mock_client, sample_device_states):
        """Test list_devices with various filters."""
        from src.homeassistant_mcp.tools.device_list import register_devices_tool

        mock_client.get_states.return_value = sample_device_states

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_devices_tool(mock_mcp, lambda: mock_client)

        # Test with domain filter
        result = await registered_func(domain="light")
        assert result["success"] is True
        assert result["total_devices"] == 4

        # Test with area filter
        result = await registered_func(area="Living Room")
        assert result["success"] is True
        assert result["total_devices"] == 4

        # Test with floor filter
        result = await registered_func(floor="Ground Floor")
        assert result["success"] is True
        assert result["total_devices"] == 8

    @pytest.mark.asyncio
    async def test_list_devices_error_handling(self):
        """Test list_devices error handling."""
        from src.homeassistant_mcp.tools.device_list import register_devices_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.get_states.side_effect = ServiceCallError("API error")

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_devices_tool(mock_mcp, lambda: mock_client)

        # Test with ServiceCallError
        result = await registered_func()
        assert result["success"] is False
        assert "API error" in result["error"]

    @pytest.mark.asyncio
    async def test_list_devices_unexpected_error(self):
        """Test list_devices handling of unexpected errors."""
        from src.homeassistant_mcp.tools.device_list import register_devices_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.get_states.side_effect = Exception("Unexpected error")

        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool

        register_devices_tool(mock_mcp, lambda: mock_client)

        # Test with unexpected error
        result = await registered_func()
        assert result["success"] is False
        assert "unexpected error" in result["error"].lower()
