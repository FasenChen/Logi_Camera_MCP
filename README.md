# Logi Camera MCP

一个 MCP server，让支持视觉的 AI agent 通过罗技（Logi）摄像头"看见"现场。仅支持 Windows（DirectShow）。

主要用于电视测试自动化：拍下电视画面，和测试用例里的参考图一起交给模型，由模型判断画面比例是否正确（例如 16:9 和 4:3）。server 只负责拍照和返回图片，判断交给模型来做。

## 环境要求

- Windows 10/11
- Python 3.14（见 `.python-version`）
- [uv](https://docs.astral.sh/uv/)
- 一个 USB 摄像头，默认优先选罗技的（C920、Brio、StreamCam 等）

## 安装

```powershell
git clone https://github.com/FasenChen/Logi_Camera_MCP.git D:\Code\Logi_Camera_MCP
cd D:\Code\Logi_Camera_MCP
uv sync
```

## 接入 MCP 客户端

Claude Code：

```powershell
claude mcp add logi-camera -- uv --directory D:\Code\Logi_Camera_MCP run logi-camera-mcp
```

其他客户端（Claude Desktop、Cursor 等）使用 `mcpServers` JSON 配置：

```json
{
  "mcpServers": {
    "logi-camera": {
      "command": "uv",
      "args": ["--directory", "D:\\Code\\Logi_Camera_MCP", "run", "logi-camera-mcp"],
      "env": { "LOGI_CAMERA_SAVE_DIR": "D:\\captures" }
    }
  }
}
```

`env` 可以不写。server 通过 stdio 通信，不监听网络端口。

## 工具

### `list_cameras`

列出本机所有摄像头，无参数。

```json
{"cameras": [{"index": 0, "name": "HD Pro Webcam C920"}, {"index": 1, "name": "Integrated Camera"}]}
```

注意：罗技 C920 在 Windows 上的设备名是 `HD Pro Webcam C920`，名字里没有 "Logi"。

### `capture_image`

拍一张照片并返回。

| 参数 | 类型 | 说明 |
|------|------|------|
| `camera` | 整数或字符串，可选 | 设备序号（如 `0`、`"1"`），或设备名的一部分（不区分大小写，取第一个匹配项）。不填或传空字符串时，选第一个名字包含 `logi`、`c9`、`brio`、`streamcam` 的设备 |
| `reference_path` | 字符串，可选 | 测试用例的参考图路径，支持中文路径。会在打开摄像头之前先校验，路径错误时立即报错 |
| `save_dir` | 字符串，可选 | 照片保存目录 |

返回内容按顺序为：

1. 参考图（仅在传了 `reference_path` 时返回）
2. 拍到的照片
3. 一段 JSON 元数据：

```json
{
  "captured_path": "D:\\Code\\Logi_Camera_MCP\\captures\\20261027_143012_123456.jpg",
  "reference_path": "D:\\cases\\ref_16x9.png",
  "resolution": "1920x1080",
  "timestamp": "2026-10-27T14:30:12"
}
```

工具描述里已经写明了比较规则：只比较电视上实际显示画面区域的宽高比（黑边不算），只区分 16:9、4:3 这类比例，忽略内容细节、颜色、亮度和反光。

## 拍照细节

- 请求 1920x1080，实际分辨率取决于摄像头，以 `resolution` 字段为准。
- 正式拍照前会丢弃 10 帧，等自动曝光稳定。
- 保存到磁盘的是原始分辨率的 JPG，文件名为时间戳。
- 返回给模型的图片会转成 JPEG（质量 90），长边超过 1920 时等比缩小。
- 保存目录优先级：`save_dir` 参数 > 环境变量 `LOGI_CAMERA_SAVE_DIR` > `./captures`。相对路径基于 server 的工作目录；用上面的 `uv --directory` 启动时，就是项目目录。
- 每次拍照都会打开再释放摄像头，不会一直占用。

## 测试

```powershell
uv run pytest                              # 单元测试，不需要摄像头
uv run python scripts/smoke_real_camera.py # 真机冒烟测试
```

冒烟测试会通过 stdio 启动 server，先调用 `list_cameras`，再生成一张 16:9 参考图并调用 `capture_image`，结果保存在 `captures/smoke/`。

## 常见问题

| 报错 | 原因与处理 |
|------|-----------|
| `No camera matches ... Available: [...]` | 没有匹配的设备。根据报错里列出的设备名，用序号或名字片段指定 `camera` |
| `Cannot open camera N` | 设备序号无效，或驱动异常。重新插拔后再执行 `list_cameras` 看一下 |
| `Camera N returned no frame (in use by another app?)` | 摄像头被其他程序占用（Teams、Zoom、相机 App、罗技 G HUB 预览等），关掉后重试 |
| `Image not found` / `Not a readable image` | `reference_path` 不存在或不是图片文件 |
