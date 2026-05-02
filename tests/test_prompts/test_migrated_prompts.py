"""Tests for migrated legacy prompts (climate, energy, scene, security, troubleshooting)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastmcp.prompts import PromptMessage


@pytest.fixture
def mock_mcp():
    """Mock FastMCP instance."""
    mcp = MagicMock()
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
    """Mock HomeAssistantClient."""
    client = AsyncMock()
    return client


@pytest.fixture
def get_client(mock_client):
    """Mock get_client function."""
    return lambda: mock_client


class TestMigratedPrompts:
    """Tests for all migrated legacy prompts."""

    @pytest.mark.asyncio
    async def test_climate_prompt_returns_list_of_prompt_messages(
        self, mock_mcp, mock_client, get_client
    ):
        """Test climate prompt returns list of PromptMessage."""
        from homeassistant_mcp.prompts.climate import register_climate_prompt

        mock_client.get_states.return_value = []

        register_climate_prompt(mock_mcp, get_client)
        optimize_climate = mock_mcp._prompts["optimize_climate"]

        result = await optimize_climate()

        assert isinstance(result, list)
        assert all(isinstance(msg, PromptMessage) for msg in result)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_energy_prompt_returns_list_of_prompt_messages(
        self, mock_mcp, mock_client, get_client
    ):
        """Test energy prompt returns list of PromptMessage."""
        from homeassistant_mcp.prompts.energy import register_energy_prompt

        mock_client.get_states.return_value = []

        register_energy_prompt(mock_mcp, get_client)
        optimize_energy = mock_mcp._prompts["optimize_energy"]

        result = await optimize_energy()

        assert isinstance(result, list)
        assert all(isinstance(msg, PromptMessage) for msg in result)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_scene_prompt_returns_list_of_prompt_messages(
        self, mock_mcp, mock_client, get_client
    ):
        """Test scene prompt returns list of PromptMessage."""
        from homeassistant_mcp.prompts.scene import register_scene_prompt

        mock_client.get_states.return_value = []

        register_scene_prompt(mock_mcp, get_client)
        create_scene = mock_mcp._prompts["create_scene"]

        result = await create_scene(name="Test Scene")

        assert isinstance(result, list)
        assert all(isinstance(msg, PromptMessage) for msg in result)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_security_prompt_returns_list_of_prompt_messages(
        self, mock_mcp, mock_client, get_client
    ):
        """Test security prompt returns list of PromptMessage."""
        from homeassistant_mcp.prompts.security import register_security_prompt

        mock_client.get_states.return_value = []

        register_security_prompt(mock_mcp, get_client)
        security_check = mock_mcp._prompts["security_check"]

        result = await security_check()

        assert isinstance(result, list)
        assert all(isinstance(msg, PromptMessage) for msg in result)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_troubleshooting_prompt_returns_list_of_prompt_messages(
        self, mock_mcp, mock_client, get_client
    ):
        """Test troubleshooting prompt returns list of PromptMessage."""
        from homeassistant_mcp.prompts.troubleshooting import register_troubleshooting_prompt

        mock_client.get_state.return_value = {
            "entity_id": "light.test",
            "state": "on",
            "last_changed": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
            "attributes": {},
        }
        mock_client.get_history.return_value = [[]]
        mock_client.get_error_log.return_value = ""

        register_troubleshooting_prompt(mock_mcp, get_client)
        troubleshoot_device = mock_mcp._prompts["troubleshoot_device"]

        result = await troubleshoot_device(entity_id="light.test")

        assert isinstance(result, list)
        assert all(isinstance(msg, PromptMessage) for msg in result)
        assert len(result) > 0


class TestMigrationCompleteness:
    """Tests to verify migration was complete and no breaking changes."""

    def test_climate_uses_correct_imports(self):
        """Verify climate.py uses PromptMessage and TextContent."""
        with open("src/homeassistant_mcp/prompts/climate.py", "r", encoding="utf-8") as f:
            content = f.read()
            assert "from fastmcp.prompts import PromptMessage" in content
            assert "from mcp.types import TextContent" in content
            assert "-> list[PromptMessage]:" in content

    def test_energy_uses_correct_imports(self):
        """Verify energy.py uses PromptMessage and TextContent."""
        with open("src/homeassistant_mcp/prompts/energy.py", "r", encoding="utf-8") as f:
            content = f.read()
            assert "from fastmcp.prompts import PromptMessage" in content
            assert "from mcp.types import TextContent" in content
            assert "-> list[PromptMessage]:" in content

    def test_scene_uses_correct_imports(self):
        """Verify scene.py uses PromptMessage and TextContent."""
        with open("src/homeassistant_mcp/prompts/scene.py", "r", encoding="utf-8") as f:
            content = f.read()
            assert "from fastmcp.prompts import PromptMessage" in content
            assert "from mcp.types import TextContent" in content
            assert "-> list[PromptMessage]:" in content

    def test_security_uses_correct_imports(self):
        """Verify security.py uses PromptMessage and TextContent."""
        with open("src/homeassistant_mcp/prompts/security.py", "r", encoding="utf-8") as f:
            content = f.read()
            assert "from fastmcp.prompts import PromptMessage" in content
            assert "from mcp.types import TextContent" in content
            assert "-> list[PromptMessage]:" in content

    def test_troubleshooting_uses_correct_imports(self):
        """Verify troubleshooting.py uses PromptMessage and TextContent."""
        with open("src/homeassistant_mcp/prompts/troubleshooting.py", "r", encoding="utf-8") as f:
            content = f.read()
            assert "from fastmcp.prompts import PromptMessage" in content
            assert "from mcp.types import TextContent" in content
            assert "-> list[PromptMessage]:" in content

    def test_all_prompts_have_tags(self):
        """Verify all migrated prompts have appropriate tags."""
        test_cases = [
            ("src/homeassistant_mcp/prompts/climate.py", "diagnostics"),
            ("src/homeassistant_mcp/prompts/energy.py", "status"),
            ("src/homeassistant_mcp/prompts/scene.py", "control"),
            ("src/homeassistant_mcp/prompts/security.py", "safety"),
            ("src/homeassistant_mcp/prompts/troubleshooting.py", "diagnostics"),
        ]

        for file_path, expected_tag in test_cases:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert f'tags={{"{expected_tag}"' in content or f"tags={{{expected_tag}" in content

    def test_climate_has_safety_guidance(self):
        """Verify climate prompt includes safety guidance."""
        with open("src/homeassistant_mcp/prompts/climate.py", "r", encoding="utf-8") as f:
            content = f.read()
            assert "Safety" in content

    def test_scene_has_safety_guidance(self):
        """Verify scene prompt includes safety guidance."""
        with open("src/homeassistant_mcp/prompts/scene.py", "r", encoding="utf-8") as f:
            content = f.read()
            assert "Safety" in content

    def test_security_has_enhanced_warnings(self):
        """Verify security prompt has enhanced safety warnings."""
        with open("src/homeassistant_mcp/prompts/security.py", "r", encoding="utf-8") as f:
            content = f.read()
            assert "CRITICAL" in content
            assert "Emergency" in content or "ALWAYS" in content
