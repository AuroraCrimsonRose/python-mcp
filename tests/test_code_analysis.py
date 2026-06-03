from __future__ import annotations

import pytest
from pathlib import Path
import tempfile

from core.tools.base import ToolContext
from tools.code_analysis import CodeAnalysisTool


class TestCodeAnalysisTool:
    """Test code analysis tool."""

    @pytest.fixture
    def tool(self) -> CodeAnalysisTool:
        return CodeAnalysisTool()

    @pytest.fixture
    def sample_py_file(self) -> Path:
        """Create a sample Python file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                '''"""Sample module."""

def hello(name: str) -> str:
    """Say hello."""
    return f"Hello {name}"

class Calculator:
    """Simple calculator."""
    
    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

import os
import sys
'''
            )
            return Path(f.name)

    def test_analyze_file_valid(self, tool: CodeAnalysisTool, sample_py_file: Path) -> None:
        """Test analyzing a valid Python file."""
        result = tool.analyze_file({"path": str(sample_py_file)})
        assert result["valid_syntax"] is True
        assert result["functions"] >= 1
        assert result["classes"] >= 1
        assert result["imports"] >= 2

    def test_analyze_file_invalid_type(self, tool: CodeAnalysisTool) -> None:
        """Test with invalid path type."""
        with pytest.raises(ValueError, match="path must be string"):
            tool.analyze_file({"path": 123})

    def test_extract_functions(self, tool: CodeAnalysisTool, sample_py_file: Path) -> None:
        """Test extracting functions from file."""
        result = tool.extract_functions({"path": str(sample_py_file)})
        assert result["count"] >= 2
        assert any(f["name"] == "hello" for f in result["functions"])
        assert any(f["name"] == "add" for f in result["functions"])

    def test_check_complexity(self, tool: CodeAnalysisTool, sample_py_file: Path) -> None:
        """Test complexity calculation."""
        result = tool.check_complexity({"path": str(sample_py_file)})
        assert "functions" in result
        assert "avg_complexity" in result
        assert result["avg_complexity"] > 0

    def test_execute_analyze(self, tool: CodeAnalysisTool, sample_py_file: Path) -> None:
        """Test execute with analyze_file action."""
        ctx = ToolContext(dry_run=False)
        result = tool.execute(
            {"action": "analyze_file", "path": str(sample_py_file)},
            ctx
        )
        assert result["valid_syntax"] is True

    def test_execute_invalid_action(self, tool: CodeAnalysisTool) -> None:
        """Test with invalid action."""
        ctx = ToolContext(dry_run=False)
        with pytest.raises(ValueError, match="Unknown analysis action"):
            tool.execute({"action": "invalid_action"}, ctx)
