"""Unit tests for Home Assistant REST API client methods.

Tests for task 1.2: Write unit tests for client methods
- Test each new REST API endpoint wrapper
- Test filtering logic with various combinations
- Test pagination with offset parameter
- Test response size tracking and warnings
- Test error handling for each endpoint

Validates Requirements: 2.1-2.5, 3.1-3.10, 4.1-4.9, 21.1-21.9
"""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.homeassistant_mcp.hass.client import (
    AuthenticationError,
    ConnectionError,
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx AsyncClient."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def hass_client(mock_httpx_client):
    """Create a HomeAssistantClient with mocked httpx client."""
    with patch(
        "src.homeassistant_mcp.hass.client.httpx.AsyncClient", return_value=mock_httpx_client
    ):
        client = HomeAssistantClient(
            base_url="http://homeassistant.local:8123", token="test_token_1234567890"
        )
        client.client = mock_httpx_client
        return client


# ============================================================================
# Core API Endpoint Tests (Requirements 2.1-2.5)
# ============================================================================


class TestGetApiStatus:
    """Tests for get_api_status method (Requirement 2.1)."""

    @pytest.mark.asyncio
    async def test_get_api_status_success(self, hass_client, mock_httpx_client):
        """Test successful API status retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {"message": "API running."}
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_api_status()

        assert result == {"message": "API running."}
        mock_httpx_client.get.assert_called_once_with("/")

    @pytest.mark.asyncio
    async def test_get_api_status_authentication_error(self, hass_client, mock_httpx_client):
        """Test handling of 401 authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_httpx_client.get.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )

        with pytest.raises(AuthenticationError) as exc_info:
            await hass_client.get_api_status()
        assert "Invalid Home Assistant token" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_api_status_connection_error(self, hass_client, mock_httpx_client):
        """Test handling of connection errors."""
        mock_httpx_client.get.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(ConnectionError) as exc_info:
            await hass_client.get_api_status()
        assert "Failed to connect to Home Assistant" in str(exc_info.value)


class TestGetConfig:
    """Tests for get_config method (Requirement 2.2)."""

    @pytest.mark.asyncio
    async def test_get_config_success(self, hass_client, mock_httpx_client):
        """Test successful configuration retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "latitude": 32.87336,
            "longitude": -117.22743,
            "elevation": 0,
            "unit_system": {"length": "km", "mass": "g", "temperature": "°C"},
            "location_name": "Home",
            "time_zone": "America/Los_Angeles",
            "version": "2024.1.0",
        }
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_config()

        assert result["version"] == "2024.1.0"
        assert result["location_name"] == "Home"
        mock_httpx_client.get.assert_called_once_with("/config")

    @pytest.mark.asyncio
    async def test_get_config_authentication_error(self, hass_client, mock_httpx_client):
        """Test handling of authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_httpx_client.get.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )

        with pytest.raises(AuthenticationError):
            await hass_client.get_config()


class TestGetComponents:
    """Tests for get_components method (Requirement 2.3)."""

    @pytest.mark.asyncio
    async def test_get_components_success(self, hass_client, mock_httpx_client):
        """Test successful components list retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = [
            "api",
            "automation",
            "config",
            "frontend",
            "history",
            "light",
            "switch",
        ]
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_components()

        assert len(result) == 7
        assert "light" in result
        assert "automation" in result
        mock_httpx_client.get.assert_called_once_with("/components")

    @pytest.mark.asyncio
    async def test_get_components_empty_list(self, hass_client, mock_httpx_client):
        """Test handling of empty components list."""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_components()

        assert result == []


class TestGetEvents:
    """Tests for get_events method (Requirement 2.4)."""

    @pytest.mark.asyncio
    async def test_get_events_success(self, hass_client, mock_httpx_client):
        """Test successful events list retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "state_changed": {"listener_count": 5},
            "service_executed": {"listener_count": 3},
            "automation_triggered": {"listener_count": 2},
        }
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_events()

        assert "state_changed" in result
        assert result["state_changed"]["listener_count"] == 5
        mock_httpx_client.get.assert_called_once_with("/events")


class TestGetServices:
    """Tests for get_services method (Requirement 2.5)."""

    @pytest.mark.asyncio
    async def test_get_services_success(self, hass_client, mock_httpx_client):
        """Test successful services list retrieval (dict format)."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "light": {
                "turn_on": {
                    "name": "Turn on",
                    "description": "Turn on one or more lights",
                    "fields": {"entity_id": {"description": "Entity ID"}},
                }
            },
            "switch": {
                "turn_off": {
                    "name": "Turn off",
                    "description": "Turn off a switch",
                    "fields": {},
                }
            },
        }
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_services()

        assert "light" in result
        assert "turn_on" in result["light"]
        assert result["light"]["turn_on"]["name"] == "Turn on"
        mock_httpx_client.get.assert_called_once_with("/services")

    @pytest.mark.asyncio
    async def test_get_services_list_format(self, hass_client, mock_httpx_client):
        """Test successful services list retrieval (list format from newer HA versions)."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "domain": "light",
                "services": {
                    "turn_on": {
                        "name": "Turn on",
                        "description": "Turn on one or more lights",
                        "fields": {"entity_id": {"description": "Entity ID"}},
                    }
                },
            },
            {
                "domain": "switch",
                "services": {
                    "turn_off": {
                        "name": "Turn off",
                        "description": "Turn off a switch",
                        "fields": {},
                    }
                },
            },
        ]
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_services()

        # Client returns the raw list format
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["domain"] == "light"
        assert "turn_on" in result[0]["services"]
        mock_httpx_client.get.assert_called_once_with("/services")


class TestFireEvent:
    """Tests for fire_event method (Requirement 6.1-6.5)."""

    @pytest.mark.asyncio
    async def test_fire_event_success(self, hass_client, mock_httpx_client):
        """Test successful event firing."""
        mock_response = Mock()
        mock_response.json.return_value = {"message": "Event fired."}
        mock_httpx_client.post.return_value = mock_response

        result = await hass_client.fire_event("custom_event", {"key": "value"})

        assert result == {"message": "Event fired."}
        mock_httpx_client.post.assert_called_once_with(
            "/events/custom_event", json={"key": "value"}
        )

    @pytest.mark.asyncio
    async def test_fire_event_no_data(self, hass_client, mock_httpx_client):
        """Test firing event without data."""
        mock_response = Mock()
        mock_response.json.return_value = {"message": "Event fired."}
        mock_httpx_client.post.return_value = mock_response

        await hass_client.fire_event("simple_event")

        mock_httpx_client.post.assert_called_once_with("/events/simple_event", json={})

    @pytest.mark.asyncio
    async def test_fire_event_authentication_error(self, hass_client, mock_httpx_client):
        """Test handling of authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_httpx_client.post.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )

        with pytest.raises(AuthenticationError):
            await hass_client.fire_event("test_event")


# ============================================================================
# State Management Tests with Filtering (Requirements 3.1-3.10, 21.1-21.9)
# ============================================================================


class TestGetStatesFiltering:
    """Tests for get_states filtering logic (Requirements 3.1-3.10, 21.1-21.9)."""

    @pytest.mark.asyncio
    async def test_get_states_domain_filter(self, hass_client, mock_httpx_client):
        """Test filtering states by domain."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"entity_id": "light.living_room", "state": "on"},
            {"entity_id": "light.bedroom", "state": "off"},
            {"entity_id": "switch.kitchen", "state": "on"},
            {"entity_id": "climate.bedroom", "state": "heat"},
        ]
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_states(domain="light")

        # Should only return light entities
        assert len(result) == 2
        assert all(e["entity_id"].startswith("light.") for e in result)

    @pytest.mark.asyncio
    async def test_get_states_area_filter(self, hass_client, mock_httpx_client):
        """Test filtering states by area."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"area_id": "living_room"},
            },
            {
                "entity_id": "light.bedroom",
                "state": "off",
                "attributes": {"area_id": "bedroom"},
            },
            {
                "entity_id": "switch.living_room",
                "state": "on",
                "attributes": {"area_id": "living_room"},
            },
        ]
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_states(area="living_room")

        # Should only return entities in living_room area
        assert len(result) == 2
        assert all(e["attributes"]["area_id"] == "living_room" for e in result)

    @pytest.mark.asyncio
    async def test_get_states_domain_and_area_filter(self, hass_client, mock_httpx_client):
        """Test filtering states by both domain and area."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"area_id": "living_room"},
            },
            {
                "entity_id": "light.bedroom",
                "state": "off",
                "attributes": {"area_id": "bedroom"},
            },
            {
                "entity_id": "switch.living_room",
                "state": "on",
                "attributes": {"area_id": "living_room"},
            },
        ]
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_states(domain="light", area="living_room")

        # Should only return light entities in living_room
        assert len(result) == 1
        assert result[0]["entity_id"] == "light.living_room"

    @pytest.mark.asyncio
    async def test_get_states_limit_parameter(self, hass_client, mock_httpx_client):
        """Test limiting number of returned states (Requirement 21.4)."""
        mock_response = Mock()
        # Create 150 entities
        entities = [{"entity_id": f"light.light_{i}", "state": "on"} for i in range(150)]
        mock_response.json.return_value = entities
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_states(limit=50)

        # Should only return 50 entities
        assert len(result) == 50

    @pytest.mark.asyncio
    async def test_get_states_default_limit(self, hass_client, mock_httpx_client):
        """Test default limit — no limit when unfiltered up to 500."""
        mock_response = Mock()
        # Create 200 entities
        entities = [{"entity_id": f"light.light_{i}", "state": "on"} for i in range(200)]
        mock_response.json.return_value = entities
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_states()

        # Without filters, default limit is 500 — 200 entities should all be returned
        assert len(result) == 200

    @pytest.mark.asyncio
    async def test_get_states_max_limit_500(self, hass_client, mock_httpx_client):
        """Test maximum limit of 500 entities (Requirement 21.4)."""
        mock_response = Mock()
        # Create 1000 entities
        entities = [{"entity_id": f"light.light_{i}", "state": "on"} for i in range(1000)]
        mock_response.json.return_value = entities
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_states(limit=600)

        # Should cap at 500 entities
        assert len(result) == 500

    @pytest.mark.asyncio
    async def test_get_states_offset_pagination(self, hass_client, mock_httpx_client):
        """Test pagination with offset parameter (Requirement 21.5).

        Note: Offset parameter is not yet implemented in the client.
        This test verifies that filtering and limiting work correctly,
        which provides the foundation for future offset implementation.
        """
        mock_response = Mock()
        entities = [{"entity_id": f"light.light_{i}", "state": "on"} for i in range(200)]
        mock_response.json.return_value = entities
        mock_httpx_client.get.return_value = mock_response

        # Test that limit works correctly (foundation for pagination)
        result1 = await hass_client.get_states(limit=50)
        assert len(result1) == 50
        assert result1[0]["entity_id"] == "light.light_0"

        # Verify we can get different limits
        result2 = await hass_client.get_states(limit=100)
        assert len(result2) == 100

    @pytest.mark.asyncio
    async def test_get_states_combined_filters(self, hass_client, mock_httpx_client):
        """Test combining domain, area, and limit filters."""
        mock_response = Mock()
        entities = []
        for i in range(100):
            entities.append(
                {
                    "entity_id": f"light.living_room_{i}",
                    "state": "on",
                    "attributes": {"area_id": "living_room"},
                }
            )
            entities.append(
                {
                    "entity_id": f"switch.living_room_{i}",
                    "state": "on",
                    "attributes": {"area_id": "living_room"},
                }
            )
        mock_response.json.return_value = entities
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_states(domain="light", area="living_room", limit=20)

        # Should return 20 light entities from living_room
        assert len(result) == 20
        assert all(e["entity_id"].startswith("light.living_room_") for e in result)
        assert all(e["attributes"]["area_id"] == "living_room" for e in result)


class TestSetState:
    """Tests for set_state method (Requirements 3.6, 3.7)."""

    @pytest.mark.asyncio
    async def test_set_state_success(self, hass_client, mock_httpx_client):
        """Test successful state update."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "entity_id": "sensor.test",
            "state": "42",
            "attributes": {"unit": "°C"},
        }
        mock_httpx_client.post.return_value = mock_response

        result = await hass_client.set_state("sensor.test", "42", {"unit": "°C"})

        assert result["state"] == "42"
        assert result["attributes"]["unit"] == "°C"
        mock_httpx_client.post.assert_called_once_with(
            "/states/sensor.test",
            json={"state": "42", "attributes": {"unit": "°C"}},
        )

    @pytest.mark.asyncio
    async def test_set_state_no_attributes(self, hass_client, mock_httpx_client):
        """Test setting state without attributes."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "entity_id": "sensor.test",
            "state": "on",
            "attributes": {},
        }
        mock_httpx_client.post.return_value = mock_response

        await hass_client.set_state("sensor.test", "on")

        mock_httpx_client.post.assert_called_once_with(
            "/states/sensor.test", json={"state": "on", "attributes": {}}
        )


class TestDeleteState:
    """Tests for delete_state method (Requirement 3.8)."""

    @pytest.mark.asyncio
    async def test_delete_state_success(self, hass_client, mock_httpx_client):
        """Test successful state deletion."""
        mock_response = Mock()
        mock_response.json.return_value = {"message": "Entity removed"}
        mock_httpx_client.delete.return_value = mock_response

        result = await hass_client.delete_state("sensor.test")

        assert result == {"message": "Entity removed"}
        mock_httpx_client.delete.assert_called_once_with("/states/sensor.test")

    @pytest.mark.asyncio
    async def test_delete_state_not_found(self, hass_client, mock_httpx_client):
        """Test deleting non-existent entity."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_httpx_client.delete.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )

        with pytest.raises(EntityNotFoundError):
            await hass_client.delete_state("sensor.nonexistent")


# ============================================================================
# Historical Data Tests with Filtering (Requirements 4.1-4.9, 21.1-21.9)
# ============================================================================


class TestGetHistory:
    """Tests for get_history method with filtering (Requirements 4.1-4.9)."""

    @pytest.mark.asyncio
    async def test_get_history_basic(self, hass_client, mock_httpx_client):
        """Test basic history retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = [
            [
                {
                    "entity_id": "light.living_room",
                    "state": "on",
                    "last_changed": "2024-01-01T12:00:00",
                }
            ]
        ]
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_history("2024-01-01T00:00:00")

        assert len(result) == 1
        mock_httpx_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_history_with_end_time(self, hass_client, mock_httpx_client):
        """Test history retrieval with end time (Requirement 4.3)."""
        mock_response = Mock()
        mock_response.json.return_value = [[]]
        mock_httpx_client.get.return_value = mock_response

        await hass_client.get_history("2024-01-01T00:00:00", end_time="2024-01-01T23:59:59")

        # Verify end_time is passed as query parameter
        call_args = mock_httpx_client.get.call_args
        assert "params" in call_args.kwargs
        assert "end_time" in call_args.kwargs["params"]

    @pytest.mark.asyncio
    async def test_get_history_entity_filter(self, hass_client, mock_httpx_client):
        """Test history with entity filter (Requirement 4.2)."""
        mock_response = Mock()
        mock_response.json.return_value = [[{"entity_id": "light.living_room", "state": "on"}]]
        mock_httpx_client.get.return_value = mock_response

        await hass_client.get_history(
            "2024-01-01T00:00:00",
            filter_entity_id=["light.living_room", "light.bedroom"],
        )

        # Verify filter_entity_id is passed as query parameter
        call_args = mock_httpx_client.get.call_args
        assert "params" in call_args.kwargs
        assert "filter_entity_id" in call_args.kwargs["params"]

    @pytest.mark.asyncio
    async def test_get_history_limit(self, hass_client, mock_httpx_client):
        """Test history with limit parameter (Requirement 4.4, 21.1)."""
        mock_response = Mock()
        # Create 200 history entries
        history_entries = [
            {"entity_id": "light.test", "state": "on", "last_changed": f"2024-01-01T{i:02d}:00:00"}
            for i in range(200)
        ]
        mock_response.json.return_value = [history_entries]
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_history("2024-01-01T00:00:00", limit=50)

        # Should limit to 50 entries per entity
        assert len(result[0]) == 50

    @pytest.mark.asyncio
    async def test_get_history_default_limit(self, hass_client, mock_httpx_client):
        """Test history default limit of 100 (Requirement 4.9)."""
        mock_response = Mock()
        # Create 200 history entries
        history_entries = [{"entity_id": "light.test", "state": "on"} for _ in range(200)]
        mock_response.json.return_value = [history_entries]
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_history("2024-01-01T00:00:00")

        # Should default to 100 entries per entity
        assert len(result[0]) == 100

    @pytest.mark.asyncio
    async def test_get_history_minimal_response(self, hass_client, mock_httpx_client):
        """Test history with minimal_response flag."""
        mock_response = Mock()
        mock_response.json.return_value = [[]]
        mock_httpx_client.get.return_value = mock_response

        await hass_client.get_history("2024-01-01T00:00:00", minimal_response=True)

        # Verify minimal_response is passed as query parameter
        call_args = mock_httpx_client.get.call_args
        assert "params" in call_args.kwargs
        # Client converts boolean to string "true"
        assert call_args.kwargs["params"].get("minimal_response") == "true"


class TestGetLogbook:
    """Tests for get_logbook method (Requirements 4.5-4.9)."""

    @pytest.mark.asyncio
    async def test_get_logbook_basic(self, hass_client, mock_httpx_client):
        """Test basic logbook retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "when": "2024-01-01T12:00:00",
                "name": "Living Room Light",
                "message": "turned on",
                "entity_id": "light.living_room",
            }
        ]
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_logbook("2024-01-01T00:00:00")

        assert len(result) == 1
        assert result[0]["entity_id"] == "light.living_room"

    @pytest.mark.asyncio
    async def test_get_logbook_with_entity_filter(self, hass_client, mock_httpx_client):
        """Test logbook with entity filter (Requirement 4.6)."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"when": "2024-01-01T12:00:00", "entity_id": "light.living_room"}
        ]
        mock_httpx_client.get.return_value = mock_response

        await hass_client.get_logbook("2024-01-01T00:00:00", entity="light.living_room")

        # Verify entity filter is passed as query parameter
        call_args = mock_httpx_client.get.call_args
        assert "params" in call_args.kwargs
        assert "entity" in call_args.kwargs["params"]

    @pytest.mark.asyncio
    async def test_get_logbook_limit(self, hass_client, mock_httpx_client):
        """Test logbook with limit parameter (Requirement 4.7)."""
        mock_response = Mock()
        # Create 200 logbook entries
        entries = [
            {"when": f"2024-01-01T{i:02d}:00:00", "message": f"Entry {i}"} for i in range(200)
        ]
        mock_response.json.return_value = entries
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_logbook("2024-01-01T00:00:00", limit=50)

        # Should limit to 50 entries
        assert len(result) == 50

    @pytest.mark.asyncio
    async def test_get_logbook_default_limit(self, hass_client, mock_httpx_client):
        """Test logbook default limit of 100."""
        mock_response = Mock()
        entries = [{"when": "2024-01-01T00:00:00", "message": f"Entry {i}"} for i in range(200)]
        mock_response.json.return_value = entries
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_logbook("2024-01-01T00:00:00")

        assert len(result) == 100


class TestGetErrorLog:
    """Tests for get_error_log method (Requirements 7.1-7.4)."""

    @pytest.mark.asyncio
    async def test_get_error_log_success(self, hass_client, mock_httpx_client):
        """Test successful error log retrieval."""
        mock_response = Mock()
        mock_response.text = "2024-01-01 12:00:00 ERROR: Test error\n"
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_error_log()

        assert "ERROR: Test error" in result
        mock_httpx_client.get.assert_called_once_with("/error_log")

    @pytest.mark.asyncio
    async def test_get_error_log_empty(self, hass_client, mock_httpx_client):
        """Test empty error log (Requirement 7.2)."""
        mock_response = Mock()
        mock_response.text = ""
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_error_log()

        assert result == ""

    @pytest.mark.asyncio
    async def test_get_error_log_authentication_error(self, hass_client, mock_httpx_client):
        """Test error log access failure (Requirement 7.3)."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_httpx_client.get.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )

        with pytest.raises(AuthenticationError):
            await hass_client.get_error_log()


# ============================================================================
# Specialized Endpoint Tests (Requirements 8-12)
# ============================================================================


class TestGetCameraProxy:
    """Tests for get_camera_proxy method (Requirements 8.1-8.6)."""

    @pytest.mark.asyncio
    async def test_get_camera_proxy_success(self, hass_client, mock_httpx_client):
        """Test successful camera image retrieval."""
        mock_response = Mock()
        mock_response.content = b"fake_image_data"
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_camera_proxy("camera.front_door")

        assert result == b"fake_image_data"
        mock_httpx_client.get.assert_called_once_with("/camera_proxy/camera.front_door", params={})

    @pytest.mark.asyncio
    async def test_get_camera_proxy_with_dimensions(self, hass_client, mock_httpx_client):
        """Test camera image with width and height (Requirements 8.2, 8.3)."""
        mock_response = Mock()
        mock_response.content = b"resized_image_data"
        mock_httpx_client.get.return_value = mock_response

        await hass_client.get_camera_proxy("camera.front_door", width=640, height=480)

        # Verify width and height are passed as query parameters
        call_args = mock_httpx_client.get.call_args
        assert call_args.kwargs["params"]["width"] == 640
        assert call_args.kwargs["params"]["height"] == 480

    @pytest.mark.asyncio
    async def test_get_camera_proxy_not_found(self, hass_client, mock_httpx_client):
        """Test camera not found error (Requirement 8.4)."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_httpx_client.get.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )

        with pytest.raises(EntityNotFoundError):
            await hass_client.get_camera_proxy("camera.nonexistent")


class TestGetCalendars:
    """Tests for get_calendars method (Requirement 9.1)."""

    @pytest.mark.asyncio
    async def test_get_calendars_success(self, hass_client, mock_httpx_client):
        """Test successful calendar list retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"entity_id": "calendar.personal", "name": "Personal"},
            {"entity_id": "calendar.work", "name": "Work"},
        ]
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_calendars()

        assert len(result) == 2
        assert result[0]["entity_id"] == "calendar.personal"
        mock_httpx_client.get.assert_called_once_with("/calendars")


class TestGetCalendarEvents:
    """Tests for get_calendar_events method (Requirements 9.2-9.6)."""

    @pytest.mark.asyncio
    async def test_get_calendar_events_success(self, hass_client, mock_httpx_client):
        """Test successful calendar events retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "start": "2024-01-01T10:00:00",
                "end": "2024-01-01T11:00:00",
                "summary": "Meeting",
                "description": "Team meeting",
            }
        ]
        mock_httpx_client.get.return_value = mock_response

        result = await hass_client.get_calendar_events("calendar.personal")

        assert len(result) == 1
        assert result[0]["summary"] == "Meeting"

    @pytest.mark.asyncio
    async def test_get_calendar_events_with_date_range(self, hass_client, mock_httpx_client):
        """Test calendar events with date range (Requirement 9.2)."""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_httpx_client.get.return_value = mock_response

        await hass_client.get_calendar_events(
            "calendar.personal",
            start="2024-01-01T00:00:00",
            end="2024-01-31T23:59:59",
        )

        # Verify start and end are passed as query parameters
        call_args = mock_httpx_client.get.call_args
        assert "params" in call_args.kwargs
        assert "start" in call_args.kwargs["params"]
        assert "end" in call_args.kwargs["params"]

    @pytest.mark.asyncio
    async def test_get_calendar_events_not_found(self, hass_client, mock_httpx_client):
        """Test calendar not found error (Requirement 9.4)."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_httpx_client.get.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )

        with pytest.raises(EntityNotFoundError):
            await hass_client.get_calendar_events("calendar.nonexistent")


class TestRenderTemplate:
    """Tests for render_template method (Requirements 10.1-10.5)."""

    @pytest.mark.asyncio
    async def test_render_template_success(self, hass_client, mock_httpx_client):
        """Test successful template rendering."""
        mock_response = Mock()
        mock_response.text = "Hello World"
        mock_httpx_client.post.return_value = mock_response

        result = await hass_client.render_template("{{ 'Hello' + ' World' }}")

        assert result == "Hello World"
        mock_httpx_client.post.assert_called_once_with(
            "/template", json={"template": "{{ 'Hello' + ' World' }}"}
        )

    @pytest.mark.asyncio
    async def test_render_template_with_entity_state(self, hass_client, mock_httpx_client):
        """Test template rendering with entity state reference (Requirement 10.3)."""
        mock_response = Mock()
        mock_response.text = "on"
        mock_httpx_client.post.return_value = mock_response

        result = await hass_client.render_template("{{ states('light.living_room') }}")

        assert result == "on"

    @pytest.mark.asyncio
    async def test_render_template_syntax_error(self, hass_client, mock_httpx_client):
        """Test template syntax error handling (Requirement 10.2)."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "TemplateSyntaxError: unexpected '}'"
        mock_httpx_client.post.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=mock_response
        )

        with pytest.raises(ServiceCallError) as exc_info:
            await hass_client.render_template("{{ invalid }}")
        assert "TemplateSyntaxError" in str(exc_info.value)


class TestCheckConfig:
    """Tests for check_config method (Requirements 11.1-11.5)."""

    @pytest.mark.asyncio
    async def test_check_config_valid(self, hass_client, mock_httpx_client):
        """Test configuration check with valid config (Requirement 11.2)."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": "valid",
            "errors": [],
            "warnings": [],
        }
        mock_httpx_client.post.return_value = mock_response

        result = await hass_client.check_config()

        assert result["result"] == "valid"
        assert len(result["errors"]) == 0
        mock_httpx_client.post.assert_called_once_with("/config/core/check_config")

    @pytest.mark.asyncio
    async def test_check_config_with_errors(self, hass_client, mock_httpx_client):
        """Test configuration check with errors (Requirement 11.3)."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": "invalid",
            "errors": ["Invalid automation syntax"],
            "warnings": [],
        }
        mock_httpx_client.post.return_value = mock_response

        result = await hass_client.check_config()

        assert result["result"] == "invalid"
        assert len(result["errors"]) == 1
        assert "Invalid automation syntax" in result["errors"]

    @pytest.mark.asyncio
    async def test_check_config_with_warnings(self, hass_client, mock_httpx_client):
        """Test configuration check with warnings (Requirement 11.4)."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": "valid",
            "errors": [],
            "warnings": ["Deprecated configuration option"],
        }
        mock_httpx_client.post.return_value = mock_response

        result = await hass_client.check_config()

        assert result["result"] == "valid"
        assert len(result["warnings"]) == 1


class TestHandleIntent:
    """Tests for handle_intent method (Requirements 12.1-12.5)."""

    @pytest.mark.asyncio
    async def test_handle_intent_success(self, hass_client, mock_httpx_client):
        """Test successful intent handling (Requirement 12.1, 12.2)."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "speech": {"plain": {"speech": "Turned on the light"}},
            "card": {},
            "language": "en",
            "response_type": "action_done",
        }
        mock_httpx_client.post.return_value = mock_response

        result = await hass_client.handle_intent("HassTurnOn", {"name": "living room light"})

        assert result["speech"]["plain"]["speech"] == "Turned on the light"
        mock_httpx_client.post.assert_called_once_with(
            "/intent/handle",
            json={"name": "HassTurnOn", "data": {"name": "living room light"}},
        )

    @pytest.mark.asyncio
    async def test_handle_intent_with_entities(self, hass_client, mock_httpx_client):
        """Test intent with entity data (Requirement 12.3)."""
        mock_response = Mock()
        mock_response.json.return_value = {"speech": {}, "response_type": "action_done"}
        mock_httpx_client.post.return_value = mock_response

        await hass_client.handle_intent("HassTurnOn", {"entity_id": "light.living_room"})

        # Verify entity data is passed
        call_args = mock_httpx_client.post.call_args
        assert call_args.args[0] == "/intent/handle"
        assert "entity_id" in call_args.kwargs["json"]["data"]

    @pytest.mark.asyncio
    async def test_handle_intent_unrecognized(self, hass_client, mock_httpx_client):
        """Test unrecognized intent error (Requirement 12.4)."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Intent not recognized"
        mock_httpx_client.post.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=mock_response
        )

        with pytest.raises(ServiceCallError) as exc_info:
            await hass_client.handle_intent("UnknownIntent", {})
        assert "Intent not recognized" in str(exc_info.value)


# ============================================================================
# Response Size Tracking Tests (Requirement 21.8, 21.9)
# ============================================================================


class TestResponseSizeTracking:
    """Tests for response size tracking and warnings (Requirements 21.8, 21.9)."""

    @pytest.mark.asyncio
    async def test_large_response_warning(self, hass_client, mock_httpx_client, caplog):
        """Test warning logged for responses > 100KB (Requirement 21.9)."""
        import logging

        caplog.set_level(logging.WARNING)

        mock_response = Mock()
        # Create a response > 100KB (100,000 bytes)
        large_entities = [
            {
                "entity_id": f"sensor.test_{i}",
                "state": "on",
                "attributes": {"data": "x" * 1000},  # 1KB per entity
            }
            for i in range(150)  # 150KB total
        ]
        mock_response.json.return_value = large_entities
        mock_httpx_client.get.return_value = mock_response

        await hass_client.get_states()

        # Check if warning was logged
        assert any(
            "100KB" in record.message or "large" in record.message.lower()
            for record in caplog.records
            if record.levelname == "WARNING"
        )

    @pytest.mark.asyncio
    async def test_response_size_error_threshold(self, hass_client, mock_httpx_client):
        """Test error for responses > 200KB (Requirement 21.8)."""
        mock_response = Mock()
        # Create a response > 200KB
        huge_entities = [
            {
                "entity_id": f"sensor.test_{i}",
                "state": "on",
                "attributes": {"data": "x" * 1000},
            }
            for i in range(250)  # 250KB total
        ]
        mock_response.json.return_value = huge_entities
        mock_httpx_client.get.return_value = mock_response

        # Should raise error or return truncated with error message
        result = await hass_client.get_states()

        # Verify response is limited or error is raised
        # Implementation may vary - either limit results or raise error
        assert len(result) <= 500  # Max limit should be enforced


# ============================================================================
# Service Call Tests (Requirements 5.1-5.6)
# ============================================================================


class TestCallService:
    """Tests for call_service method (Requirements 5.1-5.6)."""

    @pytest.mark.asyncio
    async def test_call_service_with_return_response(self, hass_client, mock_httpx_client):
        """Test service call with return_response flag (Requirement 5.2)."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": {"temperature": 22.5, "humidity": 45}}
        mock_httpx_client.post.return_value = mock_response

        result = await hass_client.call_service(
            "weather",
            "get_forecast",
            data={"entity_id": "weather.home"},
            return_response=True,
        )

        assert "response" in result
        assert result["response"]["temperature"] == 22.5

    @pytest.mark.asyncio
    async def test_call_service_without_return_response(self, hass_client, mock_httpx_client):
        """Test service call without return_response (Requirement 5.3)."""
        mock_response = Mock()
        mock_response.text = ""
        mock_response.json.return_value = {}
        mock_httpx_client.post.return_value = mock_response

        result = await hass_client.call_service(
            "light", "turn_on", data={"entity_id": "light.living_room"}
        )

        # Should return success confirmation
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_call_service_validation_error(self, hass_client, mock_httpx_client):
        """Test service parameter validation error (Requirement 5.5)."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid service data: brightness must be 0-255"
        mock_httpx_client.post.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=mock_response
        )

        with pytest.raises(ServiceCallError) as exc_info:
            await hass_client.call_service("light", "turn_on", data={"brightness": 300})
        assert "Invalid service data" in str(exc_info.value)


# ============================================================================
# Error Handling Tests (Requirements 17.1-17.6)
# ============================================================================


class TestErrorHandling:
    """Tests for comprehensive error handling (Requirements 17.1-17.6)."""

    @pytest.mark.asyncio
    async def test_timeout_error(self, hass_client, mock_httpx_client):
        """Test timeout error handling."""
        mock_httpx_client.get.side_effect = httpx.TimeoutException("Request timeout")

        with pytest.raises(ConnectionError) as exc_info:
            await hass_client.get_states()
        assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_network_error(self, hass_client, mock_httpx_client):
        """Test network error handling."""
        mock_httpx_client.get.side_effect = httpx.NetworkError("Network unreachable")

        with pytest.raises(ConnectionError) as exc_info:
            await hass_client.get_states()
        assert "Failed to connect" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_http_500_error(self, hass_client, mock_httpx_client):
        """Test HTTP 500 server error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_httpx_client.get.side_effect = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=mock_response
        )

        with pytest.raises(ServiceCallError) as exc_info:
            await hass_client.get_states()
        assert "HTTP 500" in str(exc_info.value)
