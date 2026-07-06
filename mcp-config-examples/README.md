# MCP 客户端配置示例

把对应客户端配置文件里的 `mcpServers` 对象合并进你客户端的真实配置路径。

## 通用约定

- 配置文件里的 `<repo>`、`<COMx>`、`<python>` 是**占位符**，必须替换为你本机的实际值。
- `<python>` 是能找到 `mcp` 库的 Python 解释器。
  - 用系统 Python：直接填 `python`，或填完整路径如 `C:\\Users\\<用户名>\\AppData\\Local\\Programs\\Python\\Python311\\python.exe`
  - 用一键脚本建的 `.venv`：Windows 填 `<repo>\\.venv\\Scripts\\python.exe`；Linux/macOS 填 `<repo>/.venv/bin/python`
- `<COMx>` 改成你设备的实际串口号（Windows 设备管理器 → 端口(COM 和 LPT) 查看，如 COM59）。
- 路径里的反斜杠在 JSON 里要写双反斜杠 `\\`。
- 如果你直接在本仓库目录里打开客户端（Claude Code / Cursor / ZCode 等），**优先用根目录的 `.mcp.json`**（工作区级自动加载），无需手动合并下面这些示例。本目录示例仅用于客户端不在本仓库打开的场景。

## 各客户端配置文件路径

| 客户端 | 配置文件 |
|--------|---------|
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Claude Desktop (macOS) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Cursor | Settings → MCP，或项目级 `.cursor/mcp.json` |
| ZCode / 通用 | 工作区 `.mcp.json` 或用户 `settings.json` |

## 配置示例文件

- [`claude-desktop.json`](claude-desktop.json) — Claude Desktop
- [`cursor.json`](cursor.json) — Cursor
- [`zcode.json`](zcode.json) — ZCode / 通用 stdio 客户端

## 配置完成后

1. 重启客户端，让它加载新的 MCP server。
2. 在客户端里查看 MCP server 是否连上（通常会有状态指示）。
3. 用自然语言测试：问"查最新传感器数据"——agent 应自动调用 `q_sensor` tool。
4. 测试危险保护：问"重启设备"但不要确认——应看到 `confirm=true` 拦截提示。
