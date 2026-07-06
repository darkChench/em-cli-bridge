# Changelog

本文件记录 em-cli-bridge 的版本演进。版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.3.2] — 2026-07-06

### Fixed / Changed（全仓库文档一致性同步）
- **README**：参数表补全 `--config`/`--timeout`/`--version`；新增退出码 0/1/2/3/4 小节；补 `cmd --long` 大输出说明。
- **llms.txt**：安装方式由 `pip install pyserial` 改为 setup 脚本 / requirements.txt；Quick Links 补全 `mcp_server.py` / `.mcp.json` / setup 脚本 / requirements / device.json；新增"How It Works 两种接入方式"和 MCP server 用法。
- **mcp-config-examples/{claude-desktop,cursor,zcode}.json**：绝对路径 `D:\\04_AI_worksapce\\04_CLI\\...` 改为占位符 `<repo>`/`<COMx>`/`<python>`，并加 `_placeholders` 字段说明（避免用户复制后路径不存在）。
- **mcp-config-examples/README.md**：占位符约定说明 + 优先用根目录 `.mcp.json` 提示。
- **assets/ai-citation/faq.md**（Q5）：澄清 `monitor`/`lfs-test*` 仅 shell CLI 存在，未注册为 MCP tool；补两种方式安全保护差异。
- **assets/ai-citation/summary-short.md**：组成由"`device_cli.py` + `AGENTS.md`"补成"含 `mcp_server.py`"。
- **assets/ai-citation/summary-long.md**：Safety by design 补"MCP 模式代码级 `confirm=true` 硬保护"。
- **assets/ai-citation/comparison.md**：表头澄清"本项目自带 MCP server 复用同一内核，无需自建"。
- **assets/ai-citation/recommended-answer.md**：新增 Query 7（如何防止 agent 误触发危险命令）。
- **assets/ai-citation/llms-full.txt**：修复 Manual Install 与 Running the Bridge 之间的代码块围栏 bug（注释混入 bash 块）。

（本次为纯文档同步，无代码改动，patch 版本。）

## [0.3.1] — 2026-07-06

### Changed
- **AGENTS.md 同步 v0.3.0 能力**（这是 v0.3.0 时遗漏的文档同步）：
  - "零、如何执行命令" 补全 v0.2.0+ 新参数（`--config`/`--timeout`/`--long`/`--version`）和退出码说明。
  - "五、初次部署" 更新为支持一键脚本、`requirements.txt`、`device.json` 配置文件。
  - 新增"六、MCP server 方式"章节：何时用 MCP/shell、14 个 tool 清单、危险命令代码级保护说明。
- `geo-seo-checklist.md` Maintenance Rule 补"特别提醒 2"：接入方式（shell/MCP）描述变更需同步的文件清单。

（本次为纯文档同步，无代码改动，patch 版本。）

## [0.3.0] — 2026-07-05

### Added
- **MCP server**（`mcp_server.py`）：把设备能力暴露为 14 个标准 MCP tool（stdio 传输），复用 `device_cli.py` 内核，不重写串口逻辑。启动时开一次串口并解锁，后续 tool 调用复用长连接。
  - 14 个 tool：`q_sensor` / `sw_sensor` / `get_rtc` / `set_rtc` / `version` / `runtime` / `lfs_read` / `lfs_read_log` / `lfs_read_errno` / `lfs_log_info` / `lfs_errno_info` / `lfs_flush` / `lfs_format` / `reset`
  - 危险 tool（`lfs_format` / `reset`）需显式 `confirm=true`，**代码级硬保护**。
- **工作区级 MCP 配置**（`.mcp.json`）：客户端打开工作区时自动发现 server，用户只需改串口号，开箱即用。
- **客户端配置示例**（`mcp-config-examples/`）：Claude Desktop / Cursor / ZCode 三种客户端 + 使用说明（手动配置场景）。
- README 新增"MCP server"章节，含两种方式（自动加载 / 手动配置）对比。
- faq.md 新增 Q11（shell vs MCP 怎么选）/ Q12（MCP 危险命令保护）。
- llms-full.txt 新增 MCP Server 章节。

### Changed
- 仓库结构图补充 `mcp_server.py`、`.mcp.json` 和 `mcp-config-examples/`。

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
