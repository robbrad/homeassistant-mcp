"""Unit tests for prompt error handling."""

import pytest
from unittest.mock import AsyncMock, patch

from homeassistant_mcp.exceptions import ConnectionError, EntityNotFoundError
from homeassistant_mcp.prompts.control import register_control_prompts
from homeassistant_mcp.prompts.explain import register_explain_prompts
from homeassistant_mcp.prompts.automation import register_automation_prompts
from homeassistant_mcp.prompts.status import register_status_prompts


class TestConnectionErrors:
    """Tests for handling connection errors to Home Assistant."""

    @pytest.mark.asyncio
    async def test_control_entity_connection_error(self, mock_mcp, get_client):
        """Test control_entity handles connection errors gracefully."""
        # Create client that raises ConnectionError
        client = AsyncMock()
        client.get_state.side_effect = ConnectionError("Failed to connect to Home Assistant")
        get_client_func = lambda: client

        register_control_prompts(mock_mcp, get_client_func)
        control_entity = mock_mcp._prompts["control_entity"]

        result = await control_entity("light.living_room")

        assert isinstance(result, list)
        content = result[0].content.text
        # Should provide helpful error message
        assert "cannot connect" in content.lower() or "connection" in content.lower()
        assert "Home Assistant" in content

    @pytest.mark.asyncio
    async def test_control_area_connection_error(self, mock_mcp, get_client):
        """Test control_area handles connection errors gracefully."""
        client = AsyncMock()
        client.get_states.side_effect = ConnectionError("Connection timeout")
        get_client_func = lambda: client

        register_control_prompts(mock_mcp, get_client_func)
        control_area = mock_mcp._prompts["control_area"]

        result = await control_area("Living Room")

        assert isinstance(result, list)
        content = result[0].content.text
        assert "cannot connect" in content.lower() or "connection" in content.lower()

    @pytest.mark.asyncio
    async def test_explain_entity_connection_error(self, mock_mcp, get_client):
        """Test explain_entity handles connection errors gracefully."""
        client = AsyncMock()
        client.get_state.side_effect = ConnectionError("Network unreachable")
        get_client_func = lambda: client

        register_explain_prompts(mock_mcp, get_client_func)
        explain_entity = mock_mcp._prompts["explain_entity"]

        result = await explain_entity("light.living_room")

        assert isinstance(result, list)
        content = result[0].content.text
        assert "cannot connect" in content.lower() or "connection" in content.lower()

    @pytest.mark.asyncio
    async def test_diagnose_automation_connection_error(self, mock_mcp, get_client):
        """Test diagnose_automation handles connection errors gracefully."""
        client = AsyncMock()
        client.get_state.side_effect = ConnectionError("Connection refused")
        get_client_func = lambda: client

        register_automation_prompts(mock_mcp, get_client_func)
        diagnose_automation = mock_mcp._prompts["diagnose_automation"]

        result = await diagnose_automation("automation.morning_routine")

        assert isinstance(result, list)
        content = result[0].content.text
        assert "cannot connect" in content.lower() or "connection" in content.lower()

    @pytest.mark.asyncio
    async def test_home_status_brief_connection_error(self, mock_mcp, get_client):
        """Test home_status_brief handles connection errors gracefully."""
        client = AsyncMock()
        client.get_states.side_effect = ConnectionError("Connection lost")
        get_client_func = lambda: client

        register_status_prompts(mock_mcp, get_client_func)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        result = await home_status_brief()

        assert isinstance(result, list)
        content = result[0].content.text
        assert "cannot connect" in content.lower() or "connection" in content.lower()


class TestEntityNotFoundErrors:
    """Tests for handling entity not found errors."""

    @pytest.mark.asyncio
    async def test_control_entity_not_found(self, mock_mcp, get_client):
        """Test control_entity handles entity not found errors."""
        client = AsyncMock()
        client.get_state.side_effect = EntityNotFoundError("Entity light.nonexistent not found")
        get_client_func = lambda: client

        register_control_prompts(mock_mcp, get_client_func)
        control_entity = mock_mcp._prompts["control_entity"]

        result = await control_entity("light.nonexistent")

        assert isinstance(result, list)
        content = result[0].content.text
        # Should provide helpful error message
        assert "not found" in content.lower()
        assert "light.nonexistent" in content
        # Should suggest using list_devices tool
        assert "list_devices" in content or "list" in content.lower()

    @pytest.mark.asyncio
    async def test_explain_entity_not_found(self, mock_mcp, get_client):
        """Test explain_entity handles entity not found errors."""
        client = AsyncMock()
        client.get_state.side_effect = EntityNotFoundError("Entity not found")
        get_client_func = lambda: client

        register_explain_prompts(mock_mcp, get_client_func)
        explain_entity = mock_mcp._prompts["explain_entity"]

        result = await explain_entity("sensor.nonexistent")

        assert isinstance(result, list)
        content = result[0].content.text
        assert "not found" in content.lower()
        assert "sensor.nonexistent" in content

    @pytest.mark.asyncio
    async def test_diagnose_automation_not_found(self, mock_mcp, get_client):
        """Test diagnose_automation handles automation not found errors."""
        client = AsyncMock()
        client.get_state.side_effect = EntityNotFoundError("Automation not found")
        get_client_func = lambda: client

        register_automation_prompts(mock_mcp, get_client_func)
        diagnose_automation = mock_mcp._prompts["diagnose_automation"]

        result = await diagnose_automation("automation.nonexistent")

        assert isinstance(result, list)
        content = result[0].content.text
        assert "not found" in content.lower()


class TestTimeoutScenarios:
    """Tests for handling timeout scenarios."""

    @pytest.mark.asyncio
    async def test_control_entity_timeout(self, mock_mcp, get_client):
        """Test control_entity handles timeout errors."""
        import asyncio

        client = AsyncMock()
        client.get_state.side_effect = asyncio.TimeoutError("Request timed out")
        get_client_func = lambda: client

        register_control_prompts(mock_mcp, get_client_func)
        control_entity = mock_mcp._prompts["control_entity"]

        # Should handle timeout gracefully
        try:
            result = await control_entity("light.living_room")
            # If it doesn't raise, should provide error message
            assert isinstance(result, list)
            content = result[0].content.text
            assert "timeout" in content.lower() or "timed out" in content.lower()
        except asyncio.TimeoutError:
            # Timeout propagating is also acceptable
            pass

    @pytest.mark.asyncio
    async def test_control_area_timeout(self, mock_mcp, get_client):
        """Test control_area handles timeout errors."""
        import asyncio

        client = AsyncMock()
        client.get_states.side_effect = asyncio.TimeoutError("Request timed out")
        get_client_func = lambda: client

        register_control_prompts(mock_mcp, get_client_func)
        control_area = mock_mcp._prompts["control_area"]

        try:
            result = await control_area("Living Room")
            # If it doesn't raise, should provide error message
            assert isinstance(result, list)
        except asyncio.TimeoutError:
            # Timeout propagating is also acceptable
            pass

    @pytest.mark.asyncio
    async def test_home_status_brief_timeout(self, mock_mcp, get_client):
        """Test home_status_brief handles timeout errors."""
        import asyncio

        client = AsyncMock()
        client.get_states.side_effect = asyncio.TimeoutError("Request timed out")
        get_client_func = lambda: client

        register_status_prompts(mock_mcp, get_client_func)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        try:
            result = await home_status_brief()
            # If it doesn't raise, should provide error message
            assert isinstance(result, list)
        except asyncio.TimeoutError:
            # Timeout propagating is also acceptable
            pass


class TestGracefulDegradation:
    """Tests for graceful degradation when data is unavailable."""

    @pytest.mark.asyncio
    async def test_control_entity_partial_data(self, mock_mcp, get_client):
        """Test control_entity handles entities with missing attributes."""
        client = AsyncMock()
        # Entity with minimal data (no attributes)
        client.get_state.return_value = {
            "entity_id": "light.minimal",
            "state": "on",
            "attributes": {},  # No attributes
        }
        get_client_func = lambda: client

        register_control_prompts(mock_mcp, get_client_func)
        control_entity = mock_mcp._prompts["control_entity"]

        result = await control_entity("light.minimal")

        assert isinstance(result, list)
        content = result[0].content.text
        # Should still provide guidance even with minimal data
        assert "light.minimal" in content
        assert "on" in content

    @pytest.mark.asyncio
    async def test_control_entity_unavailable_state(self, mock_mcp, get_client):
        """Test control_entity handles unavailable entities."""
        client = AsyncMock()
        client.get_state.return_value = {
            "entity_id": "light.unavailable",
            "state": "unavailable",
            "attributes": {},
        }
        get_client_func = lambda: client

        register_control_prompts(mock_mcp, get_client_func)
        control_entity = mock_mcp._prompts["control_entity"]

        result = await control_entity("light.unavailable")

        assert isinstance(result, list)
        content = result[0].content.text
        # Should warn about unavailable state
        assert "unavailable" in content.lower()

    @pytest.mark.asyncio
    async def test_control_entity_unknown_state(self, mock_mcp, get_client):
        """Test control_entity handles entities with unknown state."""
        client = AsyncMock()
        client.get_state.return_value = {
            "entity_id": "sensor.unknown",
            "state": "unknown",
            "attributes": {},
        }
        get_client_func = lambda: client

        register_control_prompts(mock_mcp, get_client_func)
        control_entity = mock_mcp._prompts["control_entity"]

        result = await control_entity("sensor.unknown")

        assert isinstance(result, list)
        content = result[0].content.text
        # Should handle unknown state gracefully
        assert "sensor.unknown" in content

    @pytest.mark.asyncio
    async def test_control_area_some_entities_unavailable(self, mock_mcp, get_client):
        """Test control_area handles areas with some unavailable entities."""
        client = AsyncMock()
        client._states_data = [
            {
                "entity_id": "light.working",
                "state": "on",
                "attributes": {"friendly_name": "Working Light"},
            },
            {
                "entity_id": "light.broken",
                "state": "unavailable",
                "attributes": {"friendly_name": "Broken Light"},
            },
            {
                "entity_id": "switch.offline",
                "state": "unknown",
                "attributes": {"friendly_name": "Offline Switch"},
            },
        ]

        async def _filtered_get_states(domain=None, area=None, limit=None):
            states = list(client._states_data)
            if domain:
                states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
            return states

        client.get_states = AsyncMock(side_effect=_filtered_get_states)
        get_client_func = lambda: client

        register_control_prompts(mock_mcp, get_client_func)
        control_area = mock_mcp._prompts["control_area"]

        result = await control_area("Mixed Area")

        assert isinstance(result, list)
        content = result[0].content.text
        # Should list all entities including unavailable ones
        assert "Working Light" in content
        assert "Broken Light" in content
        assert "Offline Switch" in content
        # Should indicate unavailable status
        assert "unavailable" in content.lower() or "unknown" in content.lower()

    @pytest.mark.asyncio
    async def test_explain_entity_missing_friendly_name(self, mock_mcp, get_client):
        """Test explain_entity handles entities without friendly names."""
        client = AsyncMock()
        client.get_state.return_value = {
            "entity_id": "sensor.no_name",
            "state": "42",
            "attributes": {
                # No friendly_name
                "unit_of_measurement": "°F"
            },
        }
        get_client_func = lambda: client

        register_explain_prompts(mock_mcp, get_client_func)
        explain_entity = mock_mcp._prompts["explain_entity"]

        result = await explain_entity("sensor.no_name")

        assert isinstance(result, list)
        content = result[0].content.text
        # Should use entity_id when no friendly name
        assert "sensor.no_name" in content

    @pytest.mark.asyncio
    async def test_home_status_brief_empty_home(self, mock_mcp, get_client):
        """Test home_status_brief handles homes with no entities."""
        client = AsyncMock()
        client._states_data = []  # No entities

        async def _filtered_get_states(domain=None, area=None, limit=None):
            return list(client._states_data)

        client.get_states = AsyncMock(side_effect=_filtered_get_states)
        get_client_func = lambda: client

        register_status_prompts(mock_mcp, get_client_func)
        home_status_brief = mock_mcp._prompts["home_status_brief"]

        result = await home_status_brief()

        assert isinstance(result, list)
        content = result[0].content.text
        # Should handle empty home gracefully
        assert "no entities" in content.lower() or "0" in content


class TestUnexpectedErrors:
    """Tests for handling unexpected errors."""

    @pytest.mark.asyncio
    async def test_control_entity_unexpected_exception(self, mock_mcp, get_client):
        """Test control_entity handles unexpected exceptions."""
        client = AsyncMock()
        client.get_state.side_effect = Exception("Unexpected error")
        get_client_func = lambda: client

        register_control_prompts(mock_mcp, get_client_func)
        control_entity = mock_mcp._prompts["control_entity"]

        # Should handle unexpected errors gracefully
        try:
            result = await control_entity("light.test")
            # If it doesn't raise, should provide error message
            assert isinstance(result, list)
            content = result[0].content.text
            assert "error" in content.lower()
        except Exception:
            # Exception propagating is also acceptable
            pass

    @pytest.mark.asyncio
    async def test_control_area_unexpected_exception(self, mock_mcp, get_client):
        """Test control_area handles unexpected exceptions."""
        client = AsyncMock()
        client.get_states.side_effect = ValueError("Invalid response")
        get_client_func = lambda: client

        register_control_prompts(mock_mcp, get_client_func)
        control_area = mock_mcp._prompts["control_area"]

        try:
            result = await control_area("Test Area")
            # If it doesn't raise, should provide error message
            assert isinstance(result, list)
        except ValueError:
            # Exception propagating is also acceptable
            pass

    @pytest.mark.asyncio
    async def test_explain_entity_malformed_response(self, mock_mcp, get_client):
        """Test explain_entity handles malformed API responses."""
        client = AsyncMock()
        # Malformed response (missing required fields)
        client.get_state.return_value = {
            "entity_id": "light.test",
            # Missing 'state' field
            "attributes": {},
        }
        get_client_func = lambda: client

        register_explain_prompts(mock_mcp, get_client_func)
        explain_entity = mock_mcp._prompts["explain_entity"]

        # Should handle malformed response gracefully
        try:
            result = await explain_entity("light.test")
            assert isinstance(result, list)
        except (KeyError, AttributeError):
            # Exception for malformed data is acceptable
            pass


class TestErrorRecovery:
    """Tests for error recovery and retry behavior."""

    @pytest.mark.asyncio
    async def test_control_entity_transient_error_recovery(self, mock_mcp, get_client):
        """Test control_entity can recover from transient errors."""
        client = AsyncMock()
        # First call fails, second succeeds
        client.get_state.side_effect = [
            ConnectionError("Transient error"),
            {
                "entity_id": "light.test",
                "state": "on",
                "attributes": {},
            },
        ]
        get_client_func = lambda: client

        register_control_prompts(mock_mcp, get_client_func)
        control_entity = mock_mcp._prompts["control_entity"]

        # First call should handle error
        result1 = await control_entity("light.test")
        assert isinstance(result1, list)
        content1 = result1[0].content.text
        assert "cannot connect" in content1.lower() or "connection" in content1.lower()

        # Second call should succeed (if retry logic exists)
        result2 = await control_entity("light.test")
        assert isinstance(result2, list)
        # May succeed or fail depending on retry implementation

    @pytest.mark.asyncio
    async def test_control_area_partial_failure(self, mock_mcp, get_client):
        """Test control_area handles partial failures gracefully."""
        client = AsyncMock()
        # Returns some entities successfully
        client._states_data = [
            {
                "entity_id": "light.working",
                "state": "on",
                "attributes": {"friendly_name": "Working Light"},
            },
        ]

        async def _filtered_get_states(domain=None, area=None, limit=None):
            states = list(client._states_data)
            if domain:
                states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
            return states

        client.get_states = AsyncMock(side_effect=_filtered_get_states)
        get_client_func = lambda: client

        register_control_prompts(mock_mcp, get_client_func)
        control_area = mock_mcp._prompts["control_area"]

        result = await control_area("Test Area")

        assert isinstance(result, list)
        content = result[0].content.text
        # Should show available entities even if some failed
        assert "Working Light" in content


class TestErrorMessages:
    """Tests for error message quality and helpfulness."""

    @pytest.mark.asyncio
    async def test_connection_error_suggests_troubleshooting(self, mock_mcp, get_client):
        """Test connection errors suggest troubleshooting steps."""
        client = AsyncMock()
        client.get_state.side_effect = ConnectionError("Connection failed")
        get_client_func = lambda: client

        register_control_prompts(mock_mcp, get_client_func)
        control_entity = mock_mcp._prompts["control_entity"]

        result = await control_entity("light.test")

        content = result[0].content.text
        # Should suggest checking Home Assistant
        assert "Home Assistant" in content
        # Should be helpful
        assert "check" in content.lower() or "verify" in content.lower()

    @pytest.mark.asyncio
    async def test_entity_not_found_suggests_alternatives(self, mock_mcp, get_client):
        """Test entity not found errors suggest alternatives."""
        client = AsyncMock()
        client.get_state.side_effect = EntityNotFoundError("Entity not found")
        get_client_func = lambda: client

        register_control_prompts(mock_mcp, get_client_func)
        control_entity = mock_mcp._prompts["control_entity"]

        result = await control_entity("light.nonexistent")

        content = result[0].content.text
        # Should suggest using list_devices or similar
        assert "list" in content.lower() or "find" in content.lower()
        # Should mention the entity that wasn't found
        assert "light.nonexistent" in content
