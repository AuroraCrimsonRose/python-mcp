from __future__ import annotations

from typing import Any
import requests

from core.tools.base import BaseTool, ToolContext
from core.tools.registry import registry
from core.events import bus
from core.config import GITEA_URL, GITEA_TOKEN
from core.subprocess import run_command


class GiteaTool(BaseTool):
    """Gitea repository management and API operations."""
    name = "gitea"
    description = "Gitea repository operations and management"

    def __init__(self):
        self.headers = {
            "Authorization": f"token {GITEA_TOKEN}",
            "Content-Type": "application/json"
        }

    def execute(
        self,
        payload: dict[str, Any],
        ctx: ToolContext
    ) -> dict[str, Any]:
        """Execute gitea action."""
        action = str(payload.get("action", "")).strip()

        bus.log(
            "GITEA",
            "gitea_execute",
            "INFO",
            {"action": action}
        )

        match action:
            case "create_repo":
                return self.create_repo(payload, ctx)
            case "list_repos":
                return self.list_repos(payload)
            case "get_repo":
                return self.get_repo(payload)
            case "create_file":
                return self.create_or_update_file(payload, ctx)
            case "update_file":
                return self.create_or_update_file(payload, ctx)
            case "get_file":
                return self.get_file(payload)
            case "git_push":
                return self.git_push(payload, ctx)
            case _:
                raise ValueError(f"Unknown gitea action: {action}")

    def create_repo(self, payload: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
        """Create a new repository on Gitea."""
        name = payload.get("name")
        private = payload.get("private", True)
        auto_init = payload.get("auto_init", True)

        if not isinstance(name, str):
            raise ValueError("name must be string")

        if ctx.dry_run:
            return {
                "dry_run": True,
                "name": name,
                "private": private,
                "message": "Would create repository (dry-run mode)"
            }

        url = f"{GITEA_URL}/api/v1/user/repos"
        payload_data = {
            "name": name,
            "private": private,
            "auto_init": auto_init
        }

        try:
            response = requests.post(url, json=payload_data, headers=self.headers)
            response.raise_for_status()
            return {
                "status": "success",
                "repo": response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "name": name
            }

    def list_repos(self, payload: dict[str, Any]) -> dict[str, Any]:
        """List repositories for the authenticated user."""
        url = f"{GITEA_URL}/api/v1/user/repos"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            repos = response.json()
            return {
                "status": "success",
                "repos": repos,
                "count": len(repos)
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def get_repo(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Get repository information."""
        owner = payload.get("owner")
        repo = payload.get("repo")

        if not isinstance(owner, str):
            raise ValueError("owner must be string")
        if not isinstance(repo, str):
            raise ValueError("repo must be string")

        url = f"{GITEA_URL}/api/v1/repos/{owner}/{repo}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return {
                "status": "success",
                "repo": response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "owner": owner,
                "repo": repo
            }

    def create_or_update_file(self, payload: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
        """Create or update a file in a repository."""
        owner = payload.get("owner")
        repo = payload.get("repo")
        path = payload.get("path")
        content = payload.get("content")
        message = payload.get("message")

        if not isinstance(owner, str):
            raise ValueError("owner must be string")
        if not isinstance(repo, str):
            raise ValueError("repo must be string")
        if not isinstance(path, str):
            raise ValueError("path must be string")
        if not isinstance(content, str):
            raise ValueError("content must be string")
        if not isinstance(message, str):
            raise ValueError("message must be string")

        if ctx.dry_run:
            return {
                "dry_run": True,
                "owner": owner,
                "repo": repo,
                "path": path,
                "message": "Would create/update file (dry-run mode)"
            }

        url = f"{GITEA_URL}/api/v1/repos/{owner}/{repo}/contents/{path}"
        payload_data = {
            "content": content,
            "message": message
        }

        try:
            response = requests.post(url, json=payload_data, headers=self.headers)
            response.raise_for_status()
            return {
                "status": "success",
                "path": path,
                "owner": owner,
                "repo": repo
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "path": path
            }

    def get_file(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Get file content from repository."""
        owner = payload.get("owner")
        repo = payload.get("repo")
        path = payload.get("path")

        if not isinstance(owner, str):
            raise ValueError("owner must be string")
        if not isinstance(repo, str):
            raise ValueError("repo must be string")
        if not isinstance(path, str):
            raise ValueError("path must be string")

        url = f"{GITEA_URL}/api/v1/repos/{owner}/{repo}/contents/{path}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return {
                "status": "success",
                "path": path,
                "content": response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": str(e),
                "path": path
            }

    def git_push(self, payload: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
        """Push local changes to repository."""
        repo_path = payload.get("repo_path")
        message = payload.get("message", "Auto-commit")

        if not isinstance(repo_path, str):
            raise ValueError("repo_path must be string")
        if not isinstance(message, str):
            raise ValueError("message must be string")

        if ctx.dry_run:
            return {
                "dry_run": True,
                "repo_path": repo_path,
                "message": "Would push changes (dry-run mode)"
            }

        cmds = [
            ["git", "-C", repo_path, "add", "."],
            ["git", "-C", repo_path, "commit", "-m", message],
            ["git", "-C", repo_path, "push"]
        ]

        results = []
        for cmd in cmds:
            result = run_command(cmd)
            results.append(result)
            if result.get("return_code") != 0:
                return {
                    "status": "error",
                    "error": result.get("stderr", "Unknown error"),
                    "command": " ".join(cmd)
                }

        return {
            "status": "success",
            "repo_path": repo_path,
            "message": message,
            "results": results
        }


registry.register(GiteaTool())
