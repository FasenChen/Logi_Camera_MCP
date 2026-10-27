# Logi Camera MCP

MCP server that gives a vision-capable agent eyes through a Logi webcam (Windows, DirectShow).
Built for TV test automation: photograph the TV and compare it with the test case's reference image,
e.g. 16:9 vs 4:3. The model does the judging; the server only takes pictures.

## Tools

| Tool | Input | Output |
|------|-------|--------|
| `list_cameras` | none | `{"cameras": [{"index": 0, "name": "..."}]}` |
| `capture_image` | `camera` (index or part of name, default first Logi: matches `logi`/`c9`/`brio`/`streamcam`), `reference_path` (optional), `save_dir` (optional) | reference image (if given), captured image, JSON `{captured_path, reference_path, resolution, timestamp}` |

Photos are saved to `save_dir`, else `LOGI_CAMERA_SAVE_DIR`, else `./captures`.
Note: the Logi C920 enumerates on Windows as `HD Pro Webcam C920`.

## Install

```powershell
uv sync
claude mcp add logi-camera -- uv --directory D:\Code\Logi_Camera_MCP run logi-camera-mcp
```

## Test

```powershell
uv run pytest                              # unit tests, no camera needed
uv run python scripts/smoke_real_camera.py # real camera over MCP stdio
```
