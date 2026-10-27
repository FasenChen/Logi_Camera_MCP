import asyncio
import json
from pathlib import Path

import numpy as np
import pytest
from mcp.server.fastmcp.exceptions import ToolError

from logi_camera_mcp import server
from logi_camera_mcp.camera import save_image

NAMES = ["XiaoMi USB 2.0 Webcam", "HD Pro Webcam C920"]


@pytest.fixture
def fake_camera(monkeypatch):
    calls = []

    def capture(index, warmup=10):
        calls.append(index)
        return np.zeros((1080, 1920, 3), np.uint8)

    monkeypatch.setattr(server, "list_devices", lambda: NAMES)
    monkeypatch.setattr(server, "capture_frame", capture)
    return calls


def call(name, args):
    return asyncio.run(server.mcp.call_tool(name, args))


def blocks(result):
    # FastMCP returns (content, structured) or just content depending on output mode.
    return result[0] if isinstance(result, tuple) else result


def test_list_cameras(fake_camera):
    text = blocks(call("list_cameras", {}))[0].text
    assert json.loads(text) == {"cameras": [{"index": 0, "name": NAMES[0]}, {"index": 1, "name": NAMES[1]}]}


def test_capture_with_reference_returns_both_images(fake_camera, tmp_path):
    ref = tmp_path / "参考" / "tc01_16x9.png"
    save_image(np.zeros((90, 160, 3), np.uint8), ref)
    out = blocks(call("capture_image", {"reference_path": str(ref), "save_dir": str(tmp_path / "out")}))
    assert [b.type for b in out] == ["image", "image", "text"]
    meta = json.loads(out[2].text)
    assert meta["resolution"] == "1920x1080"
    assert Path(meta["captured_path"]).is_file()
    assert fake_camera == [1]


def test_capture_without_reference_returns_one_image(fake_camera, tmp_path):
    out = blocks(call("capture_image", {"save_dir": str(tmp_path)}))
    assert [b.type for b in out] == ["image", "text"]


def test_numeric_string_camera_is_index(fake_camera, tmp_path):
    call("capture_image", {"camera": "0", "save_dir": str(tmp_path)})
    assert fake_camera == [0]


def test_blank_camera_uses_default_logi(fake_camera, tmp_path):
    call("capture_image", {"camera": " ", "save_dir": str(tmp_path)})
    assert fake_camera == [1]


def test_missing_reference_fails_before_capture(fake_camera, tmp_path):
    with pytest.raises(ToolError, match="not found"):
        call("capture_image", {"reference_path": str(tmp_path / "nope.png"), "save_dir": str(tmp_path)})
    assert fake_camera == []
