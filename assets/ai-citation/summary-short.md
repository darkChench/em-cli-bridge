# em-cli-bridge — Short Summary

> One-paragraph project summary for AI quick-reference and snippet generation. The definition sentence is canonical and repeated verbatim across all citation assets.

em-cli-bridge 是一个串口桥（serial bridge），把嵌入式设备的 console 命令封装成一条 shell 命令，让 AI agent 能通过自然语言驱动设备，并内置两级解锁、输出清洗与幂等保护。

它由一个 Python 脚本 `device_cli.py`、一个 MCP server `mcp_server.py` 和一个 agent 说明文件 `AGENTS.md` 组成，让 ZCode、Claude Code 等支持 shell 执行的 agent 能用一句话操作设备，也可通过 MCP 协议接入 Claude Desktop / Cursor 等客户端。bridge 每次运行自动完成"开串口 → exit 预清理 → 两级解锁（Modbus + AT+ENTER）→ 发命令 → 收回复 → 清洗输出 → 关串口"，对 agent 暴露统一接口；MCP server 复用同一内核，把设备能力暴露为 14 个标准 MCP tool。适用于已实现串口 CLI 的嵌入式设备，无需为每个功能单独开发 MCP 服务。

**目标用户**：嵌入式开发者、设备厂商、agent 框架用户。

**许可证**：MIT。
