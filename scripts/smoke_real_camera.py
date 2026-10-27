"""Real-device smoke test: start the server over stdio and call both tools against the attached camera."""

import asyncio
import json
import sys
from pathlib import Path

import numpy as np
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from logi_camera_mcp.camera import save_image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "captures" / "smoke"


def make_reference() -> Path:
    # A 16:9 frame with a white border, like a test-case reference picture.
    img = np.full((1080, 1920, 3), (180, 120, 40), np.uint8)
    img[:20], img[-20:], img[:, :20], img[:, -20:] = 255, 255, 255, 255
    path = OUT / "reference_16x9.png"
    save_image(img, path)
    return path


async def main() -> None:
    ref = make_reference()
    params = StdioServerParameters(command=sys.executable, args=["-m", "logi_camera_mcp.server"], cwd=str(ROOT))
    async with stdio_client(params) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        print("tools:", [t.name for t in (await s.list_tools()).tools])
        print("list_cameras:", (await s.call_tool("list_cameras", {})).content[0].text)
        res = await s.call_tool("capture_image", {"reference_path": str(ref), "save_dir": str(OUT)})
        if res.isError:
            raise SystemExit(f"capture_image failed: {res.content[0].text}")
        print("blocks:", [b.type for b in res.content])
        print("meta:", json.dumps(json.loads(res.content[-1].text), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
