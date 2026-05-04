"""Property-based tests for template rendering functionality.

Feature: rest-api-overhaul
Properties: 25, 26, 27, 28
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from homeassistant_mcp.exceptions import ServiceCallError
from homeassistant_mcp.tools.specialized.template import register_template_tool

# Strategies for generating test data
simple_template_strategy = st.text(
    min_size=1,
    max_size=200,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=" .,!?"),
)

entity_id_strategy = st.from_regex(r"^[a-z_]+\.[a-z0-9_]+$", fullmatch=True)

state_value_strategy = st.one_of(
    st.text(min_size=1, max_size=20),
    st.integers(min_value=0, max_value=100).map(str),
    st.sampled_from(["on", "off", "unavailable", "unknown"]),
)


def create_mock_mcp():
    """Create a mock MCP server."""
    mcp = MagicMock()
    registered_tool = None

    def tool_decorator(**kwargs):
        def decorator(func):
            nonlocal registered_tool
            registered_tool = func
            return func

        return decorator

    mcp.tool = tool_decorator
    mcp.get_registered_tool = lambda: registered_tool
    return mcp


def create_mock_client():
    """Create a mock HomeAssistantClient."""
    return AsyncMock()


def create_get_client(mock_client):
    """Create a get_client function."""
    return lambda: mock_client


# Feature: rest-api-overhaul, Property 25: Template Rendering Success
@given(
    template=st.one_of(
        simple_template_strategy,
        st.just("{{ 1 + 1 }}"),
        st.just("{{ now().year }}"),
        st.just("Hello World"),
    ),
    expected_output=st.text(max_size=500),
)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_25_template_rendering_success(template, expected_output):
    """
    Property 25: For any valid template string, rendering SHALL return
    the evaluated output.

    Validates: Requirements 10.1
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock to return expected output
    mock_client.render_template = AsyncMock(return_value=expected_output)

    # Register tool
    register_template_tool(mock_mcp, get_client)
    template_render = mock_mcp.get_registered_tool()

    # Test template rendering
    result = await template_render(template=template)

    assert result["success"] is True
    assert "result" in result
    assert result["result"] == expected_output
    assert result["template"] == template

    # Verify client was called with correct template
    mock_client.render_template.assert_called_once_with(template)


# Feature: rest-api-overhaul, Property 26: Template Syntax Error Handling
@given(
    invalid_template=st.one_of(
        st.just("{{ unclosed"),
        st.just("{% if without endif %}"),
        st.just("{{ invalid | unknown_filter }}"),
        st.just("{% for x in %}"),
        st.from_regex(r"\{\{[^}]*$", fullmatch=True),  # Unclosed braces
    ),
    error_message=st.text(min_size=10, max_size=200),
)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_26_template_syntax_error_handling(invalid_template, error_message):
    """
    Property 26: For any template with invalid syntax, rendering SHALL
    return a template error message.

    Validates: Requirements 10.2
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Setup mock to raise ServiceCallError for syntax errors
    mock_client.render_template = AsyncMock(side_effect=ServiceCallError(error_message))

    # Register tool
    register_template_tool(mock_mcp, get_client)
    template_render = mock_mcp.get_registered_tool()

    # Test error handling
    result = await template_render(template=invalid_template)

    assert result["success"] is False
    assert "error" in result
    assert "error_type" in result
    assert result["template"] == invalid_template
    assert error_message in result["error"]
    assert result["error_type"] == "ServiceCallError"


# Feature: rest-api-overhaul, Property 27: Template Entity State Access
@given(entity_id=entity_id_strategy, state_value=state_value_strategy)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_27_template_entity_state_access(entity_id, state_value):
    """
    Property 27: For any template referencing an existing entity, rendering
    SHALL use the current entity state in evaluation.

    Validates: Requirements 10.3
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Create template that references the entity
    template = f"{{{{ states('{entity_id}') }}}}"

    # Setup mock to return the state value
    mock_client.render_template = AsyncMock(return_value=state_value)

    # Register tool
    register_template_tool(mock_mcp, get_client)
    template_render = mock_mcp.get_registered_tool()

    # Test template rendering with entity reference
    result = await template_render(template=template)

    assert result["success"] is True
    assert result["result"] == state_value

    # Verify the template was passed to the client
    mock_client.render_template.assert_called_once_with(template)


# Feature: rest-api-overhaul, Property 28: Template Unavailable Entity Handling
@given(
    entity_id=entity_id_strategy,
    error_handling=st.sampled_from(["unavailable", "unknown", "none", "error"]),
)
@settings(
    max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_property_28_template_unavailable_entity_handling(entity_id, error_handling):
    """
    Property 28: For any template referencing an unavailable entity, rendering
    SHALL handle the error gracefully without crashing.

    Validates: Requirements 10.4
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Create template that references unavailable entity
    template = f"{{{{ states('{entity_id}') }}}}"

    if error_handling == "error":
        # Setup mock to raise an error
        error_msg = f"Entity {entity_id} is unavailable"
        mock_client.render_template = AsyncMock(side_effect=ServiceCallError(error_msg))

        # Register tool
        register_template_tool(mock_mcp, get_client)
        template_render = mock_mcp.get_registered_tool()

        # Test error handling
        result = await template_render(template=template)

        assert result["success"] is False
        assert "error" in result
        assert result["template"] == template
    else:
        # Setup mock to return a graceful value (unavailable, unknown, none)
        mock_client.render_template = AsyncMock(return_value=error_handling)

        # Register tool
        register_template_tool(mock_mcp, get_client)
        template_render = mock_mcp.get_registered_tool()

        # Test graceful handling
        result = await template_render(template=template)

        # Should succeed with a graceful value
        assert result["success"] is True
        assert result["result"] == error_handling


# Additional test: Complex template with multiple entities
@given(
    entity_ids=st.lists(entity_id_strategy, min_size=1, max_size=5), output=st.text(max_size=500)
)
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_complex_template_with_multiple_entities(entity_ids, output):
    """
    Test that templates can reference multiple entities and produce
    complex output.
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Create template with multiple entity references
    entity_refs = " ".join([f"{{{{ states('{eid}') }}}}" for eid in entity_ids])
    template = f"States: {entity_refs}"

    # Setup mock
    mock_client.render_template = AsyncMock(return_value=output)

    # Register tool
    register_template_tool(mock_mcp, get_client)
    template_render = mock_mcp.get_registered_tool()

    # Test rendering
    result = await template_render(template=template)

    assert result["success"] is True
    assert result["result"] == output
    mock_client.render_template.assert_called_once_with(template)


# Additional test: Template with conditional logic
@given(
    condition=st.booleans(),
    true_value=st.text(min_size=1, max_size=50),
    false_value=st.text(min_size=1, max_size=50),
)
@settings(
    max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@pytest.mark.asyncio
async def test_template_with_conditional_logic(condition, true_value, false_value):
    """
    Test that templates with conditional logic are handled correctly.
    """
    # Create mocks
    mock_mcp = create_mock_mcp()
    mock_client = create_mock_client()
    get_client = create_get_client(mock_client)

    # Create conditional template
    template = (
        f"{{% if {str(condition).lower()} %}}{true_value}{{% else %}}{false_value}{{% endif %}}"
    )
    expected = true_value if condition else false_value

    # Setup mock
    mock_client.render_template = AsyncMock(return_value=expected)

    # Register tool
    register_template_tool(mock_mcp, get_client)
    template_render = mock_mcp.get_registered_tool()

    # Test rendering
    result = await template_render(template=template)

    assert result["success"] is True
    assert result["result"] == expected
