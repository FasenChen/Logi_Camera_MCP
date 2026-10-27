from pathlib import Path

import cv2
import numpy as np

# On Windows the Logi C920 enumerates as "HD Pro Webcam C920", so match model names too.
DEFAULT_KEYWORDS = ("logi", "c9", "brio", "streamcam")


def list_devices() -> list[str]:
    from pygrabber.dshow_graph import FilterGraph

    return FilterGraph().get_input_devices()


def resolve_camera(camera: str | int | None, names: list[str]) -> int:
    if isinstance(camera, int):
        if 0 <= camera < len(names):
            return camera
    else:
        keywords = DEFAULT_KEYWORDS if camera is None else (camera.lower(),)
        for i, name in enumerate(names):
            if any(k in name.lower() for k in keywords):
                return i
    raise ValueError(f"No camera matches {camera!r}. Available: {names}")


def capture_frame(index: int, warmup: int = 10) -> np.ndarray:
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    try:
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open camera {index}")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        # Discard early frames while auto-exposure settles.
        for _ in range(warmup):
            cap.read()
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError(f"Camera {index} returned no frame (in use by another app?)")
        return frame
    finally:
        cap.release()


def read_image(path: str | Path) -> np.ndarray:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    # np.fromfile + imdecode handles non-ASCII paths, which cv2.imread does not on Windows.
    img = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Not a readable image: {path}")
    return img


def to_jpeg(img: np.ndarray, max_side: int = 1920) -> bytes:
    h, w = img.shape[:2]
    scale = max_side / max(h, w)
    if scale < 1:
        img = cv2.resize(img, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise ValueError("JPEG encoding failed")
    return buf.tobytes()


def save_image(img: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(path.suffix or ".jpg", img)
    if not ok:
        raise ValueError(f"Encoding failed for {path}")
    buf.tofile(path)
