import os
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"


def _import_names(workspace):
    env = {k: v for k, v in os.environ.items() if not k.startswith("IPH_")}
    env.update(IPH_AGENT_WORKSPACE=str(workspace), PYTHONPATH=str(SRC))
    code = (
        "from iphone_harness import admin, helpers\n"
        "print(admin.NAME, helpers.NAME, admin.APPIUM_URL)\n"
    )
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True)
    return out.stdout.split()


def test_admin_and_helpers_see_workspace_env(tmp_path):
    # `run.py` imports admin before helpers; admin must still see .env values,
    # otherwise ensure_daemon() spawns a daemon under a different IPH_NAME than
    # the one helpers connect to.
    (tmp_path / ".env").write_text("IPH_NAME=phone2\nIPH_APPIUM_URL=http://127.0.0.1:4799\n")
    assert _import_names(tmp_path) == ["phone2", "phone2", "http://127.0.0.1:4799"]


def test_real_env_wins_over_dotenv(tmp_path):
    (tmp_path / ".env").write_text("IPH_NAME=phone2\n")
    env = {k: v for k, v in os.environ.items() if not k.startswith("IPH_")}
    env.update(IPH_AGENT_WORKSPACE=str(tmp_path), IPH_NAME="phone3", PYTHONPATH=str(SRC))
    out = subprocess.run(
        [sys.executable, "-c", "from iphone_harness import admin, helpers; print(admin.NAME, helpers.NAME)"],
        env=env, capture_output=True, text=True, check=True,
    )
    assert out.stdout.split() == ["phone3", "phone3"]
