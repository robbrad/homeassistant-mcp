"""Unit tests for safety prompts."""

import pytest
from unittest.mock import MagicMock

from fastmcp.prompts import PromptMessage
from homeassistant_mcp.prompts.safety import register_safety_prompts
from homeassistant_mcp.prompts.models import SENSITIVE_DOMAINS


@pytest.fixture
def mock_mcp():
    """Mock FastMCP instance for testing."""
    mcp = MagicMock()
    # Store registered prompts
    mcp._prompts = {}

    def prompt_decorator(**kwargs):
        def wrapper(func):
            mcp._prompts[func.__name__] = func
            return func

        return wrapper

    mcp.prompt = prompt_decorator
    return mcp


@pytest.fixture
def mock_client():
    """Mock HomeAssistantClient for testing."""
    # Safety prompts don't use the client, but we provide it for consistency
    return MagicMock()


@pytest.fixture
def get_client(mock_client):
    """Mock get_client callable."""
    return lambda: mock_client


class TestSafetyPolicyPrompt:
    """Tests for safety_policy prompt."""

    @pytest.mark.asyncio
    async def test_safety_policy_returns_complete_policy(self, mock_mcp, get_client):
        """Test that safety_policy returns a complete policy document."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        result = await safety_policy()

        # Verify result structure
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], PromptMessage)
        assert result[0].role == "assistant"

        content = result[0].content.text

        # Verify main sections are present
        assert "Home Assistant Safety Policy" in content
        assert "SENSITIVE DOMAINS" in content
        assert "QUIET HOURS" in content
        assert "READ-STATE-FIRST PRINCIPLE" in content
        assert "BULK ACTIONS" in content
        assert "EMERGENCY PROCEDURES" in content
        assert "ERROR HANDLING" in content
        assert "PRIVACY AND SECURITY" in content
        assert "BEST PRACTICES" in content

    @pytest.mark.asyncio
    async def test_safety_policy_lists_all_sensitive_domains(self, mock_mcp, get_client):
        """Test that all sensitive domains are listed in the policy."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        result = await safety_policy()
        content = result[0].content.text

        # Verify all sensitive domains are mentioned
        for domain in SENSITIVE_DOMAINS:
            assert domain in content, f"Sensitive domain '{domain}' not found in policy"

        # Verify specific domain descriptions
        assert "lock" in content.lower()
        assert "alarm_control_panel" in content or "alarm" in content.lower()
        assert "garage_door" in content or "garage" in content.lower()
        assert "camera" in content.lower()
        assert "cover" in content.lower()

    @pytest.mark.asyncio
    async def test_safety_policy_defines_quiet_hours(self, mock_mcp, get_client):
        """Test that quiet hours are clearly defined."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        result = await safety_policy()
        content = result[0].content.text

        # Verify quiet hours section exists
        assert "QUIET HOURS" in content

        # Verify time range is specified
        assert "10 PM" in content or "22:00" in content
        assert "7 AM" in content or "07:00" in content

        # Verify quiet hours guidance
        assert "noisy" in content.lower() or "disturb" in content.lower()
        assert "sleep" in content.lower()

        # Verify specific restrictions
        assert "media" in content.lower() or "volume" in content.lower()
        assert "notification" in content.lower() or "announcement" in content.lower()
        assert "brightness" in content.lower() or "light" in content.lower()

    @pytest.mark.asyncio
    async def test_safety_policy_explains_read_state_first(self, mock_mcp, get_client):
        """Test that read-state-first principle is explained."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        result = await safety_policy()
        content = result[0].content.text

        # Verify read-state-first section exists
        assert "READ-STATE-FIRST PRINCIPLE" in content

        # Verify key concepts
        assert "verify" in content.lower() or "check" in content.lower()
        assert "current state" in content.lower()
        assert "before" in content.lower()

        # Verify specific guidance
        assert "resources" in content.lower() or "hass://entity" in content
        assert "redundant" in content.lower() or "unnecessary" in content.lower()

    @pytest.mark.asyncio
    async def test_safety_policy_provides_bulk_action_guidelines(self, mock_mcp, get_client):
        """Test that bulk action guidelines are provided."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        result = await safety_policy()
        content = result[0].content.text

        # Verify bulk actions section exists
        assert "BULK ACTIONS" in content

        # Verify threshold is mentioned
        assert "3" in content or "entities" in content.lower()

        # Verify required steps
        assert "list" in content.lower() or "List ALL entities" in content
        assert "confirm" in content.lower()
        assert "current state" in content.lower()

        # Verify option to exclude entities
        assert "exclude" in content.lower() or "option" in content.lower()

    @pytest.mark.asyncio
    async def test_safety_policy_documents_emergency_procedures(self, mock_mcp, get_client):
        """Test that emergency procedures are documented."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        result = await safety_policy()
        content = result[0].content.text

        # Verify emergency section exists
        assert "EMERGENCY PROCEDURES" in content or "EMERGENCY" in content

        # Verify emergency keywords are listed
        assert "emergency" in content.lower()
        assert "urgent" in content.lower()
        assert "fire" in content.lower()

        # Verify emergency response guidance
        assert "911" in content or "emergency services" in content.lower()
        assert "life safety" in content.lower() or "safety first" in content.lower()

        # Verify specific emergency actions
        assert "lock" in content.lower() or "security" in content.lower()
        assert "light" in content.lower()

    @pytest.mark.asyncio
    async def test_safety_policy_includes_confirmation_requirements(self, mock_mcp, get_client):
        """Test that confirmation requirements are clearly stated."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        result = await safety_policy()
        content = result[0].content.text

        # Verify confirmation is required for sensitive domains
        sensitive_section = content[content.find("SENSITIVE DOMAINS"):content.find("QUIET HOURS")]

        assert "confirm" in sensitive_section.lower()
        assert "ALWAYS" in sensitive_section or "always" in sensitive_section.lower()
        assert "explicit" in sensitive_section.lower()

    @pytest.mark.asyncio
    async def test_safety_policy_includes_error_handling_guidance(self, mock_mcp, get_client):
        """Test that error handling guidance is included."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        result = await safety_policy()
        content = result[0].content.text

        # Verify error handling section
        assert "ERROR HANDLING" in content

        # Verify specific error scenarios
        assert "unavailable" in content.lower()
        assert "fail" in content.lower() or "failure" in content.lower()
        assert "connection" in content.lower()

        # Verify recovery guidance
        assert "troubleshoot" in content.lower() or "alternative" in content.lower()

    @pytest.mark.asyncio
    async def test_safety_policy_includes_privacy_guidance(self, mock_mcp, get_client):
        """Test that privacy and security guidance is included."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        result = await safety_policy()
        content = result[0].content.text

        # Verify privacy section
        assert "PRIVACY" in content

        # Verify camera privacy
        assert "camera" in content.lower()
        assert "permission" in content.lower() or "explicit" in content.lower()

        # Verify data protection
        assert "sensitive" in content.lower()
        assert "code" in content.lower() or "password" in content.lower()

    @pytest.mark.asyncio
    async def test_safety_policy_includes_best_practices(self, mock_mcp, get_client):
        """Test that best practices are included."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        result = await safety_policy()
        content = result[0].content.text

        # Verify best practices section
        assert "BEST PRACTICES" in content

        # Verify communication guidance
        assert "clear" in content.lower()
        assert "explain" in content.lower()

        # Verify efficiency guidance
        assert "batch" in content.lower() or "scene" in content.lower()
        assert "automation" in content.lower()

    @pytest.mark.asyncio
    async def test_safety_policy_structure_is_well_formatted(self, mock_mcp, get_client):
        """Test that the policy is well-formatted and readable."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        result = await safety_policy()
        content = result[0].content.text

        # Verify markdown formatting
        assert "**" in content  # Bold text
        assert "##" in content  # Headers
        assert "-" in content or "*" in content  # Lists

        # Verify numbered sections
        assert "1." in content
        assert "2." in content
        assert "3." in content

        # Verify the policy is substantial (not just a stub)
        assert len(content) > 2000, "Policy should be comprehensive"

    @pytest.mark.asyncio
    async def test_safety_policy_mentions_all_required_keywords(self, mock_mcp, get_client):
        """Test that all required safety keywords are present."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        result = await safety_policy()
        content = result[0].content.text.lower()

        # Required safety keywords
        required_keywords = [
            "confirm",
            "verify",
            "check",
            "state",
            "safe",
            "security",
            "emergency",
            "error",
            "privacy",
        ]

        for keyword in required_keywords:
            assert keyword in content, f"Required keyword '{keyword}' not found in policy"

    @pytest.mark.asyncio
    async def test_safety_policy_no_parameters_required(self, mock_mcp, get_client):
        """Test that safety_policy requires no parameters."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        # Should be callable with no arguments
        result = await safety_policy()

        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_safety_policy_is_deterministic(self, mock_mcp, get_client):
        """Test that safety_policy returns the same content on multiple calls."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        result1 = await safety_policy()
        result2 = await safety_policy()

        # Content should be identical
        assert result1[0].content.text == result2[0].content.text

    @pytest.mark.asyncio
    async def test_safety_policy_includes_threshold_value(self, mock_mcp, get_client):
        """Test that the bulk action threshold value is included."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        result = await safety_policy()
        content = result[0].content.text

        # Should mention the threshold value (3 entities)
        bulk_section = content[content.find("BULK ACTIONS"):content.find("EMERGENCY")]

        assert "3" in bulk_section
        assert "entities" in bulk_section.lower()

    @pytest.mark.asyncio
    async def test_safety_policy_covers_all_requirements(self, mock_mcp, get_client):
        """Test that the policy covers all requirements from the spec."""
        register_safety_prompts(mock_mcp, get_client)
        safety_policy = mock_mcp._prompts["safety_policy"]

        result = await safety_policy()
        content = result[0].content.text

        # Requirements 2.7, 5.4, 5.5, 5.6 coverage
        # 2.7: SafetyPolicy prompt with no required parameters ✓
        # 5.4: List all Sensitive_Domains requiring confirmation ✓
        assert all(domain in content for domain in SENSITIVE_DOMAINS)

        # 5.5: Define Quiet_Hours behavior ✓
        assert "10 PM" in content or "22:00" in content
        assert "7 AM" in content or "07:00" in content

        # 5.6: Include guidance to verify current state via resources ✓
        assert "resources" in content.lower() or "hass://entity" in content
        assert "verify" in content.lower() or "check" in content.lower()
        assert "current state" in content.lower()
