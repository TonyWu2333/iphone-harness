"""Load <repo>/.env and IPH_AGENT_WORKSPACE/.env into os.environ.

Called from the package __init__ so it runs before any module (admin, _ipc,
helpers, daemon) reads IPH_* settings at import time. Variables already set
in the real environment win.
"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_env():
    workspace = Path(os.environ.get("IPH_AGENT_WORKSPACE", REPO_ROOT / "agent-workspace")).expanduser()
    for p in (REPO_ROOT / ".env", workspace / ".env"):
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
