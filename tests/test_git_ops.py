from __future__ import annotations

import pytest
from pathlib import Path
import tempfile
import subprocess

from core.tools.base import ToolContext
from tools.git_ops import GitOpsTool


class TestGitOpsTool:
    """Test git operations tool."""

    @pytest.fixture
    def tool(self) -> GitOpsTool:
        return GitOpsTool()

    @pytest.fixture
    def git_repo(self) -> Path:
        """Create a temporary git repository."""
        tmpdir = Path(tempfile.mkdtemp())
        
        subprocess.run(
            ["git", "init"],
            cwd=str(tmpdir),
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=str(tmpdir),
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=str(tmpdir),
            capture_output=True
        )
        
        (tmpdir / "test.txt").write_text("test content")
        subprocess.run(
            ["git", "add", "test.txt"],
            cwd=str(tmpdir),
            capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=str(tmpdir),
            capture_output=True
        )
        
        yield tmpdir

    def test_git_status(self, tool: GitOpsTool, git_repo: Path) -> None:
        """Test git status."""
        result = tool.git_status({"repo": str(git_repo)})
        assert "repo" in result
        assert "status_lines" in result
        assert "has_changes" in result

    def test_git_status_not_repo(self, tool: GitOpsTool) -> None:
        """Test git status on non-git directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="Not a git repository"):
                tool.git_status({"repo": tmpdir})

    def test_git_log(self, tool: GitOpsTool, git_repo: Path) -> None:
        """Test git log."""
        result = tool.git_log({"repo": str(git_repo), "limit": 5})
        assert "commits" in result
        assert "count" in result
        assert result["count"] >= 1

    def test_git_current_branch(self, tool: GitOpsTool, git_repo: Path) -> None:
        """Test getting current branch."""
        result = tool.git_current_branch({"repo": str(git_repo)})
        assert "branch" in result
        assert result["branch"] in ["master", "main"]

    def test_git_list_branches(self, tool: GitOpsTool, git_repo: Path) -> None:
        """Test listing branches."""
        result = tool.git_list_branches({"repo": str(git_repo)})
        assert "branches" in result
        assert "count" in result
        assert result["count"] >= 1

    def test_git_diff(self, tool: GitOpsTool, git_repo: Path) -> None:
        """Test git diff."""
        (git_repo / "test.txt").write_text("modified content")
        
        result = tool.git_diff({"repo": str(git_repo)})
        assert "repo" in result
        assert "diff" in result

    def test_execute_status(self, tool: GitOpsTool, git_repo: Path) -> None:
        """Test execute with status action."""
        ctx = ToolContext(dry_run=False)
        result = tool.execute(
            {"action": "status", "repo": str(git_repo)},
            ctx
        )
        assert "status_lines" in result

    def test_execute_invalid_action(self, tool: GitOpsTool, git_repo: Path) -> None:
        """Test with invalid action."""
        ctx = ToolContext(dry_run=False)
        with pytest.raises(ValueError, match="Unknown git action"):
            tool.execute(
                {"action": "invalid_action", "repo": str(git_repo)},
                ctx
            )
