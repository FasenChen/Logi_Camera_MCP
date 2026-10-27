# Logi Camera MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An MCP server that lets a vision-capable agent photograph a TV through the Logi C920 and compare it with a test-case reference image (aspect ratio, e.g. 16:9 vs 4:3).

**Architecture:** Two tools. `list_cameras` lists DirectShow devices. `capture_image` grabs one frame and returns reference image + captured image + JSON metadata in one result; the model does the judging.

**Tech Stack:** Python 3.14, uv, `mcp==1.29.0` (FastMCP), `opencv-python 5.0.0.93`, `pygrabber 0.2`, pytest 9.1.1.

**Spec:** Design agreed in chat on 2026-10-27 (two tools, inputs/outputs as below).

## Global Constraints

- Windows only (DirectShow). Device index = position in `FilterGraph().get_input_devices()`, opened with `cv2.CAP_DSHOW`.
- On this machine the Logi camera is named `HD Pro Webcam C920` (no "Logi" in the name). Default match keywords: `("logi", "c9", "brio", "streamcam")`, case-insensitive.
- Images returned to the model: JPEG, long side ≤ 1920, quality 90.
- Discard 10 warm-up frames before capture (auto-exposure settles).
- Image paths may contain Chinese characters: read with `np.fromfile` + `cv2.imdecode`, write with `cv2.imencode` + `tofile`.
- Captures always saved; default dir `env LOGI_CAMERA_SAVE_DIR` else `./captures`.

## Review Focus

- `reference_path` missing/unreadable → clear error, no capture attempted.
- No camera matches the name → error listing available device names.
- Camera opens but returns no frame (busy in another app) → clear error, device released.
- Non-ASCII paths for reference and save_dir → work.
- Reference image smaller than 1920 → not upscaled.

---

### Task 1: camera module

**Files:**
- Create: `src/logi_camera_mcp/camera.py`
- Test: `tests/test_camera.py`

**Interfaces:**
- Produces:
  - `list_devices() -> list[str]`
  - `resolve_camera(camera: str | int | None, names: list[str]) -> int` — int → bounds-checked index; str → first name containing it (case-insensitive); None → first name containing any default keyword. Raises `ValueError` naming available devices.
  - `capture_frame(index: int, warmup: int = 10) -> np.ndarray` — requests 1920x1080, raises `RuntimeError` if no frame, always releases.
  - `read_image(path: str | Path) -> np.ndarray` — raises `FileNotFoundError`/`ValueError`.
  - `to_jpeg(img: np.ndarray, max_side: int = 1920) -> bytes` — downscale only.
  - `save_image(img: np.ndarray, path: Path) -> None`

- [ ] Step 1: tests — `resolve_camera` default picks `HD Pro Webcam C920` from `["XiaoMi USB 2.0 Webcam", "HD Pro Webcam C920"]` → 1; `"xiaomi"` → 0; `5` → ValueError; `"nope"` → ValueError containing `"XiaoMi"`; `to_jpeg` of 3840x2160 decodes to 1920x1080, of 640x480 stays 640x480; `read_image`/`save_image` round-trip under a `中文` dir; `read_image` missing → FileNotFoundError.
- [ ] Step 2: run `uv run pytest tests/test_camera.py -v` → FAIL (import error).
- [ ] Step 3: implement.
- [ ] Step 4: run → PASS.
- [ ] Step 5: commit `feat: camera helpers`.

### Task 2: MCP server

**Files:**
- Create: `src/logi_camera_mcp/server.py`; Modify: `pyproject.toml` (script `logi-camera-mcp = "logi_camera_mcp.server:main"`)
- Test: `tests/test_server.py`

**Interfaces:**
- Consumes: Task 1 functions.
- Produces tools:
  - `list_cameras()` → JSON text `{"cameras": [{"index": 0, "name": "..."}]}`
  - `capture_image(camera: str | int | None = None, reference_path: str | None = None, save_dir: str | None = None)` → `[Image(reference)?, Image(captured), text JSON {captured_path, reference_path, resolution, timestamp}]`. Reference is validated before the camera opens.
  - Tool description includes the judging hint: compare the aspect ratio of the area of the TV that actually shows picture (black bars excluded); only distinguish ratios like 16:9 vs 4:3; ignore content, colour, glare.

- [ ] Step 1: tests (monkeypatch `list_devices`, `capture_frame`) — via `mcp.call_tool`: with reference → 2 image blocks + text whose JSON has `resolution == "1920x1080"` and an existing `captured_path`; without reference → 1 image; missing reference → error and `capture_frame` never called.
- [ ] Step 2: run → FAIL.
- [ ] Step 3: implement.
- [ ] Step 4: run → PASS.
- [ ] Step 5: commit `feat: MCP server with list_cameras and capture_image`.

### Task 3: real-device check + README

**Files:**
- Create: `scripts/smoke_real_camera.py`, Modify: `README.md`

- [ ] Step 1: smoke script calls both tools through the MCP stdio client against the real C920, with a generated 16:9 reference image, prints metadata and saves output.
- [ ] Step 2: run it; inspect the captured photo.
- [ ] Step 3: README with install and Claude Code `mcp add` config.
- [ ] Step 4: commit `docs: README and real-camera smoke test`.
