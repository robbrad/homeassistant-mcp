"""Safety text templates for prompts.

This module provides reusable text templates for safety messaging across all
prompts that involve potentially dangerous or disruptive actions. These templates
ensure consistent safety communication and encode best practices directly in
prompt text.

The templates use Python string formatting to allow customization with specific
entity information, states, and context while maintaining consistent structure
and messaging.

Templates:
    CONFIRMATION_TEMPLATE: Confirmation requirements for sensitive domains
    QUIET_HOURS_TEMPLATE: Warnings for actions during quiet hours
    READ_STATE_FIRST_TEMPLATE: Current state verification guidance
    BULK_ACTION_TEMPLATE: Confirmation for actions affecting multiple entities

Constants:
    SAFETY_KEYWORDS: Keywords that should appear in control prompts

Example Usage:
    # Format a confirmation message for a lock
    message = CONFIRMATION_TEMPLATE.format(
        domain="lock",
        current_state="locked"
    )
"""

# Template for confirmation requirements on sensitive domains
# This template is used when controlling devices in sensitive domains (locks, alarms, etc.)
# It ensures users explicitly confirm actions that could affect security or safety
# Format parameters: domain (str), current_state (str)
CONFIRMATION_TEMPLATE = """
⚠️ IMPORTANT: This action affects a {domain} device.

Before proceeding:
1. Verify current state: {current_state}
2. Confirm this is what you want to do
3. Ensure no one will be negatively impacted

Please confirm you want to proceed.
"""

# Template for quiet hours warnings
# Used when actions might be noisy during quiet hours (10 PM - 7 AM by default)
# Helps prevent disturbing sleep or quiet time unless explicitly requested
# Format parameters: current_time (str in HH:MM format)
QUIET_HOURS_TEMPLATE = """
🌙 Note: It's currently {current_time}, which is during quiet hours (10 PM - 7 AM).

This action might be noisy or disruptive. Consider:
- Reducing volume/brightness
- Delaying until morning
- Confirming this is necessary now
"""

# Template for read-state-first guidance
# Implements the read-state-first principle: always verify current state before actions
# This prevents redundant actions and provides context for decision-making
# Format parameters: entity_id (str), state (str), attributes (str)
READ_STATE_FIRST_TEMPLATE = """
Current state of {entity_id}:
- State: {state}
- {attributes}

I've verified the current state before suggesting actions.
"""

# Template for bulk action confirmation
# Used when actions will affect multiple entities (3+ by default)
# Ensures users review all affected entities before proceeding
# Format parameters: count (int), entity_list (str with newline-separated entities)
BULK_ACTION_TEMPLATE = """
⚠️ BULK ACTION: This will affect {count} entities.

Entities to be affected:
{entity_list}

Please review the list and confirm you want to proceed with this action.
"""

# Safety keywords that should appear in control prompts
# These keywords indicate that safety guidance is present in the prompt
# Used by property tests to verify safety features are implemented
SAFETY_KEYWORDS = {
    "confirm",  # Requires user confirmation
    "verify",  # Asks user to verify state or intent
    "current state",  # Shows current state before actions
    "check",  # Prompts user to check something
    "ensure",  # Asks user to ensure conditions are met
    "before",  # Indicates pre-action checks
    "review",  # Asks user to review information
}
