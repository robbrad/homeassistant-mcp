"""Data models for the MCP prompts layer.

This module defines the core data structures used throughout the prompts layer,
including metadata models, safety configuration, and tag taxonomy for prompt
categorization.

The models use Pydantic for type-safe validation and provide clear definitions
of sensitive domains, safety thresholds, and prompt organization patterns.

Classes:
    PromptMetadata: Metadata for a registered prompt
    SafetyConfig: Safety configuration for prompts

Constants:
    PromptTag: Type alias for valid prompt tags
    TAG_DEFINITIONS: Descriptions of each prompt tag
    SENSITIVE_DOMAINS: Set of domains requiring extra caution
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# Tag taxonomy for prompt categorization
# These tags allow prompts to be filtered and organized by purpose
# Used for visibility controls and prompt discovery
PromptTag = Literal["control", "diagnostics", "automation", "status", "safety"]

TAG_DEFINITIONS: dict[PromptTag, str] = {
    "control": "Prompts for controlling entities and areas",
    "diagnostics": "Prompts for explaining and diagnosing issues",
    "automation": "Prompts for automation creation and management",
    "status": "Prompts for monitoring and status reporting",
    "safety": "Prompts for safety policies and guidelines",
}

# Sensitive domains requiring extra caution and confirmation
# These domains involve security, safety, or privacy concerns
# Actions on these domains MUST include confirmation requirements
# - lock: Door locks and security locks
# - alarm_control_panel: Security alarm systems
# - garage_door: Garage door openers
# - camera: Security cameras and surveillance devices
# - cover: Covers (when used for garage doors or security shutters)
SENSITIVE_DOMAINS: set[str] = {
    "lock",
    "alarm_control_panel",
    "garage_door",
    "camera",
    "cover",  # When used for garage doors or security shutters
}


class PromptMetadata(BaseModel):
    """Metadata for a registered prompt."""

    name: str = Field(..., description="Unique snake_case identifier for the prompt")
    description: str = Field(..., description="Clear, concise description of the prompt")
    tags: set[PromptTag] = Field(..., description="Categorization tags for the prompt")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Parameter schema for the prompt"
    )


class SafetyConfig(BaseModel):
    """Safety configuration for prompts.

    This configuration defines the safety thresholds and rules used throughout
    the prompts layer to ensure safe smart home control.
    """

    sensitive_domains: set[str] = Field(
        default_factory=lambda: SENSITIVE_DOMAINS.copy(),
        description="Domains requiring confirmation before actions",
    )
    # Quiet hours define when noisy actions should be avoided
    # Default: 10 PM to 7 AM (22:00 to 07:00)
    # During these hours, prompts will warn about noisy actions
    quiet_hours_start: str = Field(
        default="22:00", description="Start of quiet hours (24-hour format)"
    )
    quiet_hours_end: str = Field(default="07:00", description="End of quiet hours (24-hour format)")

    # Bulk action threshold determines when to require confirmation for mass changes
    # Default: 3 entities - actions affecting 3+ entities are considered "bulk"
    # This prevents accidental mass changes and gives users a chance to review
    require_confirmation_for_bulk: bool = Field(
        default=True, description="Require confirmation for bulk actions"
    )
    min_bulk_threshold: int = Field(
        default=3, ge=1, description="Minimum number of entities to be considered bulk action"
    )
