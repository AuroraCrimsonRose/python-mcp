import requests
from core.config import GITEA_URL, GITEA_TOKEN
from core.logging_core import logger

HEADERS = {
    "Authorization": f"token {GITEA_TOKEN}",
    "Content-Type": "application/json"
}

def create_repo(name: str, private: bool = True):
    url = f"{GITEA_URL}/api/v1/user/repos"

    payload = {
        "name": name,
        "private": private,
        "auto_init": True
    }

    r = requests.post(url, json=payload, headers=HEADERS)

    logger.info(f"[GITEA] create_repo={name} status={r.status_code}")

    return r.json()

import subprocess
from core.subprocess import run_command

def git_push(repo_path: str, message: str):
    cmds = [
        ["git", "-C", repo_path, "add", "."],
        ["git", "-C", repo_path, "commit", "-m", message],
        ["git", "-C", repo_path, "push"]
    ]

    results = [run_command(c) for c in cmds]
    return results

def create_or_update_file(owner, repo, path, content, message):
    url = f"{GITEA_URL}/api/v1/repos/{owner}/{repo}/contents/{path}"

    payload = {
        "content": content.encode("utf-8").decode("utf-8"),
        "message": message
    }

    r = requests.post(url, json=payload, headers=HEADERS)

    logger.info(f"[GITEA] file={path} status={r.status_code}")

    return r.json()