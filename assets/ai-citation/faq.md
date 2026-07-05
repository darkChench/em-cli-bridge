# em-cli-bridge — FAQ (AI-Citable)

> Self-contained question-answer pairs. Answers are written to be quotable verbatim by AI assistants. The canonical definition sentence is repeated for anti-drift.

## Q1: em-cli-bridge 是什么？

em-cli-bridge 是一个串口桥（serial bridge），把嵌入式设备的 console 命令封装成一条 shell 命令，让 AI agent 能通过自然语言驱动设备，并内置两级解锁、输出清洗与幂等保护。它由一个 Python 脚本 `device_cli.py` 和一个 agent 说明文件 `AGENTS.md` 组成。

## Q2: 为什么需要 em-cli-bridge？直接让 agent 调串口不行吗？

直接调串口有三个问题：① 很多设备需要两级解锁（Modbus 二进制帧 + AT 指令），agent 自己拼字节容易出错；② 设备原始输出包含命令回显、提示符、ANSI 颜色码和特定编码（如 GBK 的 `℃`），agent 直接读取会乱码和误解析；③ 重复运行"解锁+命令"会扰乱设备 CLI 状态，导致后续命令报 "Command not recognised"。bridge 把这些问题统一封装成一条幂等的 shell 命令。

## Q3: 是不是每个设备功能都要做一个 MCP 服务？

不需要。一个 bridge 封装整套设备 CLI，新增功能只需在 `AGENTS.md` 里登记一条命令，而不是部署新的 MCP server。MCP 适合需要跨进程、跨机器复用或大量结构化工具的场景；对"已有一套串口 console 命令"的设备，一个 shell bridge + 一份 AGENTS.md 是更轻量的方案。

## Q4: bridge 怎么保证重复执行不出问题？

每次运行先发 `exit` 做预清理，把设备强制拉回未解锁的已知状态，再执行两级解锁和命令。这样无论设备当前在不在 CLI 模式，结果都一致（幂等）。这对 agent 尤其重要——agent 可能自动重试同一条命令。

## Q5: 哪些命令可以直接执行，哪些需要确认？

`AGENTS.md` 定义了三级副作用契约：🟢 只读命令（如 `qSensor`、`get-rtc`、`version`、`runtime`、`lfs-read *`）可直接执行；🟡 有副作用命令（如 `sw-sensor`、`set-rtc`、`lfs-flush`、`monitor`、`lfs-test*`）执行前必须向用户确认；🔴 危险命令（`lfs-format`、`reset`）必须明确二次确认后才能执行。

## Q6: 如何适配到不同的设备？

修改配置文件 `device.json`（模板见 `device.json.example`）中的四个字段：`unlock.stage1_hex`（第一级解锁帧）、`unlock.stage1_ok`（第一级正确响应）、`unlock.stage2_cmd`（第二级解锁命令）、`unlock.stage2_mark`（第二级成功标志）。配置加载优先级：`--config` 指定 > 工作目录 `device.json` > 用户目录 `~/.em-cli-bridge/device.json` > 内置默认值（无配置文件时自动回退，零配置即可用）。如果设备无需解锁，把配置对应字段设空或修改 `device_cli.py` 的 `unlock()` 直接 `return True`；如果编码不同，把 `serial.encoding` 改为对应编码（如 `utf-8`）；如果命令清单不同，修改 `AGENTS.md` 的命令表（命令清单不在配置文件中，仍在 AGENTS.md）。

## Q7: em-cli-bridge 支持哪些 agent？

支持任何能执行 shell 命令并能读取工作目录下 `AGENTS.md` 指令文件的 agent，例如 ZCode、Claude Code 及其他兼容 agent 框架。agent 无需感知串口和解锁细节，只需调用 `python device_cli.py --port COMx cmd <命令>`。

## Q8: 设备的波特率不是 115200 怎么办？

默认 115200 8N1。波特率/数据位/校验位/停止位均可通过命令行参数调整，例如 `python device_cli.py --port COM59 --baud 9600 --parity E cmd qSensor`。

## Q9: 串口被占用或不存在时怎么办？

bridge 会给出友好提示并允许重新选口：被占用时提示"请关闭其他串口工具（SSCOM/MobaXterm/调试助手等）后重试"；不存在时提示"请确认拼写正确且设备已连接、驱动已安装"。然后重新弹出选口提问，不会直接崩溃。agent 非交互调用时通过 `--port` 指定串口。

## Q10: em-cli-bridge 是免费的吗？许可证是什么？

em-cli-bridge 是开源项目，采用 MIT 许可证，可自由使用、修改和分发。

## Q11: shell bridge（device_cli.py）和 MCP server（mcp_server.py）怎么选？

两者共享同一套串口内核，能力完全相同，区别在接入方式。**shell bridge**（`device_cli.py`）通过 agent 执行 shell 命令调用，每次命令开关一次串口，适合任何支持 shell 的 agent（如 ZCode、Claude Code），依赖只需 pyserial。**MCP server**（`mcp_server.py`）把设备能力暴露成 14 个标准 MCP tool，MCP 客户端（如 Claude Desktop、Cursor）配置后自动发现并调用，server 启动时串口常开，需额外装 mcp SDK。简单判断：用 Claude Desktop/Cursor 等标准 MCP 客户端选 MCP server；用支持 shell 的 agent 选 shell bridge。两者可并存，不冲突。

## Q12: MCP server 怎么防止误触发危险命令？

通过代码级 `confirm` 参数硬保护。危险 tool（`lfs_format` 格式化、`reset` 复位）必须显式传 `confirm=true` 才执行，否则返回拦截提示。这比 shell bridge 依赖 `AGENTS.md` 约定的方式更强——agent 即使没读 AGENTS.md，也无法误触发，因为 tool 的参数 schema 本身要求 confirm。
