from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()


# =========================
# CORE PATHS
# =========================

WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", Path.cwd())).resolve()

LOG_DIR = WORKSPACE_ROOT / "logs"
TMP_DIR = WORKSPACE_ROOT / "tmp"
CONFIG_DIR = WORKSPACE_ROOT / "config"

LOG_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# SYSTEM LIMITS
# =========================

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))

IGNORE_DIRS = set(
    os.getenv(
        "IGNORE_DIRS",
        ".git,__pycache__,node_modules,.venv,venv,dist,build"
    ).split(",")
)


# =========================
# EVENT / DEBUG FLAGS
# =========================

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
DRY_RUN_DEFAULT = os.getenv("DRY_RUN", "false").lower() == "true"


# =========================
# GITEA CONFIG
# =========================

GITEA_URL = os.getenv("GITEA_URL", "http://localhost:3000")
GITEA_TOKEN = os.getenv("GITEA_TOKEN", "")
GITEA_USER = os.getenv("GITEA_USER", "admin")
GITEA_API_BASE = f"{GITEA_URL}/api/v1"


# =========================
# GIT CONFIG
# =========================

GIT_AUTHOR_NAME = os.getenv("GIT_AUTHOR_NAME", "CXOS")
GIT_AUTHOR_EMAIL = os.getenv("GIT_AUTHOR_EMAIL", "cxos@local")


# =========================
# MCP / SERVER CONFIG
# =========================

SERVER_NAME = os.getenv("SERVER_NAME", "CXOS-MCP")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "5432"))