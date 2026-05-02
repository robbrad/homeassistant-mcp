"""MCP prompts for guided Home Assistant task execution.

This package provides reusable, parameterized templates that guide LLM behavior
for common smart-home tasks with safety-first design principles.

The prompts layer uses FastMCP 2.0+ patterns with type-safe parameter validation
and structured guidance that encodes best practices and safety rules.

## Tag Taxonomy

Prompts are organized using a tag system for categorization and filtering:

- **control**: Prompts for controlling entities and areas
  - control_entity: Guide safe control of a single entity
  - control_area: Guide control of multiple entities in an area

- **diagnostics**: Prompts for explaining and diagnosing issues
  - explain_entity: Explain what an entity is and what it can do
  - diagnose_automation: Investigate why an automation did/didn't run
  - optimize_climate: Analyze and optimize HVAC settings
  - troubleshoot_device: Guide through troubleshooting device issues

- **automation**: Prompts for automation creation and management
  - create_automation: Guide through creating a new automation
  - suggest_automation: Convert user intent into automation suggestions

- **status**: Prompts for monitoring and status reporting
  - home_status_brief: Comprehensive home status summary
  - optimize_energy: Analyze energy usage and suggest optimizations

- **safety**: Prompts for safety policies and guidelines
  - safety_policy: Provide the assistant's operating rules
  - security_check: Comprehensive security status review

## Visibility Control Mechanism

Prompts can be filtered by tags to control which prompts are visible to users.
This allows for:
- Hiding advanced prompts from novice users
- Showing only relevant prompts based on context
- Customizing prompt availability per installation

Example:
    # Get all control prompts
    control_prompts = [p for p in all_prompts if "control" in p.tags]
    
    # Get all safety-related prompts
    safety_prompts = [p for p in all_prompts if "safety" in p.tags]

## Adding New Prompts

To add a new prompt to the system:

1. **Create the prompt module** (e.g., `my_prompt.py`):
   ```python
   from fastmcp import FastMCP
   from fastmcp.prompts import PromptMessage
   from mcp.types import TextContent
   
   def register_my_prompts(mcp: FastMCP, get_client: Callable) -> None:
       @mcp.prompt(tags={"control"})  # Choose appropriate tag(s)
       async def my_prompt(param: str) -> list[PromptMessage]:
           '''Docstring becomes prompt description.'''
           client = get_client()
           # Implementation
           return [PromptMessage(role="assistant", content=TextContent(...))]
   ```

2. **Import in __init__.py**:
   ```python
   from .my_prompt import register_my_prompts
   ```

3. **Register in register_all_prompts()**:
   ```python
   register_my_prompts(mcp, get_client)
   ```

4. **Follow safety guidelines**:
   - Use SENSITIVE_DOMAINS for security-critical devices
   - Include READ_STATE_FIRST_TEMPLATE to show current state
   - Add CONFIRMATION_TEMPLATE for sensitive actions
   - Check QUIET_HOURS for noisy actions
   - Use BULK_ACTION_TEMPLATE for multi-entity actions

## Prompt Invocation Examples

Prompts are invoked by AI assistants through the MCP protocol:

```python
# Control a single entity
result = await control_entity(
    entity_id="light.living_room",
    action="turn_on"
)

# Control an area
result = await control_area(
    area_id="Living Room",
    goal="turn off all lights"
)

# Explain an entity
result = await explain_entity(
    entity_id="climate.thermostat"
)

# Get home status
result = await home_status_brief()

# Get safety policy
result = await safety_policy()
```

## Safety Features

All prompts implement safety-first design:

1. **Read-State-First**: Always verify current state before suggesting actions
2. **Confirmation Requirements**: Require explicit confirmation for sensitive domains
3. **Quiet Hours Warnings**: Warn about noisy actions during quiet hours (10 PM - 7 AM)
4. **Bulk Action Thresholds**: Require confirmation for actions affecting 3+ entities
5. **Safety Keywords**: Include "confirm", "verify", "check" in control prompts

For more information on FastMCP prompts, see: https://gofastmcp.com/llms.txt
"""

from typing import Any

# Export data models and constants for use by prompt modules
from .models import (
    SENSITIVE_DOMAINS,
    TAG_DEFINITIONS,
    PromptMetadata,
    PromptTag,
    SafetyConfig,
)
from .safety_templates import (
    BULK_ACTION_TEMPLATE,
    CONFIRMATION_TEMPLATE,
    QUIET_HOURS_TEMPLATE,
    READ_STATE_FIRST_TEMPLATE,
    SAFETY_KEYWORDS,
)

__all__ = [
    # Core infrastructure
    "register_all_prompts",
    # New prompt registrations
    "register_control_prompts",
    "register_explain_prompts",
    "register_automation_prompts",
    "register_status_prompts",
    "register_safety_prompts",
    # Legacy prompt registrations (migrated to FastMCP 2.0+)
    "register_climate_prompt",
    "register_energy_prompt",
    "register_scene_prompt",
    "register_security_prompt",
    "register_troubleshooting_prompt",
    # Data models
    "PromptMetadata",
    "SafetyConfig",
    "PromptTag",
    "TAG_DEFINITIONS",
    "SENSITIVE_DOMAINS",
    # Safety templates
    "CONFIRMATION_TEMPLATE",
    "QUIET_HOURS_TEMPLATE",
    "READ_STATE_FIRST_TEMPLATE",
    "BULK_ACTION_TEMPLATE",
    "SAFETY_KEYWORDS",
]


def register_all_prompts(mcp: Any, get_client: Any) -> None:
    """Register all MCP prompts with the FastMCP server.

    This function registers both new prompts (following FastMCP 2.0+ patterns)
    and legacy prompts (migrated to FastMCP 2.0+) with the MCP server.

    Args:
        mcp: The FastMCP server instance
        get_client: Callable that returns the HomeAssistantClient instance

    Note:
        This function maintains backward compatibility with existing prompts
        while enabling new prompt modules to be added incrementally.

        All prompts use FastMCP 2.0+ patterns:
        - @mcp.prompt() decorator
        - Message and PromptResult types
        - Type-safe parameter validation
        - Comprehensive docstrings
    """
    # Import all registration functions
    from .automation import register_automation_prompts
    from .climate import register_climate_prompt
    from .control import register_control_prompts
    from .energy import register_energy_prompt
    from .explain import register_explain_prompts
    from .safety import register_safety_prompts
    from .scene import register_scene_prompt
    from .security import register_security_prompt
    from .status import register_status_prompts
    from .troubleshooting import register_troubleshooting_prompt

    # Register new prompt modules (designed with FastMCP 2.0+ from the start)
    register_control_prompts(mcp, get_client)
    register_explain_prompts(mcp, get_client)
    register_automation_prompts(mcp, get_client)
    register_status_prompts(mcp, get_client)
    register_safety_prompts(mcp, get_client)

    # Register legacy prompts (migrated to FastMCP 2.0+ patterns)
    register_climate_prompt(mcp, get_client)
    register_energy_prompt(mcp, get_client)
    register_scene_prompt(mcp, get_client)
    register_security_prompt(mcp, get_client)
    register_troubleshooting_prompt(mcp, get_client)
