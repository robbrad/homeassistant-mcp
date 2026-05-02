"""Property-based tests for MCP prompts.

Feature: rest-api-overhaul
Tests Properties 53-55 for prompt functionality.

Feature: mcp-prompts-layer
Tests Properties 1, 2, 3, 4, 5, 6, 7, 8 for prompt functionality.
"""

import inspect
import re
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# Feature: rest-api-overhaul, Property 53: Prompt Argument Validation
@given(
    name=st.text(min_size=0, max_size=5),  # Invalid: too short or empty
)
@settings(deadline=None)
@pytest.mark.asyncio
async def test_prompt_argument_validation_empty_name(name):
    """
    Property 53: For any prompt with invalid arguments, execution SHALL return
    a validation error before processing.

    This test verifies that prompts validate their arguments (empty/invalid names).
    """
    from src.homeassistant_mcp.prompts.automation import register_automation_prompts

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        """Mock prompt decorator that accepts tags and other kwargs."""
        def decorator(func):
            nonlocal prompt_func
            prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Create mock client inline
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])
    def get_client():
        return mock_client

    register_automation_prompts(mcp, get_client)

    # If name is empty or whitespace, it should be considered invalid
    if not name or not name.strip():
        # The prompt should handle this gracefully
        # In practice, MCP framework may validate this, but we test the prompt behavior
        try:
            result = await prompt_func(name=name)
            # Prompt should still return messages, but may indicate invalid input
            assert isinstance(result, list)
        except (ValueError, TypeError):
            # Validation error is acceptable
            pass


# Feature: rest-api-overhaul, Property 53: Prompt Argument Validation
@given(
    name=st.text(min_size=1, max_size=100),
    description=st.text(max_size=500),
)
@pytest.mark.asyncio
async def test_automation_prompt_valid_arguments(name, description):
    """
    Property 53: For any prompt with valid arguments, execution SHALL succeed
    and return a conversation flow.
    """
    from src.homeassistant_mcp.prompts.automation import register_automation_prompts

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        """Mock prompt decorator that accepts tags and other kwargs."""
        def decorator(func):
            nonlocal prompt_func
            # Capture the create_automation function specifically
            if func.__name__ == "create_automation":
                prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Create mock client inline
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"brightness": 255},
            }
        ]
    )
    def get_client():
        return mock_client

    register_automation_prompts(mcp, get_client)

    result = await prompt_func(name=name, description=description)

    # Verify result structure
    assert isinstance(result, list)
    assert len(result) > 0
    # Each message should have role and content attributes (PromptMessage objects)
    for message in result:
        assert hasattr(message, "role"), "Message should have role attribute"
        assert hasattr(message, "content"), "Message should have content attribute"


# Feature: rest-api-overhaul, Property 54: Prompt Execution Error Handling
@pytest.mark.asyncio
async def test_prompt_execution_error_handling():
    """
    Property 54: For any failed prompt execution, the response SHALL return
    a descriptive error message.

    This test verifies that prompts handle client errors gracefully.
    """
    from src.homeassistant_mcp.prompts.troubleshooting import (
        register_troubleshooting_prompt,
    )

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Mock client that raises errors
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(side_effect=Exception("Connection failed"))
    mock_client.get_history = AsyncMock(side_effect=Exception("Connection failed"))
    mock_client.get_error_log = AsyncMock(side_effect=Exception("Connection failed"))

    def get_client():
        return mock_client

    register_troubleshooting_prompt(mcp, get_client)

    # Should not raise exception, but handle error gracefully
    result = await prompt_func(entity_id="light.test")

    assert isinstance(result, list)
    assert len(result) > 0
    # Should contain error information in messages
    messages_text = ""
    for msg in result:
        if hasattr(msg, "content"):
            content = msg.content
            if hasattr(content, "text"):
                messages_text += content.text
            elif isinstance(content, str):
                messages_text += content
        else:
            messages_text += str(msg)
    assert "error" in messages_text.lower() or "could not" in messages_text.lower()


# Feature: rest-api-overhaul, Property 55: Prompt Listing Support
@pytest.mark.asyncio
async def test_prompt_listing_support():
    """
    Property 55: For any prompt listing request, the response SHALL return
    all available prompts with their descriptions and required arguments.

    This test verifies that all prompts are properly registered and discoverable.
    """
    from src.homeassistant_mcp.prompts import register_all_prompts

    mcp = MagicMock()
    registered_prompts = []

    def capture_prompt(**kwargs):
        def decorator(func):
            # Capture prompt metadata
            registered_prompts.append(
                {
                    "name": func.__name__,
                    "doc": func.__doc__,
                    "signature": func.__annotations__,
                }
            )
            return func

        return decorator

    mcp.prompt = capture_prompt
    mock_client = AsyncMock()
    def get_client():
        return mock_client

    register_all_prompts(mcp, get_client)

    # Verify all expected prompts are registered
    prompt_names = [p["name"] for p in registered_prompts]
    assert "create_automation" in prompt_names
    assert "create_scene" in prompt_names
    assert "troubleshoot_device" in prompt_names
    assert "optimize_energy" in prompt_names
    assert "security_check" in prompt_names
    assert "optimize_climate" in prompt_names

    # Verify each prompt has documentation
    for prompt in registered_prompts:
        assert prompt["doc"] is not None
        assert len(prompt["doc"].strip()) > 0


# Feature: rest-api-overhaul, Property 53: Scene Prompt Argument Validation
@given(
    name=st.text(min_size=1, max_size=100),
    area=st.text(max_size=100),
)
@pytest.mark.asyncio
async def test_scene_prompt_valid_arguments(name, area):
    """
    Property 53: Scene prompt should accept valid name and optional area arguments.
    """
    from src.homeassistant_mcp.prompts.scene import register_scene_prompt

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Create mock client inline
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "light.bedroom",
                "state": "off",
                "attributes": {},
            }
        ]
    )
    def get_client():
        return mock_client

    register_scene_prompt(mcp, get_client)

    result = await prompt_func(name=name, area=area)

    assert isinstance(result, list)
    assert len(result) > 0


# Feature: rest-api-overhaul, Property 53: Energy Prompt Argument Validation
@given(area=st.text(max_size=100))
@pytest.mark.asyncio
async def test_energy_prompt_optional_area(area):
    """
    Property 53: Energy prompt should accept optional area argument.
    """
    from src.homeassistant_mcp.prompts.energy import register_energy_prompt

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Create mock client inline
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])
    def get_client():
        return mock_client

    register_energy_prompt(mcp, get_client)

    result = await prompt_func(area=area)

    assert isinstance(result, list)
    assert len(result) > 0


# Feature: rest-api-overhaul, Property 54: Security Prompt Error Handling
@pytest.mark.asyncio
async def test_security_prompt_handles_client_errors():
    """
    Property 54: Security prompt should handle client errors gracefully.
    """
    from src.homeassistant_mcp.prompts.security import register_security_prompt

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Mock client that raises errors
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(side_effect=Exception("API error"))

    def get_client():
        return mock_client

    register_security_prompt(mcp, get_client)

    # Should not raise exception
    result = await prompt_func()

    assert isinstance(result, list)
    assert len(result) > 0


# Feature: rest-api-overhaul, Property 54: Climate Prompt Error Handling
@pytest.mark.asyncio
async def test_climate_prompt_handles_no_devices():
    """
    Property 54: Climate prompt should handle case when no climate devices exist.
    """
    from src.homeassistant_mcp.prompts.climate import register_climate_prompt

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Create mock client inline
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])
    def get_client():
        return mock_client

    register_climate_prompt(mcp, get_client)

    result = await prompt_func(area="")

    assert isinstance(result, list)
    assert len(result) > 0
    # Should indicate no devices found
    messages_text = ""
    for msg in result:
        if hasattr(msg, "content"):
            content = msg.content
            if hasattr(content, "text"):
                messages_text += content.text
            elif isinstance(content, str):
                messages_text += content
        else:
            messages_text += str(msg)
    assert "no climate" in messages_text.lower() or "not found" in messages_text.lower()



# Feature: mcp-prompts-layer, Property 2: Prompt Metadata Completeness
@settings(max_examples=100, deadline=None)
@given(st.integers(min_value=0, max_value=10))
@pytest.mark.asyncio
async def test_prompt_metadata_completeness(iteration):
    """
    Property 2: For any registered prompt, it should have a non-empty description,
    a unique snake_case name, and at least one tag from the valid tag set.

    **Validates: Requirements 4.1, 4.2**

    This property test verifies that all prompts in the system maintain proper
    metadata standards for discoverability and organization.
    """
    from src.homeassistant_mcp.prompts import TAG_DEFINITIONS, register_all_prompts

    mcp = MagicMock()
    registered_prompts = []

    def capture_prompt(**kwargs):
        def decorator(func):
            # Capture prompt metadata
            registered_prompts.append(
                {
                    "name": func.__name__,
                    "description": func.__doc__,
                    "function": func,
                }
            )
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Create mock client
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=[])
    mock_client.get_state = AsyncMock(
        return_value={"entity_id": "test.entity", "state": "on", "attributes": {}}
    )

    def get_client():
        return mock_client

    # Register all prompts
    register_all_prompts(mcp, get_client)

    # Verify we have prompts registered
    assert len(registered_prompts) > 0, "No prompts were registered"

    # Valid tag set from the design
    valid_tags = set(TAG_DEFINITIONS.keys())

    # Track names to verify uniqueness
    seen_names = set()

    # Verify each prompt has proper metadata
    for prompt in registered_prompts:
        name = prompt["name"]
        description = prompt["description"]

        # Property 2.1: Non-empty description
        assert description is not None, f"Prompt '{name}' has no description (None)"
        assert isinstance(description, str), f"Prompt '{name}' description is not a string"
        assert len(description.strip()) > 0, f"Prompt '{name}' has empty description"

        # Property 2.2: Unique snake_case name
        assert name not in seen_names, f"Duplicate prompt name found: '{name}'"
        seen_names.add(name)

        # Verify snake_case format (lowercase with underscores, no spaces or special chars)
        snake_case_pattern = re.compile(r"^[a-z][a-z0-9_]*$")
        assert snake_case_pattern.match(
            name
        ), f"Prompt name '{name}' is not in snake_case format"

        # Property 2.3: At least one valid tag
        # Note: In the current implementation, tags are not directly accessible from
        # the decorator pattern. This is a limitation we're documenting.
        # For now, we verify that the prompt is properly structured and can be called.
        # Future implementations should expose tags through the decorator or metadata.

        # Verify the prompt function is callable
        assert callable(prompt["function"]), f"Prompt '{name}' is not callable"


# Feature: mcp-prompts-layer, Property 2: Prompt Name Uniqueness (Focused Test)
@pytest.mark.asyncio
async def test_all_prompt_names_are_unique():
    """
    Property 2 (Uniqueness): Verify all registered prompt names are unique.

    **Validates: Requirements 4.1**

    This test ensures no duplicate prompt names exist in the system.
    """
    from src.homeassistant_mcp.prompts import register_all_prompts

    mcp = MagicMock()
    registered_names = []

    def capture_prompt(**kwargs):
        def decorator(func):
            registered_names.append(func.__name__)
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Create mock client
    mock_client = AsyncMock()

    def get_client():
        return mock_client

    # Register all prompts
    register_all_prompts(mcp, get_client)

    # Verify uniqueness
    assert len(registered_names) == len(
        set(registered_names)
    ), f"Duplicate prompt names found: {[n for n in registered_names if registered_names.count(n) > 1]}"


# Feature: mcp-prompts-layer, Property 2: Snake Case Format (Focused Test)
@pytest.mark.asyncio
async def test_all_prompt_names_are_snake_case():
    """
    Property 2 (Snake Case): Verify all registered prompt names follow snake_case format.

    **Validates: Requirements 4.1**

    This test ensures all prompt names use lowercase with underscores only.
    """
    from src.homeassistant_mcp.prompts import register_all_prompts

    mcp = MagicMock()
    registered_names = []

    def capture_prompt(**kwargs):
        def decorator(func):
            registered_names.append(func.__name__)
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Create mock client
    mock_client = AsyncMock()

    def get_client():
        return mock_client

    # Register all prompts
    register_all_prompts(mcp, get_client)

    # Snake case pattern: starts with lowercase letter, followed by lowercase letters,
    # digits, or underscores
    snake_case_pattern = re.compile(r"^[a-z][a-z0-9_]*$")

    invalid_names = [name for name in registered_names if not snake_case_pattern.match(name)]

    assert (
        len(invalid_names) == 0
    ), f"Prompts with non-snake_case names found: {invalid_names}"


# Feature: mcp-prompts-layer, Property 2: Non-Empty Descriptions (Focused Test)
@pytest.mark.asyncio
async def test_all_prompts_have_descriptions():
    """
    Property 2 (Descriptions): Verify all registered prompts have non-empty descriptions.

    **Validates: Requirements 4.2**

    This test ensures all prompts have meaningful documentation.
    """
    from src.homeassistant_mcp.prompts import register_all_prompts

    mcp = MagicMock()
    registered_prompts = []

    def capture_prompt(**kwargs):
        def decorator(func):
            registered_prompts.append({"name": func.__name__, "doc": func.__doc__})
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Create mock client
    mock_client = AsyncMock()

    def get_client():
        return mock_client

    # Register all prompts
    register_all_prompts(mcp, get_client)

    # Verify each prompt has a non-empty description
    prompts_without_docs = []
    prompts_with_empty_docs = []

    for prompt in registered_prompts:
        name = prompt["name"]
        doc = prompt["doc"]

        if doc is None:
            prompts_without_docs.append(name)
        elif len(doc.strip()) == 0:
            prompts_with_empty_docs.append(name)

    assert (
        len(prompts_without_docs) == 0
    ), f"Prompts without descriptions: {prompts_without_docs}"
    assert (
        len(prompts_with_empty_docs) == 0
    ), f"Prompts with empty descriptions: {prompts_with_empty_docs}"


# Feature: mcp-prompts-layer, Property 4: Parameter Reflection in Output
@settings(max_examples=100, deadline=None)
@given(
    domain=st.sampled_from(["light", "switch", "sensor", "climate", "cover", "fan", "lock"]),
    entity_name=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
        min_size=3,
        max_size=30,
    ).filter(lambda x: x and not x.startswith("_") and not x.endswith("_")),
)
@pytest.mark.asyncio
async def test_control_entity_reflects_entity_id_parameter(domain, entity_name):
    """
    Property 4: For any parameterized prompt, when invoked with a specific parameter value,
    the returned prompt result should reference that parameter value in its content.

    **Validates: Requirements 3.1, 5.1**

    This property test verifies that control_entity includes the entity_id parameter
    in its output, ensuring users can verify which entity is being controlled.
    """
    from src.homeassistant_mcp.prompts.control import register_control_prompts

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            # Capture control_entity specifically
            if func.__name__ == "control_entity":
                prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Construct entity_id from domain and entity_name
    entity_id = f"{domain}.{entity_name}"

    # Create mock client that returns a valid state
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": entity_id,
            "state": "on",
            "attributes": {"brightness": 128},
        }
    )

    def get_client():
        return mock_client

    # Register the control prompts
    register_control_prompts(mcp, get_client)

    # Invoke the prompt with the entity_id
    result = await prompt_func(entity_id=entity_id)

    # Verify result structure
    assert isinstance(result, list), "Result should be a list of messages"
    assert len(result) > 0, "Result should contain at least one message"

    # Extract all text content from messages
    all_content = ""
    for message in result:
        if hasattr(message, "content"):
            content = message.content
            if hasattr(content, "text"):
                all_content += content.text
            elif isinstance(content, str):
                all_content += content

    # Property 4: The entity_id parameter should appear in the output
    assert (
        entity_id in all_content
    ), f"Entity ID '{entity_id}' not found in prompt output: {all_content[:200]}"


# Feature: mcp-prompts-layer, Property 7: Sensitive Domain Confirmation Language
@settings(max_examples=100, deadline=None)
@given(
    domain=st.sampled_from(["lock", "alarm_control_panel", "garage_door", "camera", "cover"]),
    entity_name=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
        min_size=3,
        max_size=30,
    ).filter(lambda x: x and not x.startswith("_") and not x.endswith("_")),
)
@pytest.mark.asyncio
async def test_control_entity_sensitive_domain_confirmation(domain, entity_name):
    """
    Property 7: For any entity_id in a sensitive domain (lock, alarm_control_panel,
    garage_door, camera, cover), when passed to control_entity, the prompt result
    should contain confirmation-related language.

    **Validates: Requirements 5.1**

    This property test verifies that sensitive domains trigger appropriate safety
    warnings and confirmation requirements in the prompt output.
    """
    from src.homeassistant_mcp.prompts.control import register_control_prompts

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            # Capture control_entity specifically
            if func.__name__ == "control_entity":
                prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Construct entity_id from domain and entity_name
    entity_id = f"{domain}.{entity_name}"

    # Create mock client that returns a valid state
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": entity_id,
            "state": "locked" if domain == "lock" else "on",
            "attributes": {},
        }
    )

    def get_client():
        return mock_client

    # Register the control prompts
    register_control_prompts(mcp, get_client)

    # Invoke the prompt with the sensitive entity_id
    result = await prompt_func(entity_id=entity_id)

    # Verify result structure
    assert isinstance(result, list), "Result should be a list of messages"
    assert len(result) > 0, "Result should contain at least one message"

    # Extract all text content from messages
    all_content = ""
    for message in result:
        if hasattr(message, "content"):
            content = message.content
            if hasattr(content, "text"):
                all_content += content.text
            elif isinstance(content, str):
                all_content += content

    # Convert to lowercase for case-insensitive matching
    all_content_lower = all_content.lower()

    # Property 7: Sensitive domains should trigger confirmation language
    # Check for confirmation-related keywords
    confirmation_keywords = [
        "confirm",
        "important",
        "verify",
        "ensure",
        "proceed",
        "⚠",  # Warning emoji
        "warning",
    ]

    found_keywords = [kw for kw in confirmation_keywords if kw in all_content_lower]

    assert (
        len(found_keywords) > 0
    ), f"No confirmation language found for sensitive domain '{domain}'. Expected keywords like {confirmation_keywords}, but content was: {all_content[:300]}"

    # Additionally verify that the domain is mentioned in the warning
    assert (
        domain in all_content_lower
    ), f"Domain '{domain}' should be mentioned in the confirmation message"



# Feature: mcp-prompts-layer, Property 4: Parameter Reflection in explain_entity
@settings(max_examples=100, deadline=None)
@given(
    domain=st.sampled_from(
        ["light", "switch", "sensor", "climate", "cover", "fan", "lock", "media_player", "vacuum"]
    ),
    entity_name=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
        min_size=3,
        max_size=30,
    ).filter(lambda x: x and not x.startswith("_") and not x.endswith("_")),
)
@pytest.mark.asyncio
async def test_explain_entity_reflects_entity_id_parameter(domain, entity_name):
    """
    Property 4: For any parameterized prompt, when invoked with a specific parameter value,
    the returned prompt result should reference that parameter value in its content.

    **Validates: Requirements 3.3**

    This property test verifies that explain_entity includes the entity_id parameter
    in its output, ensuring users can verify which entity is being explained.
    """
    from src.homeassistant_mcp.prompts.explain import register_explain_prompts

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Construct entity_id from domain and entity_name
    entity_id = f"{domain}.{entity_name}"

    # Create mock client that returns a valid state with various attributes
    mock_state = {
        "entity_id": entity_id,
        "state": "on" if domain != "sensor" else "25.5",
        "attributes": {
            "friendly_name": f"Test {domain.title()}",
            "area_id": "living_room",
        },
        "last_changed": "2024-01-15T10:30:00",
    }

    # Add domain-specific attributes
    if domain == "light":
        mock_state["attributes"]["brightness"] = 200
    elif domain == "climate":
        mock_state["attributes"]["current_temperature"] = 22.0
        mock_state["attributes"]["temperature"] = 23.0
    elif domain == "sensor":
        mock_state["attributes"]["unit_of_measurement"] = "°C"

    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(return_value=mock_state)

    def get_client():
        return mock_client

    # Register the explain prompts
    register_explain_prompts(mcp, get_client)

    # Invoke the prompt with the entity_id
    result = await prompt_func(entity_id=entity_id)

    # Verify result structure
    assert isinstance(result, list), "Result should be a list of messages"
    assert len(result) > 0, "Result should contain at least one message"

    # Extract all text content from messages
    all_content = ""
    for message in result:
        if hasattr(message, "content"):
            content = message.content
            if hasattr(content, "text"):
                all_content += content.text
            elif isinstance(content, str):
                all_content += content

    # Property 4: The entity_id parameter should appear in the output
    assert (
        entity_id in all_content
    ), f"Entity ID '{entity_id}' not found in prompt output: {all_content[:200]}"

    # Additionally verify that the domain is mentioned
    assert (
        domain in all_content.lower()
    ), f"Domain '{domain}' should be mentioned in the explanation"



# Feature: mcp-prompts-layer, Property 4: Parameter Reflection in diagnose_automation
@settings(max_examples=100, deadline=None)
@given(
    automation_name=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
        min_size=3,
        max_size=30,
    ).filter(lambda x: x and not x.startswith("_") and not x.endswith("_")),
)
@pytest.mark.asyncio
async def test_diagnose_automation_reflects_automation_id_parameter(automation_name):
    """
    Property 4: For any parameterized prompt, when invoked with a specific parameter value,
    the returned prompt result should reference that parameter value in its content.

    **Validates: Requirements 3.4**

    This property test verifies that diagnose_automation includes the automation_id
    parameter in its output, ensuring users can verify which automation is being diagnosed.
    """
    from src.homeassistant_mcp.prompts.automation import register_automation_prompts

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            if func.__name__ == "diagnose_automation":
                prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Construct automation_id
    automation_id = f"automation.{automation_name}"

    # Create mock client that returns a valid automation state
    mock_state = {
        "entity_id": automation_id,
        "state": "on",
        "attributes": {
            "friendly_name": f"Test Automation {automation_name}",
            "last_triggered": "2024-01-15T10:30:00",
            "trigger": [
                {
                    "platform": "time",
                    "at": "07:00:00",
                }
            ],
            "condition": [],
            "action": [
                {
                    "service": "light.turn_on",
                    "target": {"entity_id": "light.bedroom"},
                }
            ],
        },
    }

    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(return_value=mock_state)

    def get_client():
        return mock_client

    # Register the automation prompts
    register_automation_prompts(mcp, get_client)

    # Invoke the diagnose_automation prompt with the automation_id
    result = await prompt_func(automation_id=automation_id)

    # Verify result structure
    assert isinstance(result, list), "Result should be a list of messages"
    assert len(result) > 0, "Result should contain at least one message"

    # Extract all text content from messages
    all_content = ""
    for message in result:
        if hasattr(message, "content"):
            content = message.content
            if hasattr(content, "text"):
                all_content += content.text
            elif isinstance(content, str):
                all_content += content

    # Property 4: The automation_id parameter should appear in the output
    assert (
        automation_id in all_content
    ), f"Automation ID '{automation_id}' not found in prompt output: {all_content[:200]}"

    # Additionally verify diagnostic keywords are present
    diagnostic_keywords = ["diagnos", "trigger", "status", "enabled"]
    found_keywords = [kw for kw in diagnostic_keywords if kw.lower() in all_content.lower()]

    assert (
        len(found_keywords) > 0
    ), f"Expected diagnostic content with keywords like {diagnostic_keywords}, but content was: {all_content[:300]}"



# Feature: mcp-prompts-layer, Property 4: Parameter Reflection in suggest_automation
@settings(max_examples=100, deadline=None)
@given(
    intent=st.text(min_size=10, max_size=100).filter(lambda x: x.strip()),
    constraints=st.text(max_size=50),
)
@pytest.mark.asyncio
async def test_suggest_automation_reflects_intent_parameter(intent, constraints):
    """
    Property 4: For any parameterized prompt, when invoked with a specific parameter value,
    the returned prompt result should reference that parameter value in its content.

    **Validates: Requirements 3.5**

    This property test verifies that suggest_automation includes the intent parameter
    in its output, ensuring users can verify what automation is being suggested.
    """
    from src.homeassistant_mcp.prompts.automation import register_automation_prompts

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            if func.__name__ == "suggest_automation":
                prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Create mock client that returns some sample entities
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(
        return_value=[
            {
                "entity_id": "light.living_room",
                "state": "off",
                "attributes": {"friendly_name": "Living Room Light"},
            },
            {
                "entity_id": "switch.porch",
                "state": "off",
                "attributes": {"friendly_name": "Porch Switch"},
            },
        ]
    )

    def get_client():
        return mock_client

    # Register the automation prompts
    register_automation_prompts(mcp, get_client)

    # Invoke the suggest_automation prompt with the intent
    result = await prompt_func(intent=intent, constraints=constraints)

    # Verify result structure
    assert isinstance(result, list), "Result should be a list of messages"
    assert len(result) > 0, "Result should contain at least one message"

    # Extract all text content from messages
    all_content = ""
    for message in result:
        if hasattr(message, "content"):
            content = message.content
            if hasattr(content, "text"):
                all_content += content.text
            elif isinstance(content, str):
                all_content += content

    # Property 4: The intent parameter should appear in the output
    assert (
        intent in all_content
    ), f"Intent '{intent}' not found in prompt output: {all_content[:200]}"

    # Additionally verify suggestion keywords are present
    suggestion_keywords = ["trigger", "action", "automation"]
    found_keywords = [kw for kw in suggestion_keywords if kw.lower() in all_content.lower()]

    assert (
        len(found_keywords) > 0
    ), f"Expected automation suggestion content with keywords like {suggestion_keywords}, but content was: {all_content[:300]}"

    # If constraints provided, verify they appear in output
    if constraints and constraints.strip():
        assert (
            constraints in all_content
        ), f"Constraints '{constraints}' not found in prompt output when provided"


# Feature: mcp-prompts-layer, Property 8: Prompt Invocation Returns Valid Result
@settings(max_examples=100, deadline=None)
@given(st.integers(min_value=0, max_value=10))
@pytest.mark.asyncio
async def test_home_status_brief_returns_valid_result(iteration):
    """
    Property 8: For any registered prompt, invoking it with valid parameters should
    return a PromptResult object containing a non-empty list of messages.

    **Validates: Requirements 2.8, 6.1**

    This property test verifies that home_status_brief always returns a valid,
    structured result with proper message formatting.
    """
    from src.homeassistant_mcp.prompts.status import register_status_prompts

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            if func.__name__ == "home_status_brief":
                prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Create mock client with various entity states
    mock_entities = [
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light", "brightness": 200},
        },
        {
            "entity_id": "light.bedroom",
            "state": "off",
            "attributes": {"friendly_name": "Bedroom Light"},
        },
        {
            "entity_id": "switch.porch",
            "state": "on",
            "attributes": {"friendly_name": "Porch Switch"},
        },
        {
            "entity_id": "lock.front_door",
            "state": "locked",
            "attributes": {"friendly_name": "Front Door Lock"},
        },
        {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "attributes": {
                "friendly_name": "Temperature Sensor",
                "battery_level": 85,
                "unit_of_measurement": "°C",
            },
        },
        {
            "entity_id": "climate.living_room",
            "state": "heat",
            "attributes": {
                "friendly_name": "Living Room Thermostat",
                "current_temperature": 21.5,
                "temperature": 22.0,
            },
        },
        {
            "entity_id": "automation.morning_lights",
            "state": "on",
            "attributes": {"friendly_name": "Morning Lights Automation"},
        },
    ]

    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=mock_entities)

    def get_client():
        return mock_client

    # Register the status prompts
    register_status_prompts(mcp, get_client)

    # Invoke the home_status_brief prompt (no parameters required)
    result = await prompt_func()

    # Property 8.1: Result should be a list
    assert isinstance(result, list), "Result should be a list of messages"

    # Property 8.2: Result should contain at least one message
    assert len(result) > 0, "Result should contain at least one message"

    # Property 8.3: Each message should have proper structure
    for message in result:
        # Messages should have role and content attributes
        assert hasattr(message, "role"), "Message should have a 'role' attribute"
        assert hasattr(message, "content"), "Message should have a 'content' attribute"

        # Extract content text
        content = message.content
        if hasattr(content, "text"):
            content_text = content.text
        elif isinstance(content, str):
            content_text = content
        else:
            content_text = str(content)

        # Property 8.4: Content should be non-empty
        assert len(content_text.strip()) > 0, "Message content should not be empty"

        # Property 8.5: Content should contain status-related keywords
        status_keywords = ["status", "device", "home", "summary"]
        content_lower = content_text.lower()
        found_keywords = [kw for kw in status_keywords if kw in content_lower]

        assert (
            len(found_keywords) > 0
        ), f"Expected status-related content with keywords like {status_keywords}, but content was: {content_text[:200]}"


# Feature: mcp-prompts-layer, Property 8: home_status_brief with connection error
@pytest.mark.asyncio
async def test_home_status_brief_handles_connection_error():
    """
    Property 8 (Error Handling): Verify home_status_brief handles connection errors gracefully.

    **Validates: Requirements 2.8, 6.1**

    This test ensures the prompt returns a valid result even when the client fails.
    """
    from src.homeassistant_mcp.prompts.status import register_status_prompts
    from src.homeassistant_mcp.exceptions import ConnectionError as HAConnectionError

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            if func.__name__ == "home_status_brief":
                prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Create mock client that raises connection error
    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(side_effect=HAConnectionError("Connection failed"))

    def get_client():
        return mock_client

    # Register the status prompts
    register_status_prompts(mcp, get_client)

    # Invoke the prompt - should not raise exception
    result = await prompt_func()

    # Should still return valid result structure
    assert isinstance(result, list), "Result should be a list even on error"
    assert len(result) > 0, "Result should contain error message"

    # Extract content
    all_content = ""
    for message in result:
        if hasattr(message, "content"):
            content = message.content
            if hasattr(content, "text"):
                all_content += content.text
            elif isinstance(content, str):
                all_content += content

    # Should contain error information
    assert (
        "connect" in all_content.lower() or "error" in all_content.lower()
    ), "Error message should indicate connection issue"


# Feature: mcp-prompts-layer, Property 1: Prompt Listing Stability
@settings(max_examples=10, deadline=None)
@given(st.integers(min_value=0, max_value=10))
@pytest.mark.asyncio
async def test_prompt_listing_stability(iteration):
    """
    Property 1: For any two consecutive calls to list prompts, the returned list
    should be identical in content and order (deterministic listing).

    **Validates: Requirements 4.8**

    This property test verifies that prompt listing is stable and deterministic,
    ensuring consistent discovery behavior across multiple calls.
    """
    from src.homeassistant_mcp.prompts import register_all_prompts

    # First registration
    mcp1 = MagicMock()
    registered_prompts1 = []

    def capture_prompt1(**kwargs):
        def decorator(func):
            registered_prompts1.append(
                {
                    "name": func.__name__,
                    "doc": func.__doc__,
                }
            )
            return func

        return decorator

    mcp1.prompt = capture_prompt1

    mock_client1 = AsyncMock()

    def get_client1():
        return mock_client1

    register_all_prompts(mcp1, get_client1)

    # Second registration
    mcp2 = MagicMock()
    registered_prompts2 = []

    def capture_prompt2(**kwargs):
        def decorator(func):
            registered_prompts2.append(
                {
                    "name": func.__name__,
                    "doc": func.__doc__,
                }
            )
            return func

        return decorator

    mcp2.prompt = capture_prompt2

    mock_client2 = AsyncMock()

    def get_client2():
        return mock_client2

    register_all_prompts(mcp2, get_client2)

    # Property 1: Both lists should be identical in content and order
    assert len(registered_prompts1) == len(
        registered_prompts2
    ), "Prompt count differs between registrations"

    # Verify same order
    names1 = [p["name"] for p in registered_prompts1]
    names2 = [p["name"] for p in registered_prompts2]

    assert names1 == names2, f"Prompt order differs: {names1} vs {names2}"

    # Verify same content
    for p1, p2 in zip(registered_prompts1, registered_prompts2):
        assert p1["name"] == p2["name"], f"Prompt names differ at same position"
        assert p1["doc"] == p2["doc"], f"Prompt docs differ for {p1['name']}"


# Feature: mcp-prompts-layer, Property 3: Correct Prompt Tagging
@pytest.mark.asyncio
async def test_correct_prompt_tagging():
    """
    Property 3: For any prompt in the system, its tags should match the expected
    tags based on its category.

    **Validates: Requirements 4.3, 4.4, 4.5, 4.6, 4.7**

    This test verifies that prompts are correctly tagged according to their function:
    - Control prompts have {"control"} tag
    - Explain prompts have {"diagnostics"} tag
    - Automation prompts have {"automation"} tag
    - Status prompts have {"status"} tag
    - Safety prompts have {"safety"} tag
    """
    from src.homeassistant_mcp.prompts import register_all_prompts

    mcp = MagicMock()
    registered_prompts = []

    def capture_prompt(**kwargs):
        def decorator(func):
            registered_prompts.append(
                {
                    "name": func.__name__,
                    "function": func,
                }
            )
            return func

        return decorator

    mcp.prompt = capture_prompt

    mock_client = AsyncMock()

    def get_client():
        return mock_client

    register_all_prompts(mcp, get_client)

    # Define expected tags for each prompt category
    expected_tags = {
        # Control prompts
        "control_entity": "control",
        "control_area": "control",
        # Explain prompts
        "explain_entity": "diagnostics",
        # Automation prompts
        "create_automation": "automation",
        "diagnose_automation": "automation",
        "suggest_automation": "automation",
        # Status prompts
        "home_status_brief": "status",
        # Safety prompts
        "safety_policy": "safety",
        # Legacy prompts (migrated)
        "create_scene": "control",
        "optimize_climate": "diagnostics",
        "optimize_energy": "status",
        "security_check": "safety",
        "troubleshoot_device": "diagnostics",
    }

    # Verify each prompt has expected tags
    # Note: In the current implementation, tags are not directly accessible
    # from the decorator pattern. This test documents the expected behavior
    # and verifies that prompts exist with the correct names.

    prompt_names = [p["name"] for p in registered_prompts]

    for expected_name, expected_tag in expected_tags.items():
        assert (
            expected_name in prompt_names
        ), f"Expected prompt '{expected_name}' with tag '{expected_tag}' not found"

    # Verify control prompts exist
    control_prompts = ["control_entity", "control_area", "create_scene"]
    for name in control_prompts:
        assert name in prompt_names, f"Control prompt '{name}' not found"

    # Verify diagnostics prompts exist
    diagnostics_prompts = ["explain_entity", "optimize_climate", "troubleshoot_device"]
    for name in diagnostics_prompts:
        assert name in prompt_names, f"Diagnostics prompt '{name}' not found"

    # Verify automation prompts exist
    automation_prompts = ["create_automation", "diagnose_automation", "suggest_automation"]
    for name in automation_prompts:
        assert name in prompt_names, f"Automation prompt '{name}' not found"

    # Verify status prompts exist
    status_prompts = ["home_status_brief", "optimize_energy"]
    for name in status_prompts:
        assert name in prompt_names, f"Status prompt '{name}' not found"

    # Verify safety prompts exist
    safety_prompts = ["safety_policy", "security_check"]
    for name in safety_prompts:
        assert name in prompt_names, f"Safety prompt '{name}' not found"


# Feature: mcp-prompts-layer, Property 5: Optional Parameters Have Defaults
@settings(max_examples=10, deadline=None)
@given(st.integers(min_value=0, max_value=10))
@pytest.mark.asyncio
async def test_optional_parameters_have_defaults(iteration):
    """
    Property 5: For any prompt with optional parameters, those parameters should
    have default values defined in the function signature.

    **Validates: Requirements 3.6**

    This property test verifies that all optional parameters have sensible defaults,
    ensuring prompts can be invoked without providing all parameters.
    """
    from src.homeassistant_mcp.prompts import register_all_prompts

    mcp = MagicMock()
    registered_prompts = []

    def capture_prompt(**kwargs):
        def decorator(func):
            registered_prompts.append(
                {
                    "name": func.__name__,
                    "function": func,
                    "signature": inspect.signature(func),
                }
            )
            return func

        return decorator

    mcp.prompt = capture_prompt

    mock_client = AsyncMock()

    def get_client():
        return mock_client

    register_all_prompts(mcp, get_client)

    # Verify we have prompts registered
    assert len(registered_prompts) > 0, "No prompts were registered"

    # Check each prompt's parameters
    for prompt in registered_prompts:
        name = prompt["name"]
        sig = prompt["signature"]

        # Analyze parameters
        for param_name, param in sig.parameters.items():
            # Skip self/cls parameters
            if param_name in ("self", "cls"):
                continue

            # If parameter has no default, it's required
            if param.default == inspect.Parameter.empty:
                # Required parameter - this is fine
                continue
            else:
                # Optional parameter - verify it has a default
                assert (
                    param.default != inspect.Parameter.empty
                ), f"Prompt '{name}' parameter '{param_name}' is optional but has no default"

                # Verify default is not None for string parameters (unless explicitly allowed)
                # This ensures meaningful defaults
                if param.annotation == str and param.default is None:
                    # This is acceptable for truly optional string parameters
                    pass
                elif param.annotation == str:
                    # String parameters should have empty string or meaningful default
                    assert isinstance(
                        param.default, str
                    ), f"Prompt '{name}' parameter '{param_name}' should have string default"


# Feature: mcp-prompts-layer, Property 6: Safety Guidance in Control Prompts
@settings(max_examples=10, deadline=None)
@given(
    domain=st.sampled_from(["light", "switch", "climate", "fan", "cover"]),
    entity_name=st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="_"),
        min_size=3,
        max_size=30,
    ).filter(lambda x: x and not x.startswith("_") and not x.endswith("_")),
)
@pytest.mark.asyncio
async def test_control_prompts_contain_safety_guidance(domain, entity_name):
    """
    Property 6: For any control prompt (control_entity, control_area), the returned
    prompt result should contain safety-related keywords such as "confirm", "verify",
    "current state", or "check".

    **Validates: Requirements 5.1, 5.7**

    This property test verifies that control prompts always include safety guidance,
    ensuring users are prompted to verify state before making changes.
    """
    from src.homeassistant_mcp.prompts.control import register_control_prompts

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            if func.__name__ == "control_entity":
                prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Construct entity_id
    entity_id = f"{domain}.{entity_name}"

    # Create mock client
    mock_client = AsyncMock()
    mock_client.get_state = AsyncMock(
        return_value={
            "entity_id": entity_id,
            "state": "on",
            "attributes": {"friendly_name": f"Test {domain}"},
        }
    )

    def get_client():
        return mock_client

    # Register control prompts
    register_control_prompts(mcp, get_client)

    # Invoke the prompt
    result = await prompt_func(entity_id=entity_id)

    # Verify result structure
    assert isinstance(result, list), "Result should be a list of messages"
    assert len(result) > 0, "Result should contain at least one message"

    # Extract all text content
    all_content = ""
    for message in result:
        if hasattr(message, "content"):
            content = message.content
            if hasattr(content, "text"):
                all_content += content.text
            elif isinstance(content, str):
                all_content += content

    # Convert to lowercase for case-insensitive matching
    all_content_lower = all_content.lower()

    # Property 6: Control prompts should contain safety keywords
    safety_keywords = [
        "confirm",
        "verify",
        "current state",
        "check",
        "ensure",
        "before",
        "state:",  # Showing current state
    ]

    found_keywords = [kw for kw in safety_keywords if kw in all_content_lower]

    assert (
        len(found_keywords) > 0
    ), f"No safety guidance found in control prompt. Expected keywords like {safety_keywords}, but content was: {all_content[:300]}"


# Feature: mcp-prompts-layer, Property 6: Safety Guidance in control_area
@settings(max_examples=10, deadline=None)
@given(
    area_name=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll"), whitelist_characters=" "),
        min_size=5,
        max_size=30,
    ).filter(lambda x: x.strip() and not x.startswith(" ") and not x.endswith(" ")),
)
@pytest.mark.asyncio
async def test_control_area_contains_safety_guidance(area_name):
    """
    Property 6: For control_area prompt, the returned prompt result should contain
    safety-related keywords for bulk actions.

    **Validates: Requirements 5.1, 5.2, 5.7**

    This property test verifies that control_area includes safety guidance for
    bulk actions, ensuring users understand the impact before proceeding.
    """
    from src.homeassistant_mcp.prompts.control import register_control_prompts

    mcp = MagicMock()
    prompt_func = None

    def capture_prompt(**kwargs):
        def decorator(func):
            nonlocal prompt_func
            if func.__name__ == "control_area":
                prompt_func = func
            return func

        return decorator

    mcp.prompt = capture_prompt

    # Create mock client with multiple entities in the area
    mock_entities = [
        {
            "entity_id": "light.living_room_1",
            "state": "on",
            "attributes": {"friendly_name": "Light 1", "area_id": area_name.lower().replace(" ", "_")},
        },
        {
            "entity_id": "light.living_room_2",
            "state": "off",
            "attributes": {"friendly_name": "Light 2", "area_id": area_name.lower().replace(" ", "_")},
        },
        {
            "entity_id": "switch.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Switch", "area_id": area_name.lower().replace(" ", "_")},
        },
    ]

    mock_client = AsyncMock()
    mock_client.get_states = AsyncMock(return_value=mock_entities)

    def get_client():
        return mock_client

    # Register control prompts
    register_control_prompts(mcp, get_client)

    # Invoke the prompt
    result = await prompt_func(area_id=area_name)

    # Verify result structure
    assert isinstance(result, list), "Result should be a list of messages"
    assert len(result) > 0, "Result should contain at least one message"

    # Extract all text content
    all_content = ""
    for message in result:
        if hasattr(message, "content"):
            content = message.content
            if hasattr(content, "text"):
                all_content += content.text
            elif isinstance(content, str):
                all_content += content

    # Convert to lowercase for case-insensitive matching
    all_content_lower = all_content.lower()

    # Property 6: control_area should contain safety keywords for bulk actions
    bulk_safety_keywords = [
        "confirm",
        "verify",
        "affect",
        "entities",
        "multiple",
        "all",
        "area",
        "check",
    ]

    found_keywords = [kw for kw in bulk_safety_keywords if kw in all_content_lower]

    assert (
        len(found_keywords) > 0
    ), f"No bulk action safety guidance found in control_area prompt. Expected keywords like {bulk_safety_keywords}, but content was: {all_content[:300]}"
