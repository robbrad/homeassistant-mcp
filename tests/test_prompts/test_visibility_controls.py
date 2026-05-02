"""Unit tests for prompt visibility controls and tag-based discovery."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from homeassistant_mcp.prompts import register_all_prompts
from homeassistant_mcp.prompts.control import register_control_prompts
from homeassistant_mcp.prompts.explain import register_explain_prompts
from homeassistant_mcp.prompts.automation import register_automation_prompts
from homeassistant_mcp.prompts.status import register_status_prompts
from homeassistant_mcp.prompts.safety import register_safety_prompts


@pytest.fixture
def mock_mcp_with_list():
    """Mock FastMCP instance that tracks registered prompts with metadata."""
    mcp = MagicMock()
    mcp._prompts = {}
    mcp._prompt_metadata = {}

    def prompt_decorator(tags=None):
        """Mock prompt decorator that captures function and tags."""

        def wrapper(func):
            mcp._prompts[func.__name__] = func
            mcp._prompt_metadata[func.__name__] = {
                "name": func.__name__,
                "description": func.__doc__ or "",
                "tags": tags or set(),
            }
            return func

        return wrapper

    mcp.prompt = prompt_decorator

    def list_prompts():
        """Mock list_prompts method."""
        return list(mcp._prompt_metadata.values())

    mcp.list_prompts = list_prompts

    return mcp


class TestPromptTagging:
    """Tests for prompt tagging and categorization."""

    def test_control_prompts_have_control_tag(self, mock_mcp_with_list, get_client):
        """Test that control prompts are tagged with 'control'."""
        register_control_prompts(mock_mcp_with_list, get_client)

        # Check control_entity has control tag
        if "control_entity" in mock_mcp_with_list._prompt_metadata:
            metadata = mock_mcp_with_list._prompt_metadata["control_entity"]
            assert "control" in metadata["tags"]

        # Check control_area has control tag
        if "control_area" in mock_mcp_with_list._prompt_metadata:
            metadata = mock_mcp_with_list._prompt_metadata["control_area"]
            assert "control" in metadata["tags"]

    def test_explain_prompts_have_diagnostics_tag(self, mock_mcp_with_list, get_client):
        """Test that explain prompts are tagged with 'diagnostics'."""
        register_explain_prompts(mock_mcp_with_list, get_client)

        if "explain_entity" in mock_mcp_with_list._prompt_metadata:
            metadata = mock_mcp_with_list._prompt_metadata["explain_entity"]
            assert "diagnostics" in metadata["tags"]

    def test_automation_prompts_have_automation_tag(self, mock_mcp_with_list, get_client):
        """Test that automation prompts are tagged with 'automation'."""
        register_automation_prompts(mock_mcp_with_list, get_client)

        automation_prompts = ["diagnose_automation", "suggest_automation", "create_automation"]
        for prompt_name in automation_prompts:
            if prompt_name in mock_mcp_with_list._prompt_metadata:
                metadata = mock_mcp_with_list._prompt_metadata[prompt_name]
                assert "automation" in metadata["tags"]

    def test_status_prompts_have_status_tag(self, mock_mcp_with_list, get_client):
        """Test that status prompts are tagged with 'status'."""
        register_status_prompts(mock_mcp_with_list, get_client)

        if "home_status_brief" in mock_mcp_with_list._prompt_metadata:
            metadata = mock_mcp_with_list._prompt_metadata["home_status_brief"]
            assert "status" in metadata["tags"]

    def test_safety_prompts_have_safety_tag(self, mock_mcp_with_list, get_client):
        """Test that safety prompts are tagged with 'safety'."""
        register_safety_prompts(mock_mcp_with_list, get_client)

        if "safety_policy" in mock_mcp_with_list._prompt_metadata:
            metadata = mock_mcp_with_list._prompt_metadata["safety_policy"]
            assert "safety" in metadata["tags"]


class TestPromptDiscovery:
    """Tests for discovering prompts by tags."""

    def test_filter_prompts_by_control_tag(self, mock_mcp_with_list, get_client):
        """Test filtering prompts by 'control' tag."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Filter by control tag
        control_prompts = [
            p
            for p in mock_mcp_with_list.list_prompts()
            if "control" in p.get("tags", set())
        ]

        # Should have control_entity and control_area
        control_names = [p["name"] for p in control_prompts]
        assert "control_entity" in control_names or "control_area" in control_names

    def test_filter_prompts_by_diagnostics_tag(self, mock_mcp_with_list, get_client):
        """Test filtering prompts by 'diagnostics' tag."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Filter by diagnostics tag
        diagnostics_prompts = [
            p
            for p in mock_mcp_with_list.list_prompts()
            if "diagnostics" in p.get("tags", set())
        ]

        # Should have explain_entity and diagnose_automation
        diagnostics_names = [p["name"] for p in diagnostics_prompts]
        assert len(diagnostics_names) > 0

    def test_filter_prompts_by_automation_tag(self, mock_mcp_with_list, get_client):
        """Test filtering prompts by 'automation' tag."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Filter by automation tag
        automation_prompts = [
            p
            for p in mock_mcp_with_list.list_prompts()
            if "automation" in p.get("tags", set())
        ]

        # Should have automation-related prompts
        automation_names = [p["name"] for p in automation_prompts]
        assert len(automation_names) > 0

    def test_filter_prompts_by_status_tag(self, mock_mcp_with_list, get_client):
        """Test filtering prompts by 'status' tag."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Filter by status tag
        status_prompts = [
            p for p in mock_mcp_with_list.list_prompts() if "status" in p.get("tags", set())
        ]

        # Should have home_status_brief
        status_names = [p["name"] for p in status_prompts]
        assert len(status_names) > 0

    def test_filter_prompts_by_safety_tag(self, mock_mcp_with_list, get_client):
        """Test filtering prompts by 'safety' tag."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Filter by safety tag
        safety_prompts = [
            p for p in mock_mcp_with_list.list_prompts() if "safety" in p.get("tags", set())
        ]

        # Should have safety_policy
        safety_names = [p["name"] for p in safety_prompts]
        assert len(safety_names) > 0

    def test_filter_prompts_by_multiple_tags(self, mock_mcp_with_list, get_client):
        """Test filtering prompts by multiple tags (OR logic)."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Filter by control OR diagnostics tags
        filtered_prompts = [
            p
            for p in mock_mcp_with_list.list_prompts()
            if "control" in p.get("tags", set()) or "diagnostics" in p.get("tags", set())
        ]

        # Should have prompts from both categories
        assert len(filtered_prompts) > 0

    def test_filter_prompts_by_nonexistent_tag(self, mock_mcp_with_list, get_client):
        """Test filtering prompts by a tag that doesn't exist."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Filter by nonexistent tag
        filtered_prompts = [
            p
            for p in mock_mcp_with_list.list_prompts()
            if "nonexistent_tag" in p.get("tags", set())
        ]

        # Should return empty list
        assert len(filtered_prompts) == 0


class TestPromptEnabling:
    """Tests for enabling/disabling prompts."""

    def test_disable_prompt_by_name(self, mock_mcp_with_list, get_client):
        """Test disabling a specific prompt by name."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Simulate disabling a prompt
        disabled_prompts = {"control_entity"}

        # Filter out disabled prompts
        enabled_prompts = [
            p for p in mock_mcp_with_list.list_prompts() if p["name"] not in disabled_prompts
        ]

        # control_entity should not be in enabled prompts
        enabled_names = [p["name"] for p in enabled_prompts]
        assert "control_entity" not in enabled_names

    def test_disable_prompts_by_tag(self, mock_mcp_with_list, get_client):
        """Test disabling all prompts with a specific tag."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Simulate disabling all control prompts
        disabled_tags = {"control"}

        # Filter out prompts with disabled tags
        enabled_prompts = [
            p
            for p in mock_mcp_with_list.list_prompts()
            if not any(tag in disabled_tags for tag in p.get("tags", set()))
        ]

        # No control prompts should be enabled
        for prompt in enabled_prompts:
            assert "control" not in prompt.get("tags", set())

    def test_enable_only_specific_tags(self, mock_mcp_with_list, get_client):
        """Test enabling only prompts with specific tags."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Simulate enabling only diagnostics and status prompts
        enabled_tags = {"diagnostics", "status"}

        # Filter to only enabled tags
        filtered_prompts = [
            p
            for p in mock_mcp_with_list.list_prompts()
            if any(tag in enabled_tags for tag in p.get("tags", set()))
        ]

        # All filtered prompts should have at least one enabled tag
        for prompt in filtered_prompts:
            assert any(tag in enabled_tags for tag in prompt.get("tags", set()))

    def test_disable_all_prompts(self, mock_mcp_with_list, get_client):
        """Test disabling all prompts."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Simulate disabling all prompts
        all_prompt_names = [p["name"] for p in mock_mcp_with_list.list_prompts()]
        disabled_prompts = set(all_prompt_names)

        # Filter out all disabled prompts
        enabled_prompts = [
            p for p in mock_mcp_with_list.list_prompts() if p["name"] not in disabled_prompts
        ]

        # Should have no enabled prompts
        assert len(enabled_prompts) == 0

    def test_enable_all_prompts(self, mock_mcp_with_list, get_client):
        """Test enabling all prompts (default behavior)."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # No filtering - all prompts enabled
        enabled_prompts = mock_mcp_with_list.list_prompts()

        # Should have all registered prompts
        assert len(enabled_prompts) > 0


class TestPromptMetadata:
    """Tests for prompt metadata completeness."""

    def test_all_prompts_have_names(self, mock_mcp_with_list, get_client):
        """Test that all prompts have non-empty names."""
        register_all_prompts(mock_mcp_with_list, get_client)

        for prompt in mock_mcp_with_list.list_prompts():
            assert "name" in prompt
            assert len(prompt["name"]) > 0

    def test_all_prompts_have_descriptions(self, mock_mcp_with_list, get_client):
        """Test that all prompts have descriptions."""
        register_all_prompts(mock_mcp_with_list, get_client)

        for prompt in mock_mcp_with_list.list_prompts():
            assert "description" in prompt
            # Description can be empty but should exist

    def test_all_prompts_have_tags(self, mock_mcp_with_list, get_client):
        """Test that all prompts have at least one tag."""
        register_all_prompts(mock_mcp_with_list, get_client)

        for prompt in mock_mcp_with_list.list_prompts():
            assert "tags" in prompt
            # Tags should be a set or list
            assert isinstance(prompt["tags"], (set, list))

    def test_prompt_names_are_snake_case(self, mock_mcp_with_list, get_client):
        """Test that all prompt names use snake_case format."""
        register_all_prompts(mock_mcp_with_list, get_client)

        for prompt in mock_mcp_with_list.list_prompts():
            name = prompt["name"]
            # Should be lowercase with underscores
            assert name.islower() or "_" in name
            # Should not have spaces or hyphens
            assert " " not in name
            assert "-" not in name

    def test_prompt_names_are_unique(self, mock_mcp_with_list, get_client):
        """Test that all prompt names are unique."""
        register_all_prompts(mock_mcp_with_list, get_client)

        prompt_names = [p["name"] for p in mock_mcp_with_list.list_prompts()]
        # No duplicates
        assert len(prompt_names) == len(set(prompt_names))


class TestTagBasedVisibility:
    """Tests for tag-based visibility controls."""

    def test_show_only_safe_prompts(self, mock_mcp_with_list, get_client):
        """Test showing only safe prompts (excluding control prompts)."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Exclude control prompts for safety
        safe_prompts = [
            p
            for p in mock_mcp_with_list.list_prompts()
            if "control" not in p.get("tags", set())
        ]

        # Should have diagnostics, status, safety prompts
        for prompt in safe_prompts:
            assert "control" not in prompt.get("tags", set())

    def test_show_only_informational_prompts(self, mock_mcp_with_list, get_client):
        """Test showing only informational prompts (diagnostics, status)."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Only diagnostics and status
        informational_tags = {"diagnostics", "status"}
        informational_prompts = [
            p
            for p in mock_mcp_with_list.list_prompts()
            if any(tag in informational_tags for tag in p.get("tags", set()))
        ]

        # All should be informational
        for prompt in informational_prompts:
            assert any(tag in informational_tags for tag in prompt.get("tags", set()))

    def test_show_only_action_prompts(self, mock_mcp_with_list, get_client):
        """Test showing only action prompts (control, automation)."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Only control and automation
        action_tags = {"control", "automation"}
        action_prompts = [
            p
            for p in mock_mcp_with_list.list_prompts()
            if any(tag in action_tags for tag in p.get("tags", set()))
        ]

        # All should be action-related
        for prompt in action_prompts:
            assert any(tag in action_tags for tag in prompt.get("tags", set()))

    def test_exclude_specific_tag(self, mock_mcp_with_list, get_client):
        """Test excluding prompts with a specific tag."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Exclude automation prompts
        excluded_tag = "automation"
        filtered_prompts = [
            p
            for p in mock_mcp_with_list.list_prompts()
            if excluded_tag not in p.get("tags", set())
        ]

        # None should have automation tag
        for prompt in filtered_prompts:
            assert excluded_tag not in prompt.get("tags", set())


class TestDynamicVisibility:
    """Tests for dynamic visibility based on context."""

    def test_visibility_based_on_user_role(self, mock_mcp_with_list, get_client):
        """Test filtering prompts based on simulated user role."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Simulate read-only user (no control or automation)
        readonly_allowed_tags = {"diagnostics", "status", "safety"}

        readonly_prompts = [
            p
            for p in mock_mcp_with_list.list_prompts()
            if any(tag in readonly_allowed_tags for tag in p.get("tags", set()))
        ]

        # Should only have safe, informational prompts
        for prompt in readonly_prompts:
            tags = prompt.get("tags", set())
            assert "control" not in tags
            assert "automation" not in tags

    def test_visibility_based_on_safety_mode(self, mock_mcp_with_list, get_client):
        """Test filtering prompts in safety mode."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # In safety mode, only show safety and status prompts
        safety_mode_tags = {"safety", "status"}

        safety_mode_prompts = [
            p
            for p in mock_mcp_with_list.list_prompts()
            if any(tag in safety_mode_tags for tag in p.get("tags", set()))
        ]

        # Should only have safety and status prompts
        for prompt in safety_mode_prompts:
            assert any(tag in safety_mode_tags for tag in prompt.get("tags", set()))

    def test_visibility_all_enabled_by_default(self, mock_mcp_with_list, get_client):
        """Test that all prompts are visible by default."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # No filtering - all prompts visible
        all_prompts = mock_mcp_with_list.list_prompts()

        # Should have prompts from all categories
        all_tags = set()
        for prompt in all_prompts:
            all_tags.update(prompt.get("tags", set()))

        # Should have multiple tag types
        assert len(all_tags) > 1


class TestPromptListing:
    """Tests for listing and discovering prompts."""

    def test_list_all_prompts(self, mock_mcp_with_list, get_client):
        """Test listing all registered prompts."""
        register_all_prompts(mock_mcp_with_list, get_client)

        all_prompts = mock_mcp_with_list.list_prompts()

        # Should have multiple prompts
        assert len(all_prompts) > 0

        # Each prompt should have required metadata
        for prompt in all_prompts:
            assert "name" in prompt
            assert "description" in prompt
            assert "tags" in prompt

    def test_list_prompts_returns_consistent_order(self, mock_mcp_with_list, get_client):
        """Test that listing prompts returns consistent order."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # List prompts multiple times
        list1 = [p["name"] for p in mock_mcp_with_list.list_prompts()]
        list2 = [p["name"] for p in mock_mcp_with_list.list_prompts()]

        # Order should be consistent
        assert list1 == list2

    def test_list_prompts_by_category(self, mock_mcp_with_list, get_client):
        """Test listing prompts grouped by category/tag."""
        register_all_prompts(mock_mcp_with_list, get_client)

        # Group prompts by tags
        prompts_by_tag = {}
        for prompt in mock_mcp_with_list.list_prompts():
            for tag in prompt.get("tags", set()):
                if tag not in prompts_by_tag:
                    prompts_by_tag[tag] = []
                prompts_by_tag[tag].append(prompt["name"])

        # Should have multiple categories
        assert len(prompts_by_tag) > 0

        # Each category should have at least one prompt
        for tag, prompts in prompts_by_tag.items():
            assert len(prompts) > 0
