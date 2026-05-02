"""Pydantic models for Home Assistant API responses.

This module provides type-safe data models for validating API responses from
Home Assistant. All models use Pydantic v2 for validation and serialization.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EntityState(BaseModel):
    """Entity state model for Home Assistant entities.

    Represents the complete state of a Home Assistant entity including
    its current state value, attributes, and metadata.
    """

    entity_id: str = Field(..., description="Unique identifier for the entity")
    state: str = Field(..., description="Current state value of the entity")
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Entity attributes and metadata"
    )
    last_changed: datetime = Field(..., description="Timestamp when the state value last changed")
    last_updated: datetime = Field(..., description="Timestamp when the entity was last updated")
    context: dict[str, Any] = Field(
        default_factory=dict, description="Context information for the state change"
    )


class ServiceDescription(BaseModel):
    """Service description model for Home Assistant services.

    Describes a single service including its name, description, and
    the fields it accepts as parameters.
    """

    name: str = Field(..., description="Service name")
    description: str = Field(..., description="Human-readable service description")
    fields: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Service parameter field definitions"
    )
    target: dict[str, Any] | None = Field(
        None, description="Optional target selector configuration"
    )


class DomainServices(BaseModel):
    """Services for a Home Assistant domain.

    Groups all services available within a specific domain (e.g., light, switch).
    """

    domain: str = Field(..., description="Domain name (e.g., 'light', 'switch')")
    services: dict[str, ServiceDescription] = Field(
        ..., description="Map of service names to their descriptions"
    )


class HistoryEntry(BaseModel):
    """Historical state entry for an entity.

    Represents a single point-in-time state of an entity from the history API.
    """

    entity_id: str = Field(..., description="Entity identifier")
    state: str = Field(..., description="State value at this point in time")
    attributes: dict[str, Any] | None = Field(
        None, description="Entity attributes (may be omitted in minimal responses)"
    )
    last_changed: datetime = Field(..., description="Timestamp when this state change occurred")
    last_updated: datetime = Field(..., description="Timestamp when the entity was updated")


class LogbookEntry(BaseModel):
    """Logbook entry for human-readable event logs.

    Represents a single entry in the Home Assistant logbook, providing
    human-readable descriptions of events and state changes.
    """

    when: datetime = Field(..., description="Timestamp of the logbook entry")
    name: str = Field(..., description="Name of the entity or event")
    message: str | None = Field(None, description="Human-readable message")
    domain: str | None = Field(None, description="Domain of the entity")
    entity_id: str | None = Field(None, description="Entity identifier if applicable")


class CalendarEvent(BaseModel):
    """Calendar event model.

    Represents a single event from a Home Assistant calendar entity.
    """

    start: datetime = Field(..., description="Event start date/time")
    end: datetime = Field(..., description="Event end date/time")
    summary: str = Field(..., description="Event title/summary")
    description: str | None = Field(None, description="Detailed event description")
    location: str | None = Field(None, description="Event location")


class ConfigValidation(BaseModel):
    """Configuration validation result.

    Contains the results of validating the Home Assistant configuration,
    including any errors or warnings found.
    """

    result: str = Field(..., description="Validation result: 'valid' or 'invalid'")
    errors: list[str] = Field(default_factory=list, description="List of configuration errors")
    warnings: list[str] = Field(default_factory=list, description="List of configuration warnings")


class IntentResponse(BaseModel):
    """Intent handling response.

    Contains the response from processing a Home Assistant intent,
    including speech output and optional card data.
    """

    speech: dict[str, Any] = Field(..., description="Speech response data")
    card: dict[str, Any] | None = Field(None, description="Optional card data for UI")
    language: str = Field(..., description="Response language code")
    response_type: str = Field(..., description="Type of response")
    data: dict[str, Any] | None = Field(None, description="Additional response data")
