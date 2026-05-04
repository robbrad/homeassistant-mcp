"""Unit tests for prompt parameter validation."""

import pytest
from unittest.mock import AsyncMock

from homeassistant_mcp.prompts.control import register_control_prompts
from homeassistant_mcp.prompts.explain import register_explain_prompts
from homeassistant_mcp.prompts.automation import register_automation_prompts


class TestParameterValidation:
    """Tests for parameter validation across all prompts."""

    @pytest.mark.asyncio
    async def test_control_entity_empty_entity_id(self, mock_mcp, mock_client, get_client):
        """Test control_entity with empty entity_id parameter."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        # Empty string should be handled gracefully
        result = await control_entity("")

        assert isinstance(result, list)
        content = result[0].content.text
        # Should provide helpful error message
        assert "entity_id" in content.lower() or "invalid" in content.lower()

    @pytest.mark.asyncio
    async def test_control_entity_invalid_entity_id_format(self, mock_mcp, mock_client, get_client):
        """Test control_entity with invalid entity_id format (no domain)."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        # Invalid format: no domain separator
        mock_client.get_state.return_value = {
            "entity_id": "invalid_entity",
            "state": "unknown",
            "attributes": {},
        }

        result = await control_entity("invalid_entity")

        assert isinstance(result, list)
        # Should still work but may provide guidance about format

    @pytest.mark.asyncio
    async def test_control_entity_special_characters_in_entity_id(
        self, mock_mcp, mock_client, get_client
    ):
        """Test control_entity with special characters in entity_id."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        # Entity IDs with special characters (valid in HA)
        special_entity_ids = [
            "light.living_room_1",
            "light.living-room",
            "light.living_room_2nd_floor",
            "switch.ac_unit",
        ]

        for entity_id in special_entity_ids:
            mock_client.get_state.return_value = {
                "entity_id": entity_id,
                "state": "on",
                "attributes": {},
            }

            result = await control_entity(entity_id)

            assert isinstance(result, list)
            content = result[0].content.text
            assert entity_id in content

    @pytest.mark.asyncio
    async def test_control_entity_unicode_in_entity_id(self, mock_mcp, mock_client, get_client):
        """Test control_entity with unicode characters in entity_id."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        # Unicode in entity_id (unusual but should handle gracefully)
        mock_client.get_state.return_value = {
            "entity_id": "light.café_light",
            "state": "on",
            "attributes": {},
        }

        result = await control_entity("light.café_light")

        assert isinstance(result, list)
        # Should handle unicode gracefully

    @pytest.mark.asyncio
    async def test_control_entity_very_long_entity_id(self, mock_mcp, mock_client, get_client):
        """Test control_entity with very long entity_id."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        # Very long entity_id
        long_entity_id = "light." + "a" * 200

        mock_client.get_state.return_value = {
            "entity_id": long_entity_id,
            "state": "on",
            "attributes": {},
        }

        result = await control_entity(long_entity_id)

        assert isinstance(result, list)
        # Should handle long IDs gracefully

    @pytest.mark.asyncio
    async def test_control_entity_action_parameter_empty(self, mock_mcp, mock_client, get_client):
        """Test control_entity with empty action parameter."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "light.test",
            "state": "on",
            "attributes": {},
        }

        # Empty action should use default behavior
        result = await control_entity("light.test", action="")

        assert isinstance(result, list)
        content = result[0].content.text
        assert "light.test" in content

    @pytest.mark.asyncio
    async def test_control_entity_action_parameter_special_chars(
        self, mock_mcp, mock_client, get_client
    ):
        """Test control_entity with special characters in action parameter."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "light.test",
            "state": "on",
            "attributes": {},
        }

        # Action with special characters
        result = await control_entity("light.test", action="turn_on with brightness=100")

        assert isinstance(result, list)
        content = result[0].content.text
        # Should include the action in output
        assert "turn_on with brightness=100" in content

    @pytest.mark.asyncio
    async def test_control_area_empty_area_id(self, mock_mcp, mock_client, get_client):
        """Test control_area with empty area_id parameter."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        mock_client._states_data = []

        # Empty area_id should be handled gracefully
        result = await control_area("")

        assert isinstance(result, list)
        # Should provide helpful message

    @pytest.mark.asyncio
    async def test_control_area_special_characters_in_area_id(
        self, mock_mcp, mock_client, get_client
    ):
        """Test control_area with special characters in area_id."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        mock_client._states_data = []

        # Area IDs with special characters
        special_area_ids = [
            "Living Room",
            "2nd Floor",
            "Master Bedroom",
            "Mom's Office",
            "Café Area",
        ]

        for area_id in special_area_ids:
            result = await control_area(area_id)

            assert isinstance(result, list)
            content = result[0].content.text
            assert area_id in content

    @pytest.mark.asyncio
    async def test_control_area_goal_parameter_empty(self, mock_mcp, mock_client, get_client):
        """Test control_area with empty goal parameter."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        mock_client._states_data = []

        # Empty goal should use default behavior
        result = await control_area("Living Room", goal="")

        assert isinstance(result, list)
        # Should work without goal

    @pytest.mark.asyncio
    async def test_control_area_goal_parameter_very_long(self, mock_mcp, mock_client, get_client):
        """Test control_area with very long goal parameter."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        mock_client._states_data = []

        # Very long goal description
        long_goal = "Turn off all lights and " * 50

        result = await control_area("Living Room", goal=long_goal)

        assert isinstance(result, list)
        content = result[0].content.text
        # Should handle long goals gracefully

    @pytest.mark.asyncio
    async def test_explain_entity_empty_entity_id(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with empty entity_id parameter."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        # Empty entity_id should be handled gracefully
        result = await explain_entity("")

        assert isinstance(result, list)
        content = result[0].content.text
        # Should provide helpful error message
        assert "entity_id" in content.lower() or "invalid" in content.lower()

    @pytest.mark.asyncio
    async def test_explain_entity_special_characters(self, mock_mcp, mock_client, get_client):
        """Test explain_entity with special characters in entity_id."""
        register_explain_prompts(mock_mcp, get_client)
        explain_entity = mock_mcp._prompts["explain_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "sensor.temp_2nd_floor",
            "state": "72",
            "attributes": {"unit_of_measurement": "°F"},
        }

        result = await explain_entity("sensor.temp_2nd_floor")

        assert isinstance(result, list)
        content = result[0].content.text
        assert "sensor.temp_2nd_floor" in content

    @pytest.mark.asyncio
    async def test_diagnose_automation_empty_automation_id(
        self, mock_mcp, mock_client, get_client
    ):
        """Test diagnose_automation with empty automation_id parameter."""
        register_automation_prompts(mock_mcp, get_client)
        diagnose_automation = mock_mcp._prompts["diagnose_automation"]

        # Empty automation_id should be handled gracefully
        result = await diagnose_automation("")

        assert isinstance(result, list)
        content = result[0].content.text
        # Should provide helpful error message
        assert "automation" in content.lower() or "invalid" in content.lower()

    @pytest.mark.asyncio
    async def test_diagnose_automation_invalid_format(self, mock_mcp, mock_client, get_client):
        """Test diagnose_automation with invalid automation_id format."""
        register_automation_prompts(mock_mcp, get_client)
        diagnose_automation = mock_mcp._prompts["diagnose_automation"]

        # Invalid format: not an automation entity
        mock_client.get_state.return_value = {
            "entity_id": "light.test",
            "state": "on",
            "attributes": {},
        }

        result = await diagnose_automation("light.test")

        assert isinstance(result, list)
        # Should handle gracefully even if not an automation

    @pytest.mark.asyncio
    async def test_suggest_automation_empty_intent(self, mock_mcp, mock_client, get_client):
        """Test suggest_automation with empty intent parameter."""
        register_automation_prompts(mock_mcp, get_client)
        suggest_automation = mock_mcp._prompts["suggest_automation"]

        mock_client._states_data = []

        # Empty intent should be handled gracefully
        result = await suggest_automation("")

        assert isinstance(result, list)
        content = result[0].content.text
        # Should provide helpful message about needing intent

    @pytest.mark.asyncio
    async def test_suggest_automation_special_characters_in_intent(
        self, mock_mcp, mock_client, get_client
    ):
        """Test suggest_automation with special characters in intent."""
        register_automation_prompts(mock_mcp, get_client)
        suggest_automation = mock_mcp._prompts["suggest_automation"]

        mock_client._states_data = []

        # Intent with special characters
        result = await suggest_automation("Turn on lights @ 6:00 PM & play music")

        assert isinstance(result, list)
        content = result[0].content.text
        # Should handle special characters in intent

    @pytest.mark.asyncio
    async def test_suggest_automation_constraints_parameter_empty(
        self, mock_mcp, mock_client, get_client
    ):
        """Test suggest_automation with empty constraints parameter."""
        register_automation_prompts(mock_mcp, get_client)
        suggest_automation = mock_mcp._prompts["suggest_automation"]

        mock_client._states_data = []

        # Empty constraints should use default behavior
        result = await suggest_automation("Turn on lights at sunset", constraints="")

        assert isinstance(result, list)
        # Should work without constraints


class TestParameterTypeMismatches:
    """Tests for parameter type mismatches (if applicable)."""

    @pytest.mark.asyncio
    async def test_control_entity_none_entity_id(self, mock_mcp, mock_client, get_client):
        """Test control_entity with None as entity_id."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        # None should be handled or raise appropriate error
        try:
            result = await control_entity(None)
            # If it doesn't raise, should handle gracefully
            assert isinstance(result, list)
        except (TypeError, AttributeError):
            # Type error is acceptable for None
            pass

    @pytest.mark.asyncio
    async def test_control_area_none_area_id(self, mock_mcp, mock_client, get_client):
        """Test control_area with None as area_id."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        mock_client._states_data = []

        # None should be handled or raise appropriate error
        try:
            result = await control_area(None)
            # If it doesn't raise, should handle gracefully
            assert isinstance(result, list)
        except (TypeError, AttributeError):
            # Type error is acceptable for None
            pass


class TestWhitespaceHandling:
    """Tests for whitespace handling in parameters."""

    @pytest.mark.asyncio
    async def test_control_entity_leading_trailing_whitespace(
        self, mock_mcp, mock_client, get_client
    ):
        """Test control_entity with leading/trailing whitespace in entity_id."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "light.test",
            "state": "on",
            "attributes": {},
        }

        # Entity ID with whitespace
        result = await control_entity("  light.test  ")

        assert isinstance(result, list)
        # Should handle whitespace (either strip or handle gracefully)

    @pytest.mark.asyncio
    async def test_control_area_whitespace_in_area_id(self, mock_mcp, mock_client, get_client):
        """Test control_area with whitespace in area_id."""
        register_control_prompts(mock_mcp, get_client)
        control_area = mock_mcp._prompts["control_area"]

        mock_client._states_data = []

        # Area ID with extra whitespace
        result = await control_area("  Living   Room  ")

        assert isinstance(result, list)
        # Should handle whitespace gracefully

    @pytest.mark.asyncio
    async def test_control_entity_action_only_whitespace(self, mock_mcp, mock_client, get_client):
        """Test control_entity with action parameter containing only whitespace."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "light.test",
            "state": "on",
            "attributes": {},
        }

        # Action with only whitespace
        result = await control_entity("light.test", action="   ")

        assert isinstance(result, list)
        # Should treat as empty action


class TestCaseSensitivity:
    """Tests for case sensitivity in parameters."""

    @pytest.mark.asyncio
    async def test_control_entity_uppercase_entity_id(self, mock_mcp, mock_client, get_client):
        """Test control_entity with uppercase entity_id."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        # Home Assistant entity IDs are typically lowercase
        mock_client.get_state.return_value = {
            "entity_id": "LIGHT.LIVING_ROOM",
            "state": "on",
            "attributes": {},
        }

        result = await control_entity("LIGHT.LIVING_ROOM")

        assert isinstance(result, list)
        # Should handle case (HA typically uses lowercase)

    @pytest.mark.asyncio
    async def test_control_entity_mixed_case_entity_id(self, mock_mcp, mock_client, get_client):
        """Test control_entity with mixed case entity_id."""
        register_control_prompts(mock_mcp, get_client)
        control_entity = mock_mcp._prompts["control_entity"]

        mock_client.get_state.return_value = {
            "entity_id": "Light.Living_Room",
            "state": "on",
            "attributes": {},
        }

        result = await control_entity("Light.Living_Room")

        assert isinstance(result, list)
        # Should handle mixed case
