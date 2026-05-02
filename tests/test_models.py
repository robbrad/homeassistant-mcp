"""Unit tests for Pydantic models.

Tests validation, serialization, and deserialization of all API response models.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from homeassistant_mcp.models import (
    CalendarEvent,
    ConfigValidation,
    DomainServices,
    EntityState,
    HistoryEntry,
    IntentResponse,
    LogbookEntry,
    ServiceDescription,
)


class TestEntityState:
    """Tests for EntityState model."""

    def test_valid_entity_state(self):
        """Test creating a valid EntityState."""
        data = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"brightness": 255, "color_temp": 370},
            "last_changed": "2024-01-15T10:00:00+00:00",
            "last_updated": "2024-01-15T10:00:00+00:00",
            "context": {"id": "abc123", "user_id": None},
        }
        entity = EntityState(**data)

        assert entity.entity_id == "light.living_room"
        assert entity.state == "on"
        assert entity.attributes["brightness"] == 255
        assert isinstance(entity.last_changed, datetime)
        assert isinstance(entity.last_updated, datetime)

    def test_entity_state_with_defaults(self):
        """Test EntityState with default values for optional fields."""
        data = {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "last_changed": "2024-01-15T10:00:00+00:00",
            "last_updated": "2024-01-15T10:00:00+00:00",
        }
        entity = EntityState(**data)

        assert entity.attributes == {}
        assert entity.context == {}

    def test_entity_state_missing_required_field(self):
        """Test EntityState validation fails with missing required field."""
        data = {
            "entity_id": "light.living_room",
            "state": "on",
            # Missing last_changed and last_updated
        }

        with pytest.raises(ValidationError) as exc_info:
            EntityState(**data)

        errors = exc_info.value.errors()
        assert len(errors) == 2
        assert any(e["loc"] == ("last_changed",) for e in errors)
        assert any(e["loc"] == ("last_updated",) for e in errors)

    def test_entity_state_invalid_datetime(self):
        """Test EntityState validation fails with invalid datetime."""
        data = {
            "entity_id": "light.living_room",
            "state": "on",
            "last_changed": "not-a-datetime",
            "last_updated": "2024-01-15T10:00:00+00:00",
        }

        with pytest.raises(ValidationError) as exc_info:
            EntityState(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("last_changed",) for e in errors)


class TestServiceDescription:
    """Tests for ServiceDescription model."""

    def test_valid_service_description(self):
        """Test creating a valid ServiceDescription."""
        data = {
            "name": "turn_on",
            "description": "Turn on a light",
            "fields": {
                "brightness": {
                    "description": "Brightness value",
                    "example": 255,
                }
            },
            "target": {"entity": {"domain": "light"}},
        }
        service = ServiceDescription(**data)

        assert service.name == "turn_on"
        assert service.description == "Turn on a light"
        assert "brightness" in service.fields
        assert service.target is not None

    def test_service_description_without_target(self):
        """Test ServiceDescription without target field."""
        data = {
            "name": "reload",
            "description": "Reload configuration",
            "fields": {},
        }
        service = ServiceDescription(**data)

        assert service.target is None
        assert service.fields == {}

    def test_service_description_missing_required_field(self):
        """Test ServiceDescription validation fails with missing required field."""
        data = {
            "name": "turn_on",
            # Missing description
        }

        with pytest.raises(ValidationError) as exc_info:
            ServiceDescription(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("description",) for e in errors)


class TestDomainServices:
    """Tests for DomainServices model."""

    def test_valid_domain_services(self):
        """Test creating a valid DomainServices."""
        data = {
            "domain": "light",
            "services": {
                "turn_on": {
                    "name": "turn_on",
                    "description": "Turn on a light",
                    "fields": {},
                },
                "turn_off": {
                    "name": "turn_off",
                    "description": "Turn off a light",
                    "fields": {},
                },
            },
        }
        domain = DomainServices(**data)

        assert domain.domain == "light"
        assert len(domain.services) == 2
        assert "turn_on" in domain.services
        assert isinstance(domain.services["turn_on"], ServiceDescription)

    def test_domain_services_missing_required_field(self):
        """Test DomainServices validation fails with missing required field."""
        data = {
            "domain": "light",
            # Missing services
        }

        with pytest.raises(ValidationError) as exc_info:
            DomainServices(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("services",) for e in errors)


class TestHistoryEntry:
    """Tests for HistoryEntry model."""

    def test_valid_history_entry(self):
        """Test creating a valid HistoryEntry."""
        data = {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "attributes": {"unit_of_measurement": "°C"},
            "last_changed": "2024-01-15T10:00:00+00:00",
            "last_updated": "2024-01-15T10:00:00+00:00",
        }
        entry = HistoryEntry(**data)

        assert entry.entity_id == "sensor.temperature"
        assert entry.state == "22.5"
        assert entry.attributes is not None

    def test_history_entry_minimal_response(self):
        """Test HistoryEntry without attributes (minimal response)."""
        data = {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "last_changed": "2024-01-15T10:00:00+00:00",
            "last_updated": "2024-01-15T10:00:00+00:00",
        }
        entry = HistoryEntry(**data)

        assert entry.attributes is None

    def test_history_entry_missing_required_field(self):
        """Test HistoryEntry validation fails with missing required field."""
        data = {
            "entity_id": "sensor.temperature",
            # Missing state, last_changed, last_updated
        }

        with pytest.raises(ValidationError) as exc_info:
            HistoryEntry(**data)

        errors = exc_info.value.errors()
        assert len(errors) >= 3


class TestLogbookEntry:
    """Tests for LogbookEntry model."""

    def test_valid_logbook_entry(self):
        """Test creating a valid LogbookEntry."""
        data = {
            "when": "2024-01-15T10:00:00+00:00",
            "name": "Living Room Light",
            "message": "turned on",
            "domain": "light",
            "entity_id": "light.living_room",
        }
        entry = LogbookEntry(**data)

        assert entry.name == "Living Room Light"
        assert entry.message == "turned on"
        assert entry.domain == "light"
        assert entry.entity_id == "light.living_room"

    def test_logbook_entry_with_optional_fields_none(self):
        """Test LogbookEntry with optional fields as None."""
        data = {
            "when": "2024-01-15T10:00:00+00:00",
            "name": "System Event",
        }
        entry = LogbookEntry(**data)

        assert entry.message is None
        assert entry.domain is None
        assert entry.entity_id is None

    def test_logbook_entry_missing_required_field(self):
        """Test LogbookEntry validation fails with missing required field."""
        data = {
            "name": "Living Room Light",
            # Missing when
        }

        with pytest.raises(ValidationError) as exc_info:
            LogbookEntry(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("when",) for e in errors)


class TestCalendarEvent:
    """Tests for CalendarEvent model."""

    def test_valid_calendar_event(self):
        """Test creating a valid CalendarEvent."""
        data = {
            "start": "2024-01-15T10:00:00+00:00",
            "end": "2024-01-15T11:00:00+00:00",
            "summary": "Team Meeting",
            "description": "Weekly team sync",
            "location": "Conference Room A",
        }
        event = CalendarEvent(**data)

        assert event.summary == "Team Meeting"
        assert event.description == "Weekly team sync"
        assert event.location == "Conference Room A"
        assert isinstance(event.start, datetime)
        assert isinstance(event.end, datetime)

    def test_calendar_event_without_optional_fields(self):
        """Test CalendarEvent without optional fields."""
        data = {
            "start": "2024-01-15T10:00:00+00:00",
            "end": "2024-01-15T11:00:00+00:00",
            "summary": "Quick Meeting",
        }
        event = CalendarEvent(**data)

        assert event.description is None
        assert event.location is None

    def test_calendar_event_missing_required_field(self):
        """Test CalendarEvent validation fails with missing required field."""
        data = {
            "start": "2024-01-15T10:00:00+00:00",
            "summary": "Meeting",
            # Missing end
        }

        with pytest.raises(ValidationError) as exc_info:
            CalendarEvent(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("end",) for e in errors)


class TestConfigValidation:
    """Tests for ConfigValidation model."""

    def test_valid_config_validation(self):
        """Test creating a valid ConfigValidation."""
        data = {
            "result": "valid",
            "errors": [],
            "warnings": ["Deprecated configuration option"],
        }
        validation = ConfigValidation(**data)

        assert validation.result == "valid"
        assert len(validation.errors) == 0
        assert len(validation.warnings) == 1

    def test_invalid_config_validation(self):
        """Test ConfigValidation with errors."""
        data = {
            "result": "invalid",
            "errors": ["Invalid YAML syntax", "Missing required field"],
            "warnings": [],
        }
        validation = ConfigValidation(**data)

        assert validation.result == "invalid"
        assert len(validation.errors) == 2

    def test_config_validation_with_defaults(self):
        """Test ConfigValidation with default empty lists."""
        data = {
            "result": "valid",
        }
        validation = ConfigValidation(**data)

        assert validation.errors == []
        assert validation.warnings == []

    def test_config_validation_missing_required_field(self):
        """Test ConfigValidation validation fails with missing required field."""
        data = {
            "errors": [],
            # Missing result
        }

        with pytest.raises(ValidationError) as exc_info:
            ConfigValidation(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("result",) for e in errors)


class TestIntentResponse:
    """Tests for IntentResponse model."""

    def test_valid_intent_response(self):
        """Test creating a valid IntentResponse."""
        data = {
            "speech": {"plain": {"speech": "Turned on the light"}},
            "card": {"title": "Light Control", "content": "Living room light is now on"},
            "language": "en",
            "response_type": "action_done",
            "data": {"entity_id": "light.living_room"},
        }
        response = IntentResponse(**data)

        assert response.language == "en"
        assert response.response_type == "action_done"
        assert response.card is not None
        assert response.data is not None

    def test_intent_response_without_optional_fields(self):
        """Test IntentResponse without optional fields."""
        data = {
            "speech": {"plain": {"speech": "OK"}},
            "language": "en",
            "response_type": "action_done",
        }
        response = IntentResponse(**data)

        assert response.card is None
        assert response.data is None

    def test_intent_response_missing_required_field(self):
        """Test IntentResponse validation fails with missing required field."""
        data = {
            "speech": {"plain": {"speech": "OK"}},
            "language": "en",
            # Missing response_type
        }

        with pytest.raises(ValidationError) as exc_info:
            IntentResponse(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("response_type",) for e in errors)


class TestModelSerialization:
    """Tests for model serialization and deserialization."""

    def test_entity_state_serialization(self):
        """Test EntityState can be serialized to dict."""
        entity = EntityState(
            entity_id="light.test",
            state="on",
            attributes={"brightness": 255},
            last_changed=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            last_updated=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            context={},
        )

        data = entity.model_dump()
        assert data["entity_id"] == "light.test"
        assert data["state"] == "on"
        assert isinstance(data["last_changed"], datetime)

    def test_entity_state_json_serialization(self):
        """Test EntityState can be serialized to JSON."""
        entity = EntityState(
            entity_id="light.test",
            state="on",
            attributes={"brightness": 255},
            last_changed=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            last_updated=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            context={},
        )

        json_str = entity.model_dump_json()
        assert isinstance(json_str, str)
        assert "light.test" in json_str

    def test_calendar_event_round_trip(self):
        """Test CalendarEvent serialization and deserialization."""
        original = CalendarEvent(
            start=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            end=datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
            summary="Test Event",
        )

        # Serialize to dict
        data = original.model_dump()

        # Deserialize back
        restored = CalendarEvent(**data)

        assert restored.summary == original.summary
        assert restored.start == original.start
        assert restored.end == original.end
