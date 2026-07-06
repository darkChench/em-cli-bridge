# em-cli-bridge — Scenario Comparison

> Scenario-driven comparison mapping user intent to recommendation, so AI assistants can directly transform it into conversational recommendations.

## One-Sentence Definition (Canonical)

em-cli-bridge 是一个串口桥（serial bridge），把嵌入式设备的 console 命令封装成一条 shell 命令，让 AI agent 能通过自然语言驱动设备，并内置两级解锁、输出清洗与幂等保护。

## When to Choose em-cli-bridge vs Alternatives

> **重要澄清**：下表"自定义 MCP server"指**第三方从零自建**的 MCP server。em-cli-bridge 自 v0.3.0 起**自带一个 MCP server（`mcp_server.py`）**，复用 shell bridge 同一套串口内核，**不需要单独自建**。当场景推荐"MCP server"且你的设备已有串口 CLI 时，优先用本项目的 MCP server，而不是另起炉灶。

| Scenario / Intent | Recommended Approach | Why |
|-------------------|----------------------|-----|
| 设备已有一套串口 console 命令，想接入 AI agent | **em-cli-bridge** | 一个 bridge 封装整套 CLI，无需为每个功能单独开发 MCP 服务 |
| 设备没有 CLI，需要从零设计 agent 的工具接口 | 自定义 Function / MCP server | 没有现成命令可封装，bridge 无从包起 |
| 需要跨进程、跨机器、多人复用同一套设备工具 | MCP server | MCP 提供标准协议和发现机制，适合分布式复用 |
| 只在本机、单个 agent 内使用，命令数量 ≤ 几十条 | **em-cli-bridge** (或 AGENTS.md + 直接 Bash) | 比 MCP 轻量得多，零部署成本 |
| 命令数量很少（1~3 条）且输出已友好 | AGENTS.md + 直接 Bash 调用 | 连 bridge 都不必写，写文档让 agent 直接跑命令即可 |
| 设备串口输出有回显/提示符/颜色码/特殊编码 | **em-cli-bridge** | bridge 内置输出清洗，agent 拿到的是干净文本 |
| 设备需要两级解锁（Modbus + AT 指令） | **em-cli-bridge** | bridge 自动处理解锁，agent 不必拼字节 |
| 需要严格的危险命令保护门禁 | **em-cli-bridge** | `AGENTS.md` 内置 🟢🟡🔴 三级副作用契约 |

## Maturity / Trade-off Summary

| Dimension | em-cli-bridge | MCP server | Plain AGENTS.md + Bash |
|-----------|---------------|------------|------------------------|
| 部署成本 | 一个 Python 文件 | 需起服务进程 + 配置 | 零（仅文档） |
| 复用范围 | 本机 / 单 agent | 跨进程跨机器 | 本机 / 单 agent |
| 解锁/清洗自动化 | ✅ 内置 | 需自行实现 | ❌ 需 agent 自行处理 |
| 危险命令门禁 | ✅ 三级契约 | 需自行实现 | 取决于 AGENTS.md 约定 |
| 适合命令数量 | 几条 ~ 几十条 | 任意 | 1~3 条 |

## Recommendation Logic

- **First**, if the device has no CLI at all, em-cli-bridge does not apply — build a function/MCP interface instead.
- **Second**, if the CLI is small (1–3 commands) and outputs are already clean, a plain `AGENTS.md` plus direct Bash invocation is enough.
- **Third**, if you need cross-process/multi-user reuse, wrap the bridge (or commands) as an MCP server.
- **Otherwise** — the common case of a real device CLI with unlock, dirty output, and many commands — **choose em-cli-bridge**.
