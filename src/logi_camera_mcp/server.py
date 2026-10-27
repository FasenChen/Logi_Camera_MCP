import json
import os
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Image

from logi_camera_mcp.camera import capture_frame, list_devices, read_image, resolve_camera, save_image, to_jpeg

mcp = FastMCP("logi-camera")


@mcp.tool(structured_output=False)
def list_cameras() -> str:
    """List cameras attached to this PC. The Logi C920 shows up as "HD Pro Webcam C920"."""
    return json.dumps({"cameras": [{"index": i, "name": n} for i, n in enumerate(list_devices())]}, ensure_ascii=False)


@mcp.tool(structured_output=False)
def capture_image(camera: str | int | None = None, reference_path: str | None = None, save_dir: str | None = None) -> list:
    """Take one photo with the camera (default: the Logi camera) and return it.

    If reference_path is given, the reference image is returned first, then the photo, so you can compare them.
    When judging a TV picture against the reference: compare the aspect ratio of the area of the TV that actually
    shows picture (black bars do not count). Only distinguish ratios such as 16:9 vs 4:3; ignore content details,
    colour, brightness and glare.

    Args:
        camera: device index or part of its name (see list_cameras). Default: first Logi camera.
        reference_path: optional expected image from the test case.
        save_dir: where to save the photo. Default: env LOGI_CAMERA_SAVE_DIR, else ./captures.
    """
    # Validate the reference before opening the camera so a bad path fails fast.
    reference = read_image(reference_path) if reference_path else None
    if isinstance(camera, str):
        # Clients often send "" for an omitted optional arg; blank means default camera.
        camera = camera.strip() or None
    if isinstance(camera, str) and camera.isdigit():
        camera = int(camera)
    frame = capture_frame(resolve_camera(camera, list_devices()))

    now = datetime.now()
    out_dir = Path(save_dir or os.environ.get("LOGI_CAMERA_SAVE_DIR", "captures")).resolve()
    captured_path = out_dir / f"{now:%Y%m%d_%H%M%S_%f}.jpg"
    save_image(frame, captured_path)

    h, w = frame.shape[:2]
    meta = {
        "captured_path": str(captured_path),
        "reference_path": reference_path,
        "resolution": f"{w}x{h}",
        "timestamp": now.isoformat(timespec="seconds"),
    }
    content = [] if reference is None else [Image(data=to_jpeg(reference), format="jpeg")]
    return content + [Image(data=to_jpeg(frame), format="jpeg"), json.dumps(meta, ensure_ascii=False)]


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
