"""Unit tests for the input helper control tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.homeassistant_mcp.hass.client import (
    EntityNotFoundError,
    HomeAssistantClient,
    ServiceCallError,
)
from src.homeassistant_mcp.tools.helpers.input_helpers import (
    _decrement_input_number,
    _get_input_boolean,
    _get_input_datetime,
    _get_input_number,
    _get_input_select,
    _get_input_text,
    _increment_input_number,
    _list_input_booleans,
    _list_input_datetimes,
    _list_input_numbers,
    _list_input_selects,
    _list_input_texts,
    _select_input_select_option,
    _set_input_datetime_value,
    _set_input_number_value,
    _set_input_text_value,
    _toggle_input_boolean,
    _turn_off_input_boolean,
    _turn_on_input_boolean,
)


@pytest.fixture
def mock_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock(spec=HomeAssistantClient)
    return client


@pytest.fixture
def sample_input_boolean_states():
    """Sample input boolean entity states for testing."""
    return [
        {
            "entity_id": "input_boolean.guest_mode",
            "state": "on",
            "attributes": {"friendly_name": "Guest Mode"},
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        },
        {
            "entity_id": "input_boolean.vacation_mode",
            "state": "off",
            "attributes": {"friendly_name": "Vacation Mode"},
            "last_changed": "2024-01-01T11:00:00",
            "last_updated": "2024-01-01T11:00:00",
        },
    ]


@pytest.fixture
def sample_input_number_states():
    """Sample input number entity states for testing."""
    return [
        {
            "entity_id": "input_number.temperature_threshold",
            "state": "22.5",
            "attributes": {
                "friendly_name": "Temperature Threshold",
                "min": 15.0,
                "max": 30.0,
                "step": 0.5,
                "unit_of_measurement": "°C",
            },
        },
        {
            "entity_id": "input_number.counter",
            "state": "5",
            "attributes": {
                "friendly_name": "Counter",
                "min": 0,
                "max": 100,
                "step": 1,
            },
        },
    ]


@pytest.fixture
def sample_input_select_states():
    """Sample input select entity states for testing."""
    return [
        {
            "entity_id": "input_select.home_mode",
            "state": "Home",
            "attributes": {
                "friendly_name": "Home Mode",
                "options": ["Home", "Away", "Sleep", "Vacation"],
            },
        },
    ]


@pytest.fixture
def sample_input_text_states():
    """Sample input text entity states for testing."""
    return [
        {
            "entity_id": "input_text.notification_message",
            "state": "Hello World",
            "attributes": {"friendly_name": "Notification Message"},
        },
    ]


@pytest.fixture
def sample_input_datetime_states():
    """Sample input datetime entity states for testing."""
    return [
        {
            "entity_id": "input_datetime.alarm_time",
            "state": "2024-01-15 08:30:00",
            "attributes": {
                "friendly_name": "Alarm Time",
                "has_date": True,
                "has_time": True,
            },
        },
    ]


# ============================================================================
# INPUT BOOLEAN TESTS
# ============================================================================


class TestListInputBooleans:
    """Tests for listing input booleans."""

    @pytest.mark.asyncio
    async def test_list_input_booleans_success(self, mock_client, sample_input_boolean_states):
        """Test successfully listing all input booleans."""
        mock_client.get_states.return_value = sample_input_boolean_states
        result = await _list_input_booleans(mock_client)
        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["input_booleans"]) == 2

    @pytest.mark.asyncio
    async def test_list_input_booleans_empty(self, mock_client):
        """Test listing input booleans when none exist."""
        mock_client.get_states.return_value = []
        result = await _list_input_booleans(mock_client)
        assert result["success"] is True
        assert result["count"] == 0


class TestGetInputBoolean:
    """Tests for getting a specific input boolean."""

    @pytest.mark.asyncio
    async def test_get_input_boolean_success(self, mock_client):
        """Test successfully getting a specific input boolean."""
        mock_client.get_state.return_value = {
            "entity_id": "input_boolean.guest_mode",
            "state": "on",
            "attributes": {"friendly_name": "Guest Mode"},
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }
        result = await _get_input_boolean(mock_client, "input_boolean.guest_mode")
        assert result["success"] is True
        assert result["input_boolean"]["state"] == "on"

    @pytest.mark.asyncio
    async def test_get_input_boolean_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not an input boolean."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_input_boolean(mock_client, "switch.test")
        assert "not an input boolean entity" in str(exc_info.value)


class TestTurnOnInputBoolean:
    """Tests for turning on input booleans."""

    @pytest.mark.asyncio
    async def test_turn_on_input_boolean_success(self, mock_client):
        """Test successfully turning on an input boolean."""
        mock_client.call_service.return_value = {}
        result = await _turn_on_input_boolean(mock_client, "input_boolean.guest_mode")
        assert result["success"] is True
        assert "turned on" in result["message"]

    @pytest.mark.asyncio
    async def test_turn_on_input_boolean_invalid_entity_type(self, mock_client):
        """Test turning on an entity that is not an input boolean."""
        with pytest.raises(EntityNotFoundError):
            await _turn_on_input_boolean(mock_client, "switch.test")


class TestTurnOffInputBoolean:
    """Tests for turning off input booleans."""

    @pytest.mark.asyncio
    async def test_turn_off_input_boolean_success(self, mock_client):
        """Test successfully turning off an input boolean."""
        mock_client.call_service.return_value = {}
        result = await _turn_off_input_boolean(mock_client, "input_boolean.guest_mode")
        assert result["success"] is True
        assert "turned off" in result["message"]


class TestToggleInputBoolean:
    """Tests for toggling input booleans."""

    @pytest.mark.asyncio
    async def test_toggle_input_boolean_success(self, mock_client):
        """Test successfully toggling an input boolean."""
        mock_client.call_service.return_value = {}
        result = await _toggle_input_boolean(mock_client, "input_boolean.guest_mode")
        assert result["success"] is True
        assert "toggled" in result["message"]


# ============================================================================
# INPUT NUMBER TESTS
# ============================================================================


class TestListInputNumbers:
    """Tests for listing input numbers."""

    @pytest.mark.asyncio
    async def test_list_input_numbers_success(self, mock_client, sample_input_number_states):
        """Test successfully listing all input numbers."""
        mock_client.get_states.return_value = sample_input_number_states
        result = await _list_input_numbers(mock_client)
        assert result["success"] is True
        assert result["count"] == 2


class TestGetInputNumber:
    """Tests for getting a specific input number."""

    @pytest.mark.asyncio
    async def test_get_input_number_success(self, mock_client):
        """Test successfully getting a specific input number."""
        mock_client.get_state.return_value = {
            "entity_id": "input_number.temperature_threshold",
            "state": "22.5",
            "attributes": {
                "friendly_name": "Temperature Threshold",
                "min": 15.0,
                "max": 30.0,
                "step": 0.5,
            },
        }
        result = await _get_input_number(mock_client, "input_number.temperature_threshold")
        assert result["success"] is True
        assert result["input_number"]["min"] == 15.0

    @pytest.mark.asyncio
    async def test_get_input_number_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not an input number."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_input_number(mock_client, "switch.test")
        assert "not an input number entity" in str(exc_info.value)


class TestSetInputNumberValue:
    """Tests for setting input number values."""

    @pytest.mark.asyncio
    async def test_set_input_number_value_success(self, mock_client):
        """Test successfully setting an input number value."""
        mock_client.get_state.return_value = {
            "entity_id": "input_number.temperature_threshold",
            "state": "22.5",
            "attributes": {"min": 15.0, "max": 30.0},
        }
        mock_client.call_service.return_value = {}
        result = await _set_input_number_value(
            mock_client, "input_number.temperature_threshold", 25.0
        )
        assert result["success"] is True
        assert "set to 25.0" in result["message"]

    @pytest.mark.asyncio
    async def test_set_input_number_value_out_of_range_min(self, mock_client):
        """Test setting value below minimum."""
        mock_client.get_state.return_value = {
            "entity_id": "input_number.temperature_threshold",
            "state": "22.5",
            "attributes": {"min": 15.0, "max": 30.0},
        }
        with pytest.raises(ServiceCallError) as exc_info:
            await _set_input_number_value(mock_client, "input_number.temperature_threshold", 10.0)
        assert "below minimum" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_set_input_number_value_out_of_range_max(self, mock_client):
        """Test setting value above maximum."""
        mock_client.get_state.return_value = {
            "entity_id": "input_number.temperature_threshold",
            "state": "22.5",
            "attributes": {"min": 15.0, "max": 30.0},
        }
        with pytest.raises(ServiceCallError) as exc_info:
            await _set_input_number_value(mock_client, "input_number.temperature_threshold", 35.0)
        assert "above maximum" in str(exc_info.value)


class TestIncrementInputNumber:
    """Tests for incrementing input numbers."""

    @pytest.mark.asyncio
    async def test_increment_input_number_success(self, mock_client):
        """Test successfully incrementing an input number."""
        mock_client.call_service.return_value = {}
        result = await _increment_input_number(mock_client, "input_number.counter")
        assert result["success"] is True
        assert "incremented" in result["message"]


class TestDecrementInputNumber:
    """Tests for decrementing input numbers."""

    @pytest.mark.asyncio
    async def test_decrement_input_number_success(self, mock_client):
        """Test successfully decrementing an input number."""
        mock_client.call_service.return_value = {}
        result = await _decrement_input_number(mock_client, "input_number.counter")
        assert result["success"] is True
        assert "decremented" in result["message"]


# ============================================================================
# INPUT SELECT TESTS
# ============================================================================


class TestListInputSelects:
    """Tests for listing input selects."""

    @pytest.mark.asyncio
    async def test_list_input_selects_success(self, mock_client, sample_input_select_states):
        """Test successfully listing all input selects."""
        mock_client.get_states.return_value = sample_input_select_states
        result = await _list_input_selects(mock_client)
        assert result["success"] is True
        assert result["count"] == 1


class TestGetInputSelect:
    """Tests for getting a specific input select."""

    @pytest.mark.asyncio
    async def test_get_input_select_success(self, mock_client):
        """Test successfully getting a specific input select."""
        mock_client.get_state.return_value = {
            "entity_id": "input_select.home_mode",
            "state": "Home",
            "attributes": {
                "friendly_name": "Home Mode",
                "options": ["Home", "Away", "Sleep", "Vacation"],
            },
        }
        result = await _get_input_select(mock_client, "input_select.home_mode")
        assert result["success"] is True
        assert len(result["input_select"]["options"]) == 4

    @pytest.mark.asyncio
    async def test_get_input_select_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not an input select."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_input_select(mock_client, "switch.test")
        assert "not an input select entity" in str(exc_info.value)


class TestSelectInputSelectOption:
    """Tests for selecting input select options."""

    @pytest.mark.asyncio
    async def test_select_option_success(self, mock_client):
        """Test successfully selecting an option."""
        mock_client.get_state.return_value = {
            "entity_id": "input_select.home_mode",
            "state": "Home",
            "attributes": {"options": ["Home", "Away", "Sleep", "Vacation"]},
        }
        mock_client.call_service.return_value = {}
        result = await _select_input_select_option(mock_client, "input_select.home_mode", "Away")
        assert result["success"] is True
        assert "Away" in result["message"]

    @pytest.mark.asyncio
    async def test_select_option_invalid_option(self, mock_client):
        """Test selecting an option that doesn't exist."""
        mock_client.get_state.return_value = {
            "entity_id": "input_select.home_mode",
            "state": "Home",
            "attributes": {"options": ["Home", "Away", "Sleep", "Vacation"]},
        }
        with pytest.raises(ServiceCallError) as exc_info:
            await _select_input_select_option(
                mock_client, "input_select.home_mode", "InvalidOption"
            )
        assert "not valid" in str(exc_info.value)


# ============================================================================
# INPUT TEXT TESTS
# ============================================================================


class TestListInputTexts:
    """Tests for listing input texts."""

    @pytest.mark.asyncio
    async def test_list_input_texts_success(self, mock_client, sample_input_text_states):
        """Test successfully listing all input texts."""
        mock_client.get_states.return_value = sample_input_text_states
        result = await _list_input_texts(mock_client)
        assert result["success"] is True
        assert result["count"] == 1


class TestGetInputText:
    """Tests for getting a specific input text."""

    @pytest.mark.asyncio
    async def test_get_input_text_success(self, mock_client):
        """Test successfully getting a specific input text."""
        mock_client.get_state.return_value = {
            "entity_id": "input_text.notification_message",
            "state": "Hello World",
            "attributes": {"friendly_name": "Notification Message"},
        }
        result = await _get_input_text(mock_client, "input_text.notification_message")
        assert result["success"] is True
        assert result["input_text"]["state"] == "Hello World"

    @pytest.mark.asyncio
    async def test_get_input_text_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not an input text."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_input_text(mock_client, "switch.test")
        assert "not an input text entity" in str(exc_info.value)


class TestSetInputTextValue:
    """Tests for setting input text values."""

    @pytest.mark.asyncio
    async def test_set_input_text_value_success(self, mock_client):
        """Test successfully setting an input text value."""
        mock_client.call_service.return_value = {}
        result = await _set_input_text_value(
            mock_client, "input_text.notification_message", "New Message"
        )
        assert result["success"] is True
        assert "New Message" in result["message"]


# ============================================================================
# INPUT DATETIME TESTS
# ============================================================================


class TestListInputDatetimes:
    """Tests for listing input datetimes."""

    @pytest.mark.asyncio
    async def test_list_input_datetimes_success(self, mock_client, sample_input_datetime_states):
        """Test successfully listing all input datetimes."""
        mock_client.get_states.return_value = sample_input_datetime_states
        result = await _list_input_datetimes(mock_client)
        assert result["success"] is True
        assert result["count"] == 1


class TestGetInputDatetime:
    """Tests for getting a specific input datetime."""

    @pytest.mark.asyncio
    async def test_get_input_datetime_success(self, mock_client):
        """Test successfully getting a specific input datetime."""
        mock_client.get_state.return_value = {
            "entity_id": "input_datetime.alarm_time",
            "state": "2024-01-15 08:30:00",
            "attributes": {"friendly_name": "Alarm Time", "has_date": True, "has_time": True},
        }
        result = await _get_input_datetime(mock_client, "input_datetime.alarm_time")
        assert result["success"] is True
        assert result["input_datetime"]["state"] == "2024-01-15 08:30:00"

    @pytest.mark.asyncio
    async def test_get_input_datetime_invalid_entity_type(self, mock_client):
        """Test getting an entity that is not an input datetime."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await _get_input_datetime(mock_client, "switch.test")
        assert "not an input datetime entity" in str(exc_info.value)


class TestSetInputDatetimeValue:
    """Tests for setting input datetime values."""

    @pytest.mark.asyncio
    async def test_set_input_datetime_with_datetime(self, mock_client):
        """Test setting input datetime with full datetime."""
        mock_client.call_service.return_value = {}
        result = await _set_input_datetime_value(
            mock_client, "input_datetime.alarm_time", "2024-01-15T08:30:00", None, None
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_set_input_datetime_with_date_only(self, mock_client):
        """Test setting input datetime with date only."""
        mock_client.call_service.return_value = {}
        result = await _set_input_datetime_value(
            mock_client, "input_datetime.vacation_start", None, "2024-07-01", None
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_set_input_datetime_with_time_only(self, mock_client):
        """Test setting input datetime with time only."""
        mock_client.call_service.return_value = {}
        result = await _set_input_datetime_value(
            mock_client, "input_datetime.wake_time", None, None, "07:00:00"
        )
        assert result["success"] is True


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestInputBooleanControlIntegration:
    """Integration tests for input_boolean_control tool function."""

    @pytest.mark.asyncio
    async def test_input_boolean_control_missing_entity_id(self):
        """Test input_boolean_control with missing entity_id."""
        from src.homeassistant_mcp.tools.helpers.input_helpers import register_input_boolean_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool
        register_input_boolean_tool(mock_mcp, lambda: mock_client)
        result = await registered_func(action="get")
        assert result["success"] is False
        assert "entity_id is required" in result["error"]


class TestInputNumberControlIntegration:
    """Integration tests for input_number_control tool function."""

    @pytest.mark.asyncio
    async def test_input_number_control_missing_value(self):
        """Test input_number_control set_value without value parameter."""
        from src.homeassistant_mcp.tools.helpers.input_helpers import register_input_number_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool
        register_input_number_tool(mock_mcp, lambda: mock_client)
        result = await registered_func(action="set_value", entity_id="input_number.test")
        assert result["success"] is False
        assert "value is required" in result["error"]


class TestInputSelectControlIntegration:
    """Integration tests for input_select_control tool function."""

    @pytest.mark.asyncio
    async def test_input_select_control_missing_option(self):
        """Test input_select_control select_option without option parameter."""
        from src.homeassistant_mcp.tools.helpers.input_helpers import register_input_select_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool
        register_input_select_tool(mock_mcp, lambda: mock_client)
        result = await registered_func(action="select_option", entity_id="input_select.test")
        assert result["success"] is False
        assert "option is required" in result["error"]


class TestInputTextControlIntegration:
    """Integration tests for input_text_control tool function."""

    @pytest.mark.asyncio
    async def test_input_text_control_missing_value(self):
        """Test input_text_control set_value without value parameter."""
        from src.homeassistant_mcp.tools.helpers.input_helpers import register_input_text_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool
        register_input_text_tool(mock_mcp, lambda: mock_client)
        result = await registered_func(action="set_value", entity_id="input_text.test")
        assert result["success"] is False
        assert "value is required" in result["error"]


class TestInputDatetimeControlIntegration:
    """Integration tests for input_datetime_control tool function."""

    @pytest.mark.asyncio
    async def test_input_datetime_control_missing_all_values(self):
        """Test input_datetime_control set_datetime without any value parameters."""
        from src.homeassistant_mcp.tools.helpers.input_helpers import register_input_datetime_tool

        mock_client = AsyncMock(spec=HomeAssistantClient)
        mock_mcp = MagicMock()
        registered_func = None

        def mock_tool():
            def decorator(func):
                nonlocal registered_func
                registered_func = func
                return func

            return decorator

        mock_mcp.tool = mock_tool
        register_input_datetime_tool(mock_mcp, lambda: mock_client)
        result = await registered_func(action="set_datetime", entity_id="input_datetime.test")
        assert result["success"] is False
        assert "At least one of datetime, date, or time is required" in result["error"]
