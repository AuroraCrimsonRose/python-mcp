from __future__ import annotations

import pytest
from pathlib import Path
import tempfile

from core.tools.base import ToolContext
from tools.search_code import SearchCodeTool


class TestSearchCodeTool:
    """Test code search tool."""

    @pytest.fixture
    def tool(self) -> SearchCodeTool:
        return SearchCodeTool()

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory with test files."""
        tmpdir = Path(tempfile.mkdtemp())
        
        (tmpdir / "test1.py").write_text("def hello():\n    print('hello')\n")
        (tmpdir / "test2.py").write_text("def world():\n    print('world')\n")
        (tmpdir / "data.txt").write_text("some data\n")
        
        yield tmpdir

    def test_search_literal(self, tool: SearchCodeTool, temp_dir: Path) -> None:
        """Test literal string search."""
        result = tool.search_literal({
            "pattern": "def",
            "path": str(temp_dir),
            "file_pattern": "*.py"
        })
        assert result["pattern"] == "def"
        assert result["matches_found"] >= 2

    def test_search_literal_no_matches(self, tool: SearchCodeTool, temp_dir: Path) -> None:
        """Test literal search with no matches."""
        result = tool.search_literal({
            "pattern": "nonexistent_pattern",
            "path": str(temp_dir),
            "file_pattern": "*.py"
        })
        assert result["matches_found"] == 0

    def test_search_regex(self, tool: SearchCodeTool, temp_dir: Path) -> None:
        """Test regex search."""
        result = tool.search_regex({
            "pattern": r"def \w+",
            "path": str(temp_dir),
            "file_pattern": "*.py"
        })
        assert result["matches_found"] >= 2

    def test_search_regex_invalid(self, tool: SearchCodeTool, temp_dir: Path) -> None:
        """Test regex search with invalid pattern."""
        with pytest.raises(ValueError, match="Invalid regex"):
            tool.search_regex({
                "pattern": "[invalid",
                "path": str(temp_dir)
            })

    def test_search_in_file(self, tool: SearchCodeTool, temp_dir: Path) -> None:
        """Test search within a specific file."""
        test_file = temp_dir / "test1.py"
        result = tool.search_in_file({
            "path": str(test_file),
            "pattern": "hello"
        })
        assert result["count"] >= 1

    def test_execute_literal(self, tool: SearchCodeTool, temp_dir: Path) -> None:
        """Test execute with literal action."""
        ctx = ToolContext(dry_run=False)
        result = tool.execute(
            {
                "action": "literal",
                "pattern": "def",
                "path": str(temp_dir)
            },
            ctx
        )
        assert result["matches_found"] >= 2

    def test_execute_invalid_action(self, tool: SearchCodeTool) -> None:
        """Test with invalid action."""
        ctx = ToolContext(dry_run=False)
        with pytest.raises(ValueError, match="Unknown search action"):
            tool.execute({"action": "invalid_action"}, ctx)
