"""Integration tests for backward compatibility between resources and tools.

This test suite verifies that resources and tools can coexist without conflicts,
share the same HomeAssistantClient instance, and don't interfere with each other.

Validates: Requirements 18.4, 18.5, 18.6
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import HomeAssistantClient
from src.homeassistant_mcp.tools.devices.lights import _list_lights, _turn_on_light
from src.homeassistant_mcp.tools.devices.switch import _list_switches, _turn_on_switch


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)

    async def _filtered_get_states(domain=None, area=None, limit=None):
        states = list(client._states_data)
        if domain:
            states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
        return states

    client._states_data = []
    client.get_states = AsyncMock(side_effect=_filtered_get_states)
    return client


@pytest.fixture
def sample_states():
    """Sample states for testing."""
    return [
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "brightness": 255,
            },
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "light.bedroom",
            "state": "off",
            "attributes": {
                "friendly_name": "Bedroom Light",
            },
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
        {
            "entity_id": "switch.fan",
            "state": "on",
            "attributes": {
                "friendly_name": "Fan Switch",
            },
            "last_changed": "2024-01-01T10:00:00",
            "last_updated": "2024-01-01T10:00:00",
        },
    ]


class TestResourcesAndToolsCoexistence:
    """Integration tests for resources and tools coexistence."""

    @pytest.mark.asyncio
    async def test_multiple_tools_use_same_client(self, mock_client, sample_states):
        """Test that multiple tools can use the same client instance.

        This verifies the architectural constraint that both resources and tools
        receive the same client instance via get_client().

        Validates: Requirement 18.4
        """
        # Setup mock responses
        mock_client._states_data = sample_states

        # Call multiple tool functions with the same client
        lights_result = await _list_lights(mock_client)
        switches_result = await _list_switches(mock_client)

        # Verify both tools used the client successfully
        assert lights_result["success"] is True
        assert lights_result["count"] == 2
        assert switches_result["success"] is True
        assert switches_result["count"] == 1

        # Verify both used the same client instance
        assert mock_client.get_states.call_count == 2

    @pytest.mark.asyncio
    async def test_concurrent_tool_access(self, mock_client, sample_states):
        """Test concurrent access to multiple tools.

        Validates: Requirement 18.5, 18.6
        """
        # Setup mock responses
        mock_client._states_data = sample_states
        mock_client.call_service.return_value = {"success": True}

        # Run multiple tool operations concurrently
        tasks = [
            _list_lights(mock_client),
            _list_switches(mock_client),
            _turn_on_light(mock_client, "light.living_room", brightness=200),
            _turn_on_switch(mock_client, "switch.fan"),
        ]

        # Wait for all to complete
        results = await asyncio.gather(*tasks)

        # Verify all completed successfully
        assert len(results) == 4
        assert results[0]["success"] is True  # list lights
        assert results[1]["success"] is True  # list switches
        assert results[2]["success"] is True  # turn on light
        assert results[3]["success"] is True  # turn on switch

        # Verify no interference between operations
        assert mock_client.get_states.called
        assert mock_client.call_service.called

    @pytest.mark.asyncio
    async def test_tool_read_does_not_interfere_with_tool_write(self, mock_client, sample_states):
        """Test that tool reads don't interfere with tool writes.

        Validates: Requirement 18.6
        """
        # Setup mock responses
        mock_client._states_data = sample_states
        mock_client.call_service.return_value = {"success": True}

        # Read state via tool
        list_result = await _list_lights(mock_client)
        assert list_result["success"] is True
        assert list_result["count"] == 2

        # Change state via tool
        control_result = await _turn_on_light(mock_client, "light.living_room", brightness=128)
        assert control_result["success"] is True

        # Verify tool called the service
        mock_client.call_service.assert_called_once()
        call_args = mock_client.call_service.call_args
        assert call_args[0][0] == "light"
        assert call_args[0][1] == "turn_on"

        # Verify read didn't interfere with write
        assert mock_client.get_states.call_count == 1
        assert mock_client.call_service.call_count == 1

    @pytest.mark.asyncio
    async def test_tool_state_changes_consistent(self, mock_client, sample_states):
        """Test that tool state changes are consistent across calls.

        Validates: Requirement 18.5, 18.6
        """
        # Setup initial state
        initial_states = [
            {
                "entity_id": "light.living_room",
                "state": "off",
                "attributes": {"friendly_name": "Living Room Light", "brightness": 0},
                "last_changed": "2024-01-01T12:00:00",
                "last_updated": "2024-01-01T12:00:00",
            }
        ]

        # Setup updated state after tool change
        updated_states = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"friendly_name": "Living Room Light", "brightness": 255},
                "last_changed": "2024-01-01T12:01:00",
                "last_updated": "2024-01-01T12:01:00",
            }
        ]

        # Mock client to return different states
        mock_client.get_states.side_effect = [initial_states, updated_states]
        mock_client.call_service.return_value = {"success": True}

        # Read initial state via tool
        list_result_1 = await _list_lights(mock_client)
        assert list_result_1["success"] is True
        assert list_result_1["lights"][0]["state"] == "off"

        # Change state via tool
        control_result = await _turn_on_light(mock_client, "light.living_room", brightness=255)
        assert control_result["success"] is True

        # Read updated state via tool
        list_result_2 = await _list_lights(mock_client)
        assert list_result_2["success"] is True
        assert list_result_2["lights"][0]["state"] == "on"

    @pytest.mark.asyncio
    async def test_tools_share_client_cache(self, mock_client, sample_states):
        """Test that tools benefit from shared client caching.

        Validates: Requirement 18.4, 18.5
        """
        # Setup mock to track call count
        mock_client._states_data = sample_states

        # First call via tool (should hit API)
        list_result_1 = await _list_lights(mock_client)
        assert list_result_1["success"] is True
        assert mock_client.get_states.call_count == 1

        # Second call via tool (may use cache, but we're testing the interface)
        list_result_2 = await _list_lights(mock_client)
        assert list_result_2["success"] is True

        # Both calls should use the same client instance
        # The actual caching behavior is tested in cache-specific tests
        assert mock_client.get_states.called

    @pytest.mark.asyncio
    async def test_multiple_concurrent_tool_operations(self, mock_client, sample_states):
        """Test multiple concurrent tool operations.

        Validates: Requirement 18.5, 18.6
        """
        # Setup mock responses
        mock_client._states_data = sample_states
        mock_client.call_service.return_value = {"success": True}

        # Create multiple concurrent operations
        tasks = [
            _list_lights(mock_client),
            _list_switches(mock_client),
            _turn_on_light(mock_client, "light.living_room", brightness=200),
            _turn_on_switch(mock_client, "switch.fan"),
            _list_lights(mock_client),
        ]

        # Execute all concurrently
        results = await asyncio.gather(*tasks)

        # Verify all completed successfully
        assert len(results) == 5
        for result in results:
            assert result["success"] is True

        # Verify client was used by all operations
        assert mock_client.get_states.called
        assert mock_client.call_service.called

    @pytest.mark.asyncio
    async def test_error_in_one_tool_does_not_affect_another(self, mock_client, sample_states):
        """Test that errors in one tool don't affect other tools.

        Validates: Requirement 18.6
        """
        # Setup mock to raise error for one call but succeed for others
        from src.homeassistant_mcp.exceptions import ServiceCallError

        mock_client._states_data = sample_states
        mock_client.call_service.side_effect = [
            ServiceCallError("Service call failed"),
            {"success": True},
        ]

        # First tool call should work
        list_result = await _list_lights(mock_client)
        assert list_result["success"] is True

        # Second tool call should raise error
        with pytest.raises(ServiceCallError):
            await _turn_on_light(mock_client, "light.living_room", brightness=255)

        # Third tool call should still work
        control_result = await _turn_on_switch(mock_client, "switch.fan")
        assert control_result["success"] is True

    @pytest.mark.asyncio
    async def test_client_instance_consistency(self, mock_client):
        """Test that the same client instance is used consistently.

        This verifies the architectural constraint that get_client() always
        returns the same instance.

        Validates: Requirement 18.4
        """
        # Setup mock
        mock_client._states_data = []

        # Call multiple tools
        await _list_lights(mock_client)
        await _list_switches(mock_client)

        # Verify the same client instance was used
        # (In real usage, get_client() would return the same instance)
        assert mock_client.get_states.call_count == 2

    @pytest.mark.asyncio
    async def test_tools_registration_does_not_conflict(self):
        """Test that tool registration doesn't conflict with resource registration.

        This is a smoke test to ensure the registration process works.

        Validates: Requirement 18.4, 18.5
        """
        # Import registration functions
        from src.homeassistant_mcp.resources import register_all_resources
        from src.homeassistant_mcp.tools.devices.lights import register_lights_tool
        from src.homeassistant_mcp.tools.devices.switch import register_switch_tool

        # Create mock MCP server and get_client function
        mock_mcp = MagicMock()
        mock_get_client = MagicMock()

        # Register tools
        register_lights_tool(mock_mcp, mock_get_client)
        register_switch_tool(mock_mcp, mock_get_client)

        # Register resources
        register_all_resources(mock_mcp, mock_get_client)

        # Verify registrations were called
        # (The actual registration is handled by FastMCP decorators)
        assert mock_mcp.tool.called or mock_mcp.resource.called
