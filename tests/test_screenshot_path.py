import asyncio
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"


class _FakeDriver:
    def get_screenshot_as_png(self):
        return b"\x89PNG fake"


class _FakeDaemon:
    driver = _FakeDriver()

    async def _drive(self, fn):
        return fn()


def _default_shot(monkeypatch, tmp_path, name, tmp_dir_set=False):
    sys.path.insert(0, str(SRC))
    from iphone_harness import _ipc, daemon

    monkeypatch.setattr(_ipc, "_TMP", tmp_path)
    monkeypatch.setattr(_ipc, "IPH_TMP_DIR", str(tmp_path) if tmp_dir_set else None)
    monkeypatch.setattr(daemon, "NAME", name)
    return asyncio.run(daemon._m_screenshot(_FakeDaemon(), {}))["path"]


def test_default_screenshot_path_is_per_name(monkeypatch, tmp_path):
    # Parallel daemons (one IPH_NAME per phone) must not share a screenshot file.
    a = _default_shot(monkeypatch, tmp_path, "phone1")
    b = _default_shot(monkeypatch, tmp_path, "phone2")
    assert a == str(tmp_path / "iph-phone1-shot.png")
    assert b == str(tmp_path / "iph-phone2-shot.png")
    assert Path(a).read_bytes() == Path(b).read_bytes() == b"\x89PNG fake"


def test_default_screenshot_path_with_iph_tmp_dir(monkeypatch, tmp_path):
    # IPH_TMP_DIR is already per-device; naming matches log_path().
    path = _default_shot(monkeypatch, tmp_path, "phone1", tmp_dir_set=True)
    assert path == str(tmp_path / "iph-shot.png")


def test_screenshot_sends_absolute_path(monkeypatch, tmp_path):
    sys.path.insert(0, str(SRC))
    from iphone_harness import helpers

    sent = {}

    def fake_send(req, timeout=120.0):
        sent.update(req)
        return {"result": {"path": req["params"].get("path", "/tmp/default.png")}}

    monkeypatch.setattr(helpers, "_send", fake_send)
    monkeypatch.chdir(tmp_path)
    assert helpers.screenshot("shot.png") == str(tmp_path / "shot.png")
    assert sent["params"] == {"path": str(tmp_path / "shot.png")}

    helpers.screenshot()
    assert sent["params"] == {}
