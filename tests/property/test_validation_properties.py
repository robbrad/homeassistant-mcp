"""Property-based tests for Pydantic model validation.

Tests Properties 36-37 from the design document.
"""

from datetime import datetime, timezone

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from homeassistant_mcp.models import (
    CalendarEvent,
    ConfigValidation,
    EntityState,
    HistoryEntry,
    IntentResponse,
    LogbookEntry,
    ServiceDescription,
)


# Strategy helpers for generating valid data
def text_strategy(min_size=1, max_size=100):
    """Generate text strings."""
    return st.text(
        min_size=min_size, max_size=max_size, alphabet=st.characters(blacklist_characters=["\x00"])
    )


def datetime_strategy():
    """Generate datetime objects with timezone."""
    return st.datetimes(
        min_value=datetime(2000, 1, 1),
        max_value=datetime(2030, 12, 31),
        timezones=st.just(timezone.utc),
    )


def dict_strategy():
    """Generate dictionaries with string keys and various values."""
    return st.dictionaries(
        keys=text_strategy(min_size=1, max_size=20),
        values=st.one_of(
            st.text(),
            st.integers(),
            st.floats(allow_nan=False),
            st.booleans(),
        ),
        max_size=10,
    )


def service_fields_strategy():
    """Generate service fields dictionary (dict of dicts)."""
    return st.dictionaries(
        keys=text_strategy(min_size=1, max_size=20),
        values=st.dictionaries(
            keys=text_strategy(min_size=1, max_size=10),
            values=st.one_of(st.text(), st.integers(), st.booleans()),
            max_size=3,
        ),
        max_size=5,
    )


# Feature: rest-api-overhaul, Property 36: Pydantic Response Validation
class TestPydanticResponseValidation:
    """Property 36: For any API response, the data SHALL be validated against
    the appropriate Pydantic model before being returned.
    """

    @given(
        entity_id=text_strategy(),
        state=text_strategy(),
        attributes=dict_strategy(),
        last_changed=datetime_strategy(),
        last_updated=datetime_strategy(),
        context=dict_strategy(),
    )
    def test_entity_state_validates_valid_data(
        self, entity_id, state, attributes, last_changed, last_updated, context
    ):
        """Property 36: EntityState validates valid API response data."""
        data = {
            "entity_id": entity_id,
            "state": state,
            "attributes": attributes,
            "last_changed": last_changed,
            "last_updated": last_updated,
            "context": context,
        }

        # Should successfully validate
        entity = EntityState(**data)

        # Verify all fields are preserved
        assert entity.entity_id == entity_id
        assert entity.state == state
        assert entity.attributes == attributes
        assert entity.last_changed == last_changed
        assert entity.last_updated == last_updated
        assert entity.context == context

    @given(
        name=text_strategy(),
        description=text_strategy(),
        fields=service_fields_strategy(),
    )
    def test_service_description_validates_valid_data(self, name, description, fields):
        """Property 36: ServiceDescription validates valid API response data."""
        data = {
            "name": name,
            "description": description,
            "fields": fields,
        }

        # Should successfully validate
        service = ServiceDescription(**data)

        # Verify all fields are preserved
        assert service.name == name
        assert service.description == description
        assert service.fields == fields

    @given(
        entity_id=text_strategy(),
        state=text_strategy(),
        last_changed=datetime_strategy(),
        last_updated=datetime_strategy(),
    )
    def test_history_entry_validates_valid_data(self, entity_id, state, last_changed, last_updated):
        """Property 36: HistoryEntry validates valid API response data."""
        data = {
            "entity_id": entity_id,
            "state": state,
            "last_changed": last_changed,
            "last_updated": last_updated,
        }

        # Should successfully validate
        entry = HistoryEntry(**data)

        # Verify all fields are preserved
        assert entry.entity_id == entity_id
        assert entry.state == state
        assert entry.last_changed == last_changed
        assert entry.last_updated == last_updated

    @given(
        when=datetime_strategy(),
        name=text_strategy(),
    )
    def test_logbook_entry_validates_valid_data(self, when, name):
        """Property 36: LogbookEntry validates valid API response data."""
        data = {
            "when": when,
            "name": name,
        }

        # Should successfully validate
        entry = LogbookEntry(**data)

        # Verify all fields are preserved
        assert entry.when == when
        assert entry.name == name

    @given(
        start=datetime_strategy(),
        end=datetime_strategy(),
        summary=text_strategy(),
    )
    def test_calendar_event_validates_valid_data(self, start, end, summary):
        """Property 36: CalendarEvent validates valid API response data."""
        data = {
            "start": start,
            "end": end,
            "summary": summary,
        }

        # Should successfully validate
        event = CalendarEvent(**data)

        # Verify all fields are preserved
        assert event.start == start
        assert event.end == end
        assert event.summary == summary

    @given(
        result=st.sampled_from(["valid", "invalid"]),
        errors=st.lists(text_strategy(), max_size=5),
        warnings=st.lists(text_strategy(), max_size=5),
    )
    def test_config_validation_validates_valid_data(self, result, errors, warnings):
        """Property 36: ConfigValidation validates valid API response data."""
        data = {
            "result": result,
            "errors": errors,
            "warnings": warnings,
        }

        # Should successfully validate
        validation = ConfigValidation(**data)

        # Verify all fields are preserved
        assert validation.result == result
        assert validation.errors == errors
        assert validation.warnings == warnings

    @given(
        speech=dict_strategy(),
        language=text_strategy(min_size=2, max_size=5),
        response_type=text_strategy(),
    )
    def test_intent_response_validates_valid_data(self, speech, language, response_type):
        """Property 36: IntentResponse validates valid API response data."""
        data = {
            "speech": speech,
            "language": language,
            "response_type": response_type,
        }

        # Should successfully validate
        response = IntentResponse(**data)

        # Verify all fields are preserved
        assert response.speech == speech
        assert response.language == language
        assert response.response_type == response_type


# Feature: rest-api-overhaul, Property 37: Invalid Response Error Handling
class TestInvalidResponseErrorHandling:
    """Property 37: For any API response that fails Pydantic validation,
    the response SHALL return a validation error with details about missing
    or invalid fields.
    """

    @given(
        entity_id=text_strategy(),
        state=text_strategy(),
        # Missing required fields: last_changed, last_updated
    )
    def test_entity_state_missing_required_fields(self, entity_id, state):
        """Property 37: EntityState returns validation error for missing required fields."""
        data = {
            "entity_id": entity_id,
            "state": state,
            # Missing last_changed and last_updated
        }

        with pytest.raises(ValidationError) as exc_info:
            EntityState(**data)

        # Verify error contains details about missing fields
        errors = exc_info.value.errors()
        assert len(errors) >= 2
        error_fields = {e["loc"][0] for e in errors}
        assert "last_changed" in error_fields
        assert "last_updated" in error_fields

    @given(
        entity_id=text_strategy(),
        state=text_strategy(),
        invalid_datetime=st.lists(
            st.integers(), min_size=1, max_size=3
        ),  # Use list which can't be parsed as datetime
    )
    def test_entity_state_invalid_field_type(self, entity_id, state, invalid_datetime):
        """Property 37: EntityState returns validation error for invalid field types."""
        data = {
            "entity_id": entity_id,
            "state": state,
            "last_changed": invalid_datetime,  # Should be datetime, not list
            "last_updated": datetime.now(timezone.utc),
        }

        with pytest.raises(ValidationError) as exc_info:
            EntityState(**data)

        # Verify error contains details about invalid field
        errors = exc_info.value.errors()
        assert len(errors) >= 1
        assert any(e["loc"][0] == "last_changed" for e in errors)

    @given(name=text_strategy())
    def test_service_description_missing_required_fields(self, name):
        """Property 37: ServiceDescription returns validation error for missing required fields."""
        data = {
            "name": name,
            # Missing description
        }

        with pytest.raises(ValidationError) as exc_info:
            ServiceDescription(**data)

        # Verify error contains details about missing field
        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "description" for e in errors)

    @given(
        entity_id=text_strategy(),
        state=text_strategy(),
        # Missing required fields: last_changed, last_updated
    )
    def test_history_entry_missing_required_fields(self, entity_id, state):
        """Property 37: HistoryEntry returns validation error for missing required fields."""
        data = {
            "entity_id": entity_id,
            "state": state,
            # Missing last_changed and last_updated
        }

        with pytest.raises(ValidationError) as exc_info:
            HistoryEntry(**data)

        # Verify error contains details about missing fields
        errors = exc_info.value.errors()
        assert len(errors) >= 2
        error_fields = {e["loc"][0] for e in errors}
        assert "last_changed" in error_fields
        assert "last_updated" in error_fields

    @given(name=text_strategy())
    def test_logbook_entry_missing_required_fields(self, name):
        """Property 37: LogbookEntry returns validation error for missing required fields."""
        data = {
            "name": name,
            # Missing when
        }

        with pytest.raises(ValidationError) as exc_info:
            LogbookEntry(**data)

        # Verify error contains details about missing field
        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "when" for e in errors)

    @given(
        start=datetime_strategy(),
        summary=text_strategy(),
        # Missing required field: end
    )
    def test_calendar_event_missing_required_fields(self, start, summary):
        """Property 37: CalendarEvent returns validation error for missing required fields."""
        data = {
            "start": start,
            "summary": summary,
            # Missing end
        }

        with pytest.raises(ValidationError) as exc_info:
            CalendarEvent(**data)

        # Verify error contains details about missing field
        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "end" for e in errors)

    @given(
        errors=st.lists(text_strategy(), max_size=5),
        # Missing required field: result
    )
    def test_config_validation_missing_required_fields(self, errors):
        """Property 37: ConfigValidation returns validation error for missing required fields."""
        data = {
            "errors": errors,
            # Missing result
        }

        with pytest.raises(ValidationError) as exc_info:
            ConfigValidation(**data)

        # Verify error contains details about missing field
        errors_list = exc_info.value.errors()
        assert any(e["loc"][0] == "result" for e in errors_list)

    @given(
        speech=dict_strategy(),
        language=text_strategy(min_size=2, max_size=5),
        # Missing required field: response_type
    )
    def test_intent_response_missing_required_fields(self, speech, language):
        """Property 37: IntentResponse returns validation error for missing required fields."""
        data = {
            "speech": speech,
            "language": language,
            # Missing response_type
        }

        with pytest.raises(ValidationError) as exc_info:
            IntentResponse(**data)

        # Verify error contains details about missing field
        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "response_type" for e in errors)
