from __future__ import annotations

import pytest
from pathlib import Path
import tempfile

from core.tools.base import ToolContext
from tools.python_exec import PythonExecTool


class TestPythonExecTool:
    """Test Python execution tool."""

    @pytest.fixture
    def tool(self) -> PythonExecTool:
        return PythonExecTool()

    def test_execute_snippet_simple(self, tool: PythonExecTool) -> None:
        """Test executing a simple code snippet."""
        ctx = ToolContext(dry_run=False)
        result = tool.execute_snippet(
            {"code": "x = 1 + 1\nprint(x)"},
            ctx
        )
        assert result["status"] == "success"
        assert "2" in result["output"]

    def test_execute_snippet_with_error(self, tool: PythonExecTool) -> None:
        """Test executing code with error."""
        ctx = ToolContext(dry_run=False)
        result = tool.execute_snippet(
            {"code": "x = 1 / 0"},
            ctx
        )
        assert result["status"] == "error"
        assert "ZeroDivisionError" in result["error_type"]

    def test_execute_snippet_invalid_code_type(self, tool: PythonExecTool) -> None:
        """Test with invalid code type."""
        ctx = ToolContext(dry_run=False)
        with pytest.raises(ValueError, match="code must be string"):
            tool.execute_snippet({"code": 123}, ctx)

    def test_execute_snippet_dry_run(self, tool: PythonExecTool) -> None:
        """Test snippet execution in dry-run mode."""
        ctx = ToolContext(dry_run=True)
        result = tool.execute_snippet(
            {"code": "x = 1 + 1"},
            ctx
        )
        assert result["dry_run"] is True
        assert result["message"] == "Would execute code (dry-run mode)"

    def test_execute_script(self, tool: PythonExecTool) -> None:
        """Test executing a Python script."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello from script')\n")
            script_path = f.name

        try:
            ctx = ToolContext(dry_run=False)
            result = tool.execute_script(
                {"script": script_path, "timeout": 10},
                ctx
            )
            assert result["status"] == "success"
            assert "hello from script" in result["stdout"]
        finally:
            Path(script_path).unlink()

    def test_execute_script_nonexistent(self, tool: PythonExecTool) -> None:
        """Test executing nonexistent script."""
        with pytest.raises(ValueError, match="Script not found"):
            tool.execute_script({"script": "/nonexistent/script.py"}, ToolContext())

    def test_execute_script_dry_run(self, tool: PythonExecTool) -> None:
        """Test script execution in dry-run mode."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('test')\n")
            script_path = f.name

        try:
            ctx = ToolContext(dry_run=True)
            result = tool.execute_script({"script": script_path}, ctx)
            assert result["dry_run"] is True
        finally:
            Path(script_path).unlink()

    def test_execute_action_snippet(self, tool: PythonExecTool) -> None:
        """Test execute with snippet action."""
        ctx = ToolContext(dry_run=False)
        result = tool.execute(
            {"action": "snippet", "code": "x = 42\nprint(x)"},
            ctx
        )
        assert result["status"] == "success"
        assert "42" in result["output"]

    def test_execute_invalid_action(self, tool: PythonExecTool) -> None:
        """Test with invalid action."""
        ctx = ToolContext(dry_run=False)
        with pytest.raises(ValueError, match="Unknown exec action"):
            tool.execute({"action": "invalid_action"}, ctx)
