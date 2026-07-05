# MCP 客户端配置示例

把对应客户端配置文件里的 `mcpServers` 对象合并进你客户端的真实配置路径。

## 通用约定

- `command` 必须是能找到 `mcp_server.py` 的 Python 解释器。
  - 如果用了一键脚本建的 `.venv`，把 `command` 改成虚拟环境的 Python：
    - Windows: `"command": "D:\\04_AI_worksapce\\04_CLI\\.venv\\Scripts\\python.exe"`
    - Linux/macOS: `"command": "D:/04_AI_worksapce/04_CLI/.venv/bin/python"`
- `--port COM59` 改成你设备的实际串口号（设备管理器查看）。
- 路径里的反斜杠在 JSON 里要写双反斜杠 `\\`。

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
