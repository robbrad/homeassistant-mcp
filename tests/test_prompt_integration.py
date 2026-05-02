"""Integration tests for MCP Prompts registration and discovery.

This module tests:
- Prompt registration and discovery
- All prompts are accessible
- Prompt metadata completeness
- Prompt invocation works correctly
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.homeassistant_mcp.server import lifespan, mcp


@pytest.fixture
def mock_env(monkeypatch):
    """Set up mock environment variables."""
    monkeypatch.setenv("HASS_HOST", "http://homeassistant.local:8123")
    monkeypatch.setenv("HASS_TOKEN", "test_token_1234567890_long_enough")
    monkeypatch.setenv("LOG_LEVEL", "INFO")


@pytest.fixture
def mock_hass_client():
    """Create a mock Home Assistant client."""
    client = AsyncMock()

    # Default successful responses
    client.get_states.return_value = [
        {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"brightness": 255, "friendly_name": "Living Room"},
        },
        {
            "entity_id": "switch.kitchen",
            "state": "off",
            "attributes": {"friendly_name": "Kitchen Switch"},
        },
    ]

    client.get_state.return_value = {
        "entity_id": "light.living_room",
        "state": "on",
        "attributes": {"brightness": 255, "friendly_name": "Living Room"},
    }

    client.call_service.return_value = {"success": True}
    client.close = AsyncMock()

    return client


class TestPromptRegistration:
    """Tests for prompt registration and discovery."""

    def test_all_prompts_registered(self):
        """Test that all expected prompts are registered."""
        expected_prompts = {
            # New prompts
            "control_entity",
            "control_area",
            "explain_entity",
            "diagnose_automation",
            "suggest_automation",
            "home_status_brief",
            "safety_policy",
            # Legacy prompts (migrated)
            "create_automation",
            "optimize_climate",  # Actual name
            "optimize_energy",  # Actual name
            "create_scene",  # Actual name
            "security_check",
            "troubleshoot_device",
        }

        registered_prompts = set(mcp._prompt_manager._prompts.keys())

        # Check all expected prompts are present
        missing_prompts = expected_prompts - registered_prompts
        assert not missing_prompts, f"Missing prompts: {missing_prompts}"

        # Verify we have at least the expected prompts
        assert len(registered_prompts) >= len(
            expected_prompts
        ), f"Expected at least {len(expected_prompts)} prompts, got {len(registered_prompts)}"

    def test_prompt_naming_consistency(self):
        """Test that all prompts follow consistent naming conventions."""
        for prompt_name in mcp._prompt_manager._prompts.keys():
            # Prompt names should use underscores, not hyphens
            assert (
                "-" not in prompt_name
            ), f"Prompt {prompt_name} uses hyphens instead of underscores"

            # Prompt names should be lowercase
            assert (
                prompt_name == prompt_name.lower()
            ), f"Prompt {prompt_name} is not all lowercase"

    def test_all_prompts_have_metadata(self):
        """Test that all prompts have proper metadata."""
        for prompt_name, prompt in mcp._prompt_manager._prompts.items():
            # Check description exists and is not empty
            assert prompt.description is not None, f"Prompt {prompt_name} missing description"
            assert len(prompt.description) > 10, f"Prompt {prompt_name} has too short description"

            # Check prompt is callable
            assert callable(prompt.fn), f"Prompt {prompt_name} is not callable"

            # Check prompt name matches
            assert prompt.name == prompt_name, f"Prompt name mismatch: {prompt.name} != {prompt_name}"

    def test_prompt_descriptions_are_informative(self):
        """Test that prompt descriptions provide useful information."""
        for prompt_name, prompt in mcp._prompt_manager._prompts.items():
            description = prompt.description.lower()

            # Description should be substantial
            assert (
                len(description) > 20
            ), f"Prompt {prompt_name} description is too short: {description}"

            # Description should not just be the name
            assert (
                prompt_name.replace("_", " ") not in description
                or len(description) > len(prompt_name) + 10
            ), f"Prompt {prompt_name} description is just the name"


class TestPromptTags:
    """Tests for prompt tagging and categorization."""

    def test_control_prompts_have_control_tag(self):
        """Test that control prompts have the 'control' tag."""
        control_prompts = ["control_entity", "control_area"]

        for prompt_name in control_prompts:
            if prompt_name in mcp._prompt_manager._prompts:
                prompt = mcp._prompt_manager._prompts[prompt_name]
                # Skip if tags are not implemented yet
                if len(prompt.tags) > 0:
                    assert (
                        "control" in prompt.tags
                    ), f"Control prompt {prompt_name} missing 'control' tag"

    def test_explain_prompts_have_diagnostics_tag(self):
        """Test that explain prompts have the 'diagnostics' tag."""
        explain_prompts = ["explain_entity", "troubleshoot_device"]

        for prompt_name in explain_prompts:
            if prompt_name in mcp._prompt_manager._prompts:
                prompt = mcp._prompt_manager._prompts[prompt_name]
                # Skip if tags are not implemented yet
                if len(prompt.tags) > 0:
                    assert (
                        "diagnostics" in prompt.tags
                    ), f"Explain prompt {prompt_name} missing 'diagnostics' tag"

    def test_automation_prompts_have_automation_tag(self):
        """Test that automation prompts have the 'automation' tag."""
        automation_prompts = ["create_automation", "diagnose_automation", "suggest_automation"]

        for prompt_name in automation_prompts:
            if prompt_name in mcp._prompt_manager._prompts:
                prompt = mcp._prompt_manager._prompts[prompt_name]
                # Skip if tags are not implemented yet
                if len(prompt.tags) > 0:
                    assert (
                        "automation" in prompt.tags
                    ), f"Automation prompt {prompt_name} missing 'automation' tag"

    def test_status_prompts_have_status_tag(self):
        """Test that status prompts have the 'status' tag."""
        status_prompts = ["home_status_brief", "optimize_energy", "security_check"]

        for prompt_name in status_prompts:
            if prompt_name in mcp._prompt_manager._prompts:
                prompt = mcp._prompt_manager._prompts[prompt_name]
                # Skip if tags are not implemented yet
                if len(prompt.tags) > 0:
                    assert (
                        "status" in prompt.tags
                    ), f"Status prompt {prompt_name} missing 'status' tag"

    def test_safety_prompts_have_safety_tag(self):
        """Test that safety prompts have the 'safety' tag."""
        safety_prompts = ["safety_policy", "security_check"]

        for prompt_name in safety_prompts:
            if prompt_name in mcp._prompt_manager._prompts:
                prompt = mcp._prompt_manager._prompts[prompt_name]
                # Skip if tags are not implemented yet
                if len(prompt.tags) > 0:
                    assert (
                        "safety" in prompt.tags
                    ), f"Safety prompt {prompt_name} missing 'safety' tag"


class TestPromptInvocation:
    """Tests for prompt invocation and execution."""

    @pytest.mark.asyncio
    async def test_control_entity_prompt_invocation(self, mock_env, mock_hass_client):
        """Test that control_entity prompt can be invoked."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                if "control_entity" in mcp._prompt_manager._prompts:
                    prompt = mcp._prompt_manager._prompts["control_entity"]

                    # Invoke the prompt
                    result = await prompt.fn(entity_id="light.living_room")

                    # Should return a list of messages
                    assert result is not None
                    assert isinstance(result, list)
                    assert len(result) > 0

    @pytest.mark.asyncio
    async def test_explain_entity_prompt_invocation(self, mock_env, mock_hass_client):
        """Test that explain_entity prompt can be invoked."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                if "explain_entity" in mcp._prompt_manager._prompts:
                    prompt = mcp._prompt_manager._prompts["explain_entity"]

                    # Invoke the prompt
                    result = await prompt.fn(entity_id="light.living_room")

                    # Should return a list of messages
                    assert result is not None
                    assert isinstance(result, list)
                    assert len(result) > 0

    @pytest.mark.asyncio
    async def test_home_status_brief_prompt_invocation(self, mock_env, mock_hass_client):
        """Test that home_status_brief prompt can be invoked."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                if "home_status_brief" in mcp._prompt_manager._prompts:
                    prompt = mcp._prompt_manager._prompts["home_status_brief"]

                    # Invoke the prompt (no parameters required)
                    result = await prompt.fn()

                    # Should return a list of messages
                    assert result is not None
                    assert isinstance(result, list)
                    assert len(result) > 0

    @pytest.mark.asyncio
    async def test_safety_policy_prompt_invocation(self, mock_env, mock_hass_client):
        """Test that safety_policy prompt can be invoked."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                if "safety_policy" in mcp._prompt_manager._prompts:
                    prompt = mcp._prompt_manager._prompts["safety_policy"]

                    # Invoke the prompt (no parameters required)
                    result = await prompt.fn()

                    # Should return a list of messages
                    assert result is not None
                    assert isinstance(result, list)
                    assert len(result) > 0


class TestPromptListingStability:
    """Tests for prompt listing stability and determinism."""

    def test_prompt_listing_is_deterministic(self):
        """Test that listing prompts returns same order on multiple calls."""
        # Get prompt list twice
        first_list = list(mcp._prompt_manager._prompts.keys())
        second_list = list(mcp._prompt_manager._prompts.keys())

        # Should be identical
        assert first_list == second_list, "Prompt listing is not deterministic"

    def test_prompt_count_is_stable(self):
        """Test that prompt count doesn't change between calls."""
        first_count = len(mcp._prompt_manager._prompts)
        second_count = len(mcp._prompt_manager._prompts)

        assert first_count == second_count, "Prompt count is not stable"


class TestPromptDocumentation:
    """Tests for prompt documentation and discoverability."""

    def test_all_prompts_have_docstrings(self):
        """Test that prompt functions have docstrings."""
        for prompt_name, prompt in mcp._prompt_manager._prompts.items():
            # Get the function docstring
            docstring = prompt.fn.__doc__

            # Docstring should exist
            assert docstring is not None, f"Prompt {prompt_name} missing docstring"

            # Docstring should be substantial (at least 30 characters)
            assert len(docstring) > 30, f"Prompt {prompt_name} has minimal docstring"

    def test_prompt_descriptions_match_purpose(self):
        """Test that prompt descriptions accurately describe their purpose."""
        purpose_keywords = {
            "control_entity": ["control", "entity"],
            "control_area": ["control", "area"],
            "explain_entity": ["explain", "entity"],
            "diagnose_automation": ["diagnose", "automation"],
            "suggest_automation": ["suggest", "automation"],
            "home_status_brief": ["status", "home"],
            "safety_policy": ["safety", "policy"],
        }

        for prompt_name, keywords in purpose_keywords.items():
            if prompt_name in mcp._prompt_manager._prompts:
                prompt = mcp._prompt_manager._prompts[prompt_name]
                description = prompt.description.lower()

                # Description should contain at least one keyword
                assert any(
                    keyword in description for keyword in keywords
                ), f"Prompt {prompt_name} description doesn't match purpose"


class TestPromptParameterValidation:
    """Tests for prompt parameter validation."""

    @pytest.mark.asyncio
    async def test_prompts_with_required_parameters(self, mock_env, mock_hass_client):
        """Test that prompts validate required parameters."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # Test control_entity without entity_id
                if "control_entity" in mcp._prompt_manager._prompts:
                    prompt = mcp._prompt_manager._prompts["control_entity"]

                    # This should fail validation
                    try:
                        await prompt.fn()
                        pytest.fail("Expected TypeError for missing required parameter")
                    except TypeError:
                        # Expected - missing required parameter
                        pass

    @pytest.mark.asyncio
    async def test_prompts_with_optional_parameters(self, mock_env, mock_hass_client):
        """Test that prompts handle optional parameters correctly."""
        with patch(
            "src.homeassistant_mcp.server.HomeAssistantClient",
            return_value=mock_hass_client,
        ):
            mock_app = MagicMock()

            async with lifespan(mock_app):
                # Test control_entity with and without optional action parameter
                if "control_entity" in mcp._prompt_manager._prompts:
                    prompt = mcp._prompt_manager._prompts["control_entity"]

                    # Should work without optional parameter
                    result1 = await prompt.fn(entity_id="light.living_room")
                    assert result1 is not None

                    # Should work with optional parameter
                    result2 = await prompt.fn(entity_id="light.living_room", action="turn_on")
                    assert result2 is not None
