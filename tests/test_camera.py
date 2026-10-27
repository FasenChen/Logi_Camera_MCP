import cv2
import numpy as np
import pytest

from logi_camera_mcp.camera import read_image, resolve_camera, save_image, to_jpeg

NAMES = ["XiaoMi USB 2.0 Webcam", "HD Pro Webcam C920"]


def test_default_picks_logi_c920():
    assert resolve_camera(None, NAMES) == 1


def test_name_match_is_case_insensitive():
    assert resolve_camera("xiaomi", NAMES) == 0


def test_index_out_of_range():
    with pytest.raises(ValueError):
        resolve_camera(5, NAMES)


def test_unknown_name_lists_available_devices():
    with pytest.raises(ValueError, match="XiaoMi"):
        resolve_camera("nope", NAMES)


def _decode(data: bytes) -> np.ndarray:
    return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)


def test_to_jpeg_downscales_long_side():
    img = np.zeros((2160, 3840, 3), np.uint8)
    assert _decode(to_jpeg(img)).shape[:2] == (1080, 1920)


def test_to_jpeg_does_not_upscale():
    img = np.zeros((480, 640, 3), np.uint8)
    assert _decode(to_jpeg(img)).shape[:2] == (480, 640)


def test_save_and_read_non_ascii_path(tmp_path):
    img = np.full((90, 160, 3), 128, np.uint8)
    path = tmp_path / "中文" / "参考.png"
    save_image(img, path)
    assert read_image(path).shape == (90, 160, 3)


def test_read_missing_image(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_image(tmp_path / "missing.png")
