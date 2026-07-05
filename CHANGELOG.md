# Changelog

本文件记录 em-cli-bridge 的版本演进。版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.3.0] — 2026-07-05

### Added
- **MCP server**（`mcp_server.py`）：把设备能力暴露为 14 个标准 MCP tool（stdio 传输），复用 `device_cli.py` 内核，不重写串口逻辑。启动时开一次串口并解锁，后续 tool 调用复用长连接。
  - 14 个 tool：`q_sensor` / `sw_sensor` / `get_rtc` / `set_rtc` / `version` / `runtime` / `lfs_read` / `lfs_read_log` / `lfs_read_errno` / `lfs_log_info` / `lfs_errno_info` / `lfs_flush` / `lfs_format` / `reset`
  - 危险 tool（`lfs_format` / `reset`）需显式 `confirm=true`，**代码级硬保护**。
- **客户端配置示例**（`mcp-config-examples/`）：Claude Desktop / Cursor / ZCode 三种客户端 + 使用说明。
- README 新增"MCP server"章节，含两种方式对比表。
- faq.md 新增 Q11（shell vs MCP 怎么选）/ Q12（MCP 危险命令保护）。
- llms-full.txt 新增 MCP Server 章节。

### Changed
- 仓库结构图补充 `mcp_server.py` 和 `mcp-config-examples/`。

## [0.2.1] — 2026-07-05

### Added
- **一键环境搭建**：新增 `setup.bat`（Windows）/ `setup.sh`（Linux/macOS），克隆后运行一次自动完成"建虚拟环境 + 装依赖"，实现克隆即用。
- **依赖清单**：新增 `requirements.txt`（核心依赖 pyserial）和 `requirements-mcp.txt`（MCP server 可选依赖），把 MCP 依赖拆为可选，不强求所有用户安装。
- README 新增"快速开始"章节，提供一键脚本和手动安装两条路径。
- `.gitignore` 忽略 `.venv/`。

### Changed
- README 安装章节由"pip install pyserial"升级为"快速开始"，含虚拟环境激活说明。
- 仓库结构图补全新增文件。

## [0.2.0] — 2026-07-05

### Added
- **配置文件化**：新增 `device.json`（模板见 `device.json.example`）。解锁帧、文本编码、默认超时均可配置，换设备零改代码。
  - 加载优先级：`--config` 指定 > 工作目录 `device.json` > 用户目录 `~/.em-cli-bridge/device.json` > 内置默认值。
  - 无配置文件时自动用内置默认值（RDM 设备参数），**向后兼容**，现有用户升级无需任何配置。
- **命令超时参数化**：`--timeout <秒>` 指定读取超时；`cmd --long` 用 5s 长超时，适合 `lfs-read-log` / `lfs-read` 等大输出命令。
- **规范化退出码**：成功=0，通用错误=1，解锁失败=2，串口错误=3，超时=4。agent 可据此做条件分支。
- **`--version`** 查看版本。
- 新增 `CHANGELOG.md`。

### Changed
- `device_cli.py` 重构：配置加载、超时、退出码、版本号。
- README 与 `assets/ai-citation/*` 的"适配设备"说明由"修改四个常量"改为"修改 `device.json`"。

### Fixed
- 大输出命令（如读取大日志文件）因固定 1.5s 超时可能读不全 → 现可用 `--long` / `--timeout` 加长。

## [0.1.0] — 2026-07-05

### Added
- 首个可用版本。
- `device_cli.py`：串口桥主程序，封装开串口 → exit 预清理 → 两级解锁（Modbus + AT+ENTER）→ 发命令 → 收回复 → 清洗输出 → 关串口。
- 内置输出清洗：剥离命令回显、CLI 提示符（`[Press ENTER...]` / `>`）、ANSI 颜色码；GBK 解码解决 `℃` 乱码；解锁响应剥离回显前缀。
- `AGENTS.md`：agent 行为说明（命令清单、`qSensor` 字段含义、🟢🟡🔴 三级副作用契约、自然语言→命令映射）。
- 交互式串口选择 + 占用/失败友好提示重试。
- `llms.txt` + `assets/ai-citation/`：完整的 GEO/SEO AI 引用语料库（7 个文件）。
- README、LICENSE (MIT)、.gitignore。
