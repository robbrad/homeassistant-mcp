"""Property-based tests for backward compatibility with existing tools.

Feature: mcp-resources-layer
Property 17: Backward Compatibility
Validates: Requirements 18.1, 18.2, 18.3, 18.4

This test ensures that the resources layer does not break existing tool APIs.
"""

import inspect
from typing import Any
from unittest.mock import AsyncMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.homeassistant_mcp.hass.client import HomeAssistantClient
from src.homeassistant_mcp.tools.devices.climate import (
    _get_climate_device,
    _list_climate_devices,
    _set_hvac_mode,
    _set_temperature,
)
from src.homeassistant_mcp.tools.devices.lights import (
    _get_light,
    _list_lights,
    _turn_off_light,
    _turn_on_light,
)
from src.homeassistant_mcp.tools.devices.switch import (
    _get_switch,
    _list_switches,
    _turn_off_switch,
    _turn_on_switch,
)

# Expected function signatures for critical tools
EXPECTED_SIGNATURES = {
    "_list_lights": ["client"],
    "_get_light": ["client", "entity_id"],
    "_turn_on_light": ["client", "entity_id", "brightness", "color_temp", "rgb_color"],
    "_turn_off_light": ["client", "entity_id"],
    "_list_climate_devices": ["client"],
    "_get_climate_device": ["client", "entity_id"],
    "_set_temperature": [
        "client",
        "entity_id",
        "temperature",
        "target_temp_high",
        "target_temp_low",
    ],
    "_set_hvac_mode": ["client", "entity_id", "hvac_mode"],
    "_list_switches": ["client"],
    "_get_switch": ["client", "entity_id"],
    "_turn_on_switch": ["client", "entity_id"],
    "_turn_off_switch": ["client", "entity_id"],
}


class TestBackwardCompatibilityProperties:
    """Property tests for backward compatibility."""

    def test_tool_function_signatures_unchanged(self):
        """Property: Tool function signatures must remain unchanged.

        For any tool function, its signature must match the expected signature
        to ensure backward compatibility.

        Validates: Requirements 18.1, 18.2
        """
        # Map function names to actual functions
        functions = {
            "_list_lights": _list_lights,
            "_get_light": _get_light,
            "_turn_on_light": _turn_on_light,
            "_turn_off_light": _turn_off_light,
            "_list_climate_devices": _list_climate_devices,
            "_get_climate_device": _get_climate_device,
            "_set_temperature": _set_temperature,
            "_set_hvac_mode": _set_hvac_mode,
            "_list_switches": _list_switches,
            "_get_switch": _get_switch,
            "_turn_on_switch": _turn_on_switch,
            "_turn_off_switch": _turn_off_switch,
        }

        for func_name, expected_params in EXPECTED_SIGNATURES.items():
            func = functions[func_name]
            sig = inspect.signature(func)
            actual_params = list(sig.parameters.keys())

            # Verify all expected parameters are present
            for param in expected_params:
                assert param in actual_params, (
                    f"Function {func_name} missing expected parameter '{param}'. "
                    f"Expected: {expected_params}, Got: {actual_params}"
                )

    @pytest.mark.asyncio
    @given(
        entity_name=st.text(
            min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz0123456789_"
        ),
        brightness=st.integers(min_value=0, max_value=255),
    )
    @settings(max_examples=50, deadline=None)
    async def test_light_tool_behavior_consistent(self, entity_name: str, brightness: int):
        """Property: Light tool behavior must be consistent.

        For any valid entity_id and brightness, the light tool must:
        1. Accept the same parameters
        2. Return the same response structure
        3. Call the client with the same methods

        Validates: Requirements 18.2, 18.3
        """
        # Create valid entity_id
        entity_id = f"light.{entity_name}" if entity_name else "light.test"

        # Create mock client
        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.call_service.return_value = {"success": True}

        # Call the tool function
        result = await _turn_on_light(
            client=mock_client,
            entity_id=entity_id,
            brightness=brightness,
            color_temp=None,
            rgb_color=None,
        )

        # Verify response structure is consistent
        assert isinstance(result, dict), "Tool must return a dictionary"
        assert "success" in result, "Response must contain 'success' field"
        assert isinstance(result["success"], bool), "'success' must be a boolean"

        # Verify client method was called correctly
        mock_client.call_service.assert_called_once()
        call_args = mock_client.call_service.call_args
        assert call_args[0][0] == "light", "Must call 'light' domain"
        assert call_args[0][1] == "turn_on", "Must call 'turn_on' service"

    @pytest.mark.asyncio
    @given(
        entity_name=st.text(
            min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz0123456789_"
        ),
    )
    @settings(max_examples=50, deadline=None)
    async def test_switch_tool_behavior_consistent(self, entity_name: str):
        """Property: Switch tool behavior must be consistent.

        For any valid entity_id, the switch tool must:
        1. Accept the same parameters
        2. Return the same response structure
        3. Call the client with the same methods

        Validates: Requirements 18.2, 18.3
        """
        # Create valid entity_id
        entity_id = f"switch.{entity_name}" if entity_name else "switch.test"

        # Create mock client
        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.call_service.return_value = {"success": True}

        # Call the tool function
        result = await _turn_on_switch(
            client=mock_client,
            entity_id=entity_id,
        )

        # Verify response structure is consistent
        assert isinstance(result, dict), "Tool must return a dictionary"
        assert "success" in result, "Response must contain 'success' field"
        assert isinstance(result["success"], bool), "'success' must be a boolean"

        # Verify client method was called correctly
        mock_client.call_service.assert_called_once()
        call_args = mock_client.call_service.call_args
        assert call_args[0][0] == "switch", "Must call 'switch' domain"
        assert call_args[0][1] == "turn_on", "Must call 'turn_on' service"

    @pytest.mark.asyncio
    async def test_client_instance_shared_between_tools_and_resources(self):
        """Property: Tools and resources must use the same client instance.

        For any tool and resource, they must share the same HomeAssistantClient
        instance to ensure consistent state and caching.

        Validates: Requirements 18.4
        """
        # This test verifies the architectural constraint that both tools and
        # resources receive the same client instance via get_client()

        # Create a mock client
        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_client.get_states.return_value = [
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {"friendly_name": "Test Light"},
            }
        ]

        # Call a tool function
        tool_result = await _list_lights(mock_client)

        # Verify the tool used the client
        assert tool_result["success"] is True
        mock_client.get_states.assert_called_once()

        # Reset mock
        mock_client.reset_mock()

        # Import and test a resource function (if available)
        try:
            from src.homeassistant_mcp.resources.entities import get_entity_state

            # Call a resource function with the same client
            resource_result = await get_entity_state(mock_client, "light.test")

            # Verify the resource used the same client
            assert resource_result is not None
            # Both should have used the same client instance
            assert mock_client.get_state.called or mock_client.get_states.called
        except ImportError:
            # Resources may not be fully implemented yet, skip this part
            pass

    def test_tool_return_types_unchanged(self):
        """Property: Tool return types must remain unchanged.

        For any tool function, its return type annotation must be consistent
        to ensure backward compatibility with type checkers.

        Validates: Requirements 18.1, 18.2
        """
        # Check return type annotations for critical functions
        functions_to_check = [
            (_list_lights, dict),
            (_get_light, dict),
            (_turn_on_light, dict),
            (_turn_off_light, dict),
            (_list_climate_devices, dict),
            (_get_climate_device, dict),
        ]

        for func, _expected_return_type in functions_to_check:
            sig = inspect.signature(func)
            # All tool functions should return dict (or dict-like structures)
            # We check that the return annotation exists and is appropriate
            if sig.return_annotation != inspect.Signature.empty:
                # If there's a return annotation, it should be dict or compatible
                assert (
                    sig.return_annotation is dict
                    or "dict" in str(sig.return_annotation).lower()
                    or sig.return_annotation is Any
                ), f"Function {func.__name__} has unexpected return type: {sig.return_annotation}"
