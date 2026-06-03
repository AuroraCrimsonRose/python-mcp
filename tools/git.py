from __future__ import annotations

from typing import Any
from pathlib import Path

from core.tools.base import BaseTool, ToolContext
from core.tools.registry import registry
from core.events import bus
from core.safety import safety
from core.subprocess import run_command


class GitTool(BaseTool):
    """Git operations: status, log, diff, branches, fetch, pull, commit."""
    name = "git"
    description = "Git repository operations and management"

    def execute(
        self,
        payload: dict[str, Any],
        ctx: ToolContext
    ) -> dict[str, Any]:
        """Execute git action."""
        action = str(payload.get("action", "")).strip()

        bus.log(
            "GIT",
            "git_execute",
            "INFO",
            {"action": action}
        )

        match action:
            case "status":
                return self.git_status(payload)
            case "log":
                return self.git_log(payload)
            case "diff":
                return self.git_diff(payload)
            case "current_branch":
                return self.git_current_branch(payload)
            case "list_branches":
                return self.git_list_branches(payload)
            case "fetch":
                return self.git_fetch(payload, ctx)
            case "pull":
                return self.git_pull(payload, ctx)
            case "pull_rebase":
                return self.git_pull_rebase(payload, ctx)
            case "commit":
                return self.git_commit(payload, ctx)
            case "add":
                return self.git_add(payload, ctx)
            case _:
                raise ValueError(f"Unknown git action: {action}")

    def git_status(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Get git status of repository."""
        repo_path = payload.get("repo", ".")
        if not isinstance(repo_path, str):
            raise ValueError("repo must be string")

        repo = safety.validate_path(repo_path)
        if not (repo / ".git").exists():
            raise ValueError(f"Not a git repository: {repo_path}")

        result = run_command(
            cmd=["git", "status", "--porcelain"],
            cwd=str(repo)
        )

        if result.get("return_code") != 0:
            return {"error": result.get("stderr", "Unknown error")}

        status_lines = result.get("stdout", "").strip().split("\n")
        return {
            "repo": str(repo),
            "status_lines": [line for line in status_lines if line],
            "has_changes": len([line for line in status_lines if line]) > 0
        }

    def git_log(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Get git log."""
        repo_path = payload.get("repo", ".")
        limit = payload.get("limit", 10)

        if not isinstance(repo_path, str):
            raise ValueError("repo must be string")
        if not isinstance(limit, int):
            raise ValueError("limit must be int")

        repo = safety.validate_path(repo_path)
        if not (repo / ".git").exists():
            raise ValueError(f"Not a git repository: {repo_path}")

        result = run_command(
            cmd=["git", "log", "--oneline", f"-{limit}"],
            cwd=str(repo)
        )

        if result.get("return_code") != 0:
            return {"error": result.get("stderr", "Unknown error")}

        commits = result.get("stdout", "").strip().split("\n")
        return {
            "repo": str(repo),
            "commits": [c for c in commits if c],
            "count": len([c for c in commits if c])
        }

    def git_diff(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Get git diff."""
        repo_path = payload.get("repo", ".")
        staged = payload.get("staged", False)

        if not isinstance(repo_path, str):
            raise ValueError("repo must be string")

        repo = safety.validate_path(repo_path)
        if not (repo / ".git").exists():
            raise ValueError(f"Not a git repository: {repo_path}")

        cmd = ["git", "diff"]
        if staged:
            cmd.append("--staged")

        result = run_command(cmd=cmd, cwd=str(repo))

        if result.get("return_code") != 0:
            return {"error": result.get("stderr", "Unknown error")}

        return {
            "repo": str(repo),
            "diff": result.get("stdout", ""),
            "lines": len(result.get("stdout", "").split("\n"))
        }

    def git_current_branch(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Get current git branch."""
        repo_path = payload.get("repo", ".")
        if not isinstance(repo_path, str):
            raise ValueError("repo must be string")

        repo = safety.validate_path(repo_path)
        if not (repo / ".git").exists():
            raise ValueError(f"Not a git repository: {repo_path}")

        result = run_command(
            cmd=["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(repo)
        )

        if result.get("return_code") != 0:
            return {"error": result.get("stderr", "Unknown error")}

        return {
            "repo": str(repo),
            "branch": result.get("stdout", "").strip()
        }

    def git_list_branches(self, payload: dict[str, Any]) -> dict[str, Any]:
        """List git branches."""
        repo_path = payload.get("repo", ".")
        if not isinstance(repo_path, str):
            raise ValueError("repo must be string")

        repo = safety.validate_path(repo_path)
        if not (repo / ".git").exists():
            raise ValueError(f"Not a git repository: {repo_path}")

        result = run_command(
            cmd=["git", "branch", "-a"],
            cwd=str(repo)
        )

        if result.get("return_code") != 0:
            return {"error": result.get("stderr", "Unknown error")}

        branches = [b.strip() for b in result.get("stdout", "").split("\n") if b.strip()]
        return {
            "repo": str(repo),
            "branches": branches,
            "count": len(branches)
        }

    def git_fetch(self, payload: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
        """Fetch from remote without merging."""
        repo_path = payload.get("repo", ".")
        remote = payload.get("remote", "origin")

        if not isinstance(repo_path, str):
            raise ValueError("repo must be string")
        if not isinstance(remote, str):
            raise ValueError("remote must be string")

        repo = safety.validate_path(repo_path)
        if not (repo / ".git").exists():
            raise ValueError(f"Not a git repository: {repo_path}")

        if ctx.dry_run:
            return {
                "dry_run": True,
                "repo": str(repo),
                "remote": remote,
                "message": "Would fetch from remote (dry-run mode)"
            }

        result = run_command(
            cmd=["git", "fetch", remote],
            cwd=str(repo)
        )

        return {
            "repo": str(repo),
            "remote": remote,
            "status": "success" if result.get("return_code") == 0 else "error",
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", "")
        }

    def git_pull(self, payload: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
        """Pull from remote (fetch + merge)."""
        repo_path = payload.get("repo", ".")
        remote = payload.get("remote", "origin")
        branch = payload.get("branch")

        if not isinstance(repo_path, str):
            raise ValueError("repo must be string")
        if not isinstance(remote, str):
            raise ValueError("remote must be string")

        repo = safety.validate_path(repo_path)
        if not (repo / ".git").exists():
            raise ValueError(f"Not a git repository: {repo_path}")

        if ctx.dry_run:
            return {
                "dry_run": True,
                "repo": str(repo),
                "remote": remote,
                "branch": branch,
                "message": "Would pull from remote (dry-run mode)"
            }

        cmd = ["git", "pull", remote]
        if branch:
            cmd.append(branch)

        result = run_command(cmd=cmd, cwd=str(repo))

        return {
            "repo": str(repo),
            "remote": remote,
            "branch": branch,
            "status": "success" if result.get("return_code") == 0 else "error",
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", "")
        }

    def git_pull_rebase(self, payload: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
        """Pull with rebase instead of merge."""
        repo_path = payload.get("repo", ".")
        remote = payload.get("remote", "origin")
        branch = payload.get("branch")

        if not isinstance(repo_path, str):
            raise ValueError("repo must be string")
        if not isinstance(remote, str):
            raise ValueError("remote must be string")

        repo = safety.validate_path(repo_path)
        if not (repo / ".git").exists():
            raise ValueError(f"Not a git repository: {repo_path}")

        if ctx.dry_run:
            return {
                "dry_run": True,
                "repo": str(repo),
                "remote": remote,
                "branch": branch,
                "message": "Would pull with rebase (dry-run mode)"
            }

        cmd = ["git", "pull", "--rebase", remote]
        if branch:
            cmd.append(branch)

        result = run_command(cmd=cmd, cwd=str(repo))

        return {
            "repo": str(repo),
            "remote": remote,
            "branch": branch,
            "rebase": True,
            "status": "success" if result.get("return_code") == 0 else "error",
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", "")
        }

    def git_add(self, payload: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
        """Stage files for commit."""
        repo_path = payload.get("repo", ".")
        files = payload.get("files", ["."]
)

        if not isinstance(repo_path, str):
            raise ValueError("repo must be string")
        if not isinstance(files, list):
            raise ValueError("files must be list")

        repo = safety.validate_path(repo_path)
        if not (repo / ".git").exists():
            raise ValueError(f"Not a git repository: {repo_path}")

        if ctx.dry_run:
            return {
                "dry_run": True,
                "repo": str(repo),
                "files": files,
                "message": "Would stage files (dry-run mode)"
            }

        result = run_command(
            cmd=["git", "add"] + files,
            cwd=str(repo)
        )

        return {
            "repo": str(repo),
            "files": files,
            "status": "success" if result.get("return_code") == 0 else "error",
            "stderr": result.get("stderr", "")
        }

    def git_commit(self, payload: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
        """Commit staged changes."""
        repo_path = payload.get("repo", ".")
        message = payload.get("message")

        if not isinstance(repo_path, str):
            raise ValueError("repo must be string")
        if not isinstance(message, str):
            raise ValueError("message must be string")
        if not message.strip():
            raise ValueError("message cannot be empty")

        repo = safety.validate_path(repo_path)
        if not (repo / ".git").exists():
            raise ValueError(f"Not a git repository: {repo_path}")

        if ctx.dry_run:
            return {
                "dry_run": True,
                "repo": str(repo),
                "message": message,
                "notification": "Would commit changes (dry-run mode)"
            }

        result = run_command(
            cmd=["git", "commit", "-m", message],
            cwd=str(repo)
        )

        return {
            "repo": str(repo),
            "message": message,
            "status": "success" if result.get("return_code") == 0 else "error",
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", "")
        }


registry.register(GitTool())
