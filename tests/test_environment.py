from __future__ import annotations

import pytest
import sys
import os
import platform

from core.tools.base import ToolContext
from tools.environment import EnvironmentTool


class TestEnvironmentTool:
    """Test environment tool."""

    @pytest.fixture
    def tool(self) -> EnvironmentTool:
        return EnvironmentTool()

    def test_get_info(self, tool: EnvironmentTool) -> None:
        """Test getting system info."""
        result = tool.get_info()
        assert "system" in result
        assert "machine" in result
        assert "hostname" in result
        assert result["system"] in ["Windows", "Linux", "Darwin"]

    def test_python_info(self, tool: EnvironmentTool) -> None:
        """Test getting Python info."""
        result = tool.get_python_info()
        assert "version" in result
        assert "implementation" in result
        assert "executable" in result
        assert result["version"] == platform.python_version()

    def test_env_var(self, tool: EnvironmentTool) -> None:
        """Test getting environment variable."""
        os.environ["TEST_VAR"] = "test_value"
        result = tool.get_env_var({"name": "TEST_VAR"})
        assert result["exists"] is True
        assert result["value"] == "test_value"

    def test_env_var_nonexistent(self, tool: EnvironmentTool) -> None:
        """Test getting nonexistent environment variable."""
        result = tool.get_env_var({"name": "NONEXISTENT_VAR_12345"})
        assert result["exists"] is False
        assert result["value"] is None

    def test_env_var_invalid_type(self, tool: EnvironmentTool) -> None:
        """Test with invalid name type."""
        with pytest.raises(ValueError, match="name must be string"):
            tool.get_env_var({"name": 123})

    def test_all_env_vars(self, tool: EnvironmentTool) -> None:
        """Test getting all environment variables."""
        result = tool.get_all_env_vars()
        assert "count" in result
        assert "vars" in result
        assert result["count"] > 0

    def test_execute_info(self, tool: EnvironmentTool) -> None:
        """Test execute with info action."""
        ctx = ToolContext(dry_run=False)
        result = tool.execute({"action": "info"}, ctx)
        assert "system" in result

    def test_execute_python_info(self, tool: EnvironmentTool) -> None:
        """Test execute with python_info action."""
        ctx = ToolContext(dry_run=False)
        result = tool.execute({"action": "python_info"}, ctx)
        assert "version" in result

    def test_execute_invalid_action(self, tool: EnvironmentTool) -> None:
        """Test with invalid action."""
        ctx = ToolContext(dry_run=False)
        with pytest.raises(ValueError, match="Unknown environment action"):
            tool.execute({"action": "invalid_action"}, ctx)
